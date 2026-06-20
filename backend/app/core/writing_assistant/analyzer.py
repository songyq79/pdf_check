"""
写作辅助 — 单段分析（同步语义，供实时 API 调用）。
失败保守返回空建议（不抛异常，不阻塞编辑器）。
"""
from __future__ import annotations

from loguru import logger

from app.core.ai_client import call_ai, parse_json_response
from app.core.writing_assistant import prompts


async def analyze_paragraph(paragraph: str, paper_type: str = "humanities") -> dict:
    """分析单个段落，返回四维建议 dict。"""
    def _empty() -> dict:
        out = dict(prompts.WRITING_CHECK_FALLBACK)
        out["issue_count"] = 0
        return out

    text = (paragraph or "").strip()
    if not text:
        return _empty()
    prompt = prompts.build_writing_check_prompt(text, paper_type)
    try:
        raw = await call_ai(prompt, timeout=20.0)
        result = parse_json_response(raw, dict(prompts.WRITING_CHECK_FALLBACK))
    except Exception as e:
        logger.warning(f"[writing] 分析失败，返回空建议: {e}")
        return _empty()

    # 规整：确保四个维度都是 list，统计问题数
    out = {
        "grammar": result.get("grammar") or [],
        "style": result.get("style") or [],
        "logic": result.get("logic") or [],
        "argument": result.get("argument") or [],
        "overall": result.get("overall", ""),
    }
    out["issue_count"] = sum(len(out[k]) for k in ("grammar", "style", "logic", "argument"))
    return out
