"""
选题评估核心编排（三步）：
  ① call_ai 解析选题 → 关键词 + 检索 query
  ② aggregator 检索真实文献（RAG 防幻觉）
  ③ call_ai 基于真实文献评估 → 三维评分 JSON
返回统一结果 dict，供 report_generator 渲染 + Celery 双写。
"""
from __future__ import annotations

from typing import Callable, List, Optional

from loguru import logger

from app.core.ai_client import call_ai, parse_json_response
from app.core.topic_evaluator import prompts
from app.core.topic_evaluator.literature_searcher import LiteratureSearcher


def _paper_to_dict(p) -> dict:
    """CandidatePaper → 可序列化 dict（用于结果落库/前端）。"""
    g = (lambda k: p.get(k) if isinstance(p, dict) else getattr(p, k, None))
    return {
        "title": g("title") or "",
        "authors": g("authors") or [],
        "year": g("year"),
        "doi": g("doi"),
        "url": g("url"),
        "abstract": (g("abstract") or "")[:500],
        "source": g("source_name"),
    }


_VERDICT_BANDS = [
    (8.0, "高度可行"),
    (6.5, "较可行"),
    (5.0, "可行但需打磨"),
    (0.0, "需重新斟酌"),
]


def _verdict(overall: float) -> str:
    for threshold, label in _VERDICT_BANDS:
        if overall >= threshold:
            return label
    return "需重新斟酌"


async def evaluate_topic(
    question: str,
    description: str = "",
    discipline: str = "",
    degree_level: str = "",
    paper_type: str = "humanities",
    progress_cb: Optional[Callable[[int, str], None]] = None,
) -> dict:
    """
    执行选题评估三步流程。
    progress_cb(percent, message): 可选进度回调（Loop 2 的 Celery 任务用）。
    """
    def _progress(pct: int, msg: str):
        if progress_cb:
            try:
                progress_cb(pct, msg)
            except Exception:
                pass
        logger.info(f"[topic.eval] {pct}% {msg}")

    # ── Step 1：解析选题 ──
    _progress(5, "解析选题核心")
    raw1 = await call_ai(prompts.build_topic_extraction_prompt(
        question, description, discipline, degree_level))
    parsed = parse_json_response(raw1, dict(prompts.EXTRACTION_FALLBACK))
    keywords: List[str] = parsed.get("related_keywords") or []
    queries: List[str] = parsed.get("search_queries") or []
    if not queries:
        queries = [question] if question else keywords[:3]

    # ── Step 2：检索真实文献 ──
    _progress(45, "检索相关文献")
    papers = await LiteratureSearcher().search(queries)
    papers_dict = [_paper_to_dict(p) for p in papers]

    # ── Step 3：RAG 评估 ──
    _progress(70, "生成评估报告")
    raw2 = await call_ai(prompts.build_evaluation_prompt(
        question, description, discipline, degree_level, papers, paper_type))
    result = parse_json_response(raw2, dict(prompts.EVALUATION_FALLBACK))

    # ── 汇总 ──
    def _score(k: str) -> int:
        v = result.get(k, 5)
        try:
            return max(1, min(10, int(round(float(v)))))
        except (TypeError, ValueError):
            return 5

    innovation = _score("innovation_score")
    feasibility = _score("feasibility_score")
    importance = _score("importance_score")
    overall = round((innovation + feasibility + importance) / 3, 1)

    _progress(100, "完成")
    return {
        "topic": {
            "question": question,
            "description": description,
            "discipline": discipline,
            "degree_level": degree_level,
            "paper_type": paper_type,
            "core_summary": parsed.get("core_summary", ""),
        },
        "scores": {
            "innovation": innovation,
            "feasibility": feasibility,
            "importance": importance,
            "overall": overall,
            "verdict": _verdict(overall),
        },
        "analysis": {
            "innovation": result.get("innovation_analysis", ""),
            "feasibility": result.get("feasibility_analysis", ""),
            "importance": result.get("importance_analysis", ""),
        },
        "key_novelties": result.get("key_novelties") or [],
        "technical_challenges": result.get("technical_challenges") or [],
        "improvement_suggestions": result.get("improvement_suggestions") or [],
        "related_keywords": keywords,
        "related_papers": papers_dict,
    }
