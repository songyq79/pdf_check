"""
N-gram 硬命中(精度增强 #2)
连续 N 词重合即判 direct_copy — 英文学术界铁律(通常 6 词;期刊档 5 词更严)。
命中后直接打 direct_copy + confidence=95,跳过 AI 调用。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

_WORD_RE = re.compile(r"[A-Za-z0-9']+")


@dataclass
class NgramHit:
    matched_ngram: str       # 命中的连续 N 词(小写归一化后)
    start_word_idx: int      # 在用户句中的词索引
    end_word_idx: int
    overlap_words: int       # 连续重合词数(可大于 n,若更长段落完全重合)


def _tokenize(text: str) -> List[str]:
    return [w.lower() for w in _WORD_RE.findall(text or "")]


def _build_ngrams(tokens: List[str], n: int) -> Set[str]:
    if len(tokens) < n:
        return set()
    return {" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def check(user_sentence: str, candidate_text: str, n: int = 6) -> Optional[NgramHit]:
    """
    用户句 vs 候选摘要,扫描是否存在连续 n 词重合。
    返回第一个命中(最长连续重合段)或 None。
    """
    user_tokens = _tokenize(user_sentence)
    cand_tokens = _tokenize(candidate_text)
    if len(user_tokens) < n or len(cand_tokens) < n:
        return None

    cand_ngrams = _build_ngrams(cand_tokens, n)
    if not cand_ngrams:
        return None

    best: Optional[Tuple[int, int, int]] = None  # (start, end, length)
    i = 0
    while i <= len(user_tokens) - n:
        ng = " ".join(user_tokens[i:i + n])
        if ng in cand_ngrams:
            # 尝试延长以找到最大连续重合
            end = i + n
            while end < len(user_tokens):
                ext = " ".join(user_tokens[end - n + 1:end + 1])
                if ext in cand_ngrams:
                    end += 1
                else:
                    break
            length = end - i
            if best is None or length > best[2]:
                best = (i, end, length)
            i = end  # 跳过已覆盖区间
        else:
            i += 1

    if best is None:
        return None
    start, end, length = best
    matched = " ".join(user_tokens[start:end])
    return NgramHit(
        matched_ngram=matched,
        start_word_idx=start,
        end_word_idx=end,
        overlap_words=length,
    )
