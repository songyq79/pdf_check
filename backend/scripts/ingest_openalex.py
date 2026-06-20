"""
OpenAlex 批量论文入库脚本

用法：
  cd backend
  python scripts/ingest_openalex.py --concept "computer science" --limit 100000
  python scripts/ingest_openalex.py --concept "medicine" --limit 500000

参数：
  --concept   学科关键词（OpenAlex concept name）
  --limit     目标入库数量（默认 100000）
  --batch     每批写入数量（默认 500）
  --resume    断点续传文件路径（默认 .ingest_cursor.json）

去重：
  DOI UNIQUE（主）+ title_hash UNIQUE（兜底）
  重复论文 INSERT IGNORE 自动跳过
"""

import argparse
import hashlib
import json
import re
import struct
import sys
import time
from pathlib import Path

# 加载 .env
_env = Path(__file__).parent.parent / ".env"
if _env.exists():
    from dotenv import load_dotenv
    load_dotenv(_env, override=True)

import httpx
import numpy as np
from loguru import logger
from sqlalchemy.exc import IntegrityError

# 确保 backend/ 在 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.user import SessionLocal, engine, Base
import app.models.local_paper  # noqa: F401 — 确保建表
from app.models.local_paper import LocalPaper
from app.core.plagiarism import semantic_encoder
from app.core.plagiarism.local_index import local_index

Base.metadata.create_all(bind=engine)

_OPENALEX_URL  = "https://api.openalex.org/works"
_EMAIL         = "voxtex_hub@zohomail.com"   # OpenAlex 礼貌抓取
_HEADERS       = {"User-Agent": f"PaperCheckSystem/1.0 (mailto:{_EMAIL})"}
_CURSOR_FILE   = Path(".ingest_cursor.json")
_DIM           = 384


# ── 工具函数 ──────────────────────────────────────────────────

def _normalize_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r"[^\w\s]", "", t)
    return re.sub(r"\s+", " ", t).strip()


def _title_hash(title: str) -> str:
    return hashlib.md5(_normalize_title(title).encode()).hexdigest()


def _vec_to_bytes(vec: np.ndarray) -> bytes:
    return struct.pack(f"{_DIM}f", *vec.astype(np.float32).tolist())


def _parse_authors(authorships: list) -> str:
    names = []
    for a in authorships[:5]:
        name = (a.get("author") or {}).get("display_name", "")
        if name:
            names.append(name)
    return "; ".join(names)


# ── OpenAlex 查询 ─────────────────────────────────────────────

def fetch_page(concept: str, cursor: str = "*", per_page: int = 200) -> dict:
    params = {
        "search":         concept,
        "filter":         "has_abstract:true,language:en",
        "select":         "id,doi,title,abstract_inverted_index,authorships,publication_year",
        "per-page":       per_page,
        "cursor":         cursor,
        "mailto":         _EMAIL,
    }
    for attempt in range(3):
        try:
            resp = httpx.get(_OPENALEX_URL, params=params, headers=_HEADERS, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"[ingest] 请求失败 attempt={attempt+1}: {e}")
            time.sleep(2 ** attempt)
    raise RuntimeError("OpenAlex 请求连续失败 3 次")


def reconstruct_abstract(inverted: dict) -> str:
    """将 OpenAlex 倒排索引格式还原为正常摘要文本。"""
    if not inverted:
        return ""
    positions = {}
    for word, pos_list in inverted.items():
        for p in pos_list:
            positions[p] = word
    if not positions:
        return ""
    return " ".join(positions[i] for i in sorted(positions))


# ── 写入 ─────────────────────────────────────────────────────

def insert_paper(db, work: dict) -> bool:
    """
    将一篇论文写入 MySQL + FAISS。
    返回 True 表示新增，False 表示重复跳过。
    """
    title = (work.get("title") or "").strip()
    abstract_inv = work.get("abstract_inverted_index") or {}
    abstract = reconstruct_abstract(abstract_inv).strip()

    if not title or not abstract or len(abstract) < 50:
        return False

    doi_raw = work.get("doi") or ""
    doi = doi_raw.replace("https://doi.org/", "").strip() or None
    th  = _title_hash(title)

    authors = _parse_authors(work.get("authorships") or [])
    year    = work.get("publication_year")

    # 计算向量
    vec = semantic_encoder.encode_batch([abstract])[0]
    emb = _vec_to_bytes(vec)

    paper = LocalPaper(
        doi        = doi,
        title_hash = th,
        title      = title[:1000],
        abstract   = abstract[:3000],
        authors    = authors,
        year       = year,
        source     = "openalex",
        embedding  = emb,
    )

    try:
        db.add(paper)
        db.flush()          # 获取 paper.id
        db.commit()
        # 写入 FAISS
        local_index.add(paper.id, vec)
        return True
    except IntegrityError:
        db.rollback()       # DOI 或 title_hash 重复，跳过
        return False
    except Exception as e:
        db.rollback()
        logger.warning(f"[ingest] 写入失败 title={title[:40]}: {e}")
        return False


# ── 主流程 ────────────────────────────────────────────────────

def load_cursor(resume_file: Path) -> str:
    if resume_file.exists():
        try:
            return json.loads(resume_file.read_text()).get("cursor", "*")
        except Exception:
            pass
    return "*"


def save_cursor(resume_file: Path, cursor: str, total: int) -> None:
    resume_file.write_text(json.dumps({"cursor": cursor, "total": total}))


def run(concept: str, limit: int, batch_size: int, resume_file: Path) -> None:
    logger.info(f"[ingest] 开始入库 concept={concept} limit={limit}")

    # 加载 FAISS 索引（确保可写入）
    local_index.load()

    cursor    = load_cursor(resume_file)
    inserted  = 0
    skipped   = 0
    per_page  = 200

    db = SessionLocal()
    try:
        while inserted < limit:
            data   = fetch_page(concept, cursor, per_page)
            works  = data.get("results") or []
            if not works:
                logger.info("[ingest] 无更多结果，退出")
                break

            for work in works:
                if inserted >= limit:
                    break
                ok = insert_paper(db, work)
                if ok:
                    inserted += 1
                else:
                    skipped += 1

                if (inserted + skipped) % 100 == 0:
                    logger.info(
                        f"[ingest] 已处理 {inserted+skipped} 篇 "
                        f"(入库 {inserted} / 跳过 {skipped})"
                    )

            # 断点续传
            next_cursor = (data.get("meta") or {}).get("next_cursor")
            if not next_cursor:
                logger.info("[ingest] 已到末页")
                break
            cursor = next_cursor
            save_cursor(resume_file, cursor, inserted)

            time.sleep(0.1)   # 礼貌间隔

    finally:
        db.close()

    # 清理断点文件
    if resume_file.exists():
        resume_file.unlink()

    logger.info(
        f"[ingest] 完成 concept={concept} 入库={inserted} 跳过={skipped} "
        f"FAISS总量={local_index.total}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenAlex 论文批量入库")
    parser.add_argument("--concept", required=True, help="学科关键词，如 'computer science'")
    parser.add_argument("--limit",   type=int, default=100000, help="目标入库数量")
    parser.add_argument("--batch",   type=int, default=500,    help="每批写入数量")
    parser.add_argument("--resume",  default=".ingest_cursor.json", help="断点续传文件")
    args = parser.parse_args()

    run(
        concept     = args.concept,
        limit       = args.limit,
        batch_size  = args.batch,
        resume_file = Path(args.resume),
    )
