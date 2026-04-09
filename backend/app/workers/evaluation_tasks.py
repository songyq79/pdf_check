"""
智能评价 Celery Task v2

改动：
- run_evaluation 接收 paper_struct（结构化字典）而非原始 content 字符串
- get_prompt 改为接收 paper_struct，各维度按需取内容
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from loguru import logger

from app.workers.celery_app import celery_app
from app.config import settings
from app.core.ai_client import call_ai, parse_json_response
from app.core.evaluator.prompts import get_all_dimensions, get_dimension_name, get_prompt
from app.core.evaluator.report_generator import ReportGenerationError, generate_report
from app.schemas.evaluation import EvaluationResponse, EvaluationResult


class EvaluationBaseTask(Task):
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"[Celery] 评价失败 task_id={task_id} exc={exc}")

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"[Celery] 评价成功 task_id={task_id}")


async def _evaluate_all_dimensions(paper_struct: dict) -> dict:
    """并发评价所有维度，各维度按需取 paper_struct 中的字段"""
    dimensions = get_all_dimensions()

    async def _one(dim):
        prompt = get_prompt(dim, paper_struct)
        raw_response = await call_ai(prompt, timeout=settings.BAILIAN_TIMEOUT)

        fallback = {
            "score": 0,
            "strengths": ["无法解析模型输出"],
            "weaknesses": [],
            "suggestions": [],
        }
        result = parse_json_response(raw_response, fallback=fallback)
        logger.info(f"维度 [{dim}] 完成，得分: {result.get('score', 0)}")
        return dim, result

    pairs = await asyncio.gather(*[_one(d) for d in dimensions])
    return dict(pairs)


@celery_app.task(
    bind=True,
    base=EvaluationBaseTask,
    queue="evaluation",
    name="app.workers.evaluation_tasks.run_evaluation",
    max_retries=1,
    default_retry_delay=15,
    acks_late=True,
)
def run_evaluation(
    self,
    task_id: str,
    paper_struct: dict,
    report_output_path: str,
) -> dict:
    """Celery 评价任务，接收结构化 paper_struct"""
    title = paper_struct.get("title", "未命名论文")
    logger.info(f"[Worker] 开始评价 task_id={task_id} title={title[:40]}")

    try:
        # 使用新的事件循环避免冲突
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(_evaluate_all_dimensions(paper_struct))
        finally:
            loop.close()
        
        avg_score = sum(r.get("score", 0) for r in results.values()) / len(results)
        dimensions = get_all_dimensions()

        response = EvaluationResponse(
            paper_title=title,
            overall_score=round(avg_score, 1),
            dimensions={
                dim: EvaluationResult(
                    dimension_name=get_dimension_name(dim),
                    score=results[dim].get("score", 0),
                    strengths=results[dim].get("strengths", []),
                    weaknesses=results[dim].get("weaknesses", []),
                    suggestions=results[dim].get("suggestions", []),
                )
                for dim in dimensions
            },
            evaluated_at=datetime.now(),
        )

        # 生成 Word 报告
        report_id  = str(uuid.uuid4())
        target_dir = Path(report_output_path)
        target_dir.mkdir(parents=True, exist_ok=True)
        report_path = target_dir / f"{report_id}_report.docx"

        try:
            generate_report(evaluation=response, output_path=report_path, include_chart=True)
            response.report_id = report_id
            response.report_download_url = f"/api/v1/evaluation/download/{report_id}"
        except ReportGenerationError as exc:
            logger.error(f"报告生成失败: {exc}")

        logger.info(f"[Worker] 评价完成 task_id={task_id} score={avg_score:.1f}")
        return response.model_dump(mode="json")

    except SoftTimeLimitExceeded:
        logger.error(f"[Worker] 评价超时 task_id={task_id}")
        raise

    except Exception as exc:
        logger.error(f"[Worker] 评价异常 task_id={task_id} exc={exc}")
        raise self.retry(exc=exc)
