"""
管理后台API — 系统设置、用户管理增强、订单管理
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.auth import require_admin
from app.models.user import User, get_db
from app.models.billing import Order, Subscription, QuotaBalance
from app.schemas.billing import (
    SystemConfigOut, SystemConfigUpdate, OrderOut, GrantQuotaRequest,
    RefundRejectBody, RefundApproveBody,
)
from app.services import billing_service
from app.services import payment_service

router = APIRouter()


# ── 系统设置 ──────────────────────────────────────────────────


@router.get("/settings", response_model=SystemConfigOut, summary="获取系统配置")
def get_settings(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    config = billing_service.get_all_config(db)
    return SystemConfigOut(**config)


@router.put("/settings", summary="修改系统配置")
def update_settings(
    req: SystemConfigUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    updates = req.model_dump(exclude_none=True)
    for key, value in updates.items():
        billing_service.set_config(db, key, value)
    return {"message": f"已更新 {len(updates)} 项配置"}


# ── 用户管理增强 ──────────────────────────────────────────────


class AdminUserOut(BaseModel):
    id: int
    username: str
    email: Optional[str]
    phone: Optional[str]
    nickname: Optional[str]
    is_admin: bool
    is_approved: bool
    is_active: bool
    subscription_active: bool = False
    subscription_expires: Optional[str] = None
    total_credits: int = 0
    created_at: str

    class Config:
        from_attributes = True


@router.get("/users", response_model=List[AdminUserOut], summary="用户列表（含权益）")
def list_users_enhanced(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    keyword: Optional[str] = Query(None, description="搜索用户名/手机号"),
):
    query = db.query(User)
    if keyword:
        query = query.filter(
            (User.username.contains(keyword)) |
            (User.phone.contains(keyword))
        )
    users = query.order_by(User.created_at.desc()).limit(200).all()

    from datetime import datetime
    now = datetime.utcnow()
    result = []
    for u in users:
        # 查订阅
        sub = db.query(Subscription).filter(
            Subscription.user_id == u.id,
            Subscription.is_active == True,
            Subscription.expires_at > now,
        ).first()

        # 查额度
        balances = db.query(QuotaBalance).filter(QuotaBalance.user_id == u.id).all()
        total_credits = sum(b.remaining for b in balances)

        result.append(AdminUserOut(
            id=u.id,
            username=u.username,
            email=u.email,
            phone=u.phone,
            nickname=u.nickname,
            is_admin=u.is_admin,
            is_approved=u.is_approved,
            is_active=u.is_active,
            subscription_active=sub is not None,
            subscription_expires=sub.expires_at.isoformat() if sub else None,
            total_credits=total_credits,
            created_at=u.created_at.isoformat(),
        ))
    return result


@router.get("/stats/active-users", summary="近一周活跃用户数")
def active_users_count(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    from datetime import datetime, timedelta
    from app.models.billing import UsageRecord
    since = datetime.utcnow() - timedelta(days=7)
    count = db.query(UsageRecord.user_id).filter(
        UsageRecord.created_at >= since,
    ).distinct().count()
    return {"count": count}


@router.post("/users/{user_id}/grant-quota", summary="赠送额度")
def grant_user_quota(
    user_id: int,
    req: GrantQuotaRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if req.count <= 0 or req.count > 100:
        raise HTTPException(status_code=400, detail="赠送次数需在1-100之间")
    billing_service.grant_quota(db, user_id, req.count, req.source)
    source_label = "免费试用" if req.source == "free" else "购买次数"
    return {"message": f"已赠送用户 {user.username} {req.count} 次额度（{source_label}）"}


# ── 订单管理 ──────────────────────────────────────────────────


@router.get("/orders", response_model=List[OrderOut], summary="全部订单列表")
def list_all_orders(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    status: Optional[str] = Query(None, description="按状态筛选"),
):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    return query.order_by(Order.created_at.desc()).limit(200).all()


# ── 退款审核 ──────────────────────────────────────────────────


class RefundRequestOut(BaseModel):
    """退款申请信息"""
    id: int
    order_no: str
    user_id: int
    username: Optional[str]
    amount_cents: int
    refund_reason: str
    refund_applied_at: str

    class Config:
        from_attributes = True


@router.get("/refund-requests", summary="退款申请列表")
def list_refund_requests(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """获取待审核的退款申请"""
    orders = db.query(Order, User).filter(
        Order.status == "refund_pending"
    ).join(User, Order.user_id == User.id).order_by(
        Order.refund_applied_at.desc()
    ).all()

    result = []
    for order, user in orders:
        result.append({
            "id": order.id,
            "order_no": order.order_no,
            "user_id": order.user_id,
            "username": user.username,
            "amount_cents": order.amount_cents,
            "refund_reason": order.refund_reason,
            "refund_applied_at": order.refund_applied_at.isoformat() if order.refund_applied_at else None,
        })
    return result


@router.post("/orders/{order_no}/refund-approve", summary="审核通过退款")
def approve_refund(
    order_no: str,
    req: RefundApproveBody,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """管理员审核通过，调用支付渠道实际退款（支持部分退款）"""
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 校验退款金额
    if req.refund_amount_cents < 1:
        raise HTTPException(status_code=400, detail="退款金额不能低于 0.01 元")
    if req.refund_amount_cents > order.amount_cents:
        raise HTTPException(status_code=400, detail=f"退款金额不能超过订单金额 {order.amount_cents} 分")

    # 调用支付渠道退款
    refund_no = f"R{order_no}"
    refund_ok = False
    if order.pay_method == "wechat":
        refund_ok = payment_service.refund_wechat(order_no, refund_no, req.refund_amount_cents)
    elif order.pay_method == "alipay":
        refund_ok = payment_service.refund_alipay(order_no, refund_no, req.refund_amount_cents)

    if not refund_ok:
        raise HTTPException(status_code=500, detail="支付渠道退款失败，请检查配置或稍后重试")

    try:
        billing_service.refund_order(db, order_no, req.refund_amount_cents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": f"订单 {order_no} 退款已批准，退款金额 {req.refund_amount_cents / 100:.2f} 元"}


@router.post("/orders/{order_no}/refund-reject", summary="审核拒绝退款")
def reject_refund(
    order_no: str,
    req: RefundRejectBody,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """管理员审核拒绝，恢复订单为已支付状态"""
    try:
        billing_service.reject_refund(db, order_no, req.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": f"订单 {order_no} 退款申请已拒绝"}


@router.post("/orders/{order_no}/refund", summary="直接退款（废弃，请使用 refund-approve）")
def refund_order(
    order_no: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """已废弃：请使用 /orders/{order_no}/refund-approve"""
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 调用支付渠道退款
    refund_no = f"R{order_no}"
    refund_ok = False
    if order.pay_method == "wechat":
        refund_ok = payment_service.refund_wechat(order_no, refund_no, order.amount_cents)
    elif order.pay_method == "alipay":
        refund_ok = payment_service.refund_alipay(order_no, refund_no, order.amount_cents)

    if not refund_ok:
        raise HTTPException(status_code=500, detail="支付渠道退款失败，请手动处理")

    try:
        billing_service.refund_order(db, order_no)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": f"订单 {order_no} 退款成功"}
