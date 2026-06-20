"""
语义 Embedding(精度增强 #3)
sentence-transformers/all-MiniLM-L6-v2 单例包装,替代 TF-IDF。
CPU 推理 ~50ms/句;384 维向量;归一化后 cosine 直接用点积算。
"""
from __future__ import annotations

import threading
from typing import List, Tuple

import numpy as np
from loguru import logger

_model_lock = threading.Lock()
_model_instance = None


def _get_model():
    """懒加载 + 单例。首次调用下载 ~80MB 权重,约 10-30s。"""
    global _model_instance
    if _model_instance is not None:
        return _model_instance
    with _model_lock:
        if _model_instance is not None:
            return _model_instance
        from sentence_transformers import SentenceTransformer
        from app.config import settings

        model_path = settings.SEMANTIC_MODEL_PATH or settings.SEMANTIC_MODEL_NAME
        cache_dir = settings.SEMANTIC_MODEL_CACHE_DIR or None
        logger.info(f"[semantic_encoder] 加载模型 {model_path}...")
        _model_instance = SentenceTransformer(model_path, cache_folder=cache_dir)
        logger.info("[semantic_encoder] 模型加载完成")
        return _model_instance


def encode_batch(sentences: List[str]) -> np.ndarray:
    """
    一次性批量嵌入,返回 (N, 384) 已归一化矩阵。
    空输入返回 shape=(0, 0) 的空数组。
    """
    if not sentences:
        return np.zeros((0, 0), dtype=np.float32)
    model = _get_model()
    vecs = model.encode(
        sentences,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return vecs.astype(np.float32)


def cosine_topk(
    user_vecs: np.ndarray,
    cand_vecs: np.ndarray,
    k: int = 5,
    threshold: float = 0.75,
) -> List[List[Tuple[int, float]]]:
    """
    对每个 user_vec,找 cand_vecs 中相似度 top-k 且 ≥ threshold 的候选。
    返回 List[List[(cand_idx, score)]],外层长度 == len(user_vecs)。
    """
    if user_vecs.size == 0 or cand_vecs.size == 0:
        return [[] for _ in range(len(user_vecs))]
    sim = user_vecs @ cand_vecs.T  # (N_user, N_cand),已归一化 → cosine
    results: List[List[Tuple[int, float]]] = []
    for row in sim:
        idx = np.argsort(-row)[:k]
        hits = [(int(i), float(row[i])) for i in idx if row[i] >= threshold]
        results.append(hits)
    return results
