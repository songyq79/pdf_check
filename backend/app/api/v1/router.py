"""
API v1 路由总线
"""

from fastapi import APIRouter
from loguru import logger

api_router = APIRouter()

# ── 1. 错别字检查 ─────────────────────────────────────────
# 改后：合并为一块
try:
    from app.api.v1 import proofread
    api_router.include_router(
        proofread.router,
        prefix="/proofread",
        tags=["论文校对"],
    )
    logger.info("✅ Proofread 路由加载成功")
except Exception as e:
    logger.error(f"❌ Proofread 路由加载失败: {e}")

# ── 2. 智能评价 ───────────────────────────────────────────
try:
    from app.api.v1 import evaluation
    api_router.include_router(
        evaluation.router,
        prefix="/evaluation",
        tags=["智能评价"],
    )
    logger.info("✅ Evaluation 路由加载成功")
except Exception as e:
    logger.error(f"❌ Evaluation 路由加载失败: {e}")

# ── 3. 论文格式化 ─────────────────────────────────────────
try:
    from app.api.v1 import formatter
    api_router.include_router(
        formatter.router,
        prefix="/formatter",
        tags=["论文格式化"],
    )
    logger.info("✅ Formatter 路由加载成功")
except Exception as e:
    logger.error(f"❌ Formatter 路由加载失败: {e}")

