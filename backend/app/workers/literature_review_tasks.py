"""
文献综述 Celery 任务。
镜像 topic_evaluation_tasks：new_event_loop 跑 async 五步编排 + 进度回调 +
生成 Word + save_task_result 双写。core 逻辑在 app/core/literature_reviewer/。
"""

import uuid
import asyncio
from pathlib import Path

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from loguru import logger

from app.workers.celery_app import celery_app
from app.services.task_store import save_task_result, save_task_failure
from app.core.literature_reviewer.reviewer import generate_review
from app.core.literature_reviewer.report_generator import generate_review_report


class LitReviewBaseTask(Task):
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"[Celery] 文献综述失败 task_id={task_id} exc={exc}")

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"[Celery] 文献综述成功 task_id={task_id}")


@celery_app.task(
    bind=True,
    base=LitReviewBaseTask,
    queue="lit_review",
    name="app.workers.literature_review_tasks.run_literature_review",
    max_retries=1,
    default_retry_delay=15,
    acks_late=True,
)
def run_literature_review(
    self,
    task_id: str,
    input_text: str,
    input_format: str,
    keywords: str,
    topic: str,
    discipline: str,
    paper_type: str,
    citation_style: str,
    report_output_path: str,
) -> dict:
    logger.info(f"[Worker] 开始文献综述 task_id={task_id} type={paper_type}")

    def _progress(pct: int, msg: str):
        try:
            self.update_state(state="STARTED", meta={"progress": pct, "message": msg})
        except Exception:
            pass

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                generate_review(
                    input_text=input_text,
                    input_format=input_format,
                    keywords=keywords,
                    topic=topic,
                    discipline=discipline,
                    paper_type=paper_type,
                    citation_style=citation_style,
                    progress_cb=_progress,
                )
            )
        finally:
            loop.close()

        report_id = str(uuid.uuid4())
        target_dir = Path(report_output_path)
        target_dir.mkdir(parents=True, exist_ok=True)
        report_path = target_dir / f"{report_id}_report.docx"
        try:
            generate_review_report(result, report_path)
            result["report_id"] = report_id
            result["report_download_url"] = f"/api/v1/literature-review/download/{report_id}"
        except Exception as exc:
            logger.error(f"[Worker] 文献综述报告生成失败: {exc}")

        save_task_result(task_id, "literature_review", result,
                         output_file=str(report_path))
        logger.info(f"[Worker] 文献综述完成 task_id={task_id} "
                    f"papers={result.get('meta', {}).get('papers_total')}")
        return result

    except SoftTimeLimitExceeded:
        logger.error(f"[Worker] 文献综述超时 task_id={task_id}")
        save_task_failure(task_id, "literature_review", "任务超时")
        raise

    except Exception as exc:
        logger.error(f"[Worker] 文献综述异常 task_id={task_id} exc={exc}")
        save_task_failure(task_id, "literature_review", str(exc))
        raise self.retry(exc=exc)
