"""
BibTeX 格式化/清洗（英文路径用）。
移植自 scientific_skills_ref/scripts/format_bibtex.py：
去掉 argparse/main CLI，stderr→loguru，作为库内类使用。
仅产英文 BibTeX；中文 GB/T 7714 见同目录 gbt7714.py。
"""
from __future__ import annotations

import re
from collections import OrderedDict
from typing import Dict, List

from loguru import logger


class BibTeXFormatter:
    """格式化、清洗、排序、去重 BibTeX 条目。"""

    def __init__(self):
        self.field_order = [
            "author", "editor", "title", "booktitle", "journal",
            "year", "month", "volume", "number", "pages",
            "publisher", "address", "edition", "series",
            "school", "institution", "organization",
            "howpublished", "doi", "url", "isbn", "issn",
            "note", "abstract", "keywords",
        ]

    def parse_string(self, content: str) -> List[Dict]:
        """解析 BibTeX 文本，提取条目。"""
        entries = []
        # 条目以 } 收尾，后跟下一个 @ 或文末（兼容单行/多行 .bib）
        pattern = r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\}\s*(?=@|\Z)"
        for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
            entry_type = match.group(1).lower()
            citation_key = match.group(2).strip()
            fields_text = match.group(3)

            fields: "OrderedDict[str, str]" = OrderedDict()
            field_pattern = r'(\w+)\s*=\s*\{([^}]*)\}|(\w+)\s*=\s*"([^"]*)"'
            for fm in re.finditer(field_pattern, fields_text):
                if fm.group(1):
                    fields[fm.group(1).lower()] = fm.group(2).strip()
                else:
                    fields[fm.group(3).lower()] = fm.group(4).strip()

            entries.append({"type": entry_type, "key": citation_key, "fields": fields})
        return entries

    def format_entry(self, entry: Dict) -> str:
        lines = [f'@{entry["type"]}{{{entry["key"]},']
        ordered = OrderedDict()
        for fn in self.field_order:
            if fn in entry["fields"]:
                ordered[fn] = entry["fields"][fn]
        for fn, fv in entry["fields"].items():
            if fn not in ordered:
                ordered[fn] = fv

        max_len = max((len(f) for f in ordered), default=0)
        for fn, fv in ordered.items():
            lines.append(f"  {fn.ljust(max_len)} = {{{fv}}},")
        if lines[-1].endswith(","):
            lines[-1] = lines[-1][:-1]
        lines.append("}")
        return "\n".join(lines)

    def fix_common_issues(self, entry: Dict) -> Dict:
        fixed = entry.copy()
        fields = fixed["fields"].copy()

        if "pages" in fields:
            pages = fields["pages"]
            if re.search(r"\d-\d", pages) and "--" not in pages:
                fields["pages"] = re.sub(r"(\d)-(\d)", r"\1--\2", pages)
            fields["pages"] = re.sub(r"^pp\.\s*", "", fields["pages"], flags=re.IGNORECASE)

        if "doi" in fields:
            doi = fields["doi"]
            for pfx in ("https://doi.org/", "http://doi.org/", "doi:"):
                doi = doi.replace(pfx, "")
            fields["doi"] = doi

        if "author" in fields:
            author = fields["author"].replace(";", " and").replace(" & ", " and ")
            fields["author"] = re.sub(r"\s+and\s+and\s+", " and ", author)

        fixed["fields"] = fields
        return fixed

    def deduplicate(self, entries: List[Dict]) -> List[Dict]:
        seen_dois, seen_keys, unique = set(), set(), []
        for e in entries:
            doi = e["fields"].get("doi", "").strip()
            key = e["key"]
            if doi:
                if doi in seen_dois:
                    logger.debug(f"[bibtex] 重复 DOI 跳过: {doi}")
                    continue
                seen_dois.add(doi)
            if key in seen_keys:
                logger.debug(f"[bibtex] 重复 key 跳过: {key}")
                continue
            seen_keys.add(key)
            unique.append(e)
        return unique

    def sort_entries(self, entries: List[Dict], sort_by: str = "year", descending: bool = True) -> List[Dict]:
        def key_fn(e: Dict):
            if sort_by == "year":
                return e["fields"].get("year", "9999")
            if sort_by == "author":
                a = e["fields"].get("author", "ZZZ")
                return (a.split(",")[0] if "," in a else (a.split()[0] if a else "zzz")).lower()
            if sort_by == "title":
                return e["fields"].get("title", "").lower()
            return e["key"].lower()
        return sorted(entries, key=key_fn, reverse=descending)

    def format_string(self, content: str, deduplicate: bool = True,
                      sort_by: str = "year", descending: bool = True,
                      fix_issues: bool = True) -> str:
        """端到端：解析→修正→去重→排序→输出 BibTeX 文本。"""
        entries = self.parse_string(content)
        if not entries:
            return ""
        if fix_issues:
            entries = [self.fix_common_issues(e) for e in entries]
        if deduplicate:
            entries = self.deduplicate(entries)
        if sort_by:
            entries = self.sort_entries(entries, sort_by, descending)
        return "\n\n".join(self.format_entry(e) for e in entries) + "\n"
