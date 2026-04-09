"""
格式化相关 Schema
"""
from pydantic import BaseModel
from typing import Optional

class FormatRequest(BaseModel):
    template_id: str
    
class FormatStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    result: Optional[dict] = None
    error: Optional[str] = None
    download_url: Optional[str] = None
