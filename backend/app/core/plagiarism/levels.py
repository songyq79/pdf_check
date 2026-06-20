"""
查重分级配置 - 按学历层次(本科/硕士/博士/期刊)差异化阈值与判定严格度。

数据来源:
- 本科红线 30% / 硕士 20% / 博士 10% - 教育部学位论文作假行为处理办法 + 各校通行做法
- 期刊 15% - 中国知网 VIP 检测系统常用期刊阈值

"paper_type" 约定值: "undergraduate" / "master" / "doctor" / "journal" / ""(不限)
"""
from __future__ import annotations

from typing import Dict, Any

# 风险等级阈值:rate >= high → high,rate >= medium → medium,else low
# confirm_threshold: AI 初筛后送深度确认的门槛
# strictness: 传给 AI 的严格度档位 id,对应 prompts.py 里的 _STRICTNESS_HINT
# rewrite_advice: True 时让 AI 为高相似片段生成改写建议
_LEVEL_CONFIG: Dict[str, Dict[str, Any]] = {
    "undergraduate": {
        "label":             "本科论文",
        "rate_high":         30.0,
        "rate_medium":       20.0,
        "confirm_threshold": 0.70,
        "strictness":        "lenient",
        "rewrite_advice":    False,
        "journal_advice":    False,
    },
    "master": {
        "label":             "硕士论文",
        "rate_high":         20.0,
        "rate_medium":       15.0,
        "confirm_threshold": 0.60,
        "strictness":        "standard",
        "rewrite_advice":    False,
        "journal_advice":    False,
    },
    "doctor": {
        "label":             "博士论文",
        "rate_high":         10.0,
        "rate_medium":       5.0,
        "confirm_threshold": 0.45,
        "strictness":        "strict",
        "rewrite_advice":    True,
        "journal_advice":    False,
    },
    "journal": {
        "label":             "期刊投稿",
        "rate_high":         15.0,
        "rate_medium":       10.0,
        "confirm_threshold": 0.50,
        "strictness":        "journal",
        "rewrite_advice":    True,
        "journal_advice":    True,
    },
    "": {  # 不限 / 未指定:保留原有硬编码行为
        "label":             "通用",
        "rate_high":         40.0,
        "rate_medium":       20.0,
        "confirm_threshold": 0.60,
        "strictness":        "standard",
        "rewrite_advice":    False,
        "journal_advice":    False,
    },
}


# ── 英文查重分级配置 ────────────────────────────────────────────
# 英文学术规范天然更严(连续 6 词相同即判抄袭 vs 中文约 13 字;SCI 要求 similarity < 15%)。
# embed_threshold:MiniLM cosine 相似度下限,替代 TF-IDF 阈值
# key_sentences:关键句抽取数量上限
# ngram_size:N-gram 硬命中窗口(期刊档激进到 5)
# min_confidence:ConfidenceScorer 产出低于此值的 highlight 不展示
_LEVEL_CONFIG_EN: Dict[str, Dict[str, Any]] = {
    "undergraduate": {
        "label":             "Undergraduate",
        "rate_high":         25.0,
        "rate_medium":       15.0,
        "embed_threshold":   0.80,
        "key_sentences":     8,
        "ngram_size":        6,
        "min_confidence":    60,
        "strictness":        "lenient",
        "rewrite_advice":    False,
        "journal_advice":    False,
    },
    "master": {
        "label":             "Master",
        "rate_high":         15.0,
        "rate_medium":       10.0,
        "embed_threshold":   0.75,
        "key_sentences":     10,
        "ngram_size":        6,
        "min_confidence":    50,
        "strictness":        "standard",
        "rewrite_advice":    False,
        "journal_advice":    False,
    },
    "doctor": {
        "label":             "PhD",
        "rate_high":         8.0,
        "rate_medium":       4.0,
        "embed_threshold":   0.72,
        "key_sentences":     12,
        "ngram_size":        6,
        "min_confidence":    40,
        "strictness":        "strict",
        "rewrite_advice":    True,
        "journal_advice":    False,
    },
    "journal": {
        "label":             "Journal",
        "rate_high":         12.0,
        "rate_medium":       8.0,
        "embed_threshold":   0.70,
        "key_sentences":     15,
        "ngram_size":        5,
        "min_confidence":    30,
        "strictness":        "journal",
        "rewrite_advice":    True,
        "journal_advice":    True,
    },
    "": {
        "label":             "General (EN)",
        "rate_high":         20.0,
        "rate_medium":       12.0,
        "embed_threshold":   0.75,
        "key_sentences":     10,
        "ngram_size":        6,
        "min_confidence":    50,
        "strictness":        "standard",
        "rewrite_advice":    False,
        "journal_advice":    False,
    },
}


def get_level_config(paper_type: str, language: str = "zh") -> Dict[str, Any]:
    """
    按 paper_type + language 取配置;未知值回退到"不限"。
    language="en" → LEVELS_EN;其他 → 中文原表。
    """
    if language == "en":
        return _LEVEL_CONFIG_EN.get(paper_type, _LEVEL_CONFIG_EN[""])
    return _LEVEL_CONFIG.get(paper_type, _LEVEL_CONFIG[""])


def classify_risk(rate: float, paper_type: str, language: str = "zh") -> str:
    """按 paper_type + language 对应阈值把重复率映射成 low/medium/high。"""
    cfg = get_level_config(paper_type, language)
    if rate >= cfg["rate_high"]:
        return "high"
    if rate >= cfg["rate_medium"]:
        return "medium"
    return "low"


def get_threshold_snapshot(paper_type: str, language: str = "zh") -> Dict[str, Any]:
    """
    返回当前使用的阈值快照,随 CheckResult 一起落盘,供前端展示"参照标准"。
    """
    cfg = get_level_config(paper_type, language)
    snapshot = {
        "paper_type":        paper_type or "",
        "language":          language,
        "label":             cfg["label"],
        "rate_high":         cfg["rate_high"],
        "rate_medium":       cfg["rate_medium"],
        "strictness":        cfg["strictness"],
    }
    # 中英差异字段
    if language == "en":
        snapshot.update({
            "embed_threshold": cfg["embed_threshold"],
            "key_sentences":   cfg["key_sentences"],
            "ngram_size":      cfg["ngram_size"],
            "min_confidence":  cfg["min_confidence"],
        })
    else:
        snapshot["confirm_threshold"] = cfg["confirm_threshold"]
    return snapshot
