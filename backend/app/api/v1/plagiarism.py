"""
论文查重 API
POST /api/v1/plagiarism/upload          → 上传文件,发起查重
GET  /api/v1/plagiarism/status/{id}     → 查询进度
GET  /api/v1/plagiarism/report/{id}     → 获取查重报告
GET  /api/v1/plagiarism/config          → 前端启动读取 feature flag
"""
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from loguru import logger
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import get_db
from app.api.v1.deps import require_quota, QuotaContext
from app.services.billing_service import consume_quota, check_quota, get_total_remaining
from app.models.pricing import get_feature_cost
from app.services.file_service import save_upload_file, validate_file
from app.workers.celery_app import celery_app
from app.workers.plagiarism_tasks import run_plagiarism_check

router = APIRouter()

_VALID_LANGUAGES = {"auto", "zh", "en"}


@router.get("/config", summary="前端启动读取 feature flag")
def get_plagiarism_config():
    return {
        "english_check_enabled": settings.ENABLE_ENGLISH_CHECK,
        "english_quota_cost": 2,
        "chinese_quota_cost": 1,
    }


@router.post("/upload", summary="发起查重（文件上传 或 粘贴文本，二选一）")
async def upload_and_check(
    file: Optional[UploadFile] = File(None),
    content: str = Form("", description="粘贴的论文文本（与 file 二选一，适合局部/快速自查）"),
    paper_type: str = Form(""),
    language: str = Form("auto"),
    ctx: QuotaContext = Depends(require_quota("plagiarism")),
    db: Session = Depends(get_db),
):
    if language not in _VALID_LANGUAGES:
        raise HTTPException(400, f"language 非法值: {language}")

    # Feature flag 拦截
    if language == "en" and not settings.ENABLE_ENGLISH_CHECK:
        raise HTTPException(400, "外文查重功能维护中,请使用中文查重")

    # 文件 / 粘贴文本 二选一
    if file is not None and file.filename:
        validate_file(file, allowed_types=[".docx", ".txt", ".pdf"], max_size_mb=20)
        file_path = await save_upload_file(file, settings.UPLOAD_PATH)
        logger.info(f"[plagiarism] 文件已保存 language={language}: {file_path}")
    elif content and content.strip():
        # 粘贴文本：存成临时 .txt，复用现有任务流程（任务零改动）
        text = content.strip()
        if len(text) < 50:
            raise HTTPException(400, "粘贴内容过短（至少 50 字）")
        tmp_path = Path(settings.UPLOAD_PATH) / f"paste_{uuid.uuid4().hex}.txt"
        tmp_path.write_text(text, encoding="utf-8")
        file_path = str(tmp_path)
        logger.info(f"[plagiarism] 粘贴文本已保存 language={language} 长度={len(text)}")
    else:
        raise HTTPException(400, "请上传文件或粘贴论文文本")

    # 计算本次扣费:显式 en → plagiarism_en;其他(含 auto 即便检测为 en) → plagiarism_cn,用户友好
    quota_cost = get_feature_cost("plagiarism_en" if language == "en" else "plagiarism_cn")

    # 多扣费路径预检:若配额不够扣 quota_cost 次,提前拒绝
    if ctx.billing_on and quota_cost > 1:
        quota_info = check_quota(db, ctx.user.id)
        # admin/billing_off 放行
        if quota_info["source"] not in ("admin", "billing_off"):
            if get_total_remaining(db, ctx.user.id) < quota_cost:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "code": "NO_QUOTA",
                        "message": f"本次查重需要 {quota_cost} 次额度,请先充值",
                        "pricing_url": "/api/v1/billing/pricing",
                    },
                )

    task_id = str(uuid.uuid4())
    run_plagiarism_check.apply_async(
        args=[task_id, str(file_path), paper_type, language],
        task_id=task_id,
        queue="plagiarism",
    )

    logger.info(f"[plagiarism] 任务已入队 task_id={task_id} language={language}")

    if ctx.billing_on:
        consume_quota(db, ctx.user.id, "plagiarism",
                      task_id=task_id, cost=quota_cost)

    return {
        "task_id": task_id,
        "status": "pending",
        "language": language,
        "quota_cost": quota_cost,
        "estimated_seconds": 25 if language == "en" else 8,
    }


@router.get("/status/{task_id}", summary="查询查重进度")
def get_status(task_id: str):
    result = celery_app.AsyncResult(task_id)
    state = result.state

    state_map = {
        "PENDING":  ("pending",    5),
        "STARTED":  ("processing", 30),
        "PROGRESS": ("processing", None),
        "RETRY":    ("processing", 20),
        "SUCCESS":  ("done",       100),
        "FAILURE":  ("failed",     0),
    }
    status, progress = state_map.get(state, ("pending", 5))

    stage = ""
    if state == "PROGRESS" and isinstance(result.info, dict):
        progress = result.info.get("progress", 50)
        stage = result.info.get("stage", "")

    resp = {"task_id": task_id, "status": status, "progress": progress, "stage": stage}
    if state == "FAILURE":
        resp["error"] = str(result.result)
    return resp


@router.get("/report/{task_id}", summary="获取查重报告")
def get_report(task_id: str):
    result = celery_app.AsyncResult(task_id)

    if result.state in ("PENDING", "STARTED", "PROGRESS", "RETRY"):
        raise HTTPException(202, "查重进行中,请稍候")
    if result.state == "FAILURE":
        err = str(result.result)
        if "TEXT_TOO_SHORT" in err:
            raise HTTPException(400, "文本少于200字,请上传完整论文")
        if "PDF 内容为空或为扫描版" in err or "PDF 解析失败" in err:
            raise HTTPException(400, err)
        raise HTTPException(503, f"查重失败: {err}")
    if result.state != "SUCCESS":
        raise HTTPException(400, f"未知状态: {result.state}")

    return result.result
