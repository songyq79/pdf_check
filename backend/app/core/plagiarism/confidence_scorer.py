"""
置信度评分(精度增强 #7)
三路投票:n-gram 硬命中 + embedding 相似度 + AI verdict → 0-100 分。
"""
from __future__ import annotations


_VERDICT_SCORE = {
    "direct_copy":       30,
    "paraphrase":        20,
    "common_knowledge":   5,
    "original":         -20,
}


def score(
    ngram_hit: bool,
    embed_sim: float,
    ai_verdict: str = "",
) -> int:
    """
    综合三路信号产出 0-100 置信度。

    - n-gram 硬命中 → +50(强证据)
    - embedding 分段:≥0.90 → +30;0.80-0.90 → +20;0.75-0.80 → +10
    - AI verdict:direct_copy +30 / paraphrase +20 / common_knowledge +5 / original -20
    """
    total = 0
    if ngram_hit:
        total += 50

    if embed_sim >= 0.90:
        total += 30
    elif embed_sim >= 0.80:
        total += 20
    elif embed_sim >= 0.75:
        total += 10

    verdict_key = (ai_verdict or "").strip().lower().replace(" ", "_")
    total += _VERDICT_SCORE.get(verdict_key, 0)

    return max(0, min(total, 100))
