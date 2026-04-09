"""
Celery 应用工厂
- broker:  Redis（任务队列）
- backend: Redis（结果存储）
- 队列：proofread / evaluation / formatter / default
"""

from celery import Celery
from kombu import Queue

from app.config import settings

celery_app = Celery(
    "paper_checker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.proofread_tasks",
        "app.workers.evaluation_tasks",
        "app.workers.formatter_tasks",
    ],
)

celery_app.conf.update(
    # 序列化
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 结果保留 24 小时
    result_expires=86400,

    # 路由
    task_routes={
        "app.workers.proofread_tasks.*":  {"queue": "proofread"},
        "app.workers.evaluation_tasks.*": {"queue": "evaluation"},
        "app.workers.formatter_tasks.*":  {"queue": "formatter"},
    },

    # 队列声明
    task_queues=(
        Queue("proofread"),
        Queue("evaluation"),
        Queue("formatter"),
        Queue("default"),
    ),
    task_default_queue="default",

    # AI 任务耗时长，每次预取 1 个
    worker_prefetch_multiplier=1,

    # 超时：9 分钟软超时，10 分钟强杀
    task_soft_time_limit=540,
    task_time_limit=600,

    # 任务完成后再 ack，保证崩溃时重新入队
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Windows 兼容：threads 模式支持真正的多线程并发
    # solo = 单线程（已废弃，仅适合调试）
    # threads = 多线程，Windows/Linux 均支持，适合 IO 密集型 AI 任务
    worker_pool="threads",
)
