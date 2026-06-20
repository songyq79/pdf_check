"""
文献综述提示词。
参考 SKILL_literature_review 方法论（主题化综合而非逐篇罗列、研究空白识别），
改写为返回 JSON 的提示词；砍掉其 LaTeX/PDF/外部 CLI 依赖。
两段：① categorizer 分类聚合 ② draft_generator 生成初稿。
"""

_TYPE_FOCUS = {
    "humanities": "人文社科领域，关注理论流派、范式演进与争鸣。",
    "science_engineering": "理工农医领域，关注方法/技术路线、实验结果与可重复性。",
    "arts": "艺术领域，关注创作流派、技法演变与理论-实践结合。",
}


def _papers_block(papers: list, limit: int = 30) -> str:
    lines = []
    for i, p in enumerate(papers[:limit], 1):
        title = p.get("title") if isinstance(p, dict) else getattr(p, "title", "")
        year = p.get("year") if isinstance(p, dict) else getattr(p, "year", "")
        abs = (p.get("abstract") if isinstance(p, dict) else getattr(p, "abstract", "")) or ""
        lines.append(f"{i}. {title}（{year}） 摘要: {abs[:200]}")
    return "\n".join(lines) if lines else "（无文献）"


# ── Step 3：分类聚合 ──────────────────────────────────────────

def build_categorize_prompt(papers: list, discipline: str, paper_type: str = "humanities") -> str:
    focus = _TYPE_FOCUS.get(paper_type, _TYPE_FOCUS["humanities"])
    return f"""你是一位{discipline or "该领域"}的文献综述专家。请对以下文献按研究主题聚类，并识别研究空白。

【领域特点】{focus}

【文献列表】
{_papers_block(papers)}

要求：
1. 将文献归纳为 3-5 个研究主题/方向（每篇可归入最相关的一类）。
2. 每个主题给一句话小结，列出归入该主题的文献标题。
3. 概括整体研究脉络，并指出 2-4 个研究空白（gap）。
4. 仅依据上方真实文献，禁止编造不存在的文献。

请严格按以下 JSON 输出，不要输出任何其他文字：
{{"categories": [{{"name": "主题名", "papers": ["标题1"], "summary": "一句话小结"}}], "overall_theme": "整体研究脉络", "research_gaps": ["空白1"]}}"""


CATEGORIZE_FALLBACK = {
    "categories": [],
    "overall_theme": "",
    "research_gaps": [],
}


# ── Step 4：生成综述初稿 ─────────────────────────────────────

def build_draft_prompt(categorization: dict, papers: list, topic: str,
                       discipline: str, paper_type: str = "humanities") -> str:
    focus = _TYPE_FOCUS.get(paper_type, _TYPE_FOCUS["humanities"])
    cats = categorization.get("categories", [])
    cat_block = "\n".join(
        f"- {c.get('name','')}: {c.get('summary','')}" for c in cats
    ) or "（无分类）"
    gaps = "；".join(categorization.get("research_gaps", [])) or "（未识别）"

    return f"""你是一位{discipline or "该领域"}的学者。请基于下方分类与文献，撰写一篇文献综述初稿（1500-3000字）。

【领域特点】{focus}
【综述主题】{topic or "（未指定，按文献归纳）"}
【已聚类主题】
{cat_block}
【研究空白】{gaps}

【可引用文献】
{_papers_block(papers)}

写作要求（参考系统性综述方法论）：
1. 主题化综合，按研究方向组织段落，而非逐篇罗列。
2. 比较不同研究的方法与结论，指出共识与争议。
3. 客观、学术化中文表达，可在句中以"（作者, 年份）"形式提及文献。
4. 收尾指出研究空白与未来方向。禁止编造文献。

请严格按以下 JSON 输出，不要输出任何其他文字：
{{"overview": "研究现状总览段落", "sections": [{{"title": "小节标题", "content": "该小节正文"}}], "conclusion": "总结与未来方向"}}"""


DRAFT_FALLBACK = {
    "overview": "",
    "sections": [],
    "conclusion": "",
}
