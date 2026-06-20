"""
配额检查依赖 — 用于保护需要收费的接口
"""

from dataclasses import dataclass

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.models.user import User, get_db
from app.services.billing_service import is_billing_enabled, check_quota


@dataclass
class QuotaContext:
    user: User
    billing_on: bool
    quota_info: dict   # check_quota 返回值
    action: str


def require_quota(action: str):
    """
    返回 FastAPI 依赖。
    收费关闭时直接放行；开启时检查配额，无配额返回 402。
    """
    def dependency(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> QuotaContext:
        if not is_billing_enabled(db):
            return QuotaContext(
                user=user,
                billing_on=False,
                quota_info={"allowed": True, "source": "billing_off", "detail": "收费未开启"},
                action=action,
            )

        quota_info = check_quota(db, user.id)
        if not quota_info["allowed"]:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "NO_QUOTA",
                    "message": "额度不足，请购买套餐或次数包",
                    "pricing_url": "/api/v1/billing/pricing",
                },
            )
        return QuotaContext(
            user=user,
            billing_on=True,
            quota_info=quota_info,
            action=action,
        )
    return dependency
