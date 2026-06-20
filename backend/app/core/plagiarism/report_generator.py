"""
分级查重报告增强器。

- 博士 / 期刊:对高相似片段调用 AI 生成改写建议(rewrite_suggestions)
- 期刊:额外生成整体送审建议(journal_advice)
- 本科 / 硕士 / 通用:直通,不调 AI

设计要点:
1. 不阻断主流程。AI 调用失败或 API Key 缺失,只打 warning 不抛异常。
2. 只吃/吐 plain dict,和 CheckResult.to_dict() 的结构对齐。
3. 并发安全:同 hybrid_checker,使用 ThreadPoolExecutor 并发跑改写建议。
"""
from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from loguru import logger

from app.core.plagiarism.levels import get_level_config
from app.core.plagiarism.prompts import (
    build_journal_advice_prompt,
    build_rewrite_advice_prompt,
)
from app.core.plagiarism.prompts_en import (
    JOURNAL_ADVICE_PROMPT_EN,
    REWRITE_ADVICE_PROMPT_EN,
)

# 每个论文最多生成多少条改写建议,控制成本 + 渲染开销
_MAX_REWRITE_ADVICE = 5
_REWRITE_WORKERS = 3


def _call_llm(prompt: str, api_key: str, timeout: int = 45) -> str:
    from openai import OpenAI
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=timeout,
    )
    resp = client.chat.completions.create(
        model="qwen-plus",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=512,
    )
    return resp.choices[0].message.content.strip()


def _extract_json(raw: str) -> Dict[str, Any] | None:
    """AI 可能包 markdown 代码块,先剥壳再 json.loads。"""
    if not raw:
        return None
    cleaned = raw.strip()
    # 剥 ```json ... ``` 或 ``` ... ```
    m = re.search(r"```(?:json)?\s*(.+?)\s*```", cleaned, re.DOTALL)
    if m:
        cleaned = m.group(1).strip()
    # 退一步只截第一个 { ... } 块
    if not cleaned.startswith("{"):
        m2 = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m2:
            cleaned = m2.group(0)
    try:
        return json.loads(cleaned)
    except Exception as exc:
        logger.debug(f"[plagiarism.report] JSON 解析失败: {exc} raw={raw[:120]}")
        return None


def _gen_one_rewrite(
    highlight: Dict[str, Any], source_title: str, api_key: str, level_label: str,
    language: str = "zh", source_abstract: str = "",
) -> Dict[str, Any] | None:
    if language == "en":
        prompt = REWRITE_ADVICE_PROMPT_EN.format(
            sentence=highlight["text"],
            source_abstract=source_abstract or source_title,
        )
    else:
        prompt = build_rewrite_advice_prompt(
            segment=highlight["text"],
            source=source_title,
            similarity=float(highlight["similarity"]),
            level_label=level_label,
        )
    try:
        raw = _call_llm(prompt, api_key)
    except Exception as exc:
        logger.warning(f"[plagiarism.report] 改写建议调用失败 highlight_id={highlight['id']}: {exc}")
        return None

    parsed = _extract_json(raw)
    if not parsed:
        return None
    if language == "en":
        return {
            "highlight_id": highlight["id"],
            "segment": highlight["text"],
            "similarity": highlight["similarity"],
            "source": source_title,
            "rewrite": parsed.get("rewrite", ""),
            "note": parsed.get("note", ""),
        }
    return {
        "highlight_id": highlight["id"],
        "segment": highlight["text"],
        "similarity": highlight["similarity"],
        "source": source_title,
        "issue": parsed.get("issue", ""),
        "rewrite_tip": parsed.get("rewrite_tip", ""),
        "citation_template": parsed.get("citation_template", ""),
    }


def _pick_top_highlights(result: Dict[str, Any], k: int) -> List[Dict[str, Any]]:
    """按 similarity 降序取前 k 条,用于改写建议。"""
    highlights = result.get("highlights", []) or []
    # 过滤掉明显过短(<20 字)的片段,避免改写建议无意义
    eligible = [h for h in highlights if len(h.get("text", "")) >= 20]
    eligible.sort(key=lambda h: h.get("similarity", 0), reverse=True)
    return eligible[:k]


def _source_title(result: Dict[str, Any], source_id: str) -> str:
    for s in result.get("sources", []) or []:
        if s.get("id") == source_id:
            return s.get("title") or "未知来源"
    return "未知来源"


def _source_abstract(result: Dict[str, Any], source_id: str) -> str:
    for s in result.get("sources", []) or []:
        if s.get("id") == source_id:
            return (s.get("abstract") or "")[:1000]
    return ""


def enrich_report(
    result: Dict[str, Any], paper_type: str,
    api_key: str = "", language: str = "zh",
) -> Dict[str, Any]:
    """
    根据 paper_type + language 对 result 做差异化增强,原地返回同一个 dict。

    触发规则:
    - rewrite_advice=True(博士/期刊) → 为 top highlights 生成改写建议
    - journal_advice=True(期刊) → 生成整体送审评价
    英文:prompts 用 prompts_en 中的模板,否则用中文模板。
    """
    cfg = get_level_config(paper_type, language)
    api_key = api_key or os.getenv("BAILIAN_API_KEY", "")

    needs_rewrite = bool(cfg.get("rewrite_advice"))
    needs_journal = bool(cfg.get("journal_advice"))

    if not needs_rewrite and not needs_journal:
        return result

    if not api_key:
        logger.warning("[plagiarism.report] BAILIAN_API_KEY 缺失,跳过分级增强")
        return result

    level_label = cfg.get("label", "")

    # 1) 改写建议
    if needs_rewrite:
        tops = _pick_top_highlights(result, _MAX_REWRITE_ADVICE)
        if tops:
            suggestions: List[Dict[str, Any]] = []
            with ThreadPoolExecutor(max_workers=_REWRITE_WORKERS) as executor:
                futures = {
                    executor.submit(
                        _gen_one_rewrite, h, _source_title(result, h.get("source_id", "")),
                        api_key, level_label, language,
                        _source_abstract(result, h.get("source_id", "")),
                    ): h["id"]
                    for h in tops
                }
                for fut in as_completed(futures):
                    try:
                        item = fut.result()
                    except Exception as exc:
                        logger.warning(f"[plagiarism.report] 改写建议异常: {exc}")
                        item = None
                    if item:
                        suggestions.append(item)
            # 保持原有相似度排序
            suggestions.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            result["rewrite_suggestions"] = suggestions
            logger.info(f"[plagiarism.report] 生成改写建议 {len(suggestions)} 条 label={level_label}")

    # 2) 期刊整体建议
    if needs_journal:
        summary = result.get("summary", {}) or {}
        rate = float(summary.get("rate", 0))
        high_count = sum(
            1 for h in result.get("highlights", []) or []
            if float(h.get("similarity", 0)) >= 0.8
        )
        red_line = float(cfg.get("rate_high", 15.0))
        if language == "en":
            summary_json = json.dumps({
                "rate": rate, "high_count": high_count,
                "red_line": red_line, "paper_type": paper_type,
            }, ensure_ascii=False)
            prompt = JOURNAL_ADVICE_PROMPT_EN.format(summary_json=summary_json)
        else:
            prompt = build_journal_advice_prompt(
                rate=rate, high_count=high_count, red_line=red_line,
            )
        try:
            raw = _call_llm(prompt, api_key)
            if language == "en":
                result["journal_advice"] = raw.strip()
                logger.info("[plagiarism.report] 生成英文期刊送审建议")
                return result
            parsed = _extract_json(raw)
            if parsed:
                verdict = parsed.get("verdict", "")
                top_issues = parsed.get("top_issues", []) or []
                priority = parsed.get("priority", "")
                issues_text = " / ".join(str(x) for x in top_issues)
                # 拼成一段方便前端单行渲染,结构化字段也保留
                result["journal_advice"] = (
                    f"【送审建议】{verdict}  "
                    f"【主要问题】{issues_text}  "
                    f"【修改优先级】{priority}"
                ).strip()
                result["journal_advice_detail"] = {
                    "verdict": verdict,
                    "top_issues": top_issues,
                    "priority": priority,
                    "red_line": red_line,
                }
                logger.info(f"[plagiarism.report] 生成期刊送审建议 verdict={verdict}")
            else:
                logger.warning("[plagiarism.report] 期刊建议 JSON 解析失败")
        except Exception as exc:
            logger.warning(f"[plagiarism.report] 期刊建议调用失败: {exc}")

    return result
