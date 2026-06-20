"""
文献综述 API — Loop 0 占位空壳。
真实端点（upload/status/result/download）在 Loop 5 实现。
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """占位健康检查，确认路由已挂载。"""
    return {"module": "literature_review", "status": "scaffold", "ready": False}
