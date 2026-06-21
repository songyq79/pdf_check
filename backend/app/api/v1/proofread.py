"""
统一校对 API

将原来的"错别字检查"和"AI 校对"合并为一个接口，通过 mode 参数区分深度：

  POST /api/v1/proofread/upload          → 上传文档，提交校对任务，立即返回 task_id
  GET  /api/v1/proofread/status/{id}     → 查询进度
  GET  /api/v1/proofread/download/{id}   → 下载结果
  DELETE /api/v1/proofread/task/{id}     → 撤销任务（仅 pending 状态有效）

mode 说明：
  "basic"（默认）→ 仅错别字 + 标点检查，速度快
  "full"         → 错别字 + 语法 + 段落逻辑，完整三轮
"""

import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from loguru import logger
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import get_db
from app.api.v1.deps import require_quota, QuotaContext
from app.services.billing_service import consume_quota
from app.models.pricing import get_feature_cost
from app.workers.celery_app import celery_app
from app.workers.proofread_tasks import run_proofread
from app.services.task_store import get_task_result_from_db

router = APIRouter()

PROOFREAD_DIR = settings.STORAGE_PATH / "proofread"
PROOFREAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload", summary="上传文档进行AI校对")
async def upload_for_proofread(
    file: UploadFile = File(...),
    ctx: QuotaContext = Depends(require_quota("proofread")),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(400, "仅支持 .docx 格式")

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE * 1024 * 1024:
        raise HTTPException(413, f"文件超过 {settings.MAX_FILE_SIZE}MB 限制")

    task_id = str(uuid.uuid4())   # ✅ 直接用uuid4

    in_path = PROOFREAD_DIR / f"{task_id}_in.docx"
    out_path = PROOFREAD_DIR / f"{task_id}_out.docx"

    try:
        in_path.write_bytes(content)
    except Exception as exc:
        raise HTTPException(500, f"文件保存失败: {exc}")

    run_proofread.apply_async(
        args=[task_id, str(in_path), str(out_path), "full"],
        task_id=task_id,
    )

    logger.info(f"[proofread] 任务已提交 task_id={task_id} file={file.filename}")

    if ctx.billing_on:
        consume_quota(db, ctx.user.id, "proofread", task_id=task_id,
                      cost=get_feature_cost("proofread"))

    return {
        "task_id": task_id,
        "filename": file.filename,
        "status": "pending",
        "status_url": f"/api/v1/proofread/status/{task_id}",
        "message": "文件已上传，正在后台进行AI校对",
    }


@router.get("/status/{task_id}", summary="查询校对进度")
def get_status(task_id: str):
    result = celery_app.AsyncResult(task_id)
    state  = result.state

    state_map = {
        "PENDING":  ("pending",    0),
        "STARTED":  ("processing", 20),
        "PROGRESS": ("processing", None),
        "SUCCESS":  ("completed",  100),
        "FAILURE":  ("failed",     0),
    }
    status, progress = state_map.get(state, ("pending", 0))

    if state == "PROGRESS":
        info = result.info or {}
        progress = info.get("progress", 50)

    resp = {"task_id": task_id, "status": status, "progress": progress}

    if state == "SUCCESS":
        res_data = result.result or {}
    elif state == "PENDING":
        # Redis 无记录（TTL过期 or 重启）→ 降级查 MySQL
        db_record = get_task_result_from_db(task_id)
        if db_record and db_record["status"] == "success":
            res_data = db_record["result"] or {}
            resp["status"] = "completed"
            resp["progress"] = 100
            resp["recovered_from_db"] = True
        elif db_record and db_record["status"] == "failure":
            resp["status"] = "failed"
            resp["error"] = db_record["error"]
            return resp
        else:
            return resp
    else:
        if state == "FAILURE":
            resp["error"] = str(result.result)
        return resp

    raw_stats = res_data.get("stats", {})
    checked = raw_stats.get("checked", 0)
    changed = raw_stats.get("changed", 0)
    resp["download_url"] = f"/api/v1/proofread/download/{task_id}"
    resp["stats"] = {
        "total":   checked,
        "changed": changed,
        "skipped": max(0, checked - changed),
    }
    resp["finished_at"] = datetime.now().isoformat()
    if res_data.get("warning"):
        resp["warning"] = res_data["warning"]
    if raw_stats.get("error"):
        resp["error"] = raw_stats["error"]

    return resp


@router.get("/download/{task_id}", summary="下载校对结果")
def download_result(task_id: str):
    result = celery_app.AsyncResult(task_id)

    if result.state != "SUCCESS":
        raise HTTPException(400, f"任务尚未完成（当前状态: {result.state}）")

    out_path = PROOFREAD_DIR / f"{task_id}_out.docx"
    if not out_path.exists():
        raise HTTPException(404, "结果文件不存在或已过期")

    # 固定文件名为 "AI 校对"
    filename = f"AI_校对_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx"

    return FileResponse(
        path=str(out_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.delete("/task/{task_id}", summary="撤销校对任务")
def cancel_task(task_id: str):
    result = celery_app.AsyncResult(task_id)

    if result.state not in ("PENDING", "STARTED"):
        raise HTTPException(400, f"任务已完成或失败，无法撤销（当前状态: {result.state}）")

    celery_app.control.revoke(task_id, terminate=True)
    logger.info(f"[proofread] 任务已撤销 task_id={task_id}")

    return {"task_id": task_id, "status": "cancelled", "message": "任务已撤销"}
