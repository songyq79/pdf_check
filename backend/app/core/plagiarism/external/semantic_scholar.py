"""
Semantic Scholar Graph API 适配器。
端点:/paper/search/match(主)→ /paper/search(降级)
未授权 100 req/5min;授权后放宽。
"""
from __future__ import annotations

from typing import List, Optional

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.core.plagiarism.external.base_source import (
    CandidatePaper,
    ExternalSource,
)

_FIELDS = "title,abstract,externalIds,authors,year,url"


class SemanticScholarSource(ExternalSource):
    source_name = "semantic_scholar"

    def __init__(self):
        super().__init__(cache_ttl=settings.ENGLISH_SOURCE_CACHE_TTL)
        self.base_url = settings.SEMANTIC_SCHOLAR_BASE_URL.rstrip("/")
        self.api_key = settings.SEMANTIC_SCHOLAR_API_KEY
        self.timeout = settings.SEMANTIC_SCHOLAR_TIMEOUT

    def _headers(self) -> dict:
        return {"x-api-key": self.api_key} if self.api_key else {}

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    async def _fetch(self, path: str, params: dict) -> Optional[dict]:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params, headers=self._headers())
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()

    async def _do_search(self, query: str, limit: int) -> List[CandidatePaper]:
        # 主端点:match(精确标题/短语匹配)
        try:
            data = await self._fetch(
                "/paper/search/match",
                {"query": query[:500], "fields": _FIELDS},
            )
            if data and data.get("data"):
                return self._parse(data["data"][:limit])
        except Exception as e:
            logger.debug(f"[semantic_scholar] match 端点失败 → 降级 search: {e}")

        # 降级:常规 search
        data = await self._fetch(
            "/paper/search",
            {"query": query[:500], "limit": min(limit, 100), "fields": _FIELDS},
        )
        if not data:
            return []
        return self._parse(data.get("data", [])[:limit])

    def _parse(self, items: list) -> List[CandidatePaper]:
        results: List[CandidatePaper] = []
        for it in items:
            abstract = it.get("abstract") or ""
            if not abstract.strip():
                continue
            doi = (it.get("externalIds") or {}).get("DOI")
            authors = [a.get("name", "") for a in (it.get("authors") or [])][:5]
            results.append(CandidatePaper(
                title=it.get("title") or "",
                abstract=abstract,
                doi=doi,
                url=it.get("url") or (f"https://doi.org/{doi}" if doi else None),
                authors=authors,
                year=it.get("year"),
                source_name=self.source_name,
            ))
        return results
