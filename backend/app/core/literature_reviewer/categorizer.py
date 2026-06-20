"""
文献分类聚合（call_ai → JSON）。
"""
from __future__ import annotations

from typing import List

from app.core.ai_client import call_ai, parse_json_response
from app.core.literature_reviewer import prompts


async def categorize(papers: List[dict], discipline: str = "",
                     paper_type: str = "humanities") -> dict:
    """按研究主题聚类并识别研究空白。失败返回 fallback。"""
    prompt = prompts.build_categorize_prompt(papers, discipline, paper_type)
    raw = await call_ai(prompt, timeout=40.0)
    return parse_json_response(raw, dict(prompts.CATEGORIZE_FALLBACK))
