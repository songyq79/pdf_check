"""
计费服务 — 配额检查、扣减、订单管理、邀请裂变
"""

import secrets
import time
from datetime import datetime, timedelta, timezone

def _now_cst():
    """返回北京时间（UTC+8）"""
    return datetime.now(timezone(timedelta(hours=8))).replace(tzinfo=None)
from typing import Optional

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.billing import (
    SystemConfig, Subscription, QuotaBalance, Order, UsageRecord, InviteCode,
)
from app.models.pricing import DEFAULT_PRICING, FREE_TRIAL_COUNT, REFERRAL_REWARD_COUNT


# ── 系统配置读取 ──────────────────────────────────────────────


def get_config(db: Session, key: str, default: str = "") -> str:
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return row.value if row else default


def set_config(db: Session, key: str, value: str):
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if row:
        row.value = value
        row.updated_at = _now_cst()
    else:
        db.add(SystemConfig(key=key, value=value))
    db.commit()


def is_billing_enabled(db: Session) -> bool:
    return get_config(db, "billing_enabled", "false").lower() == "true"


def get_all_config(db: Session) -> dict:
    rows = db.query(SystemConfig).all()
    return {r.key: r.value for r in rows}


# ── 免费试用 ──────────────────────────────────────────────────


def ensure_free_trial(db: Session, user_id: int):
    """注册时发放免费额度（仅执行一次）"""
    existing = db.query(QuotaBalance).filter(
        QuotaBalance.user_id == user_id,
        QuotaBalance.source == "free",
    ).first()
    if existing:
        return
    count = int(get_config(db, "free_trial_count", str(FREE_TRIAL_COUNT)))
    db.add(QuotaBalance(user_id=user_id, source="free", remaining=count))
    db.commit()
    logger.info(f"用户 {user_id} 获得 {count} 次免费试用")


# ── 配额检查 ──────────────────────────────────────────────────


def check_quota(db: Session, user_id: int) -> dict:
    """
    按优先级检查用户配额。返回:
    {"allowed": bool, "source": str|None, "detail": str}
    优先级: 订阅(有额度) > 购买 > 邀请 > 免费
    """
    # 管理员无限使用，不参与扣次数
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.is_admin:
        return {"allowed": True, "source": "admin", "detail": "管理员无限额度"}

    # 懒加载免费试用
    _lazy_ensure_free_trial(db, user_id)

    now = _now_cst()

    # 1. 检查活跃订阅 + 订阅额度
    sub = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.is_active == True,
        Subscription.expires_at > now,
    ).first()
    if sub:
        sub_balance = db.query(QuotaBalance).filter(
            QuotaBalance.user_id == user_id,
            QuotaBalance.source == "subscription",
            QuotaBalance.remaining > 0,
        ).first()
        if sub_balance:
            return {"allowed": True, "source": "subscription", "detail": f"包月剩余 {sub_balance.remaining} 次"}
        # 订阅有效但额度用完，继续检查其他来源

    # 2-4. 按优先级检查额度余额
    for source, label in [("purchase", "购买次数"), ("referral", "邀请奖励"), ("free", "免费试用")]:
        balance = db.query(QuotaBalance).filter(
            QuotaBalance.user_id == user_id,
            QuotaBalance.source == source,
            QuotaBalance.remaining > 0,
        ).first()
        if balance:
            return {"allowed": True, "source": source, "detail": f"{label}剩余 {balance.remaining} 次"}

    if sub:
        return {"allowed": False, "source": None, "detail": "本月包月额度已用完，请购买按次套餐"}
    return {"allowed": False, "source": None, "detail": "额度不足，请购买套餐"}


def _lazy_ensure_free_trial(db: Session, user_id: int):
    """首次检查配额时自动发放免费试用"""
    has_any = db.query(QuotaBalance).filter(
        QuotaBalance.user_id == user_id,
    ).first()
    if not has_any:
        ensure_free_trial(db, user_id)


# ── 配额扣减 ──────────────────────────────────────────────────


def consume_quota(db: Session, user_id: int, action: str, task_id: str = None, cost: int = 1) -> UsageRecord:
    """
    扣减配额并记录使用日志。
    cost: 本次消耗次数（默认 1；外文查重=2，选题评估=3，文献综述=5 等差异化扣费）。
    使用原子 UPDATE 防并发超卖。
    """
    quota_info = check_quota(db, user_id)
    if not quota_info["allowed"]:
        raise ValueError("额度不足")

    source = quota_info["source"]

    # 管理员不扣次数，只记录使用日志
    if source == "admin":
        record = UsageRecord(
            user_id=user_id, action=action,
            consumed_from="admin", task_id=task_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    # 原子扣减额度（包月也扣次数）；cost 次一次性扣，remaining 不足则 rowcount=0
    result = db.execute(
        text(
            "UPDATE quota_balances SET remaining = remaining - :cost "
            "WHERE user_id = :uid AND source = :src AND remaining >= :cost"
        ),
        {"uid": user_id, "src": source, "cost": cost},
    )
    if result.rowcount == 0:
        raise ValueError("额度扣减失败（并发冲突）")

    record = UsageRecord(
        user_id=user_id, action=action,
        consumed_from=source, task_id=task_id,
    )
    db.add(record)
    db.commit()
    logger.info(f"用户 {user_id} 消耗 {source} 额度，动作: {action}")
    return record


# ── 订单 ──────────────────────────────────────────────────────


def _gen_order_no() -> str:
    ts = int(time.time() * 1000)
    rand = secrets.token_hex(4)
    return f"{ts}{rand}"


def create_order(
    db: Session,
    user_id: int,
    product_type: str,
    pay_method: str,
    quantity: int = 1,
) -> Order:
    """创建待支付订单"""
    pricing = _get_pricing(db)

    if product_type == "per_use":
        amount = pricing["per_use"] * quantity
    elif product_type == "monthly":
        amount = pricing["monthly"]
        quantity = 1
    else:
        raise ValueError(f"不支持的产品类型: {product_type}")

    if pay_method not in ("wechat", "alipay"):
        raise ValueError(f"不支持的支付方式: {pay_method}")

    order = Order(
        order_no=_gen_order_no(),
        user_id=user_id,
        product_type=product_type,
        quantity=quantity,
        amount_cents=amount,
        status="pending",
        pay_method=pay_method,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    logger.info(f"创建订单 {order.order_no}: {product_type} x{quantity} = {amount}分")
    return order


def _get_pricing(db: Session) -> dict:
    """从 SystemConfig 读取当前价格，回退到默认值"""
    return {
        "per_use": int(get_config(db, "price_per_use", str(DEFAULT_PRICING["per_use"]))),
        "monthly": int(get_config(db, "price_monthly", str(DEFAULT_PRICING["monthly"]))),
    }


def confirm_payment(db: Session, order_no: str) -> Order:
    """支付回调确认，发放权益"""
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise ValueError(f"订单不存在: {order_no}")
    if order.status != "pending":
        raise ValueError(f"订单状态异常: {order.status}")

    order.status = "paid"
    order.paid_at = _now_cst()

    if order.product_type == "monthly":
        activate_subscription(db, order)
    elif order.product_type == "per_use":
        add_purchase_quota(db, order.user_id, order.quantity)

    db.commit()
    logger.info(f"订单 {order_no} 支付确认，已发放权益")
    return order


def _get_monthly_limit(db: Session) -> int:
    """获取包月每月限次，默认 20"""
    return int(get_config(db, "monthly_limit", str(DEFAULT_PRICING.get("monthly_limit", 20))))


def activate_subscription(db: Session, order: Order):
    """创建或续期包月订阅，并发放每月额度"""
    now = _now_cst()
    monthly_limit = _get_monthly_limit(db)

    # 查看是否有活跃订阅，从到期日延长
    active_sub = db.query(Subscription).filter(
        Subscription.user_id == order.user_id,
        Subscription.is_active == True,
        Subscription.expires_at > now,
    ).first()

    if active_sub:
        start = active_sub.expires_at
        active_sub.expires_at = start + timedelta(days=30)
        db.commit()
        logger.info(f"用户 {order.user_id} 订阅续期至 {active_sub.expires_at}")
    else:
        sub = Subscription(
            user_id=order.user_id,
            started_at=now,
            expires_at=now + timedelta(days=30),
            is_active=True,
            order_id=order.id,
        )
        db.add(sub)
        db.commit()
        logger.info(f"用户 {order.user_id} 新建包月订阅")

    # 发放包月额度（重置为 monthly_limit，不累加旧余额）
    sub_balance = db.query(QuotaBalance).filter(
        QuotaBalance.user_id == order.user_id,
        QuotaBalance.source == "subscription",
    ).first()
    if sub_balance:
        sub_balance.remaining = monthly_limit
    else:
        db.add(QuotaBalance(user_id=order.user_id, source="subscription", remaining=monthly_limit))
    db.commit()
    logger.info(f"用户 {order.user_id} 获得包月额度 {monthly_limit} 次")


def add_purchase_quota(db: Session, user_id: int, count: int):
    """增加购买额度"""
    balance = db.query(QuotaBalance).filter(
        QuotaBalance.user_id == user_id,
        QuotaBalance.source == "purchase",
    ).first()
    if balance:
        balance.remaining += count
    else:
        db.add(QuotaBalance(user_id=user_id, source="purchase", remaining=count))
    db.commit()


def apply_refund(db: Session, order_no: str, user_id: int, reason: str) -> Order:
    """用户申请退款"""
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise ValueError(f"订单不存在: {order_no}")
    if order.user_id != user_id:
        raise ValueError(f"无权限操作该订单")
    if order.status != "paid":
        raise ValueError(f"只有已支付订单可申请退款，当前状态: {order.status}")
    if order.refund_applied_at:
        raise ValueError(f"该订单已申请过退款，请勿重复申请")

    order.status = "refund_pending"
    order.refund_reason = reason
    order.refund_applied_at = _now_cst()
    db.commit()
    logger.info(f"用户 {user_id} 对订单 {order_no} 申请了退款，原因: {reason}")
    return order


def reject_refund(db: Session, order_no: str, reason: str) -> Order:
    """管理员拒绝退款，恢复订单为已支付状态"""
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise ValueError(f"订单不存在: {order_no}")
    if order.status != "refund_pending":
        raise ValueError(f"只能拒绝待审核退款订单，当前状态: {order.status}")

    order.status = "paid"
    order.refund_reject_reason = reason
    db.commit()
    logger.info(f"订单 {order_no} 退款申请被拒绝，原因: {reason}")
    return order


def refund_order(db: Session, order_no: str) -> Order:
    """批准退款并标记为已退款（实际退款由 payment_service 处理），同时回收剩余权益"""
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise ValueError(f"订单不存在: {order_no}")
    if order.status != "refund_pending":
        raise ValueError(f"只有待审核退款订单可批准，当前状态: {order.status}")

    order.status = "refunded"
    order.refunded_at = _now_cst()

    # 回收该订单带来的剩余权益
    if order.product_type == "per_use":
        # 按次购买：从 purchase 余额中扣除已购数量（不低于0）
        balance = db.query(QuotaBalance).filter(
            QuotaBalance.user_id == order.user_id,
            QuotaBalance.source == "purchase",
        ).first()
        if balance:
            balance.remaining = max(0, balance.remaining - order.quantity)
            logger.info(f"退款回收用户 {order.user_id} 购买额度 {order.quantity} 次，剩余 {balance.remaining} 次")

    elif order.product_type == "monthly":
        # 包月：停用订阅并清空包月额度
        now = _now_cst()
        active_sub = db.query(Subscription).filter(
            Subscription.user_id == order.user_id,
            Subscription.is_active == True,
            Subscription.expires_at > now,
        ).first()
        if active_sub:
            active_sub.is_active = False
            active_sub.expires_at = now
            logger.info(f"退款停用用户 {order.user_id} 包月订阅")

        sub_balance = db.query(QuotaBalance).filter(
            QuotaBalance.user_id == order.user_id,
            QuotaBalance.source == "subscription",
        ).first()
        if sub_balance:
            sub_balance.remaining = 0
            logger.info(f"退款清零用户 {order.user_id} 包月额度")

    db.commit()
    logger.info(f"订单 {order_no} 已批准退款，权益已回收")
    return order


# ── 管理员赠送额度 ────────────────────────────────────────────


def grant_quota(db: Session, user_id: int, count: int, source: str = "purchase"):
    """管理员手动赠送额度，source 可为 purchase 或 free"""
    if source not in ("purchase", "free"):
        source = "purchase"
    balance = db.query(QuotaBalance).filter(
        QuotaBalance.user_id == user_id,
        QuotaBalance.source == source,
    ).first()
    if balance:
        balance.remaining += count
    else:
        db.add(QuotaBalance(user_id=user_id, source=source, remaining=count))
    db.commit()
    logger.info(f"管理员赠送用户 {user_id} {count} 次额度（来源: {source}）")


# ── 邀请裂变 ──────────────────────────────────────────────────


def generate_invite_code(db: Session, user_id: int) -> str:
    """生成邀请码"""
    code = secrets.token_urlsafe(8)[:8].upper()
    # 确保唯一
    while db.query(InviteCode).filter(InviteCode.code == code).first():
        code = secrets.token_urlsafe(8)[:8].upper()
    db.add(InviteCode(code=code, owner_id=user_id))
    db.commit()
    logger.info(f"用户 {user_id} 生成邀请码: {code}")
    return code


def apply_invite_code(db: Session, invite_code: str, new_user_id: int) -> bool:
    """
    新用户使用邀请码注册，给邀请人送额度。
    返回 True 表示成功，False 表示邀请码无效。
    """
    record = db.query(InviteCode).filter(
        InviteCode.code == invite_code,
        InviteCode.used_by_id == None,
    ).first()
    if not record:
        return False

    # 不允许使用自己生成的邀请码
    if record.owner_id == new_user_id:
        logger.warning(f"用户 {new_user_id} 尝试使用自己的邀请码 {invite_code}，已拒绝")
        return False

    record.used_by_id = new_user_id
    record.used_at = _now_cst()

    # 给邀请人送额度
    reward_count = int(get_config(db, "referral_reward_count", str(REFERRAL_REWARD_COUNT)))
    owner_balance = db.query(QuotaBalance).filter(
        QuotaBalance.user_id == record.owner_id,
        QuotaBalance.source == "referral",
    ).first()
    if owner_balance:
        owner_balance.remaining += reward_count
    else:
        db.add(QuotaBalance(user_id=record.owner_id, source="referral", remaining=reward_count))

    db.commit()
    logger.info(f"邀请码 {invite_code} 被用户 {new_user_id} 使用，邀请人 {record.owner_id} 获得 {reward_count} 次额度")
    return True


# ── 用户权益摘要 ──────────────────────────────────────────────


def get_user_quota(db: Session, user_id: int) -> dict:
    """返回用户当前权益概览"""
    now = _now_cst()

    # 订阅
    sub = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.is_active == True,
        Subscription.expires_at > now,
    ).first()

    subscription_info = None
    if sub:
        days_remaining = (sub.expires_at - now).days
        sub_balance = db.query(QuotaBalance).filter(
            QuotaBalance.user_id == user_id,
            QuotaBalance.source == "subscription",
        ).first()
        subscription_info = {
            "expires_at": sub.expires_at.isoformat(),
            "days_remaining": days_remaining,
            "monthly_remaining": sub_balance.remaining if sub_balance else 0,
            "monthly_limit": _get_monthly_limit(db),
        }

    # 额度
    balances = db.query(QuotaBalance).filter(QuotaBalance.user_id == user_id).all()
    credits = {}
    total = 0
    for b in balances:
        credits[b.source] = b.remaining
        total += b.remaining

    # 是否有权限使用
    has_access = sub is not None or total > 0

    return {
        "subscription": subscription_info,
        "credits": credits,
        "total_credits": total,
        "has_access": has_access,
    }
