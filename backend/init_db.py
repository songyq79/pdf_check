#!/usr/bin/env python3
"""
数据库初始化脚本
在应用启动前运行此脚本来创建所有必要的数据库表
"""

import os
import sys
import logging
from pathlib import Path

# 设置环境变量
os.environ['APP_ENV'] = os.getenv('APP_ENV', 'production')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """初始化数据库表"""
    try:
        logger.info(f"使用环境: {os.environ.get('APP_ENV')}")

        # 导入配置和模型
        from app.config import settings
        from app.models.user import Base, engine

        logger.info(f"数据库连接: {settings.DATABASE_URL}")

        # 创建所有表
        logger.info("开始创建数据库表...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 数据库表创建成功！")

        # 验证连接
        from app.models.user import SessionLocal
        db = SessionLocal()
        try:
            db.execute("SELECT 1")
            logger.info("✅ 数据库连接验证成功！")
        finally:
            db.close()

        return True

    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}", exc_info=True)
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
            logger.info(f"✅ 目录已创建: {dir_path}")

        return True
    except Exception as e:
        logger.error(f"❌ 创建存储目录失败: {e}", exc_info=True)
        return False

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("开始初始化应用...")
    logger.info("=" * 60)

    success = True

    # 创建存储目录
    logger.info("\n[1/2] 创建存储目录...")
    if not init_storage_dirs():
        success = False

    # 初始化数据库
    logger.info("\n[2/2] 初始化数据库...")
    if not init_database():
        success = False

    logger.info("=" * 60)
    if success:
        logger.info("✅ 初始化完成！")
        sys.exit(0)
    else:
        logger.error("❌ 初始化失败！")
        sys.exit(1)
