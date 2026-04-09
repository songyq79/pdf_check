"""
应用配置 - 使用 pydantic-settings 统一管理，支持 .env 文件覆盖
"""

from pathlib import Path
from typing import List, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── 基础 ─────────────────────────────────────────────
    APP_NAME: str = "论文助手系统"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    USE_AI: bool = False

    # ── API 前缀 ──────────────────────────────────────────
    API_V1_PREFIX: str = "/api/v1"

    # ── 百炼 / 通义千问（主力 AI）────────────────────────
    BAILIAN_API_KEY: str = ""
    BAILIAN_MODEL: str = "qwen-max"
    BAILIAN_TIMEOUT: int = 60
    BAILIAN_MAX_RETRIES: int = 3

    # ── DeepSeek（百炼失败时自动切换）──────────────────────
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # ── Redis ─────────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # ── Celery ────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # ── 文件存储 ──────────────────────────────────────────
    STORAGE_PATH: Path = Path(__file__).parent.parent / "storage"
    UPLOAD_PATH: Path = Path("")
    OUTPUT_PATH: Path = Path("")
    TEMP_PATH: Path = Path("")

    @model_validator(mode="after")
    def _build_storage_paths(self) -> "Settings":
        self.UPLOAD_PATH = self.STORAGE_PATH / "uploads"
        self.OUTPUT_PATH = self.STORAGE_PATH / "outputs"
        self.TEMP_PATH   = self.STORAGE_PATH / "temp"
        # 确保所有存储目录存在
        for p in (
            self.UPLOAD_PATH,
            self.OUTPUT_PATH,
            self.TEMP_PATH,
            self.STORAGE_PATH / "formatter",
        ):
            p.mkdir(parents=True, exist_ok=True)
        return self

    # ── 文件限制 ──────────────────────────────────────────
    MAX_FILE_SIZE: int = 20          # MB
    FILE_RETENTION_HOURS: int = 24
    ALLOWED_FILE_TYPES: List[str] = [".docx"]

    # ── CORS ──────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # ── JWT（预留）────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── 日志 ──────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
        "<level>{message}</level>"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
