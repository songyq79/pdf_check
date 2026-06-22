"""
文献补检：基于用户输入的关键词或已有文献标题，用 external/aggregator
（含 OpenAlex 中文源）补充相关文献，与输入合并去重。
"""
from __future__ import annotations

from typing import List

from loguru import logger

from app.core.plagiarism.external.aggregator import (
    ExternalSourceAggregator,
    ExternalSourceAggregatorAllFailedError,
)
from app.core.plagiarism.external.reranker import rerank_papers


def _paper_to_dict(p) -> dict:
    g = (lambda k: p.get(k) if isinstance(p, dict) else getattr(p, k, None))
    return {
        "title": g("title") or "",
        "authors": g("authors") or [],
        "year": g("year"),
        "doi": g("doi"),
        "abstract": (g("abstract") or "")[:500],
        "source": g("source_name") or g("source"),
    }


def _dedup_key(p: dict) -> str:
    return (p.get("doi") or (p.get("title") or "").strip().lower())


async def enrich(
    input_papers: List[dict],
    keywords: str = "",
    discipline: str = "",
    max_new: int = 15,
) -> List[dict]:
    """返回 输入文献 + 补检文献（去重）。失败则原样返回输入。"""
    # 构造检索 query：优先关键词，否则取输入文献前若干标题
    queries: List[str] = []
    if keywords and keywords.strip():
        queries = [q.strip() for q in keywords.replace("，", ",").split(",") if q.strip()]
    if not queries:
        queries = [p["title"] for p in input_papers[:5] if p.get("title")]
    if discipline:
        queries = [f"{q} {discipline}" for q in queries] or [discipline]
    queries = queries[:5]

    new_papers: List[dict] = []
    if queries:
        try:
            grouped = await ExternalSourceAggregator().batch_search(queries, limit_per_q=5)
            raw = [p for group in grouped for p in group]
            # 语义重排去噪：补检候选按与 query 的相关度排序，取相关度高的（多给一倍缓冲，
            # 供后续与输入文献去重后仍够 max_new）。重排不可用则原序降级。
            ranked = rerank_papers(" ".join(queries), raw, top_k=max(max_new * 2, max_new))
            new_papers = [_paper_to_dict(p) for p in ranked]
        except ExternalSourceAggregatorAllFailedError:
            logger.warning("[lit.enrich] 所有外部源失败，仅用输入文献")
        except Exception as e:
            logger.warning(f"[lit.enrich] 补检异常，仅用输入文献: {e}")

    # 合并去重（输入优先保留）
    merged: dict = {}
    for p in input_papers:
        k = _dedup_key(p)
        if k:
            merged[k] = p
    added = 0
    for p in new_papers:
        if added >= max_new:
            break
        k = _dedup_key(p)
        if k and k not in merged:
            merged[k] = p
            added += 1

    result = list(merged.values())
    logger.info(f"[lit.enrich] 输入 {len(input_papers)} 篇 + 补检 {added} 篇 = {len(result)} 篇")
    return result
