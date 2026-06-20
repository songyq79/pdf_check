"""
Phase 2 建表迁移 — 机构 / 机构学生，并给 users 表补多租户列。

用法：
  cd backend
  python -m migrations.add_phase2_institution_tables

幂等：create_all 只建缺失表；users 列用 try/except ALTER（已存在则跳过）。
对现有 C端 数据零影响（新列有默认值，个人用户 institution_id 为空）。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from sqlalchemy import text, inspect

from app.models.user import Base, engine
import app.models.institution  # noqa: F401 — 注册 Institution / InstitutionStudent

_NEW_TABLES = ["institutions", "institution_students"]
_USER_COLS = [
    "ALTER TABLE users ADD COLUMN institution_id INTEGER",
    "ALTER TABLE users ADD COLUMN user_type VARCHAR(30) DEFAULT 'individual'",
]


def run() -> None:
    logger.info(f"[migrate-p2] 创建表: {_NEW_TABLES}")
    Base.metadata.create_all(bind=engine)

    # 给 users 补列（幂等）
    with engine.connect() as conn:
        for ddl in _USER_COLS:
            try:
                conn.execute(text(ddl))
                conn.commit()
                logger.info(f"[migrate-p2] 执行: {ddl}")
            except Exception:
                conn.rollback()  # 列已存在

    tables = inspect(engine).get_table_names()
    missing = [t for t in _NEW_TABLES if t not in tables]
    if missing:
        raise RuntimeError(f"[migrate-p2] 建表失败，缺失: {missing}")

    cols = {c["name"] for c in inspect(engine).get_columns("users")}
    for need in ("institution_id", "user_type"):
        if need not in cols:
            raise RuntimeError(f"[migrate-p2] users 缺列: {need}")
    logger.info("[migrate-p2] Phase 2 多租户地基迁移完成 ✅")


if __name__ == "__main__":
    run()
