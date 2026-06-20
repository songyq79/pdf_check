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
from app.services.task_store import save_task_result, save_task_failure
from app.core.evaluator.prompts import (
    get_all_dimensions, get_dimension_name, get_prompt,
    get_dimension_weight, get_integrity_prompt, get_type_name,
    DIMENSION_WEIGHTS,
)
from app.core.evaluator.report_generator import ReportGenerationError, generate_report
from app.schemas.evaluation import EvaluationResponse, EvaluationResult


class EvaluationBaseTask(Task):
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"[Celery] 评价失败 task_id={task_id} exc={exc}")

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"[Celery] 评价成功 task_id={task_id}")


async def _evaluate_all_dimensions(paper_struct: dict, paper_type: str = "humanities") -> dict:
    """并发评价所有维度（不含学术诚信，诚信检查异步后置）"""
    dimensions = get_all_dimensions()

    async def _one(dim):
        prompt = get_prompt(dim, paper_struct, paper_type)
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

    # 只并发执行维度评价，不等诚信检查
    tasks = [_one(d) for d in dimensions]
    all_results = await asyncio.gather(*tasks, return_exceptions=True)

    dim_results = {}
    for r in all_results:
        if isinstance(r, Exception):
            logger.error(f"[evaluate] 维度评价异常: {r}")
            continue
        dim, result = r
        dim_results[dim] = result

    return dim_results


async def _run_integrity_check(paper_struct: dict) -> dict:
    """学术诚信风险检查（独立调用，不阻塞主评价流程）"""
    try:
        prompt = get_integrity_prompt(paper_struct)
        raw_response = await call_ai(prompt, timeout=settings.BAILIAN_TIMEOUT)
        fallback = {"has_risk": False, "risk_items": [], "note": "无法解析"}
        return parse_json_response(raw_response, fallback=fallback)
    except Exception as e:
        logger.error(f"[evaluate] 学术诚信检查异常: {e}")
        return {"has_risk": False, "risk_items": [], "note": "检查失败"}


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
    paper_type: str = "humanities",
) -> dict:
    """Celery 评价任务，接收结构化 paper_struct 和论文类别"""
    title = paper_struct.get("title", "未命名论文")
    type_name = get_type_name(paper_type)
    logger.info(f"[Worker] 开始评价 task_id={task_id} title={title[:40]} type={type_name}")

    try:
        # 使用新的事件循环避免冲突
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # 第一阶段：只跑 5 个维度评价（不等诚信检查）
            results = loop.run_until_complete(
                _evaluate_all_dimensions(paper_struct, paper_type)
            )
        finally:
            loop.close()

        # 加权计算综合评分
        dimensions = get_all_dimensions()
        weighted_sum = 0
        total_weight = 0
        for dim in dimensions:
            if dim in results:
                weight = get_dimension_weight(dim)
                score = results[dim].get("score", 0)
                weighted_sum += score * weight
                total_weight += weight

        overall_score = round(weighted_sum / total_weight, 1) if total_weight > 0 else 0

        response = EvaluationResponse(
            paper_title=title,
            overall_score=overall_score,
            dimensions={
                dim: EvaluationResult(
                    dimension_name=get_dimension_name(dim),
                    score=results[dim].get("score", 0),
                    strengths=results[dim].get("strengths", []),
                    weaknesses=results[dim].get("weaknesses", []),
                    suggestions=results[dim].get("suggestions", []),
                )
                for dim in dimensions
                if dim in results
            },
            evaluated_at=datetime.now(),
        )

        # 第二阶段：诚信检查后置（不阻塞评分结果）
        integrity_result = None
        try:
            integrity_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(integrity_loop)
            try:
                integrity_result = integrity_loop.run_until_complete(
                    _run_integrity_check(paper_struct)
                )
            finally:
                integrity_loop.close()
        except Exception as exc:
            logger.warning(f"[Worker] 诚信检查失败，不影响评价结果: {exc}")
            integrity_result = {"has_risk": False, "risk_items": [], "note": "检查失败"}

        # 生成 Word 报告
        report_id  = str(uuid.uuid4())
        target_dir = Path(report_output_path)
        target_dir.mkdir(parents=True, exist_ok=True)
        report_path = target_dir / f"{report_id}_report.docx"

        try:
            generate_report(
                evaluation=response,
                output_path=report_path,
                include_chart=True,
                paper_type=paper_type,
                integrity_result=integrity_result,
            )
            response.report_id = report_id
            response.report_download_url = f"/api/v1/evaluation/download/{report_id}"
        except ReportGenerationError as exc:
            logger.error(f"报告生成失败: {exc}")

        logger.info(f"[Worker] 评价完成 task_id={task_id} score={overall_score:.1f} type={type_name}")

        # 将结果转为 dict，附加学术诚信和论文类别信息
        result_dict = response.model_dump(mode="json")
        result_dict["integrity"] = integrity_result
        result_dict["paper_type"] = paper_type
        result_dict["paper_type_name"] = type_name

        # 永久存储到 MySQL
        save_task_result(task_id, "evaluation", result_dict)

        return result_dict

    except SoftTimeLimitExceeded:
        logger.error(f"[Worker] 评价超时 task_id={task_id}")
        save_task_failure(task_id, "evaluation", "任务超时")
        raise

    except Exception as exc:
        logger.error(f"[Worker] 评价异常 task_id={task_id} exc={exc}")
        save_task_failure(task_id, "evaluation", str(exc))
        raise self.retry(exc=exc)
