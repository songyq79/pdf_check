"""
语言识别:区分中文 / 英文论文,驱动查重引擎路由。
主:langdetect;fallback:中英字符比例。
"""
from __future__ import annotations

import re
from typing import Literal

from loguru import logger

_SAMPLE_LEN = 2000
_ZH_RATIO_THRESHOLD = 0.30  # 中文字符占比 > 30% 判为中文


def _ratio_fallback(text: str) -> Literal["zh", "en"]:
    if not text:
        return "en"
    zh_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    total = len(re.findall(r"[A-Za-z\u4e00-\u9fff]", text))
    if total == 0:
        return "en"
    return "zh" if zh_chars / total > _ZH_RATIO_THRESHOLD else "en"


def detect_language(text: str) -> Literal["zh", "en"]:
    """
    判定文本主要语言,只返回 "zh" / "en"。
    先读前 2000 字符以加速。
    """
    sample = (text or "")[:_SAMPLE_LEN].strip()
    if not sample:
        return "en"
    try:
        from langdetect import detect, DetectorFactory
        DetectorFactory.seed = 0  # 结果稳定
        code = detect(sample)
        if code.startswith("zh"):
            return "zh"
        if code == "en":
            return "en"
        # 其他语言按字符比例再判一次,避免误判纯中文样本
        return _ratio_fallback(sample)
    except Exception as e:
        logger.warning(f"[language_detector] langdetect 失败,走 ratio fallback: {e}")
        return _ratio_fallback(sample)
