"""
论文格式化 API
POST /api/v1/formatter/format             → 上传文档 + 模板ID，格式化
GET  /api/v1/formatter/templates          → 获取模板列表
GET  /api/v1/formatter/status/{id}        → 查询进度
GET  /api/v1/formatter/download/{id}      → 下载结果
POST /api/v1/formatter/templates/upload   → 上传自定义模板
POST /api/v1/formatter/preview            → 预览文档结构
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from loguru import logger

from app.config import settings
from app.core.formatter import FormatEngine
from app.workers.celery_app import celery_app
from app.workers.formatter_tasks import run_formatting

router = APIRouter()

FORMATTER_DIR = settings.STORAGE_PATH / "formatter"
FORMATTER_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATE_DIR = settings.STORAGE_PATH.parent / "templates"
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

# 格式化引擎单例（用于模板查询等轻量操作）
format_engine = FormatEngine(template_dir=TEMPLATE_DIR, use_ai=settings.USE_AI)


@router.post("/format", summary="格式化论文")
async def format_paper(
    file: UploadFile = File(...),
    template_id: str = Form(...),
):
    """上传 .docx + 模板ID → 提交 Celery 格式化任务 → 立即返回 task_id"""
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(400, "仅支持 .docx 格式")

    task_id    = str(uuid.uuid4())
    input_path  = FORMATTER_DIR / f"{task_id}_input.docx"
    output_path = FORMATTER_DIR / f"{task_id}_output.docx"

    content = await file.read()
    if not content:
        raise HTTPException(400, "文件内容为空，请重新上传")
    input_path.write_bytes(content)
    logger.info(f"[formatter] 文件已保存 size={len(content)} path={input_path}")

    run_formatting.apply_async(
        args=[task_id, str(input_path), str(output_path), template_id],
        task_id=task_id,
    )

    logger.info(f"[formatter] 任务已提交 task_id={task_id} template={template_id}")

    return {
        "success": True,
        "task_id": task_id,
        "status": "pending",
        "status_url": f"/api/v1/formatter/status/{task_id}",
        "download_url": f"/api/v1/formatter/download/{task_id}",
    }


@router.get("/templates", summary="获取模板列表")
def list_templates(
    category: Optional[str] = Query(None, description="分类: universities/journals/custom"),
    search:   Optional[str] = Query(None, description="搜索关键词"),
):
    templates = format_engine.template_manager.list_templates(
        category=category, search=search
    )
    template_list = [
        {
            "id":               t.template_id,
            "name":             t.name,
            "category":         t.category,
            "school_or_journal": t.school_or_journal,
            "description":      t.description,
            "usage_count":      t.usage_count,
        }
        for t in templates
    ]
    categories: dict = {}
    for t in templates:
        categories[t.category] = categories.get(t.category, 0) + 1

    return {"success": True, "total": len(template_list), "categories": categories, "templates": template_list}


@router.get("/status/{task_id}", summary="查询格式化进度")
def get_format_status(task_id: str):
    result = celery_app.AsyncResult(task_id)

    state_map = {
        "PENDING": ("pending",    0),
        "STARTED": ("processing", 50),
        "SUCCESS": ("completed",  100),
        "FAILURE": ("failed",     0),
    }
    status, progress = state_map.get(result.state, ("pending", 0))

    resp = {"task_id": task_id, "status": status, "progress": progress}

    if result.state == "SUCCESS":
        result_data = result.result or {}
        resp["result"] = result_data.get("stats")
        resp["download_url"] = f"/api/v1/formatter/download/{task_id}"
        
        # 添加警告信息（如果有）
        if result_data.get("warning"):
            resp["warning"] = result_data["warning"]
            
    elif result.state == "FAILURE":
        resp["error"] = str(result.info)

    return resp


@router.get("/download/{task_id}", summary="下载格式化结果")
def download_formatted(task_id: str):
    result = celery_app.AsyncResult(task_id)

    if result.state == "PENDING":
        raise HTTPException(404, "任务不存在或排队中")
    if result.state != "SUCCESS":
        raise HTTPException(400, f"任务未完成（当前状态: {result.state}）")

    output_path = FORMATTER_DIR / f"{task_id}_output.docx"
    if not output_path.exists():
        raise HTTPException(404, "结果文件已被清理或不存在")

    original_name = "result.docx"
    if isinstance(result.result, dict):
        original_name = result.result.get("filename", "result.docx")

    return FileResponse(
        path=str(output_path),
        filename=f"格式化_{original_name}",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.post("/templates/upload", summary="上传自定义模板")
async def upload_template(
    file:             UploadFile = File(...),
    name:             str = Form(...),
    category:         str = Form("custom"),
    school_or_journal: str = Form(""),
    description:      str = Form(""),
):
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(400, "仅支持 .docx 格式")

    temp_path = FORMATTER_DIR / f"temp_{uuid.uuid4()}.docx"
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        validation = format_engine.validate_template(str(temp_path))
        if not validation["valid"]:
            temp_path.unlink(missing_ok=True)
            raise HTTPException(400, f"模板验证失败: {validation['errors']}")

        from app.core.formatter.template_manager import TemplateMetadata
        metadata = TemplateMetadata(
            template_id=str(uuid.uuid4())[:16],
            name=name,
            category=category,
            school_or_journal=school_or_journal or name,
            description=description,
            is_public=False,
        )
        template_id = format_engine.template_manager.save_template(temp_path, metadata)
        temp_path.unlink(missing_ok=True)

        return {"success": True, "template_id": template_id, "name": name, "message": "模板上传成功"}

    except HTTPException:
        raise
    except Exception as exc:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(500, f"上传失败: {exc}")


@router.post("/preview", summary="预览文档结构")
async def preview_structure(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(400, "仅支持 .docx 格式")

    temp_path = FORMATTER_DIR / f"preview_{uuid.uuid4()}.docx"
    try:
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        result = format_engine.preview_structure(str(temp_path))
        temp_path.unlink(missing_ok=True)

        return {
            "success":  True,
            "filename": file.filename,
            "sections": result["sections"],
            "stats":    result["stats"],
            "quality":  result["quality"],
            "outline":  format_engine.analyzer.export_outline(),
        }
    except Exception as exc:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(500, f"预览失败: {exc}")
