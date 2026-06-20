# Gunicorn 配置文件 - 生产环境（宝塔）
# 启动时自动初始化数据库和存储目录

import os
import sys
import logging
from pathlib import Path

# 设置生产环境变量
os.environ['APP_ENV'] = 'production'

# ── 基础配置 ────────────────────────────────────────────
# 项目目录
chdir = '/digital_human_dev/pdf_check/backend'

# 指定进程数（根据 CPU 核心数）
workers = 4

# 指定每个进程开启的线程数
threads = 2

# 启动用户
user = 'root'

# 启动模式
worker_class = 'uvicorn.workers.UvicornWorker'

# 绑定的 IP 与端口
bind = '0.0.0.0:5001'

# 设置进程文件目录（用于停止服务和重启服务，请勿删除）
pidfile = '/digital_human_dev/pdf_check/backend/gunicorn.pid'

# 设置访问日志和错误日志路径
accesslog = '/www/wwwlogs/python/backend/gunicorn_access.log'
errorlog = '/www/wwwlogs/python/backend/gunicorn_error.log'

# 日志级别
loglevel = 'info'

# 超时时间（秒）- 长任务（查重、格式化）可能需要较长时间
timeout = 300

# Worker 连接数上限
worker_connections = 1000

# 优雅关闭时间
graceful_timeout = 30

# ── 初始化钩子 ────────────────────────────────────────────

logger = logging.getLogger('gunicorn')

def init_database():
    """初始化数据库表（仅创建不存在的表，保留现有数据）"""
    try:
        from app.models.user import Base, engine
        from app.config import settings
        from sqlalchemy import inspect

        logger.info(f"[Init] 数据库连接: {settings.DATABASE_URL}")

        # 检查数据库中已存在的表
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        logger.info(f"[Init] 数据库中已存在的表: {existing_tables if existing_tables else '无'}")

        # 获取需要创建的表
        required_tables = set(Base.metadata.tables.keys())
        logger.info(f"[Init] 需要的表: {required_tables}")

        # 计算需要创建的新表
        tables_to_create = required_tables - existing_tables

        if tables_to_create:
            logger.info(f"[Init] 🔧 需要创建的新表: {tables_to_create}")
            logger.info("[Init] 开始创建数据库表...")
            Base.metadata.create_all(bind=engine)
            logger.info(f"[Init] ✅ {len(tables_to_create)} 个新表创建成功！")
        else:
            logger.info("[Init] ℹ️  所有表已存在，跳过创建（保留现有数据）")

        # 验证连接
        from app.models.user import SessionLocal
        db = SessionLocal()
        try:
            db.execute("SELECT 1")
            logger.info("[Init] ✅ 数据库连接验证成功！")
        finally:
            db.close()

        return True
    except Exception as e:
        logger.error(f"[Init] ❌ 数据库初始化失败: {e}", exc_info=True)
        return False

def init_storage_dirs():
    """创建必要的存储目录"""
    try:
        from app.config import settings

        dirs = [
            settings.STORAGE_PATH,
            settings.UPLOAD_PATH,
            settings.OUTPUT_PATH,
            settings.TEMP_PATH,
            settings.STORAGE_PATH / "formatter",
            settings.STORAGE_PATH / "wechat",
            settings.STORAGE_PATH / "alipay",
            settings.STORAGE_PATH / "faiss",
        ]

        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

        logger.info("[Init] ✅ 存储目录创建完成！")
        return True
    except Exception as e:
        logger.error(f"[Init] ❌ 创建存储目录失败: {e}", exc_info=True)
        return False

def when_ready(server):
    """Gunicorn 启动完成时执行（只运行一次）"""
    logger.info("=" * 70)
    logger.info("[Init] 🚀 开始初始化应用...")
    logger.info("=" * 70)

    # 创建存储目录
    logger.info("[Init] [1/2] 创建存储目录...")
    init_storage_dirs()

    # 初始化数据库
    logger.info("[Init] [2/2] 初始化数据库...")
    init_database()

    logger.info("=" * 70)
    logger.info("[Init] ✅ 初始化完成！应用已启动，可以接收请求")
    logger.info("=" * 70)
