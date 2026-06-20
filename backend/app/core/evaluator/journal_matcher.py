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
