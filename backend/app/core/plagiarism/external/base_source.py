"""
外部学术源抽象基类。
子类实现 async search(query, limit) → List[CandidatePaper]。
统一 Redis 缓存(7 天 TTL)、限并发、重试。
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import List, Optional

from loguru import logger


@dataclass
class CandidatePaper:
    title: str
    abstract: str
    doi: Optional[str] = None
    url: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    source_name: str = ""


class ExternalSourceError(Exception):
    """单源调用失败(不阻断 aggregator)。"""


class ExternalSource(ABC):
    """所有外部学术源的统一接口。"""

    source_name: str = "base"
    # 每个事件循环维护独立信号量：Celery 任务每次 new_event_loop，
    # 类级 asyncio.Semaphore 会绑定到创建时的循环，跨循环使用会抛
    # "bound to a different event loop"。按循环惰性创建可避免此问题。
    _sems: dict = {}

    @classmethod
    def _get_sem(cls) -> asyncio.Semaphore:
        loop = asyncio.get_event_loop()
        sem = cls._sems.get(loop)
        if sem is None:
            sem = asyncio.Semaphore(3)
            cls._sems[loop] = sem
        return sem

    def __init__(self, cache_ttl: int = 604800):
        self.cache_ttl = cache_ttl
        self._redis = self._init_redis()

    @staticmethod
    def _init_redis():
        try:
            import redis
            from app.config import settings
            return redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"[external] Redis 初始化失败,禁用缓存: {e}")
            return None

    def _cache_key(self, query: str, limit: int) -> str:
        h = hashlib.md5(f"{query}|{limit}".encode()).hexdigest()
        return f"ext_source:{self.source_name}:{h}"

    def _cache_get(self, key: str) -> Optional[List[CandidatePaper]]:
        if not self._redis:
            return None
        try:
            raw = self._redis.get(key)
            if raw:
                data = json.loads(raw)
                return [CandidatePaper(**item) for item in data]
        except Exception as e:
            logger.warning(f"[{self.source_name}] 缓存读取失败: {e}")
        return None

    def _cache_set(self, key: str, papers: List[CandidatePaper]) -> None:
        if not self._redis:
            return
        try:
            data = [asdict(p) for p in papers]
            self._redis.setex(key, self.cache_ttl, json.dumps(data))
        except Exception as e:
            logger.warning(f"[{self.source_name}] 缓存写入失败: {e}")

    async def search(self, query: str, limit: int = 20) -> List[CandidatePaper]:
        """外层:缓存 + 限并发 + 异常捕获。子类实现 _do_search。"""
        if not query or not query.strip():
            return []
        key = self._cache_key(query, limit)
        cached = self._cache_get(key)
        if cached is not None:
            logger.debug(f"[{self.source_name}] cache hit: {query[:40]}")
            return cached

        async with ExternalSource._get_sem():
            try:
                papers = await self._do_search(query, limit)
            except Exception as e:
                logger.warning(f"[{self.source_name}] 查询失败 query={query[:40]}: {e}")
                raise ExternalSourceError(str(e)) from e

        self._cache_set(key, papers)
        return papers

    @abstractmethod
    async def _do_search(self, query: str, limit: int) -> List[CandidatePaper]:
        """子类实现:纯 HTTP + 解析,不处理缓存/并发。"""
        ...
