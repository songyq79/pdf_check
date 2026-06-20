"""
选题评估 Celery 任务。
镜像 evaluation_tasks.py：new_event_loop 跑 async 编排 + 进度回调 +
生成 Word + save_task_result 双写。core 逻辑在 app/core/topic_evaluator/。
"""

import uuid
import asyncio
from pathlib import Path

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from loguru import logger

from app.workers.celery_app import celery_app
from app.services.task_store import save_task_result, save_task_failure
from app.core.topic_evaluator.evaluator import evaluate_topic
from app.core.topic_evaluator.report_generator import generate_topic_report


class TopicEvalBaseTask(Task):
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"[Celery] 选题评估失败 task_id={task_id} exc={exc}")

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"[Celery] 选题评估成功 task_id={task_id}")


@celery_app.task(
    bind=True,
    base=TopicEvalBaseTask,
    queue="topic_eval",
    name="app.workers.topic_evaluation_tasks.run_topic_evaluation",
    max_retries=1,
    default_retry_delay=15,
    acks_late=True,
)
def run_topic_evaluation(
    self,
    task_id: str,
    question: str,
    description: str,
    discipline: str,
    degree_level: str,
    paper_type: str,
    report_output_path: str,
) -> dict:
    logger.info(f"[Worker] 开始选题评估 task_id={task_id} type={paper_type}")

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
                evaluate_topic(
                    question=question,
                    description=description,
                    discipline=discipline,
                    degree_level=degree_level,
                    paper_type=paper_type,
                    progress_cb=_progress,
                )
            )
        finally:
            loop.close()

        # 生成 Word 报告（失败不阻断结果）
        report_id = str(uuid.uuid4())
        target_dir = Path(report_output_path)
        target_dir.mkdir(parents=True, exist_ok=True)
        report_path = target_dir / f"{report_id}_report.docx"
        try:
            generate_topic_report(result, report_path)
            result["report_id"] = report_id
            result["report_download_url"] = f"/api/v1/topic-evaluation/download/{report_id}"
        except Exception as exc:
            logger.error(f"[Worker] 选题评估报告生成失败: {exc}")

        save_task_result(task_id, "topic_evaluation", result,
                         output_file=str(report_path))
        logger.info(f"[Worker] 选题评估完成 task_id={task_id} "
                    f"overall={result.get('scores', {}).get('overall')}")
        return result

    except SoftTimeLimitExceeded:
        logger.error(f"[Worker] 选题评估超时 task_id={task_id}")
        save_task_failure(task_id, "topic_evaluation", "任务超时")
        raise

    except Exception as exc:
        logger.error(f"[Worker] 选题评估异常 task_id={task_id} exc={exc}")
        save_task_failure(task_id, "topic_evaluation", str(exc))
        raise self.retry(exc=exc)
