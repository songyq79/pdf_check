"""
管理后台 — 本地论文库接口
GET  /admin/local-papers/stats        统计信息
GET  /admin/local-papers              分页列表（支持搜索/过滤）
GET  /admin/local-papers/{paper_id}   论文详情
DELETE /admin/local-papers/{paper_id} 删除（MySQL + FAISS）
POST /admin/local-papers/rebuild      全量重建 FAISS 索引
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.v1.auth import require_admin
from app.models.local_paper import LocalPaper
from app.models.user import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── 统计 ─────────────────────────────────────────────────────

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), _=Depends(require_admin)):
    total = db.query(func.count(LocalPaper.id)).scalar() or 0

    # 今日写回数（created_at = 今天）
    today = date.today()
    today_count = db.query(func.count(LocalPaper.id)).filter(
        func.date(LocalPaper.created_at) == today
    ).scalar() or 0

    # 来源分布
    rows = db.query(LocalPaper.source, func.count(LocalPaper.id)).group_by(LocalPaper.source).all()
    by_source = [{"source": r[0], "count": r[1]} for r in rows]

    # FAISS 状态
    try:
        from app.core.plagiarism.local_index import local_index
        index_ready = local_index.ready
        index_size_mb = local_index.index_size_mb
        index_total = local_index.total
    except Exception:
        index_ready = False
        index_size_mb = 0.0
        index_total = 0

    return {
        "total": total,
        "today_writeback": today_count,
        "index_ready": index_ready,
        "index_size_mb": index_size_mb,
        "index_total": index_total,
        "by_source": by_source,
    }


# ── 分页列表 ──────────────────────────────────────────────────

@router.get("")
def list_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    year_from: Optional[int] = Query(None),
    year_to: Optional[int] = Query(None),
    has_embedding: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    q = db.query(LocalPaper)

    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            LocalPaper.title.like(like) |
            LocalPaper.authors.like(like) |
            LocalPaper.doi.like(like)
        )
    if source:
        q = q.filter(LocalPaper.source == source)
    if year_from:
        q = q.filter(LocalPaper.year >= year_from)
    if year_to:
        q = q.filter(LocalPaper.year <= year_to)
    if has_embedding is True:
        q = q.filter(LocalPaper.embedding.isnot(None))
    elif has_embedding is False:
        q = q.filter(LocalPaper.embedding.is_(None))

    total = q.count()
    items = q.order_by(LocalPaper.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_paper_brief(p) for p in items],
    }


# ── 详情 ─────────────────────────────────────────────────────

@router.get("/{paper_id}")
def get_paper(paper_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    paper = db.query(LocalPaper).filter(LocalPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    return _paper_detail(paper)


# ── 删除 ─────────────────────────────────────────────────────

@router.delete("/{paper_id}")
def delete_paper(paper_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    paper = db.query(LocalPaper).filter(LocalPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    db.delete(paper)
    db.commit()

    try:
        from app.core.plagiarism.local_index import local_index
        local_index.remove(paper_id)
    except Exception as e:
        logger.warning(f"[admin_papers] FAISS 删除失败（不影响 MySQL）: {e}")

    return {"message": "已删除"}


# ── 重建索引 ──────────────────────────────────────────────────

@router.post("/rebuild")
def rebuild_index(_=Depends(require_admin)):
    try:
        from app.core.plagiarism.local_index import local_index
        count = local_index.rebuild_from_db()
        return {"message": f"索引重建完成，共 {count} 篇"}
    except Exception as e:
        logger.error(f"[admin_papers] 重建索引失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── 辅助序列化 ────────────────────────────────────────────────

def _paper_brief(p: LocalPaper) -> dict:
    return {
        "id": p.id,
        "title": p.title,
        "authors": p.authors or "",
        "year": p.year,
        "doi": p.doi,
        "source": p.source,
        "has_embedding": p.embedding is not None,
        "created_at": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
    }


def _paper_detail(p: LocalPaper) -> dict:
    d = _paper_brief(p)
    d["abstract"] = p.abstract
    d["embedding_dim"] = 384 if p.embedding else None
    return d
