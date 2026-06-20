"""
应用配置文件
使用Pydantic Settings管理配置
"""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
from pydantic import model_validator
from pathlib import Path

class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "论文评价检验系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    USE_AI: bool = True  # 修复：原来写的是 USE_AI: False，不是合法的类型注解

    # API配置
    API_V1_PREFIX: str = "/api/v1"

    # 百炼大模型API配置
    BAILIAN_API_KEY: str = "sk-1a01c6b2d67b4262bcf5220c9a8c568b"
    BAILIAN_ENDPOINT: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    BAILIAN_MODEL: str = "qwen3.5-plus"
    BAILIAN_TIMEOUT: int = 60
    BAILIAN_MAX_RETRIES: int = 3

    # 百炼文件上传配置（使用阿里云SDK）
    BAILIAN_ACCESS_KEY_ID: Optional[str] = None
    BAILIAN_ACCESS_KEY_SECRET: Optional[str] = None
    BAILIAN_WORKSPACE_ID: Optional[str] = None
    BAILIAN_CATEGORY_ID: str = "cate_default"

    # DeepSeek配置（百炼失败时备用）
    DEEPSEEK_API_KEY: str = "sk-ab3c72265b7a4c6da7e1f6d5be06a218"
    DEEPSEEK_MODEL: str = "deepseek-reasoner"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # 数据库配置（可选）

    DATABASE_URL: str = "mysql+pymysql://user:password@localhost:3306/paper_check"
    DATABASE_ECHO: bool = False

    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 26301
    REDIS_DB: int = 15
    REDIS_PASSWORD: Optional[str] = "jzmNDJAF7b"

    # 文件存储配置
    STORAGE_PATH: Path = Path(__file__).parent.parent / "storage"
    UPLOAD_PATH: Path = Path("")
    OUTPUT_PATH: Path = Path("")
    TEMP_PATH: Path = Path("")

    @model_validator(mode="after")
    def build_storage_paths(self):
        self.UPLOAD_PATH = self.STORAGE_PATH / "uploads"
        self.OUTPUT_PATH = self.STORAGE_PATH / "outputs"
        self.TEMP_PATH = self.STORAGE_PATH / "temp"
        return self

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
        "https://papers.vronly-dh.com",
    ]

    # JWT配置（可选）
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Celery配置
    CELERY_BROKER_URL: str = "redis://:jzmNDJAF7b@localhost:26301/15"
    CELERY_RESULT_BACKEND: str = "redis://:jzmNDJAF7b@localhost:26301/15"

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"

    class Config:
        env_file = Path(__file__).parent.parent / ".env"  # 指向 backend/.env
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


ensure_storage_dirs()
