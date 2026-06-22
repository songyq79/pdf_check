"""
选题评估 — 文献检索（薄包 external/aggregator.py）。
中英统一入口；全部外部源失败时优雅降级返回 []（评估仍可进行，
prompt 会据空文献提示 LLM 勿编造）。
"""
from __future__ import annotations

from typing import List

from loguru import logger

from app.core.plagiarism.external.aggregator import (
    ExternalSourceAggregator,
    ExternalSourceAggregatorAllFailedError,
)
from app.core.plagiarism.external.base_source import CandidatePaper
from app.core.plagiarism.external.reranker import rerank_papers


class LiteratureSearcher:
    """复用查重模块的外部源聚合器（含 Semantic Scholar/CORE/PubMed/OpenAlex）。"""

    def __init__(self):
        self._aggregator = ExternalSourceAggregator()

    async def search(self, queries: List[str], limit_per_query: int = 5,
                     max_results: int = 10) -> List[CandidatePaper]:
        """多 query 检索→合并去重→截断。失败返回 []。"""
        queries = [q for q in (queries or []) if q and q.strip()]
        if not queries:
            return []
        try:
            grouped = await self._aggregator.batch_search(queries, limit_per_query)
        except ExternalSourceAggregatorAllFailedError:
            logger.warning("[topic.search] 所有外部源失败，返回空文献集")
            return []
        except Exception as e:
            logger.warning(f"[topic.search] 检索异常，返回空文献集: {e}")
            return []

        merged: dict = {}
        for group in grouped:
            for p in group:
                key = p.doi or (p.title or "").strip().lower()
                if key and key not in merged:
                    merged[key] = p

        # 语义重排去噪：外部源是关键词检索会混入跑题论文，
        # 用 query 与各篇 title+abstract 的相似度重排+砍噪声（编码器不可用则原序降级）。
        candidates = list(merged.values())
        results = rerank_papers(" ".join(queries), candidates, top_k=max_results)
        logger.info(
            f"[topic.search] 检索 {len(candidates)} 篇 → 重排去噪后 {len(results)} 篇"
        )
        return results
