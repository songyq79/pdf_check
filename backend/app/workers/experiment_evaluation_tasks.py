"""
实验设计评审 Celery 任务。
镜像 topic_evaluation_tasks：new_event_loop 跑 async 评审 + 进度回调 +
生成 Word + save_task_result 双写。core 逻辑在 app/core/experiment_evaluator/。
"""

import uuid
import asyncio
from pathlib import Path

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from loguru import logger

from app.workers.celery_app import celery_app
from app.services.task_store import save_task_result, save_task_failure
from app.core.experiment_evaluator.evaluator import review_experiment
from app.core.experiment_evaluator.report_generator import generate_experiment_report


class ExperimentEvalBaseTask(Task):
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"[Celery] 实验评审失败 task_id={task_id} exc={exc}")

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"[Celery] 实验评审成功 task_id={task_id}")


@celery_app.task(
    bind=True,
    base=ExperimentEvalBaseTask,
    queue="experiment_eval",
    name="app.workers.experiment_evaluation_tasks.run_experiment_evaluation",
    max_retries=1,
    default_retry_delay=15,
    acks_late=True,
)
def run_experiment_evaluation(
    self,
    task_id: str,
    plan_text: str,
    discipline: str,
    report_output_path: str,
) -> dict:
    logger.info(f"[Worker] 开始实验评审 task_id={task_id}")

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
                review_experiment(plan_text=plan_text, discipline=discipline, progress_cb=_progress)
            )
        finally:
            loop.close()

        report_id = str(uuid.uuid4())
        target_dir = Path(report_output_path)
        target_dir.mkdir(parents=True, exist_ok=True)
        report_path = target_dir / f"{report_id}_report.docx"
        try:
            generate_experiment_report(result, report_path)
            result["report_id"] = report_id
            result["report_download_url"] = f"/api/v1/experiment-evaluation/download/{report_id}"
        except Exception as exc:
            logger.error(f"[Worker] 实验评审报告生成失败: {exc}")

        save_task_result(task_id, "experiment_evaluation", result, output_file=str(report_path))
        logger.info(f"[Worker] 实验评审完成 task_id={task_id} overall={result.get('scores', {}).get('overall')}")
        return result

    except SoftTimeLimitExceeded:
        logger.error(f"[Worker] 实验评审超时 task_id={task_id}")
        save_task_failure(task_id, "experiment_evaluation", "任务超时")
        raise
    except Exception as exc:
        logger.error(f"[Worker] 实验评审异常 task_id={task_id} exc={exc}")
        save_task_failure(task_id, "experiment_evaluation", str(exc))
        raise self.retry(exc=exc)
