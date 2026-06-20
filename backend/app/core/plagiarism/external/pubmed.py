"""
PubMed E-utilities 适配器。
esearch.fcgi → efetch.fcgi?rettype=abstract&retmode=xml
无 key 3 req/s;有 key 10 req/s。
非医学查询自然返回 0。
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.core.plagiarism.external.base_source import (
    CandidatePaper,
    ExternalSource,
)


class PubMedSource(ExternalSource):
    source_name = "pubmed"

    def __init__(self):
        super().__init__(cache_ttl=settings.ENGLISH_SOURCE_CACHE_TTL)
        self.base_url = settings.PUBMED_BASE_URL.rstrip("/")
        self.api_key = settings.PUBMED_API_KEY
        self.email = settings.PUBMED_EMAIL
        self.timeout = settings.PUBMED_TIMEOUT

    def _common_params(self) -> dict:
        params = {"db": "pubmed"}
        if self.api_key:
            params["api_key"] = self.api_key
        if self.email:
            params["email"] = self.email
        return params

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    async def _do_search(self, query: str, limit: int) -> List[CandidatePaper]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 1. esearch 拿 PMID 列表
            sp = {**self._common_params(), "term": query[:500],
                  "retmax": min(limit, 20), "retmode": "json"}
            r1 = await client.get(f"{self.base_url}/esearch.fcgi", params=sp)
            r1.raise_for_status()
            pmids = r1.json().get("esearchresult", {}).get("idlist", [])
            if not pmids:
                return []

            # 2. efetch 拿详情
            fp = {**self._common_params(), "id": ",".join(pmids),
                  "rettype": "abstract", "retmode": "xml"}
            r2 = await client.get(f"{self.base_url}/efetch.fcgi", params=fp)
            r2.raise_for_status()
            return self._parse_xml(r2.text)

    def _parse_xml(self, xml_text: str) -> List[CandidatePaper]:
        results: List[CandidatePaper] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        for art in root.iter("PubmedArticle"):
            title_el = art.find(".//ArticleTitle")
            title = "".join(title_el.itertext()).strip() if title_el is not None else ""

            abstract_parts = []
            for abs_el in art.findall(".//Abstract/AbstractText"):
                txt = "".join(abs_el.itertext()).strip()
                if txt:
                    abstract_parts.append(txt)
            abstract = " ".join(abstract_parts)
            if not abstract:
                continue

            year_el = art.find(".//PubDate/Year")
            year = int(year_el.text) if year_el is not None and year_el.text and year_el.text.isdigit() else None

            authors = []
            for a in art.findall(".//Author")[:5]:
                last = a.find("LastName")
                fore = a.find("ForeName")
                name = " ".join(x.text for x in (fore, last) if x is not None and x.text)
                if name:
                    authors.append(name)

            doi = None
            for aid in art.findall(".//ArticleId"):
                if aid.attrib.get("IdType") == "doi" and aid.text:
                    doi = aid.text.strip()
                    break

            pmid_el = art.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else ""

            results.append(CandidatePaper(
                title=title,
                abstract=abstract,
                doi=doi,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                authors=authors,
                year=year,
                source_name=self.source_name,
            ))
        return results
