"""
V1 开源引擎：SimHash + TF-IDF + numpy 批处理
目标：万字论文 ≤ 5秒
"""
from __future__ import annotations
import hashlib
import re
from datetime import datetime, timezone
from typing import List, Tuple

import numpy as np

from ..base_checker import BaseChecker, CheckResult, CheckSummary, HighlightItem, SourceItem
from ..text_parser import segment_sentences, clean_text


# ─── 内置参考语料（演示用，实际可替换为真实数据库） ───────────────────────────
_REFERENCE_CORPUS: List[dict] = [
    {
        "id": "src-001",
        "title": "深度学习在自然语言处理中的应用综述",
        "author": "张三",
        "year": 2022,
        "text": "深度学习技术在自然语言处理领域取得了显著进展，包括文本分类、机器翻译、情感分析等任务。"
                "基于Transformer架构的预训练模型如BERT、GPT等已成为NLP领域的主流方法。"
                "这些模型通过大规模无监督预训练，再在特定任务上进行微调，取得了优异的性能。",
    },
    {
        "id": "src-002",
        "title": "卷积神经网络图像识别研究",
        "author": "李四",
        "year": 2021,
        "text": "卷积神经网络是图像识别领域最重要的深度学习模型之一。"
                "通过卷积层、池化层和全连接层的组合，CNN能够自动提取图像的层次化特征。"
                "ResNet、VGG、Inception等经典架构在ImageNet等基准数据集上取得了超越人类的识别精度。",
    },
    {
        "id": "src-003",
        "title": "强化学习算法综述与应用",
        "author": "王五",
        "year": 2023,
        "text": "强化学习是机器学习的重要分支，通过智能体与环境的交互来学习最优策略。"
                "Q-learning、策略梯度、Actor-Critic等算法在游戏、机器人控制等领域取得了突破性成果。"
                "深度强化学习将深度神经网络与强化学习结合，进一步提升了算法的表达能力。",
    },
]


# ─── SimHash 实现 ─────────────────────────────────────────────────────────────

def _tokenize(text: str) -> List[str]:
    """简单分词：按字符 n-gram（2-gram）"""
    text = re.sub(r"\s+", "", text)
    return [text[i:i+2] for i in range(len(text) - 1)] if len(text) > 1 else list(text)


def _simhash(text: str, bits: int = 64) -> int:
    tokens = _tokenize(text)
    if not tokens:
        return 0
    v = np.zeros(bits, dtype=np.int32)
    for token in tokens:
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        for i in range(bits):
            v[i] += 1 if (h >> i) & 1 else -1
    fingerprint = 0
    for i in range(bits):
        if v[i] > 0:
            fingerprint |= (1 << i)
    return fingerprint


def _hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def _simhash_similarity(a: int, b: int, bits: int = 64) -> float:
    return 1.0 - _hamming_distance(a, b) / bits


# ─── TF-IDF 余弦相似度 ────────────────────────────────────────────────────────

def _tfidf_similarity(text_a: str, text_b: str) -> float:
    """简化版 TF-IDF 余弦相似度（不依赖 sklearn，纯 numpy）"""
    def term_freq(text: str) -> dict:
        tokens = _tokenize(text)
        tf: dict = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        total = len(tokens) or 1
        return {k: v / total for k, v in tf.items()}

    tf_a = term_freq(text_a)
    tf_b = term_freq(text_b)
    vocab = set(tf_a) | set(tf_b)
    if not vocab:
        return 0.0
    va = np.array([tf_a.get(t, 0.0) for t in vocab])
    vb = np.array([tf_b.get(t, 0.0) for t in vocab])
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(va, vb) / (norm_a * norm_b))


# ─── 主引擎 ──────────────────────────────────────────────────────────────────

class OpenSourceChecker(BaseChecker):
    """V1：SimHash + TF-IDF，numpy 批处理"""

    SIMHASH_THRESHOLD = 0.65   # SimHash 粗筛阈值
    TFIDF_THRESHOLD = 0.75     # TF-IDF 最终判定阈值

    def __init__(self):
        # 预计算参考语料指纹
        self._ref_fingerprints = [
            (_simhash(ref["text"]), ref)
            for ref in _REFERENCE_CORPUS
        ]
        # 参考语料分句，同时预计算每句的 SimHash
        self._ref_sentences: List[Tuple[str, int, dict]] = []
        for ref in _REFERENCE_CORPUS:
            segs = segment_sentences(ref["text"], min_len=10)
            for seg, _, _ in segs:
                self._ref_sentences.append((seg, _simhash(seg), ref))

    def check(self, text: str, task_id: str, paper_type: str = "") -> CheckResult:
        text = clean_text(text)
        segments = segment_sentences(text)

        highlights: List[HighlightItem] = []
        matched_source_ids: set = set()
        dup_chars = 0
        hit_id = 0

        for seg_text, seg_start, seg_end in segments:
            seg_hash = _simhash(seg_text)

            best_sim = 0.0
            best_ref = None

            # SimHash 粗筛（使用预计算的指纹，不重复计算）
            candidates = [
                (ref_seg, ref)
                for ref_seg, ref_hash, ref in self._ref_sentences
                if _simhash_similarity(seg_hash, ref_hash) >= self.SIMHASH_THRESHOLD
            ]

            # TF-IDF 精筛
            for ref_seg, ref in candidates:
                sim = _tfidf_similarity(seg_text, ref_seg)
                if sim > best_sim:
                    best_sim = sim
                    best_ref = ref

            if best_sim >= self.TFIDF_THRESHOLD and best_ref:
                hit_id += 1
                highlights.append(HighlightItem(
                    id=hit_id,
                    text=seg_text,
                    start_pos=seg_start,
                    end_pos=seg_end,
                    similarity=round(best_sim, 4),
                    source_id=best_ref["id"],
                    ai_judged=False,
                    verdict="疑似重复",
                ))
                matched_source_ids.add(best_ref["id"])
                dup_chars += len(seg_text)

        total_chars = len(text)
        rate = round(min(dup_chars / total_chars * 100, 100), 1) if total_chars else 0.0
        risk_level = "high" if rate >= 40 else ("medium" if rate >= 20 else "low")

        sources = [
            SourceItem(
                id=ref["id"],
                title=ref["title"],
                author=ref.get("author", ""),
                year=ref.get("year"),
                url=ref.get("url"),
            )
            for ref in _REFERENCE_CORPUS
            if ref["id"] in matched_source_ids
        ]

        return CheckResult(
            task_id=task_id,
            engine="opensource",
            created_at=datetime.now(timezone.utc).isoformat(),
            raw_text=text,
            summary=CheckSummary(
                total_chars=total_chars,
                dup_chars=dup_chars,
                rate=rate,
                risk_level=risk_level,
            ),
            highlights=highlights,
            sources=sources,
        )
