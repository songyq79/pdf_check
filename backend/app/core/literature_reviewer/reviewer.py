"""
文献综述核心编排（五步）：
  ① paper_parser 解析输入（或关键词模式跳过）
  ② enrichment 补检相关文献
  ③ categorizer 分类聚合（call_ai）
  ④ draft_generator 生成初稿（call_ai）
  ⑤ 汇总结果（参考文献格式化交给 report_generator / gbt7714）
返回统一结果 dict，供 report_generator 渲染 + Celery 双写。
"""
from __future__ import annotations

from typing import Callable, List, Optional

from loguru import logger

from app.core.literature_reviewer import paper_parser
from app.core.literature_reviewer.enrichment import enrich
from app.core.literature_reviewer.categorizer import categorize
from app.core.literature_reviewer.draft_generator import generate_draft


async def generate_review(
    input_text: str = "",
    input_format: str = "auto",
    keywords: str = "",
    topic: str = "",
    discipline: str = "",
    paper_type: str = "humanities",
    citation_style: str = "gbt7714",
    length_mode: str = "short",
    language: str = "zh",
    progress_cb: Optional[Callable[[int, str], None]] = None,
) -> dict:
    def _progress(pct: int, msg: str):
        if progress_cb:
            try:
                progress_cb(pct, msg)
            except Exception:
                pass
        logger.info(f"[lit.review] {pct}% {msg}")

    # ① 解析输入
    _progress(10, "解析输入文献")
    input_papers: List[dict] = paper_parser.parse_input(input_text, input_format) if input_text else []

    # ② 补检
    _progress(35, "检索补充相关文献")
    papers = await enrich(input_papers, keywords=keywords, discipline=discipline)

    # ③ 分类
    _progress(60, "按主题聚类分析")
    categorization = await categorize(papers, discipline, paper_type)

    # ④ 初稿
    _progress(85, "生成综述初稿")
    draft = await generate_draft(categorization, papers, topic, discipline, paper_type,
                                 length_mode=length_mode, language=language)

    _progress(100, "完成")
    return {
        "meta": {
            "topic": topic,
            "keywords": keywords,
            "discipline": discipline,
            "paper_type": paper_type,
            "citation_style": citation_style,
            "length_mode": length_mode,
            "language": language,
            "papers_identified": len(input_papers),
            "papers_total": len(papers),
        },
        "categorization": categorization,
        "draft": draft,
        "papers": papers,
    }
