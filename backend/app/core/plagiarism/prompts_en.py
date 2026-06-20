"""
英文查重 AI prompts。
BATCH_VERIFY_PROMPT:批量验证用户句 vs 候选摘要的抄袭等级。
REWRITE / JOURNAL ADVICE:博士/期刊档差异化建议。
"""
from __future__ import annotations


_STRICTNESS_HINT_EN = {
    "lenient":
        "Only flag obvious direct copy (>6 consecutive words matching). "
        "Mere rewording counts as original.",
    "standard":
        "Flag direct copy and clear paraphrase (synonym swap or reorder).",
    "strict":
        "Flag direct copy, paraphrase, and conceptual lifting "
        "(same idea structure even when reworded).",
    "journal":
        "Strictest: any segment with suspected self-citation NOT explicitly "
        "marked as self-citation must be flagged. Pay special attention to "
        "common knowledge vs novel claims.",
}


def get_strictness_hint_en(key: str) -> str:
    return _STRICTNESS_HINT_EN.get(key, _STRICTNESS_HINT_EN["standard"])


BATCH_VERIFY_PROMPT = """You are a strict academic plagiarism examiner.
{strictness_hint}

For each (user_sentence, candidate_abstract) pair below, classify the plagiarism verdict:
- direct_copy      : verbatim or near-verbatim copy
- paraphrase       : same meaning, rewritten (synonym/reorder)
- common_knowledge : generic claim widely stated, not plagiarism
- original         : no plagiarism signal

Return STRICT JSON array, one object per pair, preserving input order:
[{{"idx": 0, "verdict": "direct_copy", "similarity": 0.95, "reason": "..."}}, ...]

Pairs:
{pairs_json}

Output ONLY the JSON array, no prose."""


REWRITE_ADVICE_PROMPT_EN = """You are an academic writing coach.
For the following sentence flagged as potential plagiarism, produce ONE rewritten
version that preserves the technical meaning but uses original phrasing.

Original: {sentence}
Matched source (abstract): {source_abstract}

Return JSON: {{"rewrite": "...", "note": "one-sentence explanation of what changed"}}"""


JOURNAL_ADVICE_PROMPT_EN = """You are a journal editor assistant.
Given a plagiarism report summary for a paper targeting peer-reviewed journals,
produce submission advice in 3-5 bullet points.

Summary: {summary_json}

Focus on:
- Whether current similarity rate is acceptable for SCI/SSCI submission
- Which flagged segments are riskiest and should be rewritten first
- Whether to add self-citation disclosure

Return plain English text, bullets starting with "- "."""
