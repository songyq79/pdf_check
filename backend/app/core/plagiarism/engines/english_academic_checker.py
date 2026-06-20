"""
英文学术查重引擎 V1。
流程:strip → segment → key sentence → embed → 并行查 3 API → cosine topk
→ N-gram 硬命中(直判 direct_copy)→ 剩余 AI 批处理 → confidence 评分 → 组装。
任一 API 失败不阻塞;全失败抛 AllFailedError(外层 Celery catch 后降级到 HybridChecker)。
"""
from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from loguru import logger

from app.core.plagiarism import (
    confidence_scorer,
    ngram_matcher,
    reference_stripper,
    semantic_encoder,
)
from app.core.plagiarism.base_checker import (
    BaseChecker, CheckResult, CheckSummary, HighlightItem, SourceItem,
)
from app.core.plagiarism.external.aggregator import (
    ExternalSourceAggregator,
    ExternalSourceAggregatorAllFailedError,
)
from app.core.plagiarism.external.base_source import CandidatePaper
from app.core.plagiarism.key_sentence_extractor import extract_key_sentences
from app.core.plagiarism.levels import (
    get_level_config, classify_risk, get_threshold_snapshot,
)
from app.core.plagiarism.prompts_en import (
    BATCH_VERIFY_PROMPT,
    get_strictness_hint_en,
)


def _merge_rate(highlights: List[HighlightItem], total_chars: int) -> Tuple[int, float]:
    if not highlights or total_chars == 0:
        return 0, 0.0
    intervals = sorted([(h.start_pos, h.end_pos) for h in highlights])
    merged = []
    for s, e in intervals:
        if merged and s < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append([s, e])
    dup = min(sum(e - s for s, e in merged), total_chars)
    return dup, round(dup / total_chars * 100, 1)


def _call_qwen(prompt: str, api_key: str, model: str = "qwen-plus",
               timeout: int = 90) -> str:
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
        max_tokens=2048,
    )
    return resp.choices[0].message.content.strip()


def _extract_json_array(raw: str) -> list:
    """容错提取 LLM 返回的 JSON 数组。"""
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if not m:
        return []
    try:
        return json.loads(m.group(0))
    except Exception:
        return []


class EnglishAcademicChecker(BaseChecker):

    def __init__(self):
        self._api_key = os.getenv("BAILIAN_API_KEY", "")
        if not self._api_key:
            raise RuntimeError("BAILIAN_API_KEY 未配置,无法使用 english_academic 引擎")
        self._aggregator = ExternalSourceAggregator()
        logger.info("[english_academic] 引擎初始化完成")

    def check(self, text: str, task_id: str, paper_type: str = "") -> CheckResult:
        cfg = get_level_config(paper_type, language="en")
        embed_threshold = float(cfg["embed_threshold"])
        ngram_size = int(cfg["ngram_size"])
        min_confidence = int(cfg["min_confidence"])
        max_keys = int(cfg["key_sentences"])
        strictness_hint = get_strictness_hint_en(cfg["strictness"])

        logger.info(
            f"[english_academic] task_id={task_id} len={len(text)} "
            f"paper_type={paper_type or '_'} label={cfg['label']} "
            f"embed_threshold={embed_threshold} ngram={ngram_size} "
            f"min_confidence={min_confidence}"
        )

        # 1. 剥离参考文献 + 引文标注
        cleaned = reference_stripper.preprocess_english(text)
        if len(cleaned) < 200:
            raise ValueError("TEXT_TOO_SHORT: 清洗后文本过短")

        # 2+3. 关键句抽取
        key_sents = extract_key_sentences(cleaned, max_count=max_keys)
        if not key_sents:
            logger.warning("[english_academic] 无关键句")
            return self._empty_result(task_id, cleaned, paper_type)
        logger.info(f"[english_academic] 抽取 {len(key_sents)} 个关键句")

        # 4. 用户关键句一次性 embed
        user_texts = [s for s, _, _ in key_sents]
        user_vecs = semantic_encoder.encode_batch(user_texts)

        # 5a. 先查本地 FAISS 论文库
        cand_pool: Dict[str, CandidatePaper] = {}
        per_query_cand_keys: List[List[str]] = []
        local_hit_counts: List[int] = []
        try:
            from app.core.plagiarism.local_index import local_index
            from app.models.local_paper import LocalPaper
            from app.models.user import SessionLocal

            if local_index.ready and local_index.total > 0:
                db = SessionLocal()
                try:
                    for u_vec in user_vecs:
                        hits = local_index.search(u_vec, topk=10, threshold=embed_threshold)
                        keys = []
                        for paper_id, score in hits:
                            row = db.query(LocalPaper).filter(LocalPaper.id == paper_id).first()
                            if row is None:
                                continue
                            k = row.doi or row.title.strip().lower()
                            if not k:
                                continue
                            if k not in cand_pool:
                                cand_pool[k] = CandidatePaper(
                                    title=row.title,
                                    abstract=row.abstract,
                                    authors=row.authors.split("; ") if row.authors else [],
                                    year=row.year,
                                    doi=row.doi,
                                    url=f"https://doi.org/{row.doi}" if row.doi else "",
                                    source_name="local_library",
                                )
                            keys.append(k)
                        per_query_cand_keys.append(keys)
                        local_hit_counts.append(len(keys))
                finally:
                    db.close()
                logger.info(
                    f"[english_academic] 本地命中 total_cands={len(cand_pool)} "
                    f"per_query={local_hit_counts}"
                )
        except Exception as _local_err:
            logger.warning(f"[english_academic] 本地库查询异常，降级到外部API: {_local_err}")
            cand_pool = {}
            per_query_cand_keys = []
            local_hit_counts = []

        # 5b. 本地命中不足时补查外部 API
        _LOCAL_ENOUGH = 5   # 每句至少命中5条才跳过外部API
        need_external = not local_hit_counts or any(c < _LOCAL_ENOUGH for c in local_hit_counts)
        if need_external:
            try:
                ext_cand_lists = asyncio.run(
                    self._aggregator.batch_search(user_texts, limit_per_q=10)
                )
                # 外部结果合并进 cand_pool，并写回本地库
                for q_idx, cands in enumerate(ext_cand_lists):
                    if q_idx >= len(per_query_cand_keys):
                        per_query_cand_keys.append([])
                    for c in cands:
                        k = c.doi or c.title.strip().lower()
                        if not k:
                            continue
                        cand_pool.setdefault(k, c)
                        if k not in per_query_cand_keys[q_idx]:
                            per_query_cand_keys[q_idx].append(k)
                # 异步写回本地库（不阻塞查重流程）
                self._writeback_to_local(list(cand_pool.values()), user_vecs)
            except ExternalSourceAggregatorAllFailedError:
                if not cand_pool:
                    raise  # 本地也空，无法继续，交 Celery 降级

        all_keys = list(cand_pool.keys())
        all_abstracts = [cand_pool[k].abstract for k in all_keys]

        if not all_abstracts:
            logger.info("[english_academic] 无候选摘要")
            return self._empty_result(task_id, cleaned, paper_type)

        cand_vecs = semantic_encoder.encode_batch(all_abstracts)
        key_to_idx = {k: i for i, k in enumerate(all_keys)}

        # 6. 对每个用户句算 topk
        topk = semantic_encoder.cosine_topk(
            user_vecs, cand_vecs, k=5, threshold=embed_threshold,
        )

        # 7+8. 针对每个 (user_sent, candidate) 跑 n-gram,收集需要 AI 的批次
        source_map: Dict[str, SourceItem] = {}
        highlights: List[HighlightItem] = []
        h_id = 1
        ai_pairs: List[Tuple[int, int, float, str]] = []  # (user_idx, cand_idx, embed_sim, cand_key)

        for u_idx, hits in enumerate(topk):
            for cand_idx, sim in hits:
                cand_key = all_keys[cand_idx]
                cand = cand_pool[cand_key]
                user_sent, start_pos, end_pos = key_sents[u_idx]
                ng = ngram_matcher.check(user_sent, cand.abstract, n=ngram_size)
                if ng is not None:
                    conf = confidence_scorer.score(
                        ngram_hit=True, embed_sim=sim, ai_verdict="direct_copy",
                    )
                    src_id = self._register_source(source_map, cand)
                    highlights.append(HighlightItem(
                        id=h_id, text=user_sent,
                        start_pos=start_pos, end_pos=end_pos,
                        similarity=max(sim, 0.95),
                        source_id=src_id,
                        ai_judged=False,
                        verdict="direct_copy",
                        confidence=conf,
                        ngram_hit=True,
                    ))
                    h_id += 1
                else:
                    ai_pairs.append((u_idx, cand_idx, sim, cand_key))

        # 9. AI 批处理剩余候选
        if ai_pairs:
            ai_verdicts = self._batch_ai_verify(
                ai_pairs, key_sents, cand_pool, all_keys, strictness_hint,
            )
            for (u_idx, cand_idx, sim, cand_key), verdict_obj in zip(ai_pairs, ai_verdicts):
                verdict = verdict_obj.get("verdict", "original")
                if verdict == "original":
                    continue
                ai_sim = float(verdict_obj.get("similarity", sim) or sim)
                conf = confidence_scorer.score(
                    ngram_hit=False, embed_sim=sim, ai_verdict=verdict,
                )
                if conf < min_confidence:
                    continue
                cand = cand_pool[cand_key]
                user_sent, start_pos, end_pos = key_sents[u_idx]
                src_id = self._register_source(source_map, cand)
                highlights.append(HighlightItem(
                    id=h_id, text=user_sent,
                    start_pos=start_pos, end_pos=end_pos,
                    similarity=ai_sim,
                    source_id=src_id,
                    ai_judged=True,
                    verdict=verdict,
                    confidence=conf,
                    ngram_hit=False,
                ))
                h_id += 1

        dup_chars, rate = _merge_rate(highlights, len(cleaned))
        risk = classify_risk(rate, paper_type, language="en")

        logger.info(
            f"[english_academic] done rate={rate}% risk={risk} "
            f"highlights={len(highlights)} sources={len(source_map)}"
        )

        return CheckResult(
            task_id=task_id,
            engine="english_academic",
            created_at=datetime.now().isoformat(),
            summary=CheckSummary(
                total_chars=len(cleaned),
                dup_chars=dup_chars,
                rate=rate,
                risk_level=risk,
            ),
            highlights=highlights,
            sources=list(source_map.values()),
            raw_text=cleaned,
            paper_type=paper_type or "",
            threshold_snapshot=get_threshold_snapshot(paper_type, language="en"),
        )

    def _writeback_to_local(
        self,
        cands: List[CandidatePaper],
        user_vecs,
    ) -> None:
        """将外部 API 候选论文异步写回本地库（fire-and-forget，失败不影响查重结果）。"""
        try:
            from app.core.plagiarism.local_index import local_index
            from app.models.local_paper import LocalPaper
            from app.models.user import SessionLocal
            import hashlib, re, struct, numpy as np

            if not local_index.ready:
                return

            def _normalize(t: str) -> str:
                t = t.lower()
                t = re.sub(r"[^\w\s]", "", t)
                return re.sub(r"\s+", " ", t).strip()

            def _th(t: str) -> str:
                return hashlib.md5(_normalize(t).encode()).hexdigest()

            def _to_bytes(v: np.ndarray) -> bytes:
                return struct.pack(f"384f", *v.astype(np.float32).tolist())

            db = SessionLocal()
            try:
                for c in cands:
                    if not c.abstract or len(c.abstract) < 50:
                        continue
                    th = _th(c.title)
                    doi = c.doi or None
                    exists = db.query(LocalPaper.id).filter(
                        (LocalPaper.title_hash == th) |
                        (LocalPaper.doi == doi if doi else False)
                    ).first()
                    if exists:
                        continue
                    vec = semantic_encoder.encode_batch([c.abstract])[0]
                    paper = LocalPaper(
                        doi=doi,
                        title_hash=th,
                        title=c.title[:1000],
                        abstract=c.abstract[:3000],
                        authors="; ".join(c.authors[:5]) if c.authors else "",
                        year=c.year,
                        source=c.source_name or "external",
                        embedding=_to_bytes(vec),
                    )
                    from sqlalchemy.exc import IntegrityError
                    try:
                        db.add(paper)
                        db.flush()
                        db.commit()
                        local_index.add(paper.id, vec)
                    except IntegrityError:
                        db.rollback()
                    except Exception:
                        db.rollback()
            finally:
                db.close()
        except Exception as e:
            logger.debug(f"[english_academic] writeback_to_local 失败(非致命): {e}")

    def _register_source(
        self, source_map: Dict[str, SourceItem], cand: CandidatePaper,
    ) -> str:
        key = cand.doi or cand.title.strip().lower()
        if key in source_map:
            return source_map[key].id
        src_id = f"src-{len(source_map) + 1}"
        source_map[key] = SourceItem(
            id=src_id,
            title=cand.title,
            author=", ".join(cand.authors[:3]),
            year=cand.year,
            url=cand.url,
            doi=cand.doi,
            source_name=cand.source_name,
            abstract=cand.abstract,
        )
        return src_id

    def _batch_ai_verify(
        self,
        ai_pairs: List[Tuple[int, int, float, str]],
        key_sents: List[Tuple[str, int, int]],
        cand_pool: Dict[str, CandidatePaper],
        all_keys: List[str],
        strictness_hint: str,
    ) -> List[dict]:
        """批量送 qwen-plus 判定。失败时所有返回 original。"""
        if not ai_pairs:
            return []

        pairs_payload = []
        for idx, (u_idx, cand_idx, _, cand_key) in enumerate(ai_pairs):
            cand = cand_pool[cand_key]
            pairs_payload.append({
                "idx": idx,
                "user_sentence": key_sents[u_idx][0][:800],
                "candidate_abstract": cand.abstract[:1200],
            })

        prompt = BATCH_VERIFY_PROMPT.format(
            strictness_hint=strictness_hint,
            pairs_json=json.dumps(pairs_payload, ensure_ascii=False),
        )
        try:
            raw = _call_qwen(prompt, self._api_key, model="qwen-plus", timeout=90)
            arr = _extract_json_array(raw)
            by_idx = {int(x.get("idx", -1)): x for x in arr if isinstance(x, dict)}
            return [by_idx.get(i, {"verdict": "original", "similarity": 0.0})
                    for i in range(len(ai_pairs))]
        except Exception as e:
            logger.warning(f"[english_academic] 批量 AI 判定失败: {e}")
            return [{"verdict": "original", "similarity": 0.0} for _ in ai_pairs]

    def _empty_result(self, task_id: str, text: str, paper_type: str) -> CheckResult:
        return CheckResult(
            task_id=task_id,
            engine="english_academic",
            created_at=datetime.now().isoformat(),
            summary=CheckSummary(
                total_chars=len(text), dup_chars=0, rate=0.0, risk_level="low",
            ),
            raw_text=text,
            paper_type=paper_type or "",
            threshold_snapshot=get_threshold_snapshot(paper_type, language="en"),
        )
