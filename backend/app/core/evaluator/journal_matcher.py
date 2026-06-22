"""
期刊投稿匹配。
基于已有评价结果（总分 + 论文类别）从本地 journals 表推荐匹配期刊。

设计取舍：作为免费、同步的内联接口，采用确定性启发式打分（按论文总分与
期刊层级的匹配度），不每次调 AI——更快、零 token 成本、结果可解释。
期刊数据来自 scripts/seed_journals.py 预先导入的 journals 表。
"""
from __future__ import annotations

from typing import List

from loguru import logger
from sqlalchemy.orm import Session

from app.models.phase1 import Journal
from app.core.plagiarism.external.reranker import score_texts

# 论文类别 → 期刊 category 关键词（粗映射，匹配不到则不按类别过滤）
_TYPE_CATEGORY_KEYWORDS = {
    "humanities": ["社科", "人文", "经济", "管理", "教育", "法学", "文学", "历史", "哲学", "social"],
    "science_engineering": ["理", "工", "医", "农", "计算机", "信息", "材料", "science", "engineering", "medical"],
    "arts": ["艺术", "设计", "美术", "音乐", "art", "design"],
}


def _required_score(impact_factor: float) -> int:
    """该期刊大致需要的论文总分门槛（影响因子越高门槛越高）。"""
    jif = impact_factor or 0
    if jif >= 5:
        return 85
    if jif >= 2:
        return 78
    return 70


def _match_score(paper_score: float, impact_factor: float) -> int:
    """论文总分与期刊层级的匹配度（1-10）。"""
    req = _required_score(impact_factor)
    diff = (paper_score or 0) - req
    return max(1, min(10, round(7 + diff / 5)))


def _reason(paper_score: float, impact_factor: float, match: int) -> str:
    req = _required_score(impact_factor)
    if (paper_score or 0) >= req + 5:
        return "论文水平较充分匹配该期刊层级，命中率较高"
    if (paper_score or 0) >= req:
        return "论文水平基本匹配，建议打磨后投稿"
    return "该期刊层级偏高，建议作为冲刺目标或先提升论文质量"


class JournalMatcher:
    def get_recommendations(self, db: Session, evaluation_result: dict,
                            top_n: int = 8) -> List[dict]:
        overall = evaluation_result.get("overall_score", 0)
        paper_type = evaluation_result.get("paper_type", "humanities")

        journals = db.query(Journal).all()
        if not journals:
            logger.warning("[journal_matcher] journals 表为空，请先运行 scripts/seed_journals.py")
            return []

        # 按类别粗过滤
        keywords = _TYPE_CATEGORY_KEYWORDS.get(paper_type, [])
        filtered = [
            j for j in journals
            if not keywords or (j.category and any(k in j.category for k in keywords))
        ]
        if not filtered:
            filtered = journals  # 匹配不到则不过滤

        scored = []
        for j in filtered:
            ms = _match_score(overall, j.impact_factor or 0)
            scored.append({
                "id": j.id,
                "name_zh": j.name_zh,
                "name_en": j.name_en,
                "issn": j.issn,
                "impact_factor": j.impact_factor,
                "jcr_rank": j.jcr_rank,
                "category": j.category,
                "match_score": ms,
                "review_days_avg": j.review_days_avg,
                "acceptance_rate": j.acceptance_rate,
                "is_open_access": j.is_open_access,
                "reason": _reason(overall, j.impact_factor or 0, ms),
            })

        scored.sort(key=lambda x: (x["match_score"], x["impact_factor"] or 0), reverse=True)
        return scored[:top_n]

    def select_by_content(self, db: Session, title: str = "", abstract: str = "",
                          keywords: str = "", paper_type: str = "", top_n: int = 8) -> dict:
        """
        维普式「投稿选刊」：按论文内容(标题+摘要+关键词)做主题语义匹配。
        用多语言模型算 论文 vs 期刊画像(刊名+类别) 的相似度排序。
        模型不可用时降级为按类别关键词粗匹配。
        返回 {"journals": [...], "matched_by": "semantic"|"fallback"}。
        """
        journals = db.query(Journal).all()
        if not journals:
            logger.warning("[journal_select] journals 表为空，请先 seed_journals.py")
            return {"journals": [], "matched_by": "empty"}

        # 可选按论文类别粗过滤（匹配不到则不过滤）
        kw = _TYPE_CATEGORY_KEYWORDS.get(paper_type, [])
        pool = [j for j in journals if not kw or (j.category and any(k in j.category for k in kw))]
        if not pool:
            pool = journals

        paper_text = " ".join(x for x in [title, keywords, abstract] if x).strip()[:1500]
        profiles = [
            " ".join(x for x in [j.name_zh or "", j.name_en or "", j.category or ""] if x)
            for j in pool
        ]

        sims = score_texts(paper_text, profiles) if paper_text else None

        results = []
        if sims is not None:
            matched_by = "semantic"
            for j, s in zip(pool, sims):
                results.append((j, s))
            results.sort(key=lambda x: x[1], reverse=True)
        else:
            # 降级：无模型/无内容 → 按类别命中 + 影响因子排
            matched_by = "fallback"
            for j in pool:
                hit = 1.0 if (kw and j.category and any(k in j.category for k in kw)) else 0.3
                results.append((j, hit + (j.impact_factor or 0) / 100))
            results.sort(key=lambda x: x[1], reverse=True)

        out = []
        for j, sim in results[:top_n]:
            # cosine→1-10 匹配度（语义模式）；fallback 时给中性分
            if matched_by == "semantic":
                ms = max(1, min(10, round(float(sim) * 14)))
            else:
                ms = 6
            out.append({
                "id": j.id, "name_zh": j.name_zh, "name_en": j.name_en,
                "issn": j.issn, "impact_factor": j.impact_factor, "jcr_rank": j.jcr_rank,
                "category": j.category, "match_score": ms,
                "similarity": round(float(sim), 3) if matched_by == "semantic" else None,
                "review_days_avg": j.review_days_avg, "acceptance_rate": j.acceptance_rate,
                "is_open_access": j.is_open_access, "submission_url": j.submission_url,
            })
        logger.info(f"[journal_select] {matched_by} 匹配 → {len(out)} 本期刊")
        return {"journals": out, "matched_by": matched_by}

    def get_detail(self, db: Session, journal_id: int) -> dict:
        j = db.query(Journal).filter(Journal.id == journal_id).first()
        if not j:
            return {}
        return {
            "id": j.id,
            "name_zh": j.name_zh,
            "name_en": j.name_en,
            "issn": j.issn,
            "impact_factor": j.impact_factor,
            "jcr_rank": j.jcr_rank,
            "category": j.category,
            "submission_url": j.submission_url,
            "review_days_avg": j.review_days_avg,
            "acceptance_rate": j.acceptance_rate,
            "format_requirements": j.format_requirements,
            "is_open_access": j.is_open_access,
        }
