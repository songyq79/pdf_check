"""
校对 Celery Task

统一处理 basic（错别字）和 full（完整三轮）两种模式。
"""

from app.workers.celery_app import celery_app
from app.core.proofreadme.pipeline import process_word_sync
from app.services.task_store import save_task_result, save_task_failure
from loguru import logger


@celery_app.task(
    bind=True,
    name="run_proofread",
    queue="proofread",
    soft_time_limit=540,
    time_limit=600,
    max_retries=2,
)
def run_proofread(self, task_id: str, in_path: str, out_path: str, mode: str = "full"):
    """
    Celery 校对任务。

    Args:
        task_id: 任务 ID（仅用于日志）
        in_path:  输入文档路径
        out_path: 输出文档路径
        mode:     "basic" | "full"（默认 "full"）
    """
    logger.info(f"[task] 开始校对 task_id={task_id} mode={mode}")
    try:
        self.update_state(state="PROGRESS", meta={"progress": 10})
        stats = process_word_sync(in_path, out_path, mode=mode)
        self.update_state(state="PROGRESS", meta={"progress": 95})
        
        # 检查是否有错误或使用了降级模式
        result = {"stats": stats, "mode": mode}

        if stats.get("fallback_mode"):
            result["warning"] = "文档格式异常，已使用简化模式处理（可能丢失部分格式）"
            logger.warning(f"[task] 校对完成（降级模式） task_id={task_id} stats={stats}")
        elif stats.get("error"):
            logger.error(f"[task] 校对失败 task_id={task_id} error={stats['error']}")
        else:
            logger.info(f"[task] 校对完成 task_id={task_id} stats={stats}")

        # 永久存储到 MySQL（Redis TTL过期后仍可查询）
        import os
        out_filename = os.path.basename(out_path) if os.path.exists(out_path) else None
        save_task_result(task_id, "proofread", result, output_file=out_filename)

        return result
    except Exception as exc:
        logger.error(f"[task] 校对失败 task_id={task_id}: {exc}")
        save_task_failure(task_id, "proofread", str(exc))
        raise self.retry(exc=exc)
