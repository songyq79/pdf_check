"""
本地论文库模型

MySQL 是唯一真数据源，FAISS 是加速层（可随时从此表重建）。
去重：DOI UNIQUE（主）+ title_hash UNIQUE（兜底）。
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, LargeBinary

from app.models.user import Base


class LocalPaper(Base):
    __tablename__ = "local_papers"

    id          = Column(Integer, primary_key=True, index=True)
    doi         = Column(String(255), unique=True, nullable=True, index=True)
    title_hash  = Column(String(32),  unique=True, nullable=False, index=True)
    title       = Column(Text, nullable=False)
    abstract    = Column(Text, nullable=False)
    authors     = Column(String(500), nullable=True)
    year        = Column(Integer, nullable=True)
    source      = Column(String(50),  nullable=False, default="openalex")
    embedding   = Column(LargeBinary, nullable=True)   # 384 × float32 = 1536 bytes
    created_at  = Column(DateTime, default=datetime.utcnow)
