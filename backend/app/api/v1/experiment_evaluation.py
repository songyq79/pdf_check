"""
实验设计评审 API（理工科，异步）。
表单输入实验方案 → Celery 任务 → 轮询 → 结果 / 下载 Word。配额：3 credits。
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from loguru import logger
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import get_db
from app.models.billing import QuotaBalance
from app.api.v1.deps import require_quota, QuotaContext
from app.services.billing_service import consume_quota, get_total_remaining
from app.models.pricing import get_feature_cost
from app.workers.celery_app import celery_app
from app.workers.experiment_evaluation_tasks import run_experiment_evaluation

router = APIRouter()

_QUOTA_COST = get_feature_cost("experiment_evaluation")


@router.post("/upload", summary="提交实验设计评审任务")
async def submit_experiment(
    plan_text: str = Form(..., description="实验方案全文"),
    discipline: str = Form("", description="学科（如生物学/化学/材料）"),
    ctx: QuotaContext = Depends(require_quota("experiment_evaluation")),
    db: Session = Depends(get_db),
):
    plan = (plan_text or "").strip()
    if len(plan) < 30:
        raise HTTPException(400, "实验方案内容过短，请补充详细方案")
    if not settings.BAILIAN_API_KEY and not settings.DEEPSEEK_API_KEY:
        raise HTTPException(503, "AI 服务未配置")

    if ctx.billing_on and ctx.quota_info.get("source") not in ("admin", "billing_off"):
        if get_total_remaining(db, ctx.user.id) < _QUOTA_COST:
            raise HTTPException(
                status_code=402,
                detail={"code": "NO_QUOTA", "message": f"实验评审需要 {_QUOTA_COST} 次额度，请先充值",
                        "pricing_url": "/api/v1/billing/pricing"},
            )

    task_id = str(uuid.uuid4())
    run_experiment_evaluation.apply_async(
        args=[task_id, plan, discipline, str(settings.OUTPUT_PATH)],
        task_id=task_id,
    )
    logger.info(f"[exp-eval] 任务入队 task_id={task_id}")

    if ctx.billing_on:
        consume_quota(db, ctx.user.id, "experiment_evaluation", task_id=task_id, cost=_QUOTA_COST)

    return {
        "task_id": task_id,
        "status": "pending",
        "quota_cost": _QUOTA_COST,
        "status_url": f"/api/v1/experiment-evaluation/status/{task_id}",
        "result_url": f"/api/v1/experiment-evaluation/result/{task_id}",
        "message": "实验设计评审任务已提交",
    }


@router.get("/status/{task_id}", summary="查询实验评审进度")
def get_status(task_id: str):
    result = celery_app.AsyncResult(task_id)
    state = result.state
    state_map = {
        "PENDING": ("pending", 0), "STARTED": ("processing", 40),
        "RETRY": ("processing", 20), "SUCCESS": ("completed", 100), "FAILURE": ("failed", 0),
    }
    status, progress = state_map.get(state, ("pending", 0))
    if state == "STARTED" and isinstance(result.info, dict):
        progress = result.info.get("progress", progress)
    resp = {"task_id": task_id, "status": status, "progress": progress}
    if state == "FAILURE":
        resp["error"] = str(result.result)
    return resp


@router.get("/result/{task_id}", summary="获取实验评审结果")
def get_result(task_id: str):
    result = celery_app.AsyncResult(task_id)
    if result.state == "PENDING":
        raise HTTPException(202, "任务排队中，请稍候")
    if result.state in ("STARTED", "RETRY"):
        raise HTTPException(202, "评审进行中，请稍候")
    if result.state == "FAILURE":
        raise HTTPException(503, f"评审失败: {result.result}")
    if result.state != "SUCCESS":
        raise HTTPException(400, f"未知状态: {result.state}")
    return result.result


@router.get("/download/{report_id}", summary="下载实验评审报告")
def download_report(report_id: str):
    report_path = settings.OUTPUT_PATH / f"{report_id}_report.docx"
    if not report_path.exists():
        raise HTTPException(404, "报告文件不存在或已过期")
    return FileResponse(
        path=str(report_path),
        filename=f"实验设计评审_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
