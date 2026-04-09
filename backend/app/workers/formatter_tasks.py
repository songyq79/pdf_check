"""
格式化 Celery Task
"""

from pathlib import Path

from celery import Task
from loguru import logger

from app.workers.celery_app import celery_app
from app.config import settings
from app.core.formatter import FormatEngine


class FormatterTask(Task):
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"[Celery] 格式化失败 task_id={task_id} exc={exc}")

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"[Celery] 格式化成功 task_id={task_id}")


@celery_app.task(
    bind=True,
    base=FormatterTask,
    queue="formatter",
    name="app.workers.formatter_tasks.run_formatting",
    max_retries=1,
    acks_late=True,
)
def run_formatting(
    self,
    task_id: str,
    input_path: str,
    output_path: str,
    template_id: str,
) -> dict:
    """Celery 格式化任务"""
    logger.info(f"[Worker] 开始格式化 task_id={task_id} template={template_id}")

    template_dir = settings.STORAGE_PATH.parent / "templates"
    engine = FormatEngine(template_dir=template_dir, use_ai=settings.USE_AI)

    try:
        result = engine.format_document(input_path, output_path, template_id)

        if result.get("success"):
            # 检查是否有警告信息（降级处理）
            response = {
                "stats": result.get("stats", {}),
                "template": result.get("template", {}),
                "time_elapsed": result.get("time_elapsed", 0),
            }
            
            if result.get("warning"):
                response["warning"] = result["warning"]
                logger.warning(f"[Worker] 格式化完成（降级模式） task_id={task_id} warning={result['warning']}")
            else:
                logger.info(f"[Worker] 格式化成功 task_id={task_id}")
            
            return response
        else:
            # 格式化失败，返回详细错误信息
            error_detail = result.get("detail", result.get("error", "未知错误"))
            suggestions = result.get("suggestions", [])
            
            # 如果有建议，添加到错误信息中
            if suggestions:
                error_msg = f"{error_detail}\n建议：\n" + "\n".join(f"• {s}" for s in suggestions)
            else:
                error_msg = error_detail
            
            raise Exception(error_msg)

    except Exception as exc:
        logger.error(f"[Worker] 格式化异常 task_id={task_id} exc={exc}")
        raise self.retry(exc=exc)
