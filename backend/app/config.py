"""
应用配置 - 使用 pydantic-settings 统一管理，支持 .env 文件覆盖
支持多环境: APP_ENV=development (默认，使用 .env) 或 APP_ENV=production (使用 .env.production)
"""

from pathlib import Path
from typing import List, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings


def _get_env_file():
    """同时加载 .env 和 .env.production，后者优先级更高（覆盖前者）"""
    base = Path(__file__).parent.parent
    files = []
    if (base / ".env").exists():
        files.append(str(base / ".env"))
    if (base / ".env.production").exists():
        files.append(str(base / ".env.production"))
    return files if files else ".env"


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

    # ── 数据库 ────────────────────────────────────────────
    # 本地开发默认 SQLite；云部署在 .env 里改为 MySQL URL
    DATABASE_URL: str = "sqlite:///./storage/app.db"

    # ── Redis ─────────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 26301
    REDIS_DB: int = 15
    REDIS_PASSWORD: Optional[str] = "jzmNDJAF7b"

    # ── Celery ────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://:jzmNDJAF7b@localhost:26301/15"
    CELERY_RESULT_BACKEND: str = "redis://:jzmNDJAF7b@localhost:26301/15"

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
            self.STORAGE_PATH / "wechat",
            self.STORAGE_PATH / "alipay",
        ):
            p.mkdir(parents=True, exist_ok=True)

        # 处理相对路径的支付密钥文件
        if self.WECHAT_PRIVATE_KEY_PATH and not Path(self.WECHAT_PRIVATE_KEY_PATH).is_absolute():
            self.WECHAT_PRIVATE_KEY_PATH = str(self.STORAGE_PATH / self.WECHAT_PRIVATE_KEY_PATH)
        if self.WECHAT_PUBLIC_KEY_PATH and not Path(self.WECHAT_PUBLIC_KEY_PATH).is_absolute():
            self.WECHAT_PUBLIC_KEY_PATH = str(self.STORAGE_PATH / self.WECHAT_PUBLIC_KEY_PATH)
        if self.ALIPAY_PRIVATE_KEY_PATH and not Path(self.ALIPAY_PRIVATE_KEY_PATH).is_absolute():
            self.ALIPAY_PRIVATE_KEY_PATH = str(self.STORAGE_PATH / self.ALIPAY_PRIVATE_KEY_PATH)
        if self.ALIPAY_PUBLIC_KEY_PATH and not Path(self.ALIPAY_PUBLIC_KEY_PATH).is_absolute():
            self.ALIPAY_PUBLIC_KEY_PATH = str(self.STORAGE_PATH / self.ALIPAY_PUBLIC_KEY_PATH)

        return self

    # ── 文件限制 ──────────────────────────────────────────
    MAX_FILE_SIZE: int = 20          # MB
    FILE_RETENTION_HOURS: int = 24
    ALLOWED_FILE_TYPES: List[str] = [".docx"]

    # ── CORS ──────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://papers.vronly-dh.com",
    ]

    # ── JWT ─────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7天

    # ── 微信支付（Native） ────────────────────────────────
    WECHAT_MCH_ID: str = ""
    WECHAT_APP_ID: str = ""
    WECHAT_API_V3_KEY: str = ""
    WECHAT_CERT_SERIAL_NO: str = ""
    WECHAT_PRIVATE_KEY_PATH: str = ""
    WECHAT_PUBLIC_KEY_PATH: str = ""
    WECHAT_PUBLIC_KEY_ID: str = ""
    WECHAT_NOTIFY_URL: str = ""

    # ── 微信登录（开放平台） ──────────────────────────────
    WECHAT_LOGIN_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""
    WECHAT_REDIRECT_URI: str = ""

    # ── 支付宝（支付 + 登录） ─────────────────────────────
    ALIPAY_APP_ID: str = ""
    ALIPAY_PRIVATE_KEY_PATH: str = ""
    ALIPAY_PUBLIC_KEY_PATH: str = ""
    ALIPAY_NOTIFY_URL: str = ""
    ALIPAY_REDIRECT_URI: str = ""

    # ── 阿里云短信 ────────────────────────────────────────
    ALIYUN_SMS_ACCESS_KEY: str = ""
    ALIYUN_SMS_ACCESS_SECRET: str = ""
    ALIYUN_SMS_SIGN_NAME: str = ""
    ALIYUN_SMS_TEMPLATE_CODE: str = ""

    # ── Semantic Scholar ──────────────────────────────────
    SEMANTIC_SCHOLAR_API_KEY: str = ""
    SEMANTIC_SCHOLAR_BASE_URL: str = "https://api.semanticscholar.org/graph/v1"
    SEMANTIC_SCHOLAR_TIMEOUT: int = 10

    # ── CORE ──────────────────────────────────────────────
    CORE_API_KEY: str = ""
    CORE_BASE_URL: str = "https://api.core.ac.uk/v3"
    CORE_TIMEOUT: int = 15

    # ── PubMed ────────────────────────────────────────────
    PUBMED_EMAIL: str = ""
    PUBMED_API_KEY: str = ""
    PUBMED_BASE_URL: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    PUBMED_TIMEOUT: int = 10

    # ── 维普 CQVIP（中文文献主力源）─────────────────────────
    VIP_API_KEY: str = ""
    VIP_BASE_URL: str = "https://superapi.cqvip.com"
    VIP_TIMEOUT: int = 15

    # ── 英文查重通用(LEVELS_EN 未命中档位时的 fallback)─────
    ENGLISH_CHECK_KEY_SENTENCES: int = 10
    ENGLISH_CHECK_CANDIDATES_PER_SENTENCE: int = 5
    ENGLISH_CHECK_EMBED_THRESHOLD: float = 0.75
    ENGLISH_CHECK_NGRAM_SIZE: int = 6
    ENGLISH_CHECK_MIN_CONFIDENCE: int = 50
    ENGLISH_SOURCE_CACHE_TTL: int = 604800  # 7 天

    # ── Embedding 模型 ────────────────────────────────────
    SEMANTIC_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    SEMANTIC_MODEL_PATH: str = ""
    SEMANTIC_MODEL_CACHE_DIR: str = "./models/st"

    # ── Feature Flag ──────────────────────────────────────
    ENABLE_ENGLISH_CHECK: bool = True

    # ── 日志 ──────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
        "<level>{message}</level>"
    )

    class Config:
        env_file = _get_env_file()
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()

# 生产环境强制覆盖 Redis 配置（绕过 pydantic-settings 字段缓存问题）
if "mysql" in settings.DATABASE_URL.lower():
    import sys
    _PROD_BROKER = "redis://:jzmNDJAF7b@localhost:26301/15"
    object.__setattr__(settings, "CELERY_BROKER_URL", _PROD_BROKER)
    object.__setattr__(settings, "CELERY_RESULT_BACKEND", _PROD_BROKER)
    object.__setattr__(settings, "REDIS_HOST", "localhost")
    object.__setattr__(settings, "REDIS_PORT", 26301)
    object.__setattr__(settings, "REDIS_DB", 15)
    object.__setattr__(settings, "REDIS_PASSWORD", "jzmNDJAF7b")
    print(f"[CONFIG] 生产环境已覆盖 CELERY_BROKER_URL={settings.CELERY_BROKER_URL}", file=sys.stderr)
