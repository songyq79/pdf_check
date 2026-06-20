"""
Phase 1 新增数据表模型 — 选题评估 / 文献综述 / 期刊库
表结构对应 PRD「数据库变化」一节。
JSON 列用 SQLAlchemy 通用 JSON 类型（SQLite 存 TEXT，MySQL 存 JSON）。
结果同时双写 TaskRecord（task_type 区分），本表为业务侧明细。
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, JSON, Index,
)

from app.models.user import Base


class TopicEvaluation(Base):
    __tablename__ = "topic_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    task_id = Column(String(64), index=True, nullable=False)
    question = Column(Text, nullable=True)            # 拟研究问题
    description = Column(Text, nullable=True)          # 研究方向描述
    discipline = Column(String(50), nullable=True)     # 学科分类
    degree_level = Column(String(20), nullable=True)   # 本科/硕士/博士
    evaluation_result = Column(JSON, nullable=True)    # 三维评分 + 分析
    related_papers = Column(JSON, nullable=True)       # 检索到的相关文献
    created_at = Column(DateTime, default=datetime.utcnow)


class LiteratureReview(Base):
    __tablename__ = "literature_reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    task_id = Column(String(64), index=True, nullable=False)
    input_papers = Column(JSON, nullable=True)         # 用户输入的论文/关键词
    enriched_papers = Column(JSON, nullable=True)      # 补检后的文献集
    categorization = Column(JSON, nullable=True)       # 分类结果
    draft_content = Column(Text, nullable=True)        # 综述初稿正文
    created_at = Column(DateTime, default=datetime.utcnow)


class Journal(Base):
    __tablename__ = "journals"

    id = Column(Integer, primary_key=True, index=True)
    name_zh = Column(String(200), nullable=True)
    name_en = Column(String(200), nullable=True)
    issn = Column(String(20), index=True, nullable=True)
    impact_factor = Column(Float, nullable=True)
    jcr_rank = Column(String(50), nullable=True)
    category = Column(String(100), index=True, nullable=True)
    submission_url = Column(String(500), nullable=True)
    review_days_avg = Column(Integer, nullable=True)
    acceptance_rate = Column(Float, nullable=True)
    format_requirements = Column(JSON, nullable=True)
    is_open_access = Column(Boolean, default=False)


# 复合索引:按学科 + 影响因子筛选期刊（journal_matcher 主查询路径）
Index("ix_journals_category_if", Journal.category, Journal.impact_factor)
