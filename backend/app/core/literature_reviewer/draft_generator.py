"""
文献综述初稿生成（call_ai → JSON）。
"""
from __future__ import annotations

from typing import List

from app.core.ai_client import call_ai, parse_json_response
from app.core.literature_reviewer import prompts


async def generate_draft(categorization: dict, papers: List[dict], topic: str = "",
                         discipline: str = "", paper_type: str = "humanities") -> dict:
    """基于分类与文献生成综述初稿。失败返回 fallback。"""
    prompt = prompts.build_draft_prompt(categorization, papers, topic, discipline, paper_type)
    raw = await call_ai(prompt, timeout=60.0)
    return parse_json_response(raw, dict(prompts.DRAFT_FALLBACK))
