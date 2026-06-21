"""
高级写作辅助 API（同步，实时逐段检查，不走 Celery）。
配额：每段检查 2 credits（前端按需触发，非每击键自动，避免烧额度）。
"""

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import get_db
from app.api.v1.deps import require_quota, QuotaContext
from app.services.billing_service import consume_quota
from app.models.pricing import get_feature_cost
from app.core.writing_assistant.analyzer import analyze_paragraph

router = APIRouter()

_QUOTA_COST = get_feature_cost("writing_assist")
_VALID_TYPES = ("humanities", "science_engineering", "arts")
_MAX_LEN = 2000


class WritingCheckRequest(BaseModel):
    paragraph: str
    paper_type: str = "humanities"


@router.post("/check", summary="逐段写作检查（实时，消耗 2 次）")
async def check(
    req: WritingCheckRequest,
    ctx: QuotaContext = Depends(require_quota("writing_assist")),
    db: Session = Depends(get_db),
):
    paragraph = (req.paragraph or "").strip()
    if not paragraph:
        raise HTTPException(400, "段落内容为空")
    if len(paragraph) > _MAX_LEN:
        raise HTTPException(400, f"单段过长（>{_MAX_LEN} 字），请分段检查")
    if not settings.BAILIAN_API_KEY and not settings.DEEPSEEK_API_KEY:
        raise HTTPException(503, "AI 服务未配置")
    paper_type = req.paper_type if req.paper_type in _VALID_TYPES else "humanities"

    result = await analyze_paragraph(paragraph, paper_type)

    # 检查成功后扣费（每段 2 次）
    if ctx.billing_on:
        consume_quota(db, ctx.user.id, "writing_assist", cost=_QUOTA_COST)

    result["quota_cost"] = _QUOTA_COST
    logger.info(f"[writing] 段落检查完成 issue_count={result.get('issue_count')}")
    return result
