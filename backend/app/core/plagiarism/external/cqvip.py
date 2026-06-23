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


def search_sources_sync(query: str, limit: int = 2) -> List[dict]:
    """
    同步检索维普真实相似论文（供查重等同步场景：Celery 线程内调用）。
    返回 [{title, author, year, url, journal}]。无 key/失败返回 []。
    用于中文查重「相似来源参考」——给可疑段落找真实已发表论文作为出处佐证。
    """
    key = getattr(settings, "VIP_API_KEY", "") or ""
    q = (query or "").strip()
    if not key or not q:
        return []
    base = getattr(settings, "VIP_BASE_URL", "https://superapi.cqvip.com").rstrip("/")
    url = f"{base}/unifiedsearch/search/v1/paper/adv-search"
    try:
        with httpx.Client(timeout=getattr(settings, "VIP_TIMEOUT", 15)) as c:
            r = c.post(url, json={"page": 1, "size": min(max(1, limit), 5),
                                  "searchField": "U", "content": q[:200]},
                       headers={"Authorization": f"Bearer {key}",
                                "Content-Type": "application/json"})
            r.raise_for_status()
            d = r.json()
    except Exception as e:
        logger.warning(f"[cqvip] 同步相似来源检索失败: {e}")
        return []
    if not d or d.get("code") != 200:
        return []
    out: List[dict] = []
    for it in (d.get("data") or [])[:limit]:
        title = (it.get("title") or "").strip()
        if not title:
            continue
        authors = [(a.get("name") or "").strip() for a in (it.get("authorInfo") or [])]
        authors = [a for a in authors if a][:3]
        doi = (it.get("doi") or "").strip() or None
        y = it.get("year")
        year = int(str(y)[:4]) if y and str(y).isdigit() else None
        out.append({
            "title": title,
            "author": "、".join(authors),
            "year": year,
            "url": f"https://doi.org/{doi}" if doi else None,
            "journal": (it.get("journalInfo") or {}).get("name"),
        })
    return out


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
    async def _post(self, body: dict,
                    path: str = "/unifiedsearch/search/v1/paper/adv-search") -> Optional[dict]:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=body, headers=self._headers())
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()

    async def get_journal_full(self, name: str) -> Optional[dict]:
        """期刊查询(按刊名)→拿 id→期刊详情→归一化。无 key/未命中返回 None。"""
        if not self.api_key or not (name or "").strip():
            return None
        try:
            q = await self._post(
                {"page": 1, "size": 1, "searchField": "N", "content": name.strip()[:60]},
                path="/journal/v1/search",
            )
            if not q or q.get("code") != 200 or not q.get("data"):
                return None
            base = q["data"][0]
            jid = base.get("id")
            detail = base
            if jid:
                dd = await self._post({"id": jid}, path="/journal/v1/detail")
                if dd and dd.get("code") == 200 and dd.get("data"):
                    detail = dd["data"]
            return self._normalize_journal(detail)
        except Exception as e:
            logger.warning(f"[cqvip] 期刊详情获取失败 name={name}: {e}")
            return None

    @staticmethod
    def _normalize_journal(d: dict) -> dict:
        def _join(v):
            return "、".join(x for x in (v or []) if x) if isinstance(v, list) else (v or "")
        return {
            "id": d.get("id"),
            "name": d.get("journalName") or "",
            "issn": d.get("issn") or None,
            "cnno": d.get("cnno") or None,
            "impact_factor": d.get("impactFactor") or None,
            "cas_part": _join(d.get("casPart")) or None,        # 中科院分区
            "jcr_part": _join(d.get("jcrPart")) or None,        # JCR 分区
            "jcr_impact": d.get("jcrImpact") or None,
            "review_speed": d.get("reviewSpeed") or None,       # 审稿周期
            "pub_period": d.get("journalPubPeriod") or None,    # 发行周期
            "is_oa": bool(d.get("isOa")),
            "stopped": d.get("stopBInactive") not in (0, None, "0"),
            "core_tags": d.get("listJournalSource") or [],      # 核心标签-中文/收录
            "domain": d.get("domain") or [],
            "publisher": _join(d.get("publisher")) or None,
            "intro": (d.get("journalIntro") or "")[:300],
        }

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

    async def discover_journals(self, topic: str, size: int = 20) -> List[dict]:
        """
        投稿选刊「相似文献去向」：按主题检索真实论文，聚合它们发表的期刊。
        返回 [{name, count, ranges, samples, year}]，按出现频次降序——
        即"该主题的论文常发表在这些期刊"。无 key/失败返回 []。
        """
        if not self.api_key:
            return []
        try:
            body = {"page": 1, "size": min(max(1, size), 20), "searchField": "U",
                    "content": (topic or "")[:200]}
            data = await self._post(body)
        except Exception as e:
            logger.warning(f"[cqvip] 选刊发现检索失败: {e}")
            return []
        if not data or data.get("code") != 200:
            return []

        agg: dict = {}
        for p in (data.get("data") or []):
            ji = p.get("journalInfo") or {}
            name = (ji.get("name") or "").strip()
            if not name:
                continue
            e = agg.setdefault(name, {"name": name, "count": 0, "ranges": ji.get("range") or [],
                                      "year": ji.get("year"), "samples": []})
            e["count"] += 1
            title = (p.get("title") or "").strip()
            if title and len(e["samples"]) < 3:
                e["samples"].append(title)
        return sorted(agg.values(), key=lambda x: x["count"], reverse=True)

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
