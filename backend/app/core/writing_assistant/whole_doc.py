"""
整篇写作辅助 — 解析 docx → 过滤 → 并发逐段四维检查 → 汇总。

复用校对(proofreadme.pipeline)已验证的 docx 处理：
- _has_drawing：含图片(w:drawing/pict/vml)的段落跳过
- _is_empty_para：空段跳过
- _get_para_text：只取直接子 run 文本（不含已删除文字）
- _should_skip_para：标题/超短/参考文献/封面字段跳过

额外：写作分析(逻辑/论证)对超短段无意义，再加最小长度过滤；并发受 Semaphore 限制；
表格不参与（写作辅助只看正文段落）。任何单段失败不阻塞整体（analyze_paragraph 自身降级返回空）。
"""
from __future__ import annotations

import asyncio
from typing import Callable, List, Optional

from docx import Document
from loguru import logger

from app.core.proofreadme.pipeline import (
    _has_drawing,
    _is_empty_para,
    _get_para_text,
    _should_skip_para,
)
from app.core.writing_assistant.analyzer import analyze_paragraph

_MIN_LEN = 40       # 写作四维分析的最小段落长度（短句不值得分析）
_MAX_PARAS = 300    # 单文档分析段落上限，防极端长文/烧额度
_CONCURRENCY = 12   # AI 并发数


async def analyze_document(
    file_path: str,
    paper_type: str = "humanities",
    progress_cb: Optional[Callable[[int, int], None]] = None,
    concurrency: int = _CONCURRENCY,
) -> dict:
    """
    返回:
    {
      "total_paragraphs": 文档总段数,
      "checked": 实际送检段数,
      "total_issues": 建议总数,
      "paragraphs": [  # 仅含有建议的段
        {"index", "text", "grammar", "style", "logic", "argument", "overall", "issue_count"}
      ]
    }
    """
    doc = Document(file_path)
    all_paras = doc.paragraphs

    # 1) 收集待分析段落（过滤图片/空段/标题/超短/参考文献）
    targets: List[tuple] = []
    for idx, p in enumerate(all_paras):
        elem = p._p
        if _has_drawing(elem) or _is_empty_para(elem):
            continue
        text = _get_para_text(elem).strip()
        if not text:
            continue
        skip, _reason = _should_skip_para(text)
        if skip or len(text) < _MIN_LEN:
            continue
        targets.append((idx, text))
        if len(targets) >= _MAX_PARAS:
            logger.info(f"[writing.whole] 达到上限 {_MAX_PARAS} 段，截断")
            break

    total = len(targets)
    if total == 0:
        return {"total_paragraphs": len(all_paras), "checked": 0, "total_issues": 0, "paragraphs": []}

    # 2) 并发逐段检查（Semaphore 限并发）
    sem = asyncio.Semaphore(max(1, concurrency))
    results: List[Optional[tuple]] = [None] * total
    done = 0
    lock = asyncio.Lock()

    async def _work(i: int, idx: int, text: str):
        nonlocal done
        async with sem:
            r = await analyze_paragraph(text, paper_type)
        async with lock:
            done += 1
            if progress_cb:
                try:
                    progress_cb(done, total)
                except Exception:
                    pass
        results[i] = (idx, text, r)

    await asyncio.gather(*[_work(i, idx, t) for i, (idx, t) in enumerate(targets)])

    # 3) 汇总，仅保留有建议的段
    out_paras: List[dict] = []
    total_issues = 0
    for item in results:
        if not item:
            continue
        idx, text, r = item
        ic = r.get("issue_count", 0)
        total_issues += ic
        if ic > 0:
            out_paras.append({
                "index": idx,
                "text": text[:300],
                "grammar": r.get("grammar") or [],
                "style": r.get("style") or [],
                "logic": r.get("logic") or [],
                "argument": r.get("argument") or [],
                "overall": r.get("overall", ""),
                "issue_count": ic,
            })

    logger.info(
        f"[writing.whole] 总 {len(all_paras)} 段 → 送检 {total} 段 → "
        f"{len(out_paras)} 段有建议，共 {total_issues} 条"
    )
    return {
        "total_paragraphs": len(all_paras),
        "checked": total,
        "total_issues": total_issues,
        "paragraphs": out_paras,
    }
