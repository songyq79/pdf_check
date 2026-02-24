"""
FastAPI应用入口
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys
from pathlib import Path

from app.config import settings


# ── 日志初始化（先创建目录再挂载文件handler）─────────────────────────
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


# ── 路由懒加载（避免一个模块崩溃影响整体启动）──────────────────────────
from app.api.v1.router import api_router


# ── 生命周期管理（替代已废弃的 on_event）─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动
    logger.info(f"{'='*50}")
    logger.info(f"  {settings.APP_NAME} v{settings.APP_VERSION} 启动")
    logger.info(f"  API文档: http://localhost:8000/docs")
    logger.info(f"  存储路径: {settings.STORAGE_PATH}")
    if not settings.BAILIAN_API_KEY:
        logger.warning("  ⚠️  BAILIAN_API_KEY 未配置，智能评价功能不可用")
    logger.info(f"{'='*50}")
    yield
    # 关闭
    logger.info(f"{settings.APP_NAME} 已关闭")


# ── 创建应用 ──────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="论文评价及检验系统API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS中间件 ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 全局异常捕获（防止未处理异常把500错误吞掉不记录）────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"未处理异常 [{request.method} {request.url}]: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"},
    )

# ── 注册路由 ──────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ── 基础端点 ──────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "api_key_configured": bool(settings.BAILIAN_API_KEY),
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
