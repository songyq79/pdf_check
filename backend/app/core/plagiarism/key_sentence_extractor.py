"""
英文关键句抽取(启发式,不调 AI)。
优先:含数字/百分比、定义/方法陈述句。
过滤:引用标注残留、疑问句、过短。
分布约束:覆盖全文,避免全抽自某一段。
"""
from __future__ import annotations

import re
from typing import List, Tuple

_DIGIT_RE = re.compile(r"\b\d+(?:\.\d+)?%?\b")
_DEF_RE = re.compile(
    r"\b(is|are)\s+defined\s+as\b|"
    r"\bwe\s+propose\b|"
    r"\bthis\s+(paper|study|work)\s+(presents|proposes|investigates|examines)\b|"
    r"\bthe\s+(objective|aim|goal|purpose)\s+(is|was)\b|"
    r"\bwe\s+(found|show|demonstrate|observe|report|conclude)\b",
    re.IGNORECASE,
)
_CITE_LEFTOVER_RE = re.compile(r"\[\d+\]|\bet\s+al\.?\b", re.IGNORECASE)
_QUESTION_RE = re.compile(r"\?\s*$")


def _score(sent: str) -> int:
    """启发式评分,分高优先抽取。"""
    s = 0
    if _DEF_RE.search(sent):
        s += 5
    if _DIGIT_RE.search(sent):
        s += 2
    if _CITE_LEFTOVER_RE.search(sent):
        s -= 3
    if _QUESTION_RE.search(sent):
        s -= 2
    if len(sent) < 50:
        s -= 1
    if len(sent) > 300:
        s -= 1
    return s


def _split_sentences(text: str) -> List[Tuple[str, int, int]]:
    """英文断句,返回 [(sent, start, end)]。"""
    pattern = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
    sents: List[Tuple[str, int, int]] = []
    last = 0
    for m in pattern.finditer(text):
        end = m.start() + 1  # 包含标点
        seg = text[last:end].strip()
        if seg:
            sents.append((seg, last, end))
        last = m.end()
    if last < len(text):
        seg = text[last:].strip()
        if seg:
            sents.append((seg, last, len(text)))
    return sents


def extract_key_sentences(
    text: str,
    max_count: int = 10,
    min_len: int = 30,
) -> List[Tuple[str, int, int]]:
    """
    抽取关键句,上限 max_count。
    三段分布:前 1/3(intro)、中 1/3(method/results)、后 1/3(discussion/conclusion)
    每段至少占一定配额,避免全文偏抽。
    """
    sents = _split_sentences(text)
    sents = [(s, a, b) for s, a, b in sents if len(s) >= min_len and not _QUESTION_RE.search(s)]
    if not sents:
        return []

    n = len(sents)
    if n <= max_count:
        return sents

    # 按位置分三段,每段配额比例 2 : 3 : 3(方法/结果/结论更关键)
    q1 = max(1, max_count * 2 // 8)
    q2 = max(1, max_count * 3 // 8)
    q3 = max_count - q1 - q2
    thirds = [sents[: n // 3], sents[n // 3 : 2 * n // 3], sents[2 * n // 3 :]]
    quotas = [q1, q2, q3]

    picked: List[Tuple[str, int, int]] = []
    for bucket, quota in zip(thirds, quotas):
        ranked = sorted(bucket, key=lambda x: _score(x[0]), reverse=True)
        picked.extend(ranked[:quota])

    # 按原文顺序返回
    picked.sort(key=lambda x: x[1])
    return picked[:max_count]
