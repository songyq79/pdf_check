"""
API v1 路由总线
"""

from fastapi import APIRouter
from loguru import logger

api_router = APIRouter()

# ── 0. 认证 ───────────────────────────────────────────────
try:
    from app.api.v1 import auth
    api_router.include_router(
        auth.router,
        prefix="/auth",
        tags=["认证"],
    )
    logger.info("✅ Auth 路由加载成功")
except Exception as e:
    logger.error(f"❌ Auth 路由加载失败: {e}")

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

# ── 4. 论文查重 ───────────────────────────────────────────
try:
    from app.api.v1 import plagiarism
    api_router.include_router(
        plagiarism.router,
        prefix="/plagiarism",
        tags=["论文查重"],
    )
    logger.info("✅ Plagiarism 路由加载成功")
except Exception as e:
    logger.error(f"❌ Plagiarism 路由加载失败: {e}")

# ── 5. 计费 ──────────────────────────────────────────────
try:
    from app.api.v1 import billing
    api_router.include_router(
        billing.router,
        prefix="/billing",
        tags=["计费"],
    )
    logger.info("✅ Billing 路由加载成功")
except Exception as e:
    logger.error(f"❌ Billing 路由加载失败: {e}")

# ── 6. 管理后台 ──────────────────────────────────────────
try:
    from app.api.v1 import admin
    api_router.include_router(
        admin.router,
        prefix="/admin",
        tags=["管理后台"],
    )
    logger.info("✅ Admin 路由加载成功")
except Exception as e:
    logger.error(f"❌ Admin 路由加载失败: {e}")

# ── 7. 管理后台 — 本地论文库 ─────────────────────────────
try:
    from app.api.v1 import admin_papers
    api_router.include_router(
        admin_papers.router,
        prefix="/admin/local-papers",
        tags=["管理后台-论文库"],
    )
    logger.info("✅ AdminPapers 路由加载成功")
except Exception as e:
    logger.error(f"❌ AdminPapers 路由加载失败: {e}")

# ── 8. 选题评估（Phase 1，Loop 0 占位）────────────────────
try:
    from app.api.v1 import topic_evaluation
    api_router.include_router(
        topic_evaluation.router,
        prefix="/topic-evaluation",
        tags=["选题评估"],
    )
    logger.info("✅ TopicEvaluation 路由加载成功")
except Exception as e:
    logger.error(f"❌ TopicEvaluation 路由加载失败: {e}")

# ── 9. 文献综述（Phase 1，Loop 0 占位）────────────────────
try:
    from app.api.v1 import literature_review
    api_router.include_router(
        literature_review.router,
        prefix="/literature-review",
        tags=["文献综述"],
    )
    logger.info("✅ LiteratureReview 路由加载成功")
except Exception as e:
    logger.error(f"❌ LiteratureReview 路由加载失败: {e}")
