"""
应用配置文件
使用Pydantic Settings管理配置
"""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "论文评价检验系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API配置
    API_V1_PREFIX: str = "/api/v1"

    # 百炼大模型API配置（未配置时功能降级，不崩溃）
    BAILIAN_API_KEY: str = ""
    BAILIAN_ENDPOINT: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    BAILIAN_MODEL: str = "qwen-max"
    BAILIAN_TIMEOUT: int = 60
    BAILIAN_MAX_RETRIES: int = 3

    # 百炼文件上传配置（使用阿里云SDK）
    BAILIAN_ACCESS_KEY_ID: Optional[str] = None
    BAILIAN_ACCESS_KEY_SECRET: Optional[str] = None
    BAILIAN_WORKSPACE_ID: Optional[str] = None
    BAILIAN_CATEGORY_ID: str = "cate_default"

    # 数据库配置（可选）
    DATABASE_URL: str = "mysql+pymysql://user:password@localhost:3306/paper_check"
    DATABASE_ECHO: bool = False

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # 文件存储配置
    STORAGE_PATH: Path = Path(__file__).parent.parent / "storage"
    UPLOAD_PATH: Path = STORAGE_PATH / "uploads"
    OUTPUT_PATH: Path = STORAGE_PATH / "outputs"
    TEMP_PATH: Path = STORAGE_PATH / "temp"

    # 文件大小限制（MB）
    MAX_FILE_SIZE: int = 20

    # 文件保留时间（小时）
    FILE_RETENTION_HOURS: int = 24

    # 允许的文件类型
    ALLOWED_FILE_TYPES: list = [".docx"]

    # CORS配置
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # JWT配置（可选）
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建配置实例
settings = Settings()


# 确保存储目录存在
def ensure_storage_dirs():
    """确保所有存储目录存在"""
    settings.UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
    settings.OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    settings.TEMP_PATH.mkdir(parents=True, exist_ok=True)


# 应用启动时调用
ensure_storage_dirs()
