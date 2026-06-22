"""
整篇写作辅助 Celery 任务。
镜像 topic_evaluation_tasks：new_event_loop 跑 async analyze_document + 进度回调 +
save_task_result 双写。core 逻辑在 app/core/writing_assistant/whole_doc.py。
"""

import asyncio

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from loguru import logger

from app.workers.celery_app import celery_app
from app.services.task_store import save_task_result, save_task_failure
from app.core.writing_assistant.whole_doc import analyze_document


class WritingWholeBaseTask(Task):
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"[Celery] 整篇写作辅助失败 task_id={task_id} exc={exc}")

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"[Celery] 整篇写作辅助成功 task_id={task_id}")


@celery_app.task(
    bind=True,
    base=WritingWholeBaseTask,
    queue="writing_assist",
    name="app.workers.writing_whole_tasks.run_writing_whole",
    max_retries=1,
    default_retry_delay=15,
    acks_late=True,
)
def run_writing_whole(self, task_id: str, file_path: str, paper_type: str) -> dict:
    logger.info(f"[Worker] 开始整篇写作辅助 task_id={task_id} type={paper_type}")

    def _progress(done: int, total: int):
        try:
            pct = int(done / total * 100) if total else 0
            self.update_state(
                state="STARTED",
                meta={"progress": pct, "message": f"已检查 {done}/{total} 段"},
            )
        except Exception:
            pass

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                analyze_document(file_path, paper_type, progress_cb=_progress)
            )
        finally:
            loop.close()

        save_task_result(task_id, "writing_whole", result, output_file=file_path)
        logger.info(
            f"[Worker] 整篇写作辅助完成 task_id={task_id} "
            f"送检={result.get('checked')} 建议={result.get('total_issues')}"
        )
        return result

    except SoftTimeLimitExceeded:
        logger.error(f"[Worker] 整篇写作辅助超时 task_id={task_id}")
        save_task_failure(task_id, "writing_whole", "任务超时")
        raise

    except Exception as exc:
        logger.error(f"[Worker] 整篇写作辅助异常 task_id={task_id} exc={exc}")
        save_task_failure(task_id, "writing_whole", str(exc))
        raise self.retry(exc=exc)
