"""
文献综述 API。
两种输入：上传文件（txt/csv/bib）或填关键词；二选一即可。
提交 Celery 任务 → 轮询 status → 取 result / 下载 Word。
配额：5 credits。
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Form, File, UploadFile, Depends, HTTPException
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
from app.workers.literature_review_tasks import run_literature_review

router = APIRouter()

_QUOTA_COST = get_feature_cost("literature_review")
_VALID_TYPES = ("humanities", "science_engineering", "arts")
_EXT_FORMAT = {".txt": "txt", ".csv": "csv", ".bib": "bib"}


@router.post("/upload", summary="提交文献综述任务（文件或关键词）")
async def submit_review(
    file: Optional[UploadFile] = File(None, description="论文列表文件 txt/csv/bib"),
    keywords: str = Form("", description="关键词（逗号分隔，与文件二选一）"),
    topic: str = Form("", description="综述主题"),
    discipline: str = Form("", description="学科"),
    paper_type: str = Form("humanities"),
    citation_style: str = Form("gbt7714"),
    ctx: QuotaContext = Depends(require_quota("literature_review")),
    db: Session = Depends(get_db),
):
    if paper_type not in _VALID_TYPES:
        paper_type = "humanities"
    if not settings.BAILIAN_API_KEY and not settings.DEEPSEEK_API_KEY:
        raise HTTPException(503, "AI 服务未配置：请在 .env 配置 BAILIAN_API_KEY 或 DEEPSEEK_API_KEY")

    # 读取输入：文件优先，否则关键词
    input_text = ""
    input_format = "auto"
    if file is not None and file.filename:
        ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in _EXT_FORMAT:
            raise HTTPException(400, "仅支持 .txt / .csv / .bib 文件")
        raw = await file.read()
        input_text = raw.decode("utf-8", errors="ignore")
        input_format = _EXT_FORMAT[ext]

    if not input_text.strip() and not keywords.strip():
        raise HTTPException(400, "请上传论文列表文件，或填写关键词")

    # cost>1 预检
    if ctx.billing_on and ctx.quota_info.get("source") not in ("admin", "billing_off"):
        if get_total_remaining(db, ctx.user.id) < _QUOTA_COST:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "NO_QUOTA",
                    "message": f"文献综述需要 {_QUOTA_COST} 次额度，请先充值",
                    "pricing_url": "/api/v1/billing/pricing",
                },
            )

    task_id = str(uuid.uuid4())
    run_literature_review.apply_async(
        args=[task_id, input_text, input_format, keywords, topic, discipline,
              paper_type, citation_style, str(settings.OUTPUT_PATH)],
        task_id=task_id,
    )
    logger.info(f"[lit-review] 任务入队 task_id={task_id} type={paper_type}")

    if ctx.billing_on:
        consume_quota(db, ctx.user.id, "literature_review", task_id=task_id, cost=_QUOTA_COST)

    return {
        "task_id": task_id,
        "status": "pending",
        "quota_cost": _QUOTA_COST,
        "status_url": f"/api/v1/literature-review/status/{task_id}",
        "result_url": f"/api/v1/literature-review/result/{task_id}",
        "message": "文献综述任务已提交，正在后台执行",
    }


@router.get("/status/{task_id}", summary="查询文献综述进度")
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
    if state == "STARTED" and isinstance(result.info, dict):
        progress = result.info.get("progress", progress)
    resp = {"task_id": task_id, "status": status, "progress": progress}
    if state == "STARTED" and isinstance(result.info, dict):
        resp["progress_stage"] = result.info.get("message", "")
    if state == "FAILURE":
        resp["error"] = str(result.result)
    return resp


@router.get("/result/{task_id}", summary="获取文献综述结果")
def get_result(task_id: str):
    result = celery_app.AsyncResult(task_id)
    if result.state == "PENDING":
        raise HTTPException(202, "任务排队中，请稍候")
    if result.state in ("STARTED", "RETRY"):
        raise HTTPException(202, "综述生成中，请稍候")
    if result.state == "FAILURE":
        raise HTTPException(503, f"综述失败: {result.result}")
    if result.state != "SUCCESS":
        raise HTTPException(400, f"未知状态: {result.state}")
    return result.result


@router.get("/download/{report_id}", summary="下载文献综述报告")
def download_report(report_id: str):
    report_path = settings.OUTPUT_PATH / f"{report_id}_report.docx"
    if not report_path.exists():
        raise HTTPException(404, "报告文件不存在或已过期")
    return FileResponse(
        path=str(report_path),
        filename=f"文献综述_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
