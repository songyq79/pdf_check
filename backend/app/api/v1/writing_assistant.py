"""
高级写作辅助 API（同步，实时逐段检查，不走 Celery）。
配额：每段检查 2 credits（前端按需触发，非每击键自动，避免烧额度）。
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import get_db
from app.api.v1.deps import require_quota, QuotaContext
from app.services.billing_service import consume_quota, get_total_remaining
from app.services.file_service import validate_file, save_upload_file
from app.models.pricing import get_feature_cost
from app.core.writing_assistant.analyzer import analyze_paragraph
from app.workers.celery_app import celery_app
from app.workers.writing_whole_tasks import run_writing_whole

router = APIRouter()

_QUOTA_COST = get_feature_cost("writing_assist")
_WHOLE_COST = get_feature_cost("writing_whole")
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


# ── 整篇检查（异步，上传 docx）────────────────────────────────

@router.post("/check-document", summary="整篇写作检查（上传 docx，异步）")
async def check_document(
    file: UploadFile = File(...),
    paper_type: str = Form("humanities"),
    ctx: QuotaContext = Depends(require_quota("writing_whole")),
    db: Session = Depends(get_db),
):
    if not settings.BAILIAN_API_KEY and not settings.DEEPSEEK_API_KEY:
        raise HTTPException(503, "AI 服务未配置")
    if paper_type not in _VALID_TYPES:
        paper_type = "humanities"

    validate_file(file, allowed_types=[".docx"], max_size_mb=20)
    file_path = await save_upload_file(file, settings.UPLOAD_PATH)

    # 整篇按 flat 计费，预检总额度
    if ctx.billing_on and ctx.quota_info.get("source") not in ("admin", "billing_off"):
        if get_total_remaining(db, ctx.user.id) < _WHOLE_COST:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "NO_QUOTA",
                    "message": f"整篇写作检查需要 {_WHOLE_COST} 次额度，请先充值",
                    "pricing_url": "/api/v1/billing/pricing",
                },
            )

    task_id = str(uuid.uuid4())
    run_writing_whole.apply_async(
        args=[task_id, str(file_path), paper_type],
        task_id=task_id,
        queue="writing_assist",
    )
    logger.info(f"[writing] 整篇任务入队 task_id={task_id} type={paper_type}")

    if ctx.billing_on:
        consume_quota(db, ctx.user.id, "writing_whole", task_id=task_id, cost=_WHOLE_COST)

    return {
        "task_id": task_id,
        "status": "pending",
        "quota_cost": _WHOLE_COST,
        "status_url": f"/api/v1/writing-assistant/document-status/{task_id}",
        "result_url": f"/api/v1/writing-assistant/document-result/{task_id}",
        "message": "整篇写作检查已提交，正在后台执行",
    }


@router.get("/document-status/{task_id}", summary="查询整篇检查进度")
def document_status(task_id: str):
    result = celery_app.AsyncResult(task_id)
    state = result.state
    state_map = {
        "PENDING": ("pending", 0),
        "STARTED": ("processing", 30),
        "RETRY": ("processing", 20),
        "SUCCESS": ("completed", 100),
        "FAILURE": ("failed", 0),
    }
    status, progress = state_map.get(state, ("pending", 0))
    if state == "STARTED" and isinstance(result.info, dict):
        progress = result.info.get("progress", progress)
    resp = {"task_id": task_id, "status": status, "progress": progress}
    if state == "FAILURE":
        resp["error"] = str(result.result)
    return resp


@router.get("/document-result/{task_id}", summary="获取整篇检查结果")
def document_result(task_id: str):
    result = celery_app.AsyncResult(task_id)
    if result.state == "PENDING":
        raise HTTPException(202, "任务排队中，请稍候")
    if result.state in ("STARTED", "RETRY"):
        raise HTTPException(202, "检查进行中，请稍候")
    if result.state == "FAILURE":
        raise HTTPException(503, f"检查失败: {result.result}")
    if result.state != "SUCCESS":
        raise HTTPException(400, f"未知状态: {result.state}")
    return result.result
