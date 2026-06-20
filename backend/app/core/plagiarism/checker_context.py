"""
策略持有者(单例)
- language="zh" → 按 PLAGIARISM_ENGINE 选 hybrid/opensource
- language="en" → EnglishAcademicChecker
"""
from __future__ import annotations

import os
from typing import Dict, Tuple

from .base_checker import BaseChecker


_instances: Dict[Tuple[str, str], BaseChecker] = {}


class CheckerContext:
    """按 (engine, language) 缓存单例。"""

    def get_checker(self, language: str = "zh") -> BaseChecker:
        engine = os.getenv("PLAGIARISM_ENGINE", "hybrid").lower()
        key = (engine, language)
        if key not in _instances:
            _instances[key] = self._build(engine, language)
        return _instances[key]

    def _build(self, engine: str, language: str) -> BaseChecker:
        if language == "en":
            from .engines.english_academic_checker import EnglishAcademicChecker
            return EnglishAcademicChecker()
        if engine == "hybrid":
            from .engines.hybrid_checker import HybridChecker
            return HybridChecker()
        from .engines.opensource_checker import OpenSourceChecker
        return OpenSourceChecker()

    def get_fallback_checker(self) -> BaseChecker:
        """外文全源失败时降级到中文 hybrid。"""
        key = ("hybrid", "zh")
        if key not in _instances:
            from .engines.hybrid_checker import HybridChecker
            _instances[key] = HybridChecker()
        return _instances[key]


_ctx_instance: "CheckerContext | None" = None


def get_checker_context() -> CheckerContext:
    global _ctx_instance
    if _ctx_instance is None:
        _ctx_instance = CheckerContext()
    return _ctx_instance
