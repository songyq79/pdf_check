"""
OpenAlex Works API 适配器。
端点:/works?search=...&filter=has_abstract:true
免费、无需 API key;礼貌抓取用 mailto 进 polite pool。
中文文献覆盖优于 PubMed(纯英文医学),作为中文路径主力源。

摘要还原:OpenAlex 返回的是 abstract_inverted_index(倒排索引),
需还原为正常文本(逻辑同 scripts/ingest_openalex.py)。
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

_BASE_URL = "https://api.openalex.org"
_SELECT = "id,doi,title,abstract_inverted_index,authorships,publication_year"
# 礼貌抓取邮箱:复用既有 ingest 脚本里登记的邮箱,可被 settings 覆盖
_DEFAULT_EMAIL = "voxtex_hub@zohomail.com"


def _reconstruct_abstract(inverted: Optional[dict]) -> str:
    """将 OpenAlex 倒排索引格式 {word: [positions]} 还原为正常摘要文本。"""
    if not inverted:
        return ""
    positions: dict = {}
    for word, pos_list in inverted.items():
        for p in pos_list:
            positions[p] = word
    if not positions:
        return ""
    return " ".join(positions[i] for i in sorted(positions))


class OpenAlexSource(ExternalSource):
    source_name = "openalex"

    def __init__(self):
        super().__init__(
            cache_ttl=getattr(settings, "ENGLISH_SOURCE_CACHE_TTL", 604800),
        )
        self.email = getattr(settings, "OPENALEX_EMAIL", _DEFAULT_EMAIL)
        self.timeout = getattr(settings, "OPENALEX_TIMEOUT", 30)

    def _headers(self) -> dict:
        return {"User-Agent": f"PaperCheckSystem/1.0 (mailto:{self.email})"}

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    async def _fetch(self, params: dict) -> Optional[dict]:
        url = f"{_BASE_URL}/works"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, params=params, headers=self._headers())
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()

    async def _do_search(self, query: str, limit: int) -> List[CandidatePaper]:
        params = {
            "search": query[:500],
            "filter": "has_abstract:true",
            "select": _SELECT,
            "per-page": min(limit, 50),
            "mailto": self.email,
        }
        data = await self._fetch(params)
        if not data:
            return []
        return self._parse(data.get("results", [])[:limit])

    def _parse(self, items: list) -> List[CandidatePaper]:
        results: List[CandidatePaper] = []
        for it in items:
            abstract = _reconstruct_abstract(it.get("abstract_inverted_index"))
            if not abstract.strip():
                continue
            doi_raw = it.get("doi") or ""
            doi = doi_raw.replace("https://doi.org/", "").strip() or None
            authors = [
                (a.get("author") or {}).get("display_name", "")
                for a in (it.get("authorships") or [])
            ]
            authors = [a for a in authors if a][:5]
            results.append(CandidatePaper(
                title=it.get("title") or "",
                abstract=abstract,
                doi=doi,
                url=it.get("id") or (f"https://doi.org/{doi}" if doi else None),
                authors=authors,
                year=it.get("publication_year"),
                source_name=self.source_name,
            ))
        return results
