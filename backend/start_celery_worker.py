#!/usr/bin/env python3
"""
Celery Worker 启动脚本 - 专为宝塔面板设计
直接设置生产环境的 Redis 配置，绕过环境变量问题
"""

import os
import sys

# 第一步：设置生产环境标记
os.environ["APP_ENV"] = "production"

# 第二步：直接设置 Redis 配置（覆盖所有其他配置来源）
os.environ["CELERY_BROKER_URL"] = "redis://:jzmNDJAF7b@localhost:26301/15"
os.environ["CELERY_RESULT_BACKEND"] = "redis://:jzmNDJAF7b@localhost:26301/15"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "26301"
os.environ["REDIS_DB"] = "15"
os.environ["REDIS_PASSWORD"] = "jzmNDJAF7b"

# 第三步：启动 Celery Worker
if __name__ == "__main__":
    from celery.bin import worker
    from app.workers.celery_app import celery_app

    # 获取队列名（从命令行参数）
    queues = sys.argv[1:] if len(sys.argv) > 1 else ["default"]

    # 启动 Worker
    app = celery_app
    worker_app = worker.worker(app=app)
    options = {
        "queues": queues,
        "loglevel": "info",
        "concurrency": 4,
        "pool": "threads",
    }
    worker_app.run(**options)
