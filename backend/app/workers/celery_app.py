"""
Celery 应用工厂
- broker:  Redis（任务队列）
- backend: Redis（结果存储）
- 队列：proofread / evaluation / formatter / default
"""

import sys
from pathlib import Path
from celery import Celery
from kombu import Queue


celery_app = Celery(
    "paper_checker",
    broker="redis://:jzmNDJAF7b@localhost:26301/15",
    backend= "redis://:jzmNDJAF7b@localhost:26301/15",
    include=[
        "app.workers.proofread_tasks",
        "app.workers.evaluation_tasks",
        "app.workers.formatter_tasks",
        "app.workers.plagiarism_tasks",
        "app.workers.topic_evaluation_tasks",
        "app.workers.literature_review_tasks",
        "app.workers.experiment_evaluation_tasks",
        "app.workers.writing_whole_tasks",
    ],
)

celery_app.conf.update(
    # 序列化
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 结果保留 7 天（原24小时太短，Redis重启或TTL到期会丢失任务结果）
    result_expires=604800,

    # 路由
    task_routes={
        "app.workers.proofread_tasks.*":  {"queue": "proofread"},
        "app.workers.evaluation_tasks.*": {"queue": "evaluation"},
        "app.workers.formatter_tasks.*":  {"queue": "formatter"},
        "app.workers.plagiarism_tasks.*": {"queue": "plagiarism"},
        # Phase 1 新增队列路由
        "app.workers.topic_evaluation_tasks.*": {"queue": "topic_eval"},
        "app.workers.literature_review_tasks.*": {"queue": "lit_review"},
        "app.workers.experiment_evaluation_tasks.*": {"queue": "experiment_eval"},
        "app.workers.writing_whole_tasks.*": {"queue": "writing_assist"},
    },

    # 队列声明
    task_queues=(
        Queue("proofread"),
        Queue("evaluation"),
        Queue("formatter"),
        Queue("plagiarism"),
        Queue("default"),
        # Phase 1 新增队列
        Queue("topic_eval"),
        Queue("lit_review"),
        # Phase 2 新增队列
        Queue("experiment_eval"),
        Queue("writing_assist"),
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

    # 并发线程数：AI 调用是纯 IO 等待，可开较高并发
    # 32vCPU + 128GB 服务器，IO密集型任务可设为 CPU核心数 × 4
    worker_concurrency=128,
)
