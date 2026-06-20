"""
GB/T 7714-2015 参考文献格式化（中文学位论文标准）。
无现成参考，从零实现。聚焦最常见的期刊论文 [J]，对缺失字段容错。

期刊格式：
  主要责任者. 题名[J]. 刊名, 年, 卷(期): 起止页码. DOI.
作者规则：≤3 全列；>3 取前 3 + "等"（中文）/ "et al"（英文）。

输入支持 dict 或具备同名属性的对象（如 aggregator 的 CandidatePaper：
title/authors/year/doi/url，缺 journal/volume/issue/pages 时自动省略）。
"""
from __future__ import annotations

import re
from typing import Any, List, Optional


def _get(entry: Any, key: str, default=None):
    if isinstance(entry, dict):
        return entry.get(key, default)
    return getattr(entry, key, default)


def _has_cjk(text: str) -> bool:
    return bool(re.search(r"[一-鿿]", text or ""))


def _normalize_authors(authors) -> List[str]:
    """authors 可能是 list[str] 或 'A and B' / 'A; B' 字符串。"""
    if not authors:
        return []
    if isinstance(authors, str):
        parts = re.split(r"\s+and\s+|;|，|,", authors)
        return [p.strip() for p in parts if p.strip()]
    return [str(a).strip() for a in authors if str(a).strip()]


def format_authors(authors, is_cjk: bool) -> str:
    names = _normalize_authors(authors)
    if not names:
        return "佚名" if is_cjk else "Anon"
    etal = "等" if is_cjk else "et al"
    if len(names) > 3:
        return ", ".join(names[:3]) + ", " + etal
    return ", ".join(names)


def format_reference(entry: Any, index: Optional[int] = None) -> str:
    """单条 GB/T 7714 [J] 参考文献。"""
    title = (_get(entry, "title", "") or "").strip()
    is_cjk = _has_cjk(title) or _has_cjk(str(_get(entry, "authors", "")))

    authors = format_authors(_get(entry, "authors"), is_cjk)
    year = _get(entry, "year")
    journal = (_get(entry, "journal") or _get(entry, "venue") or "").strip()
    volume = _get(entry, "volume")
    issue = _get(entry, "issue") or _get(entry, "number")
    pages = (_get(entry, "pages") or "").strip()
    doi_raw = (_get(entry, "doi") or "").strip()
    doi = doi_raw.replace("https://doi.org/", "").replace("http://doi.org/", "") or None

    # 有 DOI 但无页码 → [J/OL] 电子版标识
    type_tag = "[J/OL]" if (doi and not pages) else "[J]"

    parts: List[str] = []
    parts.append(f"{authors}. {title}{type_tag}.")

    # 刊名, 年, 卷(期): 页码.  缺啥省啥
    tail_segments: List[str] = []
    if journal:
        tail_segments.append(journal)
    if year:
        tail_segments.append(str(year))
    vol_issue = ""
    if volume:
        vol_issue = str(volume)
        if issue:
            vol_issue += f"({issue})"
    elif issue:
        vol_issue = f"({issue})"

    pub = ""
    if tail_segments:
        pub = ", ".join(tail_segments)
        if vol_issue and pages:
            pub += f", {vol_issue}: {pages}"
        elif vol_issue:
            pub += f", {vol_issue}"
        elif pages:
            pub += f": {pages}"
        pub += "."
    if pub:
        parts.append(pub)

    if doi:
        parts.append(f"DOI:{doi}.")

    ref = " ".join(parts)
    return f"[{index}] {ref}" if index is not None else ref


def format_references(entries: List[Any]) -> str:
    """整段带序号参考文献表。"""
    return "\n".join(format_reference(e, i + 1) for i, e in enumerate(entries))
