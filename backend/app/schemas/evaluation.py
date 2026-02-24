"""
智能评价相关的数据模型
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime


class EvaluationResult(BaseModel):
    """单个维度的评价结果"""
    dimension_name: str = Field(..., description="维度名称")
    score: int = Field(..., ge=0, le=100, description="得分(0-100)")
    strengths: List[str] = Field(..., description="优点列表")
    weaknesses: List[str] = Field(..., description="问题列表")
    suggestions: List[str] = Field(..., description="改进建议列表")


class EvaluationResponse(BaseModel):
    """评价响应"""
    paper_title: str = Field(..., description="论文标题")
    overall_score: float = Field(..., ge=0, le=100, description="综合评分")
    dimensions: Dict[str, EvaluationResult] = Field(..., description="各维度评价结果")
    evaluated_at: datetime = Field(..., description="评价时间")
    report_id: Optional[str] = Field(None, description="报告ID")
    report_download_url: Optional[str] = Field(None, description="报告下载URL")

    class Config:
        json_schema_extra = {
            "example": {
                "paper_title": "基于深度学习的图像识别研究",
                "overall_score": 85.5,
                "dimensions": {
                    "academic_standard": {
                        "dimension_name": "学术规范性",
                        "score": 88,
                        "strengths": ["结构完整", "格式规范"],
                        "weaknesses": ["部分术语不够准确"],
                        "suggestions": ["建议统一学术术语"]
                    }
                },
                "evaluated_at": "2026-02-09T12:00:00",
                "report_id": "550e8400-e29b-41d4-a716-446655440000",
                "report_download_url": "/api/v1/evaluation/download/550e8400-e29b-41d4-a716-446655440000"
            }
        }
