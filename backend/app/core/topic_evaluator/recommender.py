"""
选题推荐核心：给学科 + 关键词 → 生成候选选题。
两步（RAG 接地，防幻觉）：
  ① LiteratureSearcher 按关键词检索真实文献（含语义重排去噪）
  ② call_ai 基于真实文献判断研究现状/空白，生成 N 个候选选题 JSON
与 evaluate_topic 区别：那个是"评一个给定选题"，这个是"从无到有出选题"。
"""
from __future__ import annotations

from typing import Callable, List, Optional

from loguru import logger

from app.core.ai_client import call_ai, parse_json_response
from app.core.topic_evaluator import prompts
from app.core.topic_evaluator.evaluator import _paper_to_dict
from app.core.topic_evaluator.literature_searcher import LiteratureSearcher

_VALID_TYPES = ("humanities", "science_engineering", "arts")


async def recommend_topics(
    discipline: str = "",
    paper_type: str = "humanities",
    keywords: str = "",
    degree_level: str = "",
    count: int = 5,
    progress_cb: Optional[Callable[[int, str], None]] = None,
) -> dict:
    """返回 {topics:[{title,innovation,feasibility,direction,keywords}], related_papers:[...]}。"""
    def _progress(pct: int, msg: str):
        if progress_cb:
            try:
                progress_cb(pct, msg)
            except Exception:
                pass
        logger.info(f"[topic.recommend] {pct}% {msg}")

    if paper_type not in _VALID_TYPES:
        paper_type = "humanities"
    count = max(3, min(8, count))

    # ① 检索真实文献（按关键词；空关键词则跳过检索）
    _progress(20, "检索领域文献")
    queries: List[str] = [k.strip() for k in (keywords or "").replace("，", ",").split(",") if k.strip()]
    papers = []
    if queries:
        try:
            papers = await LiteratureSearcher().search(queries[:3], limit_per_query=5, max_results=10)
        except Exception as e:
            logger.warning(f"[topic.recommend] 检索失败，无文献接地: {e}")
    papers_dict = [_paper_to_dict(p) for p in papers]

    # ② LLM 生成候选选题（基于真实文献）
    _progress(60, "生成候选选题")
    raw = await call_ai(prompts.build_recommendation_prompt(
        discipline, paper_type, keywords, degree_level, papers, count))
    parsed = parse_json_response(raw, dict(prompts.RECOMMENDATION_FALLBACK))

    topics = []
    for t in (parsed.get("topics") or [])[:count]:
        if not isinstance(t, dict):
            continue
        title = (t.get("title") or "").strip()
        if not title:
            continue
        topics.append({
            "title": title,
            "innovation": t.get("innovation", ""),
            "feasibility": t.get("feasibility", ""),
            "direction": t.get("direction", ""),
            "keywords": t.get("keywords") or [],
        })

    _progress(100, "完成")
    return {
        "discipline": discipline,
        "paper_type": paper_type,
        "keywords": keywords,
        "degree_level": degree_level,
        "topics": topics,
        "related_papers": papers_dict,
    }
