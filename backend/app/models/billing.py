"""
计费相关数据库模型
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text,
    UniqueConstraint,
)

from app.models.user import Base


class SystemConfig(Base):
    """系统配置（键值对）"""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Subscription(Base):
    """包月订阅"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class QuotaBalance(Base):
    """额度余额（按来源分行记录）"""
    __tablename__ = "quota_balances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    source = Column(String(20), nullable=False)  # free / purchase / referral / subscription
    remaining = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "source", name="uq_user_source"),
    )


class Order(Base):
    """订单"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(32), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_type = Column(String(10), nullable=False)   # per_use / monthly
    quantity = Column(Integer, default=1)                # 按次购买数量
    amount_cents = Column(Integer, nullable=False)       # 金额（分）
    status = Column(String(15), default="pending")       # pending / paid / cancelled / refund_pending / refunded
    pay_method = Column(String(10), nullable=True)       # wechat / alipay
    pay_url = Column(Text, nullable=True)                # 支付二维码链接
    paid_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)
    refund_reason = Column(Text, nullable=True)          # 用户填写的退款原因
    refund_reject_reason = Column(Text, nullable=True)   # 管理员拒绝原因
    refund_applied_at = Column(DateTime, nullable=True)  # 用户申请退款时间
    refund_amount_cents = Column(Integer, nullable=True) # 实际退款金额（分），None=全额
    created_at = Column(DateTime, default=datetime.utcnow)


class UsageRecord(Base):
    """使用记录"""
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(30), nullable=False)          # evaluation / plagiarism / proofread / formatter
    consumed_from = Column(String(20), nullable=False)   # subscription / purchase / referral / free
    task_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TaskRecord(Base):
    """任务结果永久存储（Redis TTL过期后从此表恢复）"""
    __tablename__ = "task_records"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(64), unique=True, nullable=False, index=True)
    task_type = Column(String(20), nullable=False)   # proofread / evaluation / formatter / plagiarism
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    status = Column(String(10), nullable=False, default="pending")  # pending / success / failure
    result_json = Column(Text, nullable=True)        # Celery result dict 序列化
    output_file = Column(String(255), nullable=True) # 输出文件路径（相对 storage/outputs/）
    error_msg = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)


class InviteCode(Base):
    """邀请码"""
    __tablename__ = "invite_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(16), unique=True, nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    used_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
