"""
检索结果语义重排去噪（多语言）。

外部源是关键词检索（不排序），会混入跑题论文。这里用一个**多语言** sentence-transformers
模型算 query 与每篇 title+abstract 的 cosine 相似度，按相似度降序重排并砍掉低分噪声。

为什么独立于查重的 semantic_encoder：
- 查重用的是 all-MiniLM-L6-v2（英文），对中文相似度判断不准；
- 中文是选题/文献综述的主场景，这里单独用多语言模型 paraphrase-multilingual-MiniLM-L12-v2，
  与查重模型互不影响（查重阈值是按 L6 调的，不能改）。

降级原则（绝不破坏检索流程）：模型不可用 / 异常 / 空输入 → 原样返回（仅按 top_k 截断），不抛错。
"""
from __future__ import annotations

import threading
from typing import List, Optional

from loguru import logger

from app.core.plagiarism.external.base_source import CandidatePaper

# 多语言重排模型（中英皆可）。可被 settings.RERANK_MODEL_NAME 覆盖。
_DEFAULT_RERANK_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

_model_lock = threading.Lock()
_model_instance = None
_model_failed = False  # 加载失败后不再重试，直接降级


def _get_model():
    """懒加载 + 单例多语言模型；失败置 _model_failed 并返回 None（调用方降级）。"""
    global _model_instance, _model_failed
    if _model_instance is not None:
        return _model_instance
    if _model_failed:
        return None
    with _model_lock:
        if _model_instance is not None:
            return _model_instance
        if _model_failed:
            return None
        try:
            from sentence_transformers import SentenceTransformer
            from app.config import settings

            name = getattr(settings, "RERANK_MODEL_NAME", "") or _DEFAULT_RERANK_MODEL
            cache_dir = getattr(settings, "SEMANTIC_MODEL_CACHE_DIR", None) or None
            logger.info(f"[rerank] 加载多语言重排模型 {name}...")
            _model_instance = SentenceTransformer(name, cache_folder=cache_dir)
            logger.info("[rerank] 重排模型加载完成")
            return _model_instance
        except Exception as e:
            _model_failed = True
            logger.warning(f"[rerank] 重排模型加载失败，后续降级为原序: {e}")
            return None


def score_texts(query: str, texts: List[str]) -> Optional[List[float]]:
    """
    返回 query 与每个 text 的 cosine 相似度列表（多语言模型）。
    模型不可用 / 异常 / 空输入 → 返回 None（调用方降级）。
    供期刊主题语义选刊等复用。
    """
    if not query or not query.strip() or not texts:
        return None
    model = _get_model()
    if model is None:
        return None
    try:
        vecs = model.encode(
            [query] + list(texts),
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        qv, cv = vecs[0], vecs[1:]
        return [float(s) for s in (cv @ qv)]
    except Exception as e:
        logger.warning(f"[rerank] score_texts 失败: {e}")
        return None


def rerank_papers(
    query: str,
    papers: List[CandidatePaper],
    top_k: int = 10,
    min_score: float = 0.25,
) -> List[CandidatePaper]:
    """
    按与 query 的语义相似度重排候选文献并去噪。
    :param min_score: 低于此 cosine 分判为噪声丢弃；全被丢弃则保留重排后 top_k（不至空集）。
    :return: 重排+过滤后的列表（≤ top_k）。任何异常都降级为 papers[:top_k]。
    """
    if not query or not query.strip() or not papers:
        return papers[:top_k]
    if len(papers) == 1:
        return papers

    model = _get_model()
    if model is None:
        return papers[:top_k]

    try:
        texts = [
            ((p.title or "") + ". " + (p.abstract or "")).strip()[:1000]
            for p in papers
        ]
        vecs = model.encode(
            [query] + texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        qv, cv = vecs[0], vecs[1:]
        sims = cv @ qv  # 归一化向量点积 = cosine
        scored = sorted(
            zip(papers, (float(s) for s in sims)),
            key=lambda x: x[1],
            reverse=True,
        )
        kept = [p for p, s in scored if s >= min_score]
        if not kept:
            logger.info(f"[rerank] 全部低于阈值 {min_score}，保留重排后 top_k")
            kept = [p for p, _ in scored]

        result = kept[:top_k]
        logger.info(
            f"[rerank] {len(papers)} 篇 → 去噪后 {len(result)} 篇（最高分 {scored[0][1]:.3f}）"
        )
        return result
    except Exception as e:
        logger.warning(f"[rerank] 重排失败，降级为原序: {e}")
        return papers[:top_k]
