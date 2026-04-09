"""
错别字检查相关 Schema
"""
from pydantic import BaseModel
from typing import Optional

class SpellCheckStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    stats: Optional[dict] = None
    error: Optional[str] = None
    download_url: Optional[str] = None
