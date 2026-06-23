"""
外部学术源聚合器。
并行调用 Semantic Scholar / CORE / PubMed,任一失败不阻塞;全失败抛 AllFailedError。
按 DOI/title 去重。
"""
from __future__ import annotations

import asyncio
import re
from typing import Dict, List

from loguru import logger

from app.core.plagiarism.external.base_source import (
    CandidatePaper,
    ExternalSource,
    ExternalSourceError,
)
from app.core.plagiarism.external.core_api import CoreSource
from app.core.plagiarism.external.cqvip import CqvipSource
from app.core.plagiarism.external.openalex import OpenAlexSource
from app.core.plagiarism.external.pubmed import PubMedSource
from app.core.plagiarism.external.semantic_scholar import SemanticScholarSource


class ExternalSourceAggregatorAllFailedError(Exception):
    """所有外部源全部失败,触发 HybridChecker 降级。"""


def _normalize_title(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", (t or "").lower())).strip()


class ExternalSourceAggregator:

    def __init__(self):
        self.sources: List[ExternalSource] = [
            SemanticScholarSource(),
            CoreSource(),
            PubMedSource(),
            OpenAlexSource(),  # 中文+多语言覆盖,选题评估/文献综述/查重共享
            CqvipSource(),     # 维普:中文文献主力源(需 VIP_API_KEY;未配置则静默跳过)
        ]

    async def search(self, query: str, limit: int = 10) -> List[CandidatePaper]:
        """单 query 并行调三源,合并去重。"""
        tasks = [s.search(query, limit) for s in self.sources]
        raw = await asyncio.gather(*tasks, return_exceptions=True)

        merged: Dict[str, CandidatePaper] = {}
        failures = 0
        for src, res in zip(self.sources, raw):
            if isinstance(res, Exception):
                failures += 1
                logger.warning(f"[aggregator] {src.source_name} 失败: {res}")
                continue
            for p in res:
                key = p.doi or _normalize_title(p.title)
                if not key:
                    continue
                if key not in merged:
                    merged[key] = p
        if failures == len(self.sources) and not merged:
            raise ExternalSourceAggregatorAllFailedError(
                "所有外部学术源均不可用"
            )
        return list(merged.values())

    async def batch_search(self, queries: List[str], limit_per_q: int = 10) -> List[List[CandidatePaper]]:
        """多 query 限速并发(semaphore=2),避免免费 API 429 限速。"""
        sem = asyncio.Semaphore(2)

        async def _bounded(q: str, limit: int) -> List[CandidatePaper]:
            async with sem:
                result = await self.search(q, limit)
                await asyncio.sleep(1.0)
                return result

        tasks = [_bounded(q, limit_per_q) for q in queries]
        raw = await asyncio.gather(*tasks, return_exceptions=True)
        all_failed = True
        results: List[List[CandidatePaper]] = []
        for q, res in zip(queries, raw):
            if isinstance(res, ExternalSourceAggregatorAllFailedError):
                results.append([])
                continue
            if isinstance(res, Exception):
                logger.warning(f"[aggregator] query 失败 {q[:40]}: {res}")
                results.append([])
                continue
            all_failed = False
            results.append(res)
        if all_failed and queries:
            raise ExternalSourceAggregatorAllFailedError(
                "所有 query 的外部源全部失败"
            )
        return results
