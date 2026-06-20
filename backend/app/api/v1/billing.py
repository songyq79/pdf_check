"""
计费API — 用户端：定价、配额、下单、支付回调、使用记录、邀请码
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.models.user import User, get_db
from app.models.billing import Order, UsageRecord, InviteCode
from app.schemas.billing import (
    OrderCreate, OrderOut, QuotaResponse, PricingResponse,
    InviteCodeOut, UsageRecordOut, RefundRequestBody,
)
from app.services import billing_service
from app.services import payment_service

router = APIRouter()


# ── 定价（公开） ──────────────────────────────────────────────


@router.get("/pricing", response_model=PricingResponse, summary="获取定价信息")
def get_pricing(db: Session = Depends(get_db)):
    enabled = billing_service.is_billing_enabled(db)
    config = billing_service.get_all_config(db)
    per_use = int(config.get("price_per_use", "990"))
    monthly = int(config.get("price_monthly", "6990"))
    monthly_limit = int(config.get("monthly_limit", "20"))
    return PricingResponse(
        billing_enabled=enabled,
        per_use_yuan=f"{per_use / 100:.2f}",
        monthly_yuan=f"{monthly / 100:.2f}",
        monthly_limit=monthly_limit,
        free_trial_count=int(config.get("free_trial_count", "1")),
        referral_reward_count=int(config.get("referral_reward_count", "3")),
    )


# ── 我的配额 ──────────────────────────────────────────────────


@router.get("/quota", response_model=QuotaResponse, summary="查询我的配额")
def get_my_quota(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return billing_service.get_user_quota(db, user.id)


# ── 创建订单 ──────────────────────────────────────────────────


@router.post("/orders", response_model=OrderOut, summary="创建订单并获取支付二维码")
def create_order(
    req: OrderCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        order = billing_service.create_order(
            db, user.id, req.product_type, req.pay_method, req.quantity,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 调用支付接口获取二维码链接
    description = "论文助手-包月套餐" if order.product_type == "monthly" else f"论文助手-{order.quantity}次使用"
    pay_url = None

    if order.pay_method == "wechat":
        pay_url = payment_service.create_wechat_pay(
            order.order_no, order.amount_cents, description,
        )
    elif order.pay_method == "alipay":
        pay_url = payment_service.create_alipay(
            order.order_no, order.amount_cents, description,
        )

    if pay_url:
        order.pay_url = pay_url
        db.commit()
        db.refresh(order)

    return order


# ── 我的订单列表 ──────────────────────────────────────────────


@router.get("/orders", response_model=List[OrderOut], summary="我的订单列表")
def list_my_orders(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Order).filter(
        Order.user_id == user.id,
    ).order_by(Order.created_at.desc()).limit(50).all()


# ── 查询订单状态（前端轮询） ──────────────────────────────────


@router.get("/orders/{order_no}/status", summary="查询订单支付状态")
def get_order_status(
    order_no: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(
        Order.order_no == order_no,
        Order.user_id == user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return {"order_no": order.order_no, "status": order.status}


# ── 申请退款 ──────────────────────────────────────────────────


@router.post("/orders/{order_no}/refund-request", summary="申请退款")
def apply_refund(
    order_no: str,
    req: RefundRequestBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        billing_service.apply_refund(db, order_no, user.id, req.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": f"订单 {order_no} 退款申请已提交，请等待管理员审核"}


# ── 微信支付回调 ──────────────────────────────────────────────


@router.post("/callback/wechat", summary="微信支付回调")
async def wechat_callback(request: Request, db: Session = Depends(get_db)):
    headers = dict(request.headers)
    body = await request.body()

    data = payment_service.verify_wechat_callback(headers, body)
    if not data:
        raise HTTPException(status_code=400, detail="验签失败")

    order_no = data.get("out_trade_no")
    trade_state = data.get("trade_state")

    if trade_state == "SUCCESS" and order_no:
        try:
            billing_service.confirm_payment(db, order_no)
        except ValueError:
            pass  # 重复回调或订单异常，忽略

    return {"code": "SUCCESS", "message": "OK"}


# ── 支付宝回调 ────────────────────────────────────────────────


@router.post("/callback/alipay", summary="支付宝支付回调")
async def alipay_callback(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    params = dict(form)

    if not payment_service.verify_alipay_callback(params):
        raise HTTPException(status_code=400, detail="验签失败")

    trade_status = params.get("trade_status")
    order_no = params.get("out_trade_no")

    if trade_status == "TRADE_SUCCESS" and order_no:
        try:
            billing_service.confirm_payment(db, order_no)
        except ValueError:
            pass

    return "success"


# ── 使用记录 ──────────────────────────────────────────────────


@router.get("/usage", response_model=List[UsageRecordOut], summary="使用记录")
def list_usage(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(UsageRecord).filter(
        UsageRecord.user_id == user.id,
    ).order_by(UsageRecord.created_at.desc()).limit(100).all()


# ── 邀请码 ────────────────────────────────────────────────────


@router.post("/invite/generate", summary="生成邀请码")
def gen_invite_code(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    code = billing_service.generate_invite_code(db, user.id)
    return {"code": code}


@router.get("/invite/my-codes", response_model=List[InviteCodeOut], summary="我的邀请码")
def list_invite_codes(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(InviteCode).filter(
        InviteCode.owner_id == user.id,
    ).order_by(InviteCode.created_at.desc()).all()
