"""
查重基类 + 统一数据结构
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class HighlightItem:
    id: int
    text: str
    start_pos: int
    end_pos: int
    similarity: float
    source_id: str
    ai_judged: bool = False
    verdict: str = "疑似重复"
    confidence: int = 0          # 0-100,由 ConfidenceScorer 产出;中文引擎不填
    ngram_hit: bool = False      # 是否 N-gram 硬命中,前端可据此加粗重合词


@dataclass
class SourceItem:
    id: str
    title: str
    author: str = ""
    year: Optional[int] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    source_name: Optional[str] = None   # semantic_scholar | core | pubmed
    abstract: Optional[str] = None


@dataclass
class CheckSummary:
    total_chars: int
    dup_chars: int
    rate: float          # 百分比，保留1位小数
    risk_level: str      # low / medium / high


@dataclass
class CheckResult:
    task_id: str
    engine: str
    created_at: str
    summary: CheckSummary
    highlights: List[HighlightItem] = field(default_factory=list)
    sources: List[SourceItem] = field(default_factory=list)
    raw_text: str = ""   # 原文（用于前端高亮定位）
    # 分级查重:paper_type(原值) + 阈值快照 + 差异化建议字段
    paper_type: str = ""
    threshold_snapshot: Dict[str, Any] = field(default_factory=dict)
    rewrite_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    journal_advice: str = ""

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "engine": self.engine,
            "created_at": self.created_at,
            "raw_text": self.raw_text,
            "paper_type": self.paper_type,
            "threshold_snapshot": self.threshold_snapshot,
            "rewrite_suggestions": self.rewrite_suggestions,
            "journal_advice": self.journal_advice,
            "summary": {
                "total_chars": self.summary.total_chars,
                "dup_chars": self.summary.dup_chars,
                "rate": self.summary.rate,
                "risk_level": self.summary.risk_level,
            },
            "highlights": [
                {
                    "id": h.id,
                    "text": h.text,
                    "start_pos": h.start_pos,
                    "end_pos": h.end_pos,
                    "similarity": round(h.similarity, 4),
                    "source_id": h.source_id,
                    "ai_judged": h.ai_judged,
                    "verdict": h.verdict,
                    "confidence": h.confidence,
                    "ngram_hit": h.ngram_hit,
                }
                for h in self.highlights
            ],
            "sources": [
                {
                    "id": s.id,
                    "title": s.title,
                    "author": s.author,
                    "year": s.year,
                    "url": s.url,
                    "doi": s.doi,
                    "source_name": s.source_name,
                    "abstract": s.abstract,
                }
                for s in self.sources
            ],
        }


class BaseChecker(ABC):
    """所有查重引擎的统一接口"""

    @abstractmethod
    def check(self, text: str, task_id: str, paper_type: str = "") -> CheckResult:
        """
        执行查重，返回 CheckResult。
        子类必须实现此方法。
        """
        ...
