"""
Phase 1 建表迁移脚本 — 选题评估 / 文献综述 / 期刊库

用法：
  cd backend
  python -m migrations.add_phase1_tables

幂等：create_all 只创建缺失的表，不会 ALTER 或删除现有表，
对 evaluation/proofread/formatter/plagiarism 等存量数据零影响。
"""

import sys
from pathlib import Path

# 确保 backend/ 在 sys.path（直接 python migrations/xxx.py 时）
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from app.models.user import Base, engine
import app.models.phase1  # noqa: F401 — 注册 TopicEvaluation/LiteratureReview/Journal


_NEW_TABLES = ["topic_evaluations", "literature_reviews", "journals"]


def run() -> None:
    logger.info(f"[migrate] 创建 Phase 1 表: {_NEW_TABLES}")
    before = set(_existing_tables())
    Base.metadata.create_all(bind=engine)
    after = set(_existing_tables())
    created = sorted(after - before)
    if created:
        logger.info(f"[migrate] 新建表: {created}")
    else:
        logger.info("[migrate] 目标表已存在，无需新建")
    missing = [t for t in _NEW_TABLES if t not in after]
    if missing:
        raise RuntimeError(f"[migrate] 建表失败，缺失: {missing}")
    logger.info("[migrate] Phase 1 建表完成 ✅")


def _existing_tables() -> list:
    from sqlalchemy import inspect
    return inspect(engine).get_table_names()


if __name__ == "__main__":
    run()
