"""
维普 CQVIP 文献检索适配器（中文文献主力源）。
端点：POST {base}/unifiedsearch/search/v1/paper/adv-search
鉴权：Header Authorization: Bearer <VIP_API_KEY>（无需签名）

请求体：page/size(≤20)/searchField(U主题 T篇名 K关键词 R摘要 D DOI)/content
        + 可选 yearStart/yearEnd/language(zh中文 ot外文)/isOa/pdf
响应 data[]：id/title/abstr/authorInfo[].name/journalInfo/year/doi/keywordInfo/...

未配置 VIP_API_KEY 时静默返回 []（不阻塞 aggregator，其它源照常）。
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


class CqvipSource(ExternalSource):
    source_name = "cqvip"

    def __init__(self):
        super().__init__(cache_ttl=getattr(settings, "ENGLISH_SOURCE_CACHE_TTL", 604800))
        self.api_key = getattr(settings, "VIP_API_KEY", "") or ""
        self.base_url = getattr(settings, "VIP_BASE_URL", "https://superapi.cqvip.com").rstrip("/")
        self.timeout = getattr(settings, "VIP_TIMEOUT", 15)
        # 是否只取中文文献（维普强项）。留空 = 全部
        self.language = getattr(settings, "VIP_LANGUAGE", "")  # "zh" / "ot" / ""

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    async def _post(self, body: dict) -> Optional[dict]:
        url = f"{self.base_url}/unifiedsearch/search/v1/paper/adv-search"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=body, headers=self._headers())
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()

    async def _do_search(self, query: str, limit: int) -> List[CandidatePaper]:
        if not self.api_key:
            logger.warning("[cqvip] VIP_API_KEY 未配置，跳过维普源")
            return []
        body = {
            "page": 1,
            "size": min(max(1, limit), 20),
            "searchField": "U",          # 按主题检索（最通用）
            "content": (query or "")[:200],
        }
        if self.language in ("zh", "ot"):
            body["language"] = self.language

        data = await self._post(body)
        if not data or data.get("code") != 200:
            return []
        return self._parse(data.get("data") or [])

    def _parse(self, items: list) -> List[CandidatePaper]:
        results: List[CandidatePaper] = []
        for it in items:
            abstract = (it.get("abstr") or "").strip()
            title = (it.get("title") or "").strip()
            if not title and not abstract:
                continue
            authors = [
                (a.get("name") or "").strip()
                for a in (it.get("authorInfo") or [])
            ]
            authors = [a for a in authors if a][:5]
            doi = (it.get("doi") or "").strip() or None
            year = None
            y = it.get("year")
            if y and str(y).isdigit():
                year = int(str(y)[:4])
            results.append(CandidatePaper(
                title=title,
                abstract=abstract,
                doi=doi,
                url=(f"https://doi.org/{doi}" if doi else None),
                authors=authors,
                year=year,
                source_name=self.source_name,
            ))
        return results
