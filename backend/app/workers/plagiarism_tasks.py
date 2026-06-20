"""
查重 Celery Task
queue: plagiarism
"""
import hashlib
import json
import os
from pathlib import Path

# 必须在所有业务 import 之前加载 .env
# 根据 APP_ENV 环境变量加载正确的配置文件
from dotenv import load_dotenv

app_env = os.getenv("APP_ENV", "development")
if app_env == "production":
    _env_path = Path(__file__).parent.parent.parent / ".env.production"
else:
    _env_path = Path(__file__).parent.parent.parent / ".env"

if _env_path.exists():
    load_dotenv(_env_path, override=True)

from loguru import logger
from app.workers.celery_app import celery_app
from app.services.task_store import save_task_result, save_task_failure


def _get_redis_client():
    try:
        import redis
        from app.config import settings
        return redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
    except Exception:
        return None


_STAGES_ZH = [
    (5,  "解析文档..."),
    (20, "执行查重..."),
    (80, "生成建议..."),
    (90, "写入缓存..."),
]

_STAGES_EN = [
    (5,  "解析文档..."),
    (15, "检测语言..."),
    (25, "提取关键句..."),
    (40, "查询 Semantic Scholar..."),
    (55, "查询 CORE..."),
    (65, "查询 PubMed..."),
    (80, "AI 判定中..."),
    (95, "生成报告..."),
]


def _update(self, progress: int, stage: str = ""):
    self.update_state(
        state="PROGRESS",
        meta={"progress": progress, "status": "processing", "stage": stage},
    )


@celery_app.task(
    bind=True,
    name="run_plagiarism_check",
    queue="plagiarism",
    soft_time_limit=180,
    time_limit=240,
    max_retries=1,
)
def run_plagiarism_check(
    self,
    task_id: str,
    file_path: str,
    paper_type: str = "",
    language: str = "zh",
):
    """
    查重主任务。语言分流:zh → HybridChecker;en → EnglishAcademicChecker。
    en 全源失败降级到 HybridChecker,engine 标为 english_academic_fallback。
    """
    logger.info(f"[plagiarism] 开始查重 task_id={task_id} language={language}")
    _update(self, 5, "解析文档...")

    try:
        from app.core.plagiarism.text_parser import parse_file, clean_text
        from app.core.plagiarism.checker_context import get_checker_context
        from app.core.plagiarism.report_generator import enrich_report

        raw_text = parse_file(file_path)
        text = clean_text(raw_text)

        if len(text) < 200:
            raise ValueError("TEXT_TOO_SHORT: 文本少于200字,请上传完整论文")

        # 语言自动检测(auto → en/zh)
        if language == "auto":
            from app.core.plagiarism.language_detector import detect_language
            _update(self, 15, "检测语言...")
            language = detect_language(text)
            logger.info(f"[plagiarism] 检测到语言={language}")

        # 缓存 key 加入 language
        text_md5 = hashlib.md5(text.encode()).hexdigest()
        cache_key = f"plagiarism:cache:{language}:{paper_type or '_'}:{text_md5}"

        redis_client = _get_redis_client()
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                logger.info(f"[plagiarism] 缓存命中 task_id={task_id}")
                result = json.loads(cached)
                result["task_id"] = task_id
                return result

        _update(self, 25, "提取关键句..." if language == "en" else "执行查重...")

        ctx = get_checker_context()
        result_dict = None
        fallback_used = False

        if language == "en":
            _update(self, 40, "查询外部学术库...")
            try:
                checker = ctx.get_checker("en")
                check_result = checker.check(text, task_id, paper_type)
                result_dict = check_result.to_dict()
                _update(self, 80, "AI 判定中...")
            except Exception as exc:
                from app.core.plagiarism.external.aggregator import (
                    ExternalSourceAggregatorAllFailedError,
                )
                if isinstance(exc, ExternalSourceAggregatorAllFailedError):
                    logger.warning(
                        f"[plagiarism] 外部学术源全部失败,降级到 HybridChecker: {exc}"
                    )
                    fallback_used = True
                else:
                    raise
        else:
            checker = ctx.get_checker("zh")
            check_result = checker.check(text, task_id, paper_type)
            result_dict = check_result.to_dict()

        if fallback_used:
            fb = ctx.get_fallback_checker()
            check_result = fb.check(text, task_id, paper_type)
            result_dict = check_result.to_dict()
            result_dict["engine"] = "english_academic_fallback"

        # 分级增强
        _update(self, 90 if language == "zh" else 95, "生成报告...")
        try:
            enrich_report(result_dict, paper_type, language=language)
        except Exception as exc:
            logger.warning(f"[plagiarism] 分级增强失败: {exc}")

        # 写缓存(24小时)
        if redis_client:
            try:
                cache_data = {k: v for k, v in result_dict.items() if k != "raw_text"}
                redis_client.setex(cache_key, 86400, json.dumps(cache_data))
            except Exception as e:
                logger.warning(f"[plagiarism] 缓存写入失败: {e}")

        logger.info(
            f"[plagiarism] 完成 task_id={task_id} "
            f"rate={result_dict['summary']['rate']}% "
            f"engine={result_dict['engine']}"
        )

        # 永久存储到 MySQL（Redis 缓存24小时，MySQL 永久）
        save_task_result(task_id, "plagiarism", {k: v for k, v in result_dict.items() if k != "raw_text"})

        return result_dict

    except Exception as exc:
        logger.error(f"[plagiarism] 任务失败 task_id={task_id}: {exc}")
        save_task_failure(task_id, "plagiarism", str(exc))
        raise
