"""
论文校对 LLM 模块

提供三种检查能力，全部返回结构化 JSON：
1. proofread_text   - 错别字 + 标点检查
2. check_grammar    - 句子语法检查
3. check_paragraph  - 段落逻辑/连贯性检查（仅对较长段落）

所有函数都是异步的，失败时保守返回原文（不抛异常）。
"""

import asyncio
from typing import List, Tuple
from loguru import logger

from app.core.ai_client import call_ai, parse_json_response


# ─────────────────────────────────────────────────────────────
# Prompt 模板
# ─────────────────────────────────────────────────────────────

_PROOFREAD_PROMPT = """你是一位专业的学术论文校对专家。请对以下文本进行错别字和标点检查。

严格规则：
1. 只修正错别字（形近字、音近字替换错误）和中文标点错误
2. 不修改专业术语、人名、地名、英文单词
3. 不修改参考文献编号（如[1][2][1,2]）
4. 不修改数字、公式、单位
5. 【最高优先级】文中形如 __PROTxxxxxx_0000__ 的占位符必须原样保留，不得删除或修改
6. 不改变句子结构、语序、语义
7. 无错误时 corrected 与原文完全相同

以 JSON 格式返回（不要加 markdown 代码块）：
{{"corrected": "校对后文本", "changes": [["原文", "修正", "类型说明"]]}}

原文：{text}"""


_GRAMMAR_PROMPT = """你是一位专业的学术论文语法审校专家。请对以下文本进行语法检查。

检查范围：
1. 语法错误（主谓不一致、成分缺失、词序混乱）
2. 语义重复（同一意思重复表达）
3. 明显病句（逻辑不通）

严格限制：
- 只改正明确的语法错误，不进行文风优化
- 不修改专业术语、数字、引用标注
- 【最高优先级】文中形如 __PROTxxxxxx_0000__ 的占位符必须原样保留，不得删除或修改
- 修改幅度尽量小，保持原意
- 无语法问题时 corrected 与原文完全相同

以 JSON 格式返回（不要加 markdown 代码块）：
{{"corrected": "修正后文本", "changes": [["原文片段", "修正片段", "语法问题说明"]]}}

原文：{text}"""


_PARAGRAPH_PROMPT = """你是一位专业的学术论文审校专家。请检查以下段落的逻辑连贯性和表达完整性。

检查范围：
1. 段落内句子之间逻辑跳跃或断层
2. 前后指代不清（代词指向模糊）
3. 段落内部明显矛盾

严格限制：
- 只标注问题，不对文本进行大幅重写
- 修改范围仅限于能用少量词语解决的问题
- 保持学术写作风格
- 不修改专业术语、数字、引用
- 【最高优先级】文中形如 __PROTxxxxxx_0000__ 的占位符必须原样保留，不得删除或修改
- 无问题时 corrected 与原文完全相同

以 JSON 格式返回（不要加 markdown 代码块）：
{{"corrected": "修正后文本", "changes": [["原文片段", "修正片段", "问题说明"]], "issues": ["发现的问题摘要"]}}

段落原文：{text}"""


_FULL_PROMPT = """你是专业学术论文校对专家，请一次性完成以下三类检查：
1. 错别字和标点（形近字、音近字、中文标点错误）
2. 语法问题（主谓不一致、成分缺失、语义重复、明显病句）
3. 段落逻辑（逻辑跳跃、指代不清、段落内矛盾，仅超80字段落需检查）

严格规则：
- 不修改专业术语、人名、地名、英文单词、数字、公式、单位、参考文献编号
- 【最高优先级】文中形如 __PROTxxxxxx_0000__ 的占位符必须原样保留，不得删除或修改
- 只改正明确错误，不进行文风优化，修改幅度尽量小
- 无问题时 corrected 与原文完全相同

以 JSON 格式返回（不要加 markdown 代码块）：
{{"corrected": "修正后文本", "changes": [["原文片段", "修正片段", "错别字/标点|语法|段落逻辑"]]}}

原文：{text}"""


# ─────────────────────────────────────────────────────────────
# 内部：单次合并调用
# ─────────────────────────────────────────────────────────────

async def _full_check_once(text: str) -> Tuple[str, list]:
    """一次 AI 调用完成三层检查，内部使用。"""
    prompt = _FULL_PROMPT.format(text=text)
    try:
        raw    = await call_ai(prompt)
        result = parse_json_response(raw, fallback={"corrected": text, "changes": []})
        corrected = result.get("corrected", text) or text
        changes   = result.get("changes", [])
        return corrected, changes
    except Exception as e:
        logger.error(f"[full_check] AI 失败，返回原文: {e}")
        return text, []


# ─────────────────────────────────────────────────────────────
# 核心函数（保持原有签名）
# ─────────────────────────────────────────────────────────────

async def proofread_text(text: str) -> Tuple[str, list]:
    """
    错别字 + 标点检查。
    Returns: (校对后文本, 修改列表)
    """
    prompt = _PROOFREAD_PROMPT.format(text=text)
    try:
        raw    = await call_ai(prompt)
        result = parse_json_response(raw, fallback={"corrected": text, "changes": []})
        corrected = result.get("corrected", text) or text
        changes   = result.get("changes", [])
        if changes:
            logger.info(f"[spell] 发现 {len(changes)} 处错别字/标点: {changes}")
        return corrected, changes
    except Exception as e:
        logger.error(f"[spell] AI 失败，返回原文: {e}")
        return text, []


async def check_grammar(text: str) -> Tuple[str, list]:
    """
    语法检查。
    Returns: (修正后文本, 修改列表)
    """
    prompt = _GRAMMAR_PROMPT.format(text=text)
    try:
        raw    = await call_ai(prompt)
        result = parse_json_response(raw, fallback={"corrected": text, "changes": []})
        corrected = result.get("corrected", text) or text
        changes   = result.get("changes", [])
        if changes:
            logger.info(f"[grammar] 发现 {len(changes)} 处语法问题: {changes}")
        return corrected, changes
    except Exception as e:
        logger.error(f"[grammar] AI 失败，返回原文: {e}")
        return text, []


async def check_paragraph_logic(text: str) -> Tuple[str, list]:
    """
    段落逻辑检查（仅对 > 80 字的段落有意义）。
    Returns: (修正后文本, 问题列表)
    """
    if len(text) < 80:
        return text, []

    prompt = _PARAGRAPH_PROMPT.format(text=text)
    try:
        raw    = await call_ai(prompt)
        result = parse_json_response(raw, fallback={"corrected": text, "changes": [], "issues": []})
        corrected = result.get("corrected", text) or text
        issues    = result.get("issues", [])
        changes   = result.get("changes", [])
        if issues:
            logger.info(f"[paragraph] 发现段落问题: {issues}")
        return corrected, changes
    except Exception as e:
        logger.error(f"[paragraph] AI 失败，返回原文: {e}")
        return text, []


async def full_proofread(text: str) -> Tuple[str, list]:
    """
    完整校对：三层检查合并为一次 AI 调用，提升速度。
    返回合并后的修正文本和所有修改记录。
    """
    corrected, changes = await _full_check_once(text)

    all_changes = []
    for c in changes:
        # 兼容原有格式：每条 change 末尾追加大类标签
        if len(c) >= 3:
            all_changes.append(c)
        else:
            all_changes.append(c + ["校对"])

    if all_changes:
        logger.info(f"[full_proofread] 共发现 {len(all_changes)} 处问题: {all_changes}")

    return corrected, all_changes


# ─────────────────────────────────────────────────────────────
# 批量并发校对
# ─────────────────────────────────────────────────────────────

async def batch_proofread(
    chunks: List[str],
    concurrency: int = 5,
) -> List[Tuple[str, list]]:
    """
    并发校对多个文本块（错别字 + 标点，不含语法/段落，适合表格单元格等短文本）。
    """
    sem = asyncio.Semaphore(concurrency)

    async def _limited(chunk: str) -> Tuple[str, list]:
        async with sem:
            return await proofread_text(chunk)

    return list(await asyncio.gather(*[_limited(c) for c in chunks]))