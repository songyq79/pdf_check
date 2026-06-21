"""
选题评估 API。
表单输入（非文件上传）→ 提交 Celery 任务 → 轮询 status → 取 result / 下载 Word。
配额：3 credits（require_quota + consume_quota cost=3）。
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
from app.services.billing_service import consume_quota, check_quota, get_total_remaining
from app.models.pricing import get_feature_cost
from app.workers.celery_app import celery_app
from app.workers.topic_evaluation_tasks import run_topic_evaluation

router = APIRouter()

_QUOTA_COST = get_feature_cost("topic_evaluation")
_VALID_TYPES = ("humanities", "science_engineering", "arts")


@router.post("/upload", summary="提交选题评估任务")
async def submit_topic(
    question: str = Form(..., description="拟研究问题"),
    description: str = Form("", description="研究方向描述"),
    discipline: str = Form("", description="学科分类"),
    degree_level: str = Form("", description="学位阶段：本科/硕士/博士"),
    paper_type: str = Form("humanities", description="论文类别"),
    ctx: QuotaContext = Depends(require_quota("topic_evaluation")),
    db: Session = Depends(get_db),
):
    if not question or not question.strip():
        raise HTTPException(400, "请填写拟研究问题")
    if paper_type not in _VALID_TYPES:
        paper_type = "humanities"
    if not settings.BAILIAN_API_KEY and not settings.DEEPSEEK_API_KEY:
        raise HTTPException(503, "AI 服务未配置：请在 .env 配置 BAILIAN_API_KEY 或 DEEPSEEK_API_KEY")

    # cost>1 预检：总额度不足提前拒绝（与查重一致）
    if ctx.billing_on and ctx.quota_info.get("source") not in ("admin", "billing_off"):
        if get_total_remaining(db, ctx.user.id) < _QUOTA_COST:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "NO_QUOTA",
                    "message": f"选题评估需要 {_QUOTA_COST} 次额度，请先充值",
                    "pricing_url": "/api/v1/billing/pricing",
                },
            )

    task_id = str(uuid.uuid4())
    run_topic_evaluation.apply_async(
        args=[task_id, question, description, discipline, degree_level,
              paper_type, str(settings.OUTPUT_PATH)],
        task_id=task_id,
    )
    logger.info(f"[topic-eval] 任务入队 task_id={task_id} type={paper_type}")

    if ctx.billing_on:
        consume_quota(db, ctx.user.id, "topic_evaluation", task_id=task_id, cost=_QUOTA_COST)

    return {
        "task_id": task_id,
        "status": "pending",
        "quota_cost": _QUOTA_COST,
        "status_url": f"/api/v1/topic-evaluation/status/{task_id}",
        "result_url": f"/api/v1/topic-evaluation/result/{task_id}",
        "message": "选题评估任务已提交，正在后台执行",
    }


@router.get("/status/{task_id}", summary="查询选题评估进度")
def get_status(task_id: str):
    result = celery_app.AsyncResult(task_id)
    state = result.state

    state_map = {
        "PENDING": ("pending", 0),
        "STARTED": ("processing", 40),
        "RETRY": ("processing", 20),
        "SUCCESS": ("completed", 100),
        "FAILURE": ("failed", 0),
    }
    status, progress = state_map.get(state, ("pending", 0))

    # STARTED 时若任务回传了细粒度进度，优先用它
    if state == "STARTED" and isinstance(result.info, dict):
        progress = result.info.get("progress", progress)

    resp = {"task_id": task_id, "status": status, "progress": progress}
    if state == "FAILURE":
        resp["error"] = str(result.result)
    return resp


@router.get("/result/{task_id}", summary="获取选题评估结果")
def get_result(task_id: str):
    result = celery_app.AsyncResult(task_id)

    if result.state == "PENDING":
        raise HTTPException(202, "任务排队中，请稍候")
    if result.state in ("STARTED", "RETRY"):
        raise HTTPException(202, "评估进行中，请稍候")
    if result.state == "FAILURE":
        raise HTTPException(503, f"评估失败: {result.result}")
    if result.state != "SUCCESS":
        raise HTTPException(400, f"未知状态: {result.state}")

    return result.result


@router.get("/download/{report_id}", summary="下载选题评估报告")
def download_report(report_id: str):
    report_path = settings.OUTPUT_PATH / f"{report_id}_report.docx"
    if not report_path.exists():
        raise HTTPException(404, "报告文件不存在或已过期")
    return FileResponse(
        path=str(report_path),
        filename=f"选题评估报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
