"""
CORE v3 API 适配器。
免费无 key:10 req/min;带 key 更高。
"""
from __future__ import annotations

from typing import List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.core.plagiarism.external.base_source import (
    CandidatePaper,
    ExternalSource,
)


class CoreSource(ExternalSource):
    source_name = "core"

    def __init__(self):
        super().__init__(cache_ttl=settings.ENGLISH_SOURCE_CACHE_TTL)
        self.base_url = settings.CORE_BASE_URL.rstrip("/")
        self.api_key = settings.CORE_API_KEY
        self.timeout = settings.CORE_TIMEOUT

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    async def _do_search(self, query: str, limit: int) -> List[CandidatePaper]:
        url = f"{self.base_url}/search/works"
        params = {"q": query[:500], "limit": min(limit, 20)}
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            resp = await client.get(url, params=params, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()

        results: List[CandidatePaper] = []
        for it in (data.get("results") or [])[:limit]:
            abstract = it.get("abstract") or ""
            if not abstract.strip():
                continue
            authors = [a.get("name", "") for a in (it.get("authors") or [])][:5]
            doi = it.get("doi")
            results.append(CandidatePaper(
                title=it.get("title") or "",
                abstract=abstract,
                doi=doi,
                url=it.get("downloadUrl") or (it.get("sourceFulltextUrls") or [None])[0]
                    or (f"https://doi.org/{doi}" if doi else None),
                authors=authors,
                year=it.get("yearPublished"),
                source_name=self.source_name,
            ))
        return results
