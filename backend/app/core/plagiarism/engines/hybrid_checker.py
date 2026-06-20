"""
Hybrid 查重引擎 V2
直接调用百炼大模型（qwen-turbo / qwen-plus）分析论文片段是否存在抄袭痕迹。
不依赖参考语料库，纯 AI 语义判断。

V2.1:支持 paper_type 分级 - 按本科/硕士/博士/期刊调整:
- 送深度确认的门槛(confirm_threshold)
- qwen-plus 判定严格度(prompts 里的 strictness hint)
- 风险等级阈值(classify_risk)
"""
from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Tuple, Dict

from loguru import logger

from app.core.plagiarism.base_checker import (
    BaseChecker, CheckResult, CheckSummary, HighlightItem, SourceItem,
)
from app.core.plagiarism.levels import (
    get_level_config, classify_risk, get_threshold_snapshot,
)
from app.core.plagiarism.prompts import get_strictness_hint

CHUNK_SIZE = 400
CHUNK_OVERLAP = 50
BATCH_SIZE = 8
MAX_PLUS_CONFIRM = 8
MAX_WORKERS = 4


def _split_chunks(text: str) -> List[Tuple[int, int, str]]:
    chunks = []
    pos = 0
    while pos < len(text):
        end = min(pos + CHUNK_SIZE, len(text))
        chunks.append((pos, end, text[pos:end]))
        if end == len(text):
            break
        pos += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def _calc_dup_rate(highlights: list, total_chars: int) -> Tuple[int, float]:
    """合并重叠区间后计算不重复的重复字符数，避免超过100%"""
    if not highlights or total_chars == 0:
        return 0, 0.0
    intervals = sorted([(h.start_pos, h.end_pos) for h in highlights], key=lambda x: x[0])
    merged = []
    for start, end in intervals:
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append([start, end])
    dup_chars = sum(e - s for s, e in merged)
    dup_chars = min(dup_chars, total_chars)
    rate = round(dup_chars / total_chars * 100, 1)
    return dup_chars, rate


def _call_llm(model: str, prompt: str, api_key: str, timeout: int = 60) -> str:
    from openai import OpenAI
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=timeout,
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1024,
    )
    return resp.choices[0].message.content.strip()


def _screen_one_batch(batch_idx: int, batch: List[Tuple[int, int, str]], api_key: str) -> List[Tuple[int, int, str, float]]:
    numbered = "\n\n".join(f"[{j+1}] {c[2]}" for j, c in enumerate(batch))
    prompt = f"""你是一位学术论文查重专家。请分析以下论文片段，判断每个片段是否存在抄袭或高度相似于已知文献的痕迹。

评判标准：
- 1.0：几乎确定是直接抄袭或逐字复制
- 0.7~0.9：高度疑似，措辞与常见文献高度雷同
- 0.4~0.6：有一定相似性，可能是改写或意译
- 0.0~0.3：原创性较高，无明显抄袭痕迹

请对每个片段给出 0~1 的相似度分数，格式严格如下（每行一个）：
[序号] 分数

论文片段：
{numbered}

请直接输出评分，不要解释："""

    try:
        raw = _call_llm("qwen-turbo", prompt, api_key, timeout=45)
        logger.debug(f"[hybrid] turbo batch-{batch_idx} 响应: {raw[:100]}")
        score_map = {}
        auto_idx = 1
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            m = re.match(r"[\[\(]?(\d+)[\]\)]?\s+([\d.]+)", line)
            if m:
                score_map[int(m.group(1))] = min(max(float(m.group(2)), 0.0), 1.0)
            else:
                m2 = re.match(r"^([\d.]+)$", line)
                if m2:
                    score_map[auto_idx] = min(max(float(m2.group(1)), 0.0), 1.0)
                    auto_idx += 1
        return [(start, end, chunk, score_map.get(j + 1, 0.3))
                for j, (start, end, chunk) in enumerate(batch)]
    except Exception as e:
        logger.warning(f"[hybrid] turbo batch-{batch_idx} 失败: {e}")
        return [(start, end, chunk, 0.3) for start, end, chunk in batch]


def _batch_screen(chunks: List[Tuple[int, int, str]], api_key: str) -> List[Tuple[int, int, str, float]]:
    batches = [chunks[i: i + BATCH_SIZE] for i in range(0, len(chunks), BATCH_SIZE)]
    results_map: Dict[int, list] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_screen_one_batch, idx, batch, api_key): idx
            for idx, batch in enumerate(batches)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results_map[idx] = future.result()
            except Exception as e:
                logger.warning(f"[hybrid] batch-{idx} 异常: {e}")
                results_map[idx] = [(s, e, c, 0.3) for s, e, c in batches[idx]]
    results = []
    for idx in range(len(batches)):
        results.extend(results_map.get(idx, []))
    return results


def _confirm_one(
    start: int, end: int, chunk: str, sim: float, api_key: str,
    strictness_hint: str = "",
) -> Tuple[int, int, str, float, str, str]:
    """
    深度确认单片段，返回 (start, end, chunk, final_sim, verdict, source_ref)
    source_ref: AI 分析出的具体文献引用信息
    strictness_hint: 分级严格度提示(由 paper_type 决定),空串则按通用标准
    """
    hint_block = f"\n{strictness_hint}\n" if strictness_hint else ""
    prompt = f"""你是一位严格的学术论文查重专家。请深度分析以下论文片段，判断是否存在抄袭。
{hint_block}
请给出：
1. 最终相似度（0~1）
2. 判定结论（直接抄袭 / 疑似改写 / 通用表述 / 原创）
3. 疑似来源（如能识别，写出具体文献名称、作者、期刊/出版社、年份；若无法识别写"未知来源"）

格式：
相似度: 0.XX
结论: XXX
来源: XXX

论文片段：
{chunk}"""
    try:
        raw = _call_llm("qwen-plus", prompt, api_key, timeout=60)
        logger.debug(f"[hybrid] plus 确认: {raw[:150]}")
        final_sim = sim
        verdict = "疑似重复"
        source_ref = "未知来源"

        sim_m = re.search(r"相似度[：:]\s*([\d.]+)", raw)
        if sim_m:
            final_sim = min(max(float(sim_m.group(1)), 0.0), 1.0)
        verdict_m = re.search(r"结论[：:]\s*(.+)", raw)
        if verdict_m:
            verdict = verdict_m.group(1).strip()
        source_m = re.search(r"来源[：:]\s*(.+)", raw)
        if source_m:
            source_ref = source_m.group(1).strip()

        return (start, end, chunk, final_sim, verdict, source_ref)
    except Exception as e:
        logger.warning(f"[hybrid] plus 确认失败: {e}")
        return (start, end, chunk, sim, "疑似重复", "未知来源")


def _deep_confirm(
    candidates: List[Tuple[int, int, str, float]], api_key: str,
    strictness_hint: str = "",
) -> List[Tuple[int, int, str, float, str, str]]:
    confirmed = [None] * len(candidates)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_confirm_one, s, e, c, sim, api_key, strictness_hint): i
            for i, (s, e, c, sim) in enumerate(candidates)
        }
        for future in as_completed(futures):
            i = futures[future]
            confirmed[i] = future.result()
    return confirmed


class HybridChecker(BaseChecker):

    def __init__(self):
        self._api_key = os.getenv("BAILIAN_API_KEY", "")
        if not self._api_key:
            raise RuntimeError("BAILIAN_API_KEY 未配置，无法使用 hybrid 引擎")
        logger.info(f"[hybrid] 引擎初始化完成，API KEY 前8位: {self._api_key[:8]}...")

    def check(self, text: str, task_id: str, paper_type: str = "") -> CheckResult:
        cfg = get_level_config(paper_type)
        confirm_threshold = float(cfg["confirm_threshold"])
        strictness_hint = get_strictness_hint(cfg["strictness"])

        logger.info(
            f"[hybrid] 开始查重 task_id={task_id} 文本长度={len(text)} "
            f"paper_type={paper_type or '_'} label={cfg['label']} "
            f"confirm_threshold={confirm_threshold} rate_high={cfg['rate_high']}%"
        )
        chunks = _split_chunks(text)
        logger.info(f"[hybrid] 共切分 {len(chunks)} 个片段，并发初筛中...")

        screened = _batch_screen(chunks, self._api_key)
        logger.info(f"[hybrid] 初筛完成")

        candidates = sorted(
            [(s, e, c, sim) for s, e, c, sim in screened if sim >= confirm_threshold],
            key=lambda x: x[3], reverse=True
        )[:MAX_PLUS_CONFIRM]
        logger.info(f"[hybrid] 送 qwen-plus 深度确认: {len(candidates)} 个")

        confirmed = (
            _deep_confirm(candidates, self._api_key, strictness_hint)
            if candidates else []
        )

        # 收集 plus 确认的来源信息，去重建立 sources 列表
        source_map: Dict[str, SourceItem] = {}  # source_ref -> SourceItem
        confirmed_ranges = set()
        highlights: List[HighlightItem] = []
        h_id = 1

        for item in confirmed:
            start, end, chunk, final_sim, verdict, source_ref = item
            confirmed_ranges.add((start, end))
            if final_sim < 0.4:
                continue
            # 来源去重
            if source_ref not in source_map:
                src_id = f"src-{len(source_map)+1}"
                source_map[source_ref] = SourceItem(
                    id=src_id,
                    title=source_ref,
                    author="",
                    year=None,
                    url=None,
                )
            src_id = source_map[source_ref].id
            highlights.append(HighlightItem(
                id=h_id,
                text=chunk,
                start_pos=start,
                end_pos=end,
                similarity=final_sim,
                source_id=src_id,
                ai_judged=True,
                verdict=verdict,
            ))
            h_id += 1

        # turbo 初筛高分但未送 plus 的片段
        for s, e, c, sim in screened:
            if (s, e) in confirmed_ranges:
                continue
            if sim >= 0.4:
                src_ref = "AI初筛疑似相似（未深度确认）"
                if src_ref not in source_map:
                    src_id = f"src-{len(source_map)+1}"
                    source_map[src_ref] = SourceItem(
                        id=src_id, title=src_ref, author="", year=None, url=None,
                    )
                src_id = source_map[src_ref].id
                highlights.append(HighlightItem(
                    id=h_id,
                    text=c,
                    start_pos=s,
                    end_pos=e,
                    similarity=sim,
                    source_id=src_id,
                    ai_judged=True,
                    verdict="疑似相似",
                ))
                h_id += 1

        sources = list(source_map.values())

        # 合并重叠区间计算真实重复率，避免超过100%
        dup_chars, rate = _calc_dup_rate(highlights, len(text))
        risk_level = classify_risk(rate, paper_type)

        logger.info(
            f"[hybrid] 查重完成 rate={rate}% risk={risk_level} "
            f"label={cfg['label']} highlights={len(highlights)} sources={len(sources)}"
        )

        return CheckResult(
            task_id=task_id,
            engine="hybrid-v2",
            created_at=datetime.now().isoformat(),
            summary=CheckSummary(
                total_chars=len(text),
                dup_chars=dup_chars,
                rate=rate,
                risk_level=risk_level,
            ),
            highlights=highlights,
            sources=sources,
            raw_text=text,
            paper_type=paper_type or "",
            threshold_snapshot=get_threshold_snapshot(paper_type),
        )
