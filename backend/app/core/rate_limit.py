"""
统一限流器（基于 slowapi）。

用法：
    from app.core.rate_limit import limiter
    @router.post("/login")
    @limiter.limit("10/minute")
    def login(request: Request, ...):   # 必须带 request: Request 参数
        ...

主程序 app/main.py 已完成 limiter 注册与 429 异常处理，无需重复注册。

限流后端：
- 默认使用进程内存（单进程/开发够用）。
- 生产多进程/多实例部署时，建议设置 RATE_LIMIT_STORAGE_URI=redis://... 以便
  各进程共享计数（否则每个进程各算各的，实际阈值会被放大 N 倍）。
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.config import settings


def _client_key(request: Request) -> str:
    """优先取 X-Forwarded-For 首个 IP（反向代理场景），否则取直连地址。"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return get_remote_address(request)


_storage_uri = getattr(settings, "RATE_LIMIT_STORAGE_URI", "") or "memory://"

limiter = Limiter(key_func=_client_key, storage_uri=_storage_uri)
