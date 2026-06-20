"""
用户输入文献解析：txt（每行一个标题）/ csv（title,authors,year）/ bib（BibTeX）。
统一输出标准化论文 dict 列表：{title, authors:[], year, doi, abstract}。
"""
from __future__ import annotations

import csv
import io
import re
from typing import List

from loguru import logger

from app.core.literature_reviewer.format_bibtex import BibTeXFormatter


def _norm(title="", authors=None, year=None, doi=None, abstract="") -> dict:
    if isinstance(authors, str):
        authors = [a.strip() for a in re.split(r"[;,，]| and ", authors) if a.strip()]
    return {
        "title": (title or "").strip(),
        "authors": authors or [],
        "year": year,
        "doi": (doi or None),
        "abstract": (abstract or "").strip(),
    }


def parse_txt(content: str) -> List[dict]:
    """每行一个论文标题。"""
    return [_norm(title=line.strip()) for line in content.splitlines() if line.strip()]


def parse_csv(content: str) -> List[dict]:
    """CSV，识别 title/authors/year 列（表头不敏感）。无表头则首列当标题。"""
    papers: List[dict] = []
    reader = csv.reader(io.StringIO(content))
    rows = [r for r in reader if any(c.strip() for c in r)]
    if not rows:
        return []
    header = [h.strip().lower() for h in rows[0]]
    has_header = any(h in ("title", "标题", "题名", "authors", "作者", "year", "年份") for h in header)
    idx = {"title": 0, "authors": None, "year": None}
    if has_header:
        for i, h in enumerate(header):
            if h in ("title", "标题", "题名"):
                idx["title"] = i
            elif h in ("authors", "author", "作者"):
                idx["authors"] = i
            elif h in ("year", "年份", "年"):
                idx["year"] = i
        data_rows = rows[1:]
    else:
        data_rows = rows
    for r in data_rows:
        title = r[idx["title"]] if idx["title"] < len(r) else ""
        authors = r[idx["authors"]] if idx["authors"] is not None and idx["authors"] < len(r) else ""
        year = r[idx["year"]] if idx["year"] is not None and idx["year"] < len(r) else None
        if title.strip():
            papers.append(_norm(title=title, authors=authors, year=year))
    return papers


def parse_bib(content: str) -> List[dict]:
    """BibTeX → 标准化 dict。"""
    entries = BibTeXFormatter().parse_string(content)
    papers = []
    for e in entries:
        f = e.get("fields", {})
        papers.append(_norm(
            title=f.get("title", ""),
            authors=f.get("author", ""),
            year=f.get("year"),
            doi=f.get("doi"),
            abstract=f.get("abstract", ""),
        ))
    return papers


def _detect_format(content: str) -> str:
    head = content.lstrip()[:200]
    if "@" in head and re.search(r"@\w+\s*\{", head):
        return "bib"
    if "," in head and ("\n" in content) and len(content.splitlines()[0].split(",")) >= 2:
        return "csv"
    return "txt"


def parse_input(content: str, fmt: str = "auto") -> List[dict]:
    """统一入口。fmt: auto/txt/csv/bib。"""
    if not content or not content.strip():
        return []
    if fmt == "auto":
        fmt = _detect_format(content)
    try:
        if fmt == "bib":
            papers = parse_bib(content)
        elif fmt == "csv":
            papers = parse_csv(content)
        else:
            papers = parse_txt(content)
    except Exception as e:
        logger.warning(f"[paper_parser] 解析失败({fmt})，降级按纯文本: {e}")
        papers = parse_txt(content)
    logger.info(f"[paper_parser] 解析 {fmt} 得到 {len(papers)} 篇")
    return papers
