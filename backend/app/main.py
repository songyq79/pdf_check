"""
FastAPI 应用入口
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import settings
# ── 日志初始化 ────────────────────────────────────────────
_log_dir = Path(__file__).parent.parent / "logs"
_log_dir.mkdir(parents=True, exist_ok=True)

logger.remove()
logger.add(
    sys.stdout,
    format=settings.LOG_FORMAT,
    level=settings.LOG_LEVEL,
    colorize=True,
)
logger.add(
    str(_log_dir / "app_{time:YYYY-MM-DD}.log"),
    format=settings.LOG_FORMAT,
    level=settings.LOG_LEVEL,
    rotation="00:00",
    retention="30 days",
    encoding="utf-8",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据库
    from app.models.user import init_db
    init_db()

    logger.info("=" * 55)
    logger.info(f"  {settings.APP_NAME}  v{settings.APP_VERSION}  启动")
    logger.info(f"  API 文档: http://localhost:8000/docs")
    logger.info(f"  存储路径: {settings.STORAGE_PATH}")
    if not settings.BAILIAN_API_KEY:
        logger.warning("  ⚠️  BAILIAN_API_KEY 未配置，AI 功能不可用")
    if not settings.DEEPSEEK_API_KEY:
        logger.warning("  ⚠️  DEEPSEEK_API_KEY 未配置，DeepSeek 备用不可用")
    logger.info("=" * 55)
    yield
    logger.info(f"{settings.APP_NAME} 已关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="论文格式化 / 错别字检查 / AI评价 一体化系统",
    # 生产环境(DEBUG=False)关闭 API 文档，避免暴露接口结构
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ── 限流器注册（登录/短信/AI 等敏感接口用 @limiter.limit 装饰）──────────
from slowapi.errors import RateLimitExceeded  # noqa: E402
from slowapi import _rate_limit_exceeded_handler  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"未处理异常 [{request.method} {request.url}]: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"},
    )


# 注册路由
from app.api.v1.router import api_router  # noqa: E402
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

print("\n" + "="*50)
print(">>> 验证：当前加载的路由包含：")
for r in app.routes:
    if hasattr(r, "path"):
        print(f"  - {r.path}")
print("="*50 + "\n")


@app.get("/", tags=["系统"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["系统"])
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "bailian_configured": bool(settings.BAILIAN_API_KEY),
        "deepseek_configured": bool(settings.DEEPSEEK_API_KEY),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
