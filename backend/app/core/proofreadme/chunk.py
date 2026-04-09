"""
文本分块与保护词处理

功能：
- 保护不应被 AI 修改的内容（公式、数字、引用、缩写等）
- 按语义句子边界分块，避免破坏语义

Bug 修复记录：
- [fix1] 增加对格式空格（全角空格 \u3000、连续半角空格）的保护，
         避免 AI 把标题字间距"摘  要"、"前  言"中的空格当错误删掉
- [fix2] 参考文献引用保护改为匹配前置空格，防止 ' [1]' 中的空格被误删
- [fix3] protect_terms 替换后对占位符周围的单个空格做二次保护，
         防止 AI 把 '__PROT__ 欧盟' 中的空格当多余空格删掉
"""

import re
import uuid
from typing import Tuple

# ─────────────────────────────────────────────────────────────
# 保护模式（按优先级从高到低排列）
# ─────────────────────────────────────────────────────────────
PROTECT_PATTERNS = [
    r'\$\$[\s\S]+?\$\$',                           # LaTeX 块公式
    r'\$[^$\n]+?\$',                                # LaTeX 行内公式
    # [fix2] 引用前的空格也一起保护，避免 ' [1]' 中空格被误删
    r'[ \t]*\[\d+(?:[,，]\d+)*\]',                  # 参考文献编号 [1] [1,2]（含前置空格）
    r'[ \t]*\[[\d\s,，\-–]+\]',                     # 参考文献范围 [1-3]（含前置空格）
    r'https?://\S+',                                # URL
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # 邮箱
    r'(?<![一-龥])[A-Za-z]{1}[A-Za-z0-9_\-\.]{1,}(?![一-龥])',  # 英文单词/缩写
    r'\d+\.?\d*\s*%',                               # 百分比
    r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}',            # 日期
    r'\d+\.?\d*\s*(?:mm|cm|m|km|kg|g|mg|L|ml|℃|°C|Hz|MHz|GHz|px|pt|em)',  # 带单位数字
    r'\d+(?:\.\d+)?',                               # 纯数字
    # [fix1] 保护格式空格，防止标题字间距被 AI 当错误删除
    '\u3000+',                                     # 全角空格（单个或连续）
    r' {2,}',                                       # 连续2个及以上半角空格
]


def protect_terms(text: str) -> Tuple[str, dict]:
    """
    提取并保护不应被校对的内容。
    Returns: (替换占位符后的文本, {占位符: 原始内容} 映射)
    """
    all_matches = []
    for pat in PROTECT_PATTERNS:
        for match in re.finditer(pat, text):
            all_matches.append((match.start(), match.end(), match.group()))

    # 按起始位置升序，同位置优先保留更长的匹配
    all_matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))

    # 贪心去除重叠区间
    non_overlapping = []
    last_end = 0
    for start, end, value in all_matches:
        if start >= last_end:
            non_overlapping.append((start, end, value))
            last_end = end

    # 分配占位符（加随机盐，避免与原文冲突）
    salt = uuid.uuid4().hex[:6]
    protected: dict = {}
    tokens = []
    for i, (start, end, value) in enumerate(non_overlapping):
        token = f"__PROT{salt}_{i:04d}__"
        protected[token] = value
        tokens.append((start, end, token))

    # 用列表收集片段后 join，避免字符串反复拼接的 O(n²) 开销
    parts = []
    prev = 0
    for start, end, token in tokens:
        parts.append(text[prev:start])
        parts.append(token)
        prev = end
    parts.append(text[prev:])
    result = "".join(parts)

    # [fix3] 二次保护：把占位符紧邻的单个空格并入占位符，防止 AI 误删
    # 匹配 token后紧跟单个空格（后面不是空格，避免与 ' {2,}' 重叠）
    def _merge_trailing(m):
        tok = m.group(1)
        new_tok = tok[:-2] + "T__"   # 把末尾 __ 换成 T__
        protected[new_tok] = protected[tok] + " "
        return new_tok

    # 匹配 单个空格后紧跟token（前面不是空格）
    def _merge_leading(m):
        tok = m.group(1)
        new_tok = "__L" + tok[2:]    # 把开头 __ 换成 __L
        protected[new_tok] = " " + protected[tok]
        return new_tok

    result = re.sub(r'(__PROT[0-9a-f]{6}_\d{4}__) (?! )', _merge_trailing, result)
    result = re.sub(r'(?<! ) (__PROT[0-9a-f]{6}_\d{4}(?:T)?__)', _merge_leading, result)

    return result, protected


def restore_terms(text: str, protected: dict) -> str:
    """还原保护词"""
    for token, original in protected.items():
        text = text.replace(token, original)
    return text


def paginate_chunks(text: str, max_len: int = 400) -> list:
    """
    按句子语义边界分块，保留语义完整性。
    """
    # 段落级别先按空行切分，再在段落内按句末标点切分
    paragraphs = re.split(r'\n{2,}', text)
    all_sentences = []
    for para in paragraphs:
        sentences = re.split(r'(?<=[。！？；…])', para)
        all_sentences.extend(s for s in sentences if s.strip())

    chunks, buf = [], ""
    for s in all_sentences:
        if len(s) > max_len:
            # 先把 buf 已有内容入队
            if buf.strip():
                chunks.append(buf.strip())
                buf = ""
            # 单句超长，按逗号进一步切
            sub = re.split(r'(?<=[，,、：:])', s)
            for seg in sub:
                # 单个分段仍超长时强制硬切
                while len(seg) > max_len:
                    chunks.append(seg[:max_len])
                    seg = seg[max_len:]
                if len(buf) + len(seg) > max_len and buf:
                    chunks.append(buf.strip())
                    buf = seg
                else:
                    buf += seg
        elif len(buf) + len(s) > max_len and buf:
            chunks.append(buf.strip())
            buf = s
        else:
            buf += s

    if buf.strip():
        chunks.append(buf.strip())

    return chunks if chunks else [text]
