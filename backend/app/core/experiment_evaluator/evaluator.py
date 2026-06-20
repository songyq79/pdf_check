"""
实验设计评审核心编排（单步 AI 评审，无需检索）。
返回统一结果 dict，供 report_generator 渲染 + Celery 双写。
"""
from __future__ import annotations

from typing import Callable, Optional

from loguru import logger

from app.core.ai_client import call_ai, parse_json_response
from app.core.experiment_evaluator import prompts


def _score(result: dict, key: str) -> int:
    v = result.get(key, 5)
    try:
        return max(1, min(10, int(round(float(v)))))
    except (TypeError, ValueError):
        return 5


_VERDICT_BANDS = [
    (8.0, "设计严谨"),
    (6.5, "基本可行，需完善"),
    (5.0, "存在明显缺陷"),
    (0.0, "需重新设计"),
]


def _verdict(overall: float) -> str:
    for threshold, label in _VERDICT_BANDS:
        if overall >= threshold:
            return label
    return "需重新设计"


async def review_experiment(
    plan_text: str,
    discipline: str = "",
    progress_cb: Optional[Callable[[int, str], None]] = None,
) -> dict:
    def _progress(pct: int, msg: str):
        if progress_cb:
            try:
                progress_cb(pct, msg)
            except Exception:
                pass
        logger.info(f"[exp.review] {pct}% {msg}")

    _progress(10, "解析实验方案")
    _progress(40, "对照结构性错误清单评审")
    raw = await call_ai(prompts.build_review_prompt(plan_text, discipline), timeout=60.0)
    result = parse_json_response(raw, dict(prompts.REVIEW_FALLBACK))

    sci = _score(result, "scientific_validity_score")
    comp = _score(result, "completeness_score")
    overall = round((sci + comp) / 2, 1)

    _progress(100, "完成")
    return {
        "discipline": discipline,
        "scores": {
            "scientific_validity": sci,
            "completeness": comp,
            "overall": overall,
            "verdict": _verdict(overall),
        },
        "analysis": {
            "scientific_validity": result.get("scientific_validity", ""),
            "completeness": result.get("completeness", ""),
        },
        "risks": result.get("risks") or [],
        "detected_flaws": result.get("detected_flaws") or [],
        "cost_estimate": result.get("cost_estimate", ""),
        "methodology_suggestions": result.get("methodology_suggestions") or [],
    }
