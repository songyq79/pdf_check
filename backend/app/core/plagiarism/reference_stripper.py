"""
参考文献剥离(精度增强 #1)
- strip_references:删除 References / Bibliography / Works Cited / 参考文献 节到文末
- strip_inline_citations:删除正文里 [12] / [12,15] / [12-18] / (Smith et al., 2020) / (Smith, 2020; Jones, 2021)

用户自己引用被误判为抄袭是英文查重最大假阳性来源。预处理阶段一次性剥离。
"""
from __future__ import annotations

import re

# References 节锚点 — 独占一行、大小写不敏感
_REF_HEADER_RE = re.compile(
    r"(?im)^\s*(references?|bibliography|works\s+cited|参考文献|reference\s+list)\s*$"
)

# Fallback：PDF提取文本可能没有换行，匹配 "References" 紧跟 [1] 的模式
_REF_HEADER_INLINE_RE = re.compile(
    r"(?i)\b(References?|Bibliography|Works\s+Cited|参考文献)\s{0,10}"
    r"(?:\n\s*)?(?=\[\s*1\s*\]|\b1\s*[\.\)])"
)

# [12] / [12, 15] / [12-18]
_BRACKET_CITE_RE = re.compile(r"\[\s*\d+(?:\s*[-,–;]\s*\d+)*\s*\]")

# (Smith, 2020) / (Smith et al., 2020) / (Smith & Jones 2020) / (Smith, 2020; Jones, 2021)
# 作者名含大写首字母;年份四位数字 19xx/20xx
_AUTHOR_PART = (
    r"[A-Z][A-Za-z'`\-]+"
    r"(?:\s+et\s+al\.?)?"
    r"(?:\s+(?:&|and)\s+[A-Z][A-Za-z'`\-]+)?"
)
_CITE_UNIT = (
    rf"{_AUTHOR_PART}"
    r"(?:,\s*|\s+)(?:19|20)\d{2}[a-z]?"
)
_PAREN_CITE_RE = re.compile(
    rf"\(\s*{_CITE_UNIT}(?:\s*;\s*{_CITE_UNIT})*\s*\)"
)


def strip_references(text: str) -> str:
    """删除 References 节到文末,保留正文。"""
    if not text:
        return text
    m = _REF_HEADER_RE.search(text)
    if m:
        return text[:m.start()].rstrip()
    # Fallback：PDF提取文本中 "References" 不在独立行时
    m2 = _REF_HEADER_INLINE_RE.search(text)
    if m2:
        return text[:m2.start()].rstrip()
    return text


def strip_inline_citations(text: str) -> str:
    """删除正文引文标注,保留句子主干。"""
    if not text:
        return text
    text = _BRACKET_CITE_RE.sub("", text)
    text = _PAREN_CITE_RE.sub("", text)
    # 清理引文剥离后残留的双空格
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    return text


def preprocess_english(text: str) -> str:
    """组合:剥离参考文献节 + 去引文标注。"""
    return strip_inline_citations(strip_references(text))
