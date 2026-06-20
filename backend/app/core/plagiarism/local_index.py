"""
本地 FAISS 论文索引管理器

架构：
  MySQL  = 唯一真数据源（存元数据 + embedding BLOB）
  FAISS  = 加速层（可随时从 MySQL 重建，IndexIDMap 支持按 paper_id 删除）

使用方式（单例）：
  from app.core.plagiarism.local_index import local_index
  results = local_index.search(vec, topk=10, threshold=0.75)
"""

from __future__ import annotations

import struct
import threading
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
from loguru import logger

from app.config import settings

_FAISS_DIR  = settings.STORAGE_PATH / "faiss"
_INDEX_PATH = _FAISS_DIR / "papers.index"
_DIM        = 384   # all-MiniLM-L6-v2 输出维度
_MIN_REBUILD_COUNT = 100   # MySQL 论文数低于此值时跳过重建


def _vec_to_bytes(vec: np.ndarray) -> bytes:
    return struct.pack(f"{_DIM}f", *vec.astype(np.float32).tolist())


def _bytes_to_vec(b: bytes) -> np.ndarray:
    return np.array(struct.unpack(f"{_DIM}f", b), dtype=np.float32)


class LocalIndex:
    def __init__(self):
        self._lock  = threading.Lock()
        self._index = None   # faiss.IndexIDMap
        self._ready = False

    # ── 初始化 ────────────────────────────────────────────────

    def load(self) -> None:
        """启动时调用：优先从磁盘加载，否则从 MySQL 重建。"""
        _FAISS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            import faiss
        except ImportError:
            logger.warning("[local_index] faiss-cpu 未安装，本地论文库禁用")
            return

        with self._lock:
            if _INDEX_PATH.exists():
                try:
                    self._index = faiss.read_index(str(_INDEX_PATH))
                    self._ready = True
                    logger.info(
                        f"[local_index] 从磁盘加载索引，共 {self._index.ntotal} 篇"
                    )
                    return
                except Exception as e:
                    logger.warning(f"[local_index] 磁盘索引损坏，重建: {e}")

            self._rebuild_locked()

    def rebuild_from_db(self) -> int:
        """手动触发全量重建（Admin 页面调用）。"""
        with self._lock:
            return self._rebuild_locked()

    def _rebuild_locked(self) -> int:
        """从 MySQL embedding 列全量重建 FAISS 索引（调用前需持有 _lock）。"""
        try:
            import faiss
            from app.models.user import SessionLocal
            from app.models.local_paper import LocalPaper

            db = SessionLocal()
            try:
                rows = db.query(
                    LocalPaper.id, LocalPaper.embedding
                ).filter(LocalPaper.embedding.isnot(None)).all()
            finally:
                db.close()

            if len(rows) < _MIN_REBUILD_COUNT:
                logger.info(f"[local_index] 论文数 {len(rows)} < {_MIN_REBUILD_COUNT}，跳过重建")
                self._index = faiss.IndexIDMap(faiss.IndexFlatIP(_DIM))
                self._ready = True
                return 0

            flat   = faiss.IndexFlatIP(_DIM)
            index  = faiss.IndexIDMap(flat)
            ids    = np.array([r.id for r in rows], dtype=np.int64)
            vecs   = np.vstack([_bytes_to_vec(r.embedding) for r in rows])
            index.add_with_ids(vecs, ids)

            faiss.write_index(index, str(_INDEX_PATH))
            self._index = index
            self._ready = True
            logger.info(f"[local_index] 重建完成，共 {len(rows)} 篇")
            return len(rows)

        except Exception as e:
            logger.error(f"[local_index] 重建失败: {e}")
            return 0

    # ── 查询 ─────────────────────────────────────────────────

    def search(
        self,
        vec: np.ndarray,
        topk: int = 10,
        threshold: float = 0.70,
    ) -> List[Tuple[int, float]]:
        """
        向量相似度检索。
        返回 [(paper_id, score), ...]，按相似度降序，score >= threshold。
        """
        if not self._ready or self._index is None:
            return []
        if self._index.ntotal == 0:
            return []

        try:
            q = vec.astype(np.float32).reshape(1, _DIM)
            k = min(topk, self._index.ntotal)
            scores, ids = self._index.search(q, k)
            results = []
            for score, pid in zip(scores[0], ids[0]):
                if pid < 0:
                    continue
                if float(score) >= threshold:
                    results.append((int(pid), float(score)))
            return results
        except Exception as e:
            logger.warning(f"[local_index] search 失败: {e}")
            return []

    # ── 写入 ─────────────────────────────────────────────────

    def add(self, paper_id: int, vec: np.ndarray) -> None:
        """新增一条向量（MySQL 已写入后调用）。"""
        if not self._ready or self._index is None:
            return
        try:
            import faiss
            v = vec.astype(np.float32).reshape(1, _DIM)
            ids = np.array([paper_id], dtype=np.int64)
            with self._lock:
                self._index.add_with_ids(v, ids)
                faiss.write_index(self._index, str(_INDEX_PATH))
        except Exception as e:
            logger.warning(f"[local_index] add 失败 paper_id={paper_id}: {e}")

    def remove(self, paper_id: int) -> None:
        """删除一条向量（MySQL 已删除后调用）。"""
        if not self._ready or self._index is None:
            return
        try:
            import faiss
            ids = np.array([paper_id], dtype=np.int64)
            selector = faiss.IDSelectorArray(ids)
            with self._lock:
                self._index.remove_ids(selector)
                faiss.write_index(self._index, str(_INDEX_PATH))
        except Exception as e:
            logger.warning(f"[local_index] remove 失败 paper_id={paper_id}: {e}")

    # ── 统计 ─────────────────────────────────────────────────

    @property
    def total(self) -> int:
        if self._index is None:
            return 0
        return int(self._index.ntotal)

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def index_size_mb(self) -> float:
        if _INDEX_PATH.exists():
            return round(_INDEX_PATH.stat().st_size / 1024 / 1024, 1)
        return 0.0


# 全局单例，由 main.py lifespan 调用 local_index.load()
local_index = LocalIndex()
