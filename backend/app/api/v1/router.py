"""
API v1 路由汇总
每个模块独立加载，单个模块失败不影响其他模块启动
"""

from fastapi import APIRouter
from loguru import logger

api_router = APIRouter()


# ── 错别字检查 ─────────────────────────────────────────────────────────
try:
    from app.api.v1 import spell_check
    api_router.include_router(
        spell_check.router,
        prefix="/spell-check",
        tags=["错别字检查"],
    )
    logger.info("✅ 路由加载成功: spell-check")
except Exception as e:
    logger.error(f"❌ 路由加载失败 [spell-check]: {e}")


# ── 智能评价 ──────────────────────────────────────────────────────────
try:
    from app.api.v1 import evaluation
    api_router.include_router(
        evaluation.router,
        prefix="/evaluation",
        tags=["智能评价"],
    )
    logger.info("✅ 路由加载成功: evaluation")
except Exception as e:
    logger.error(f"❌ 路由加载失败 [evaluation]: {e}")


# ── 论文格式化（主要格式化引擎）──────────────────────────────────────
try:
    from app.api.v1.formatter_api import router as formatter_router
    api_router.include_router(
        formatter_router,
        prefix="/formatter",
        tags=["论文格式化"],
    )
    logger.info("✅ 路由加载成功: formatter")
except Exception as e:
    logger.error(f"❌ 路由加载失败 [formatter]: {e}")


# ── AI校对（proofreadme pipeline）────────────────────────────────────
try:
    from app.api.v1.proofreader import router as proofreadme_router
    api_router.include_router(
        proofreadme_router,
        prefix="/proofreadme",
        tags=["AI校对"],
    )
    logger.info("✅ 路由加载成功: proofreadme")
except Exception as e:
    logger.error(f"❌ 路由加载失败 [proofreadme]: {e}")
