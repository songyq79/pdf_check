"""
计费相关 Pydantic 模型
"""

from datetime import datetime
from typing import Optional, Dict

from pydantic import BaseModel, field_validator


# ── 订单 ──────────────────────────────────────────────────────


class OrderCreate(BaseModel):
    product_type: str       # per_use / monthly
    pay_method: str         # wechat / alipay
    quantity: int = 1       # 按次购买数量（仅 per_use 有效）

    @field_validator('quantity')
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v < 1:
            raise ValueError('购买次数不能小于1')
        if v > 100:
            raise ValueError('单次购买次数不能超过100')
        return v


class OrderOut(BaseModel):
    order_no: str
    user_id: int
    product_type: str
    quantity: int
    amount_cents: int
    status: str
    pay_method: Optional[str]
    pay_url: Optional[str]
    paid_at: Optional[datetime]
    refund_reason: Optional[str]
    refund_reject_reason: Optional[str]
    refund_applied_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ── 配额 ──────────────────────────────────────────────────────


class QuotaResponse(BaseModel):
    subscription: Optional[dict] = None   # {expires_at, days_remaining} 或 None
    credits: Dict[str, int] = {}          # {free: N, purchase: N, referral: N}
    total_credits: int = 0
    has_access: bool = False


# ── 邀请码 ────────────────────────────────────────────────────


class InviteCodeOut(BaseModel):
    code: str
    used_by_id: Optional[int]
    used_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ── 使用记录 ──────────────────────────────────────────────────


class UsageRecordOut(BaseModel):
    action: str
    consumed_from: str
    task_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── 系统配置 ──────────────────────────────────────────────────


class SystemConfigUpdate(BaseModel):
    billing_enabled: Optional[str] = None
    price_per_use: Optional[str] = None
    price_monthly: Optional[str] = None
    free_trial_count: Optional[str] = None
    referral_reward_count: Optional[str] = None


class SystemConfigOut(BaseModel):
    billing_enabled: str = "false"
    price_per_use: str = "300"
    price_monthly: str = "9900"
    free_trial_count: str = "1"
    referral_reward_count: str = "3"


# ── 定价（公开） ──────────────────────────────────────────────


class PricingResponse(BaseModel):
    billing_enabled: bool
    per_use_yuan: str           # "9.90"
    monthly_yuan: str           # "69.90"
    monthly_limit: int = 20     # 包月每月限次
    free_trial_count: int
    referral_reward_count: int


# ── 管理员赠送 ────────────────────────────────────────────────


class GrantQuotaRequest(BaseModel):
    count: int
    source: str = "purchase"  # purchase | free


# ── 退款相关 ──────────────────────────────────────────────────


class RefundRequestBody(BaseModel):
    reason: str  # 用户申请退款的原因


class RefundRejectBody(BaseModel):
    reason: str  # 管理员拒绝的原因


class RefundApproveBody(BaseModel):
    refund_amount_cents: int  # 实际退款金额（分），最小1，最大不超过订单金额
