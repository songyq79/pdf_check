"""
字符级 Diff 引擎

基于 difflib.SequenceMatcher 计算两段文本的字符级差异，
输出 OOXML 修订节点需要的 opcodes。
"""

from difflib import SequenceMatcher
from typing import List, Tuple


def compute_diff(old: str, new: str) -> List[Tuple]:
    """
    计算字符级别的文本差异。
    返回所有非 equal 的 opcodes：[(tag, i1, i2, j1, j2), ...]
    tag 可能值：'replace' | 'delete' | 'insert'
    """
    matcher = SequenceMatcher(None, old, new, autojunk=False)
    return [op for op in matcher.get_opcodes() if op[0] != "equal"]


def has_diff(old: str, new: str) -> bool:
    """快速判断两段文本是否有差异"""
    return old != new


def diff_summary(old: str, new: str) -> dict:
    """
    返回差异摘要（用于日志）。
    """
    ops = compute_diff(old, new)
    return {
        "has_change": bool(ops),
        "op_count":   len(ops),
        "old_len":    len(old),
        "new_len":    len(new),
    }
