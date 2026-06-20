"""
计费系统集成测试
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.billing import (
    Subscription, QuotaBalance, Order, UsageRecord, InviteCode, SystemConfig,
)
from app.services import billing_service
from app.models.pricing import FREE_TRIAL_COUNT, REFERRAL_REWARD_COUNT


class TestBillingService:
    """计费服务单元测试"""

    def test_ensure_free_trial(self, db: Session, test_user: User):
        """测试免费试用自动发放"""
        billing_service.ensure_free_trial(db, test_user.id)

        balance = db.query(QuotaBalance).filter(
            QuotaBalance.user_id == test_user.id,
            QuotaBalance.source == "free",
        ).first()

        assert balance is not None
        assert balance.remaining == FREE_TRIAL_COUNT

    def test_check_quota_with_free_trial(self, db: Session, test_user: User):
        """测试配额检查：有免费试用"""
        billing_service.ensure_free_trial(db, test_user.id)

        result = billing_service.check_quota(db, test_user.id)

        assert result["allowed"] is True
        assert result["source"] == "free"

    def test_check_quota_no_quota(self, db: Session, test_user: User):
        """测试配额检查：无配额时自动发放免费试用"""
        # check_quota() 使用懒加载机制，会自动发放免费试用
        result = billing_service.check_quota(db, test_user.id)

        assert result["allowed"] is True
        assert result["source"] == "free"

    def test_consume_quota(self, db: Session, test_user: User):
        """测试配额扣减"""
        billing_service.ensure_free_trial(db, test_user.id)

        record = billing_service.consume_quota(db, test_user.id, "evaluation", "task-123")

        assert record is not None
        assert record.user_id == test_user.id
        assert record.action == "evaluation"
        assert record.consumed_from == "free"

        # 验证配额已扣减
        balance = db.query(QuotaBalance).filter(
            QuotaBalance.user_id == test_user.id,
            QuotaBalance.source == "free",
        ).first()
        assert balance.remaining == 0

    def test_consume_quota_no_quota(self, db: Session, test_user: User):
        """测试扣减时无配额（但会自动发放免费试用，所以会消耗免费配额）"""
        # 首次调用时，check_quota会自动发放免费试用，所以实际上会扣减免费配额
        record = billing_service.consume_quota(db, test_user.id, "evaluation")
        assert record is not None
        assert record.consumed_from == "free"

        # 再次调用应该抛出异常（没有配额了）
        with pytest.raises(ValueError, match="额度不足"):
            billing_service.consume_quota(db, test_user.id, "evaluation")

    def test_create_order(self, db: Session, test_user: User):
        """测试创建订单"""
        order = billing_service.create_order(
            db, test_user.id, "per_use", "wechat", quantity=5
        )

        assert order.user_id == test_user.id
        assert order.product_type == "per_use"
        assert order.quantity == 5
        assert order.status == "pending"
        assert order.pay_method == "wechat"
        assert order.amount_cents == 300 * 5  # 3元/次 = 300分/次

    def test_activate_subscription_new(self, db: Session, test_user: User):
        """测试激活新订阅"""
        order = billing_service.create_order(db, test_user.id, "monthly", "alipay")
        order.status = "paid"
        order.paid_at = datetime.utcnow()
        db.commit()

        billing_service.activate_subscription(db, order)

        sub = db.query(Subscription).filter(
            Subscription.user_id == test_user.id,
        ).first()

        assert sub is not None
        assert sub.is_active is True
        assert sub.expires_at > datetime.utcnow()

    def test_activate_subscription_extend(self, db: Session, test_user: User):
        """测试订阅续期（叠加）"""
        # 创建第一个订阅
        order1 = billing_service.create_order(db, test_user.id, "monthly", "wechat")
        order1.status = "paid"
        db.commit()
        billing_service.activate_subscription(db, order1)

        sub = db.query(Subscription).filter(
            Subscription.user_id == test_user.id,
        ).first()
        first_expiry = sub.expires_at

        # 创建第二个订阅（续期）
        order2 = billing_service.create_order(db, test_user.id, "monthly", "wechat")
        order2.status = "paid"
        db.commit()
        billing_service.activate_subscription(db, order2)

        # 验证续期后的到期时间
        db.refresh(sub)
        assert sub.expires_at > first_expiry

    def test_add_purchase_quota(self, db: Session, test_user: User):
        """测试添加购买配额"""
        billing_service.add_purchase_quota(db, test_user.id, 10)

        balance = db.query(QuotaBalance).filter(
            QuotaBalance.user_id == test_user.id,
            QuotaBalance.source == "purchase",
        ).first()

        assert balance is not None
        assert balance.remaining == 10

    def test_generate_and_apply_invite_code(self, db: Session, user1: User, user2: User):
        """测试邀请码生成和使用"""
        # 用户1生成邀请码
        code = billing_service.generate_invite_code(db, user1.id)
        assert code is not None
        assert len(code) == 8

        # 用户2使用邀请码
        result = billing_service.apply_invite_code(db, code, user2.id)
        assert result is True

        # 验证用户1获得邀请奖励
        balance = db.query(QuotaBalance).filter(
            QuotaBalance.user_id == user1.id,
            QuotaBalance.source == "referral",
        ).first()
        assert balance is not None
        assert balance.remaining == REFERRAL_REWARD_COUNT

    def test_grant_quota(self, db: Session, test_user: User):
        """测试管理员赠送额度"""
        billing_service.grant_quota(db, test_user.id, 5)

        balance = db.query(QuotaBalance).filter(
            QuotaBalance.user_id == test_user.id,
            QuotaBalance.source == "purchase",
        ).first()

        assert balance.remaining == 5

    def test_get_user_quota(self, db: Session, test_user: User):
        """测试获取用户权益摘要"""
        billing_service.ensure_free_trial(db, test_user.id)
        billing_service.add_purchase_quota(db, test_user.id, 3)

        quota = billing_service.get_user_quota(db, test_user.id)

        assert quota["total_credits"] == FREE_TRIAL_COUNT + 3
        assert quota["has_access"] is True
        assert quota["credits"]["free"] == FREE_TRIAL_COUNT
        assert quota["credits"]["purchase"] == 3

    def test_config_management(self, db: Session):
        """测试系统配置管理"""
        billing_service.set_config(db, "test_key", "test_value")

        value = billing_service.get_config(db, "test_key")
        assert value == "test_value"

        all_config = billing_service.get_all_config(db)
        assert "test_key" in all_config

    def test_is_billing_enabled(self, db: Session):
        """测试收费开关"""
        # 默认关闭
        assert billing_service.is_billing_enabled(db) is False

        # 打开收费
        billing_service.set_config(db, "billing_enabled", "true")
        assert billing_service.is_billing_enabled(db) is True

    def test_check_quota_priority(self, db: Session, test_user: User):
        """测试配额检查优先级：订阅 > 购买 > 邀请 > 免费"""
        # 只有免费试用
        result = billing_service.check_quota(db, test_user.id)
        assert result["source"] == "free"

        # 加入购买配额后，优先级应该是购买 > 免费
        billing_service.add_purchase_quota(db, test_user.id, 1)
        result = billing_service.check_quota(db, test_user.id)
        assert result["source"] == "purchase"

        # 加入邀请奖励后，优先级应该是购买 > 邀请 > 免费
        db.add(QuotaBalance(user_id=test_user.id, source="referral", remaining=1))
        db.commit()
        result = billing_service.check_quota(db, test_user.id)
        assert result["source"] == "purchase"

        # 加入订阅后，优先级最高
        order = billing_service.create_order(db, test_user.id, "monthly", "wechat")
        order.status = "paid"
        db.commit()
        billing_service.activate_subscription(db, order)
        result = billing_service.check_quota(db, test_user.id)
        assert result["source"] == "subscription"


class TestBillingAPI:
    """计费API端点测试"""

    def test_get_pricing(self, client, db: Session):
        """测试获取定价"""
        response = client.get("/api/v1/billing/pricing")

        assert response.status_code == 200
        data = response.json()
        assert "billing_enabled" in data
        assert "per_use_yuan" in data
        assert "monthly_yuan" in data

    def test_get_my_quota_unauthorized(self, client):
        """测试未授权获取配额"""
        response = client.get("/api/v1/billing/quota")
        assert response.status_code == 401

    def test_get_my_quota_authorized(self, client, db: Session, test_user_token: str, test_user: User):
        """测试授权用户获取配额"""
        billing_service.ensure_free_trial(db, test_user.id)

        response = client.get(
            "/api/v1/billing/quota",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "credits" in data
        assert data["total_credits"] == FREE_TRIAL_COUNT

    def test_create_order(self, client, db: Session, test_user_token: str, test_user: User):
        """测试创建订单"""
        response = client.post(
            "/api/v1/billing/orders",
            json={
                "product_type": "per_use",
                "pay_method": "wechat",
                "quantity": 2,
            },
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "order_no" in data
        assert data["product_type"] == "per_use"
        assert data["quantity"] == 2
        assert data["status"] == "pending"

    def test_list_my_orders(self, client, db: Session, test_user_token: str, test_user: User):
        """测试获取我的订单"""
        # 创建一个订单
        billing_service.create_order(db, test_user.id, "per_use", "alipay", 1)

        response = client.get(
            "/api/v1/billing/orders",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_generate_invite_code(self, client, token: str):
        """测试生成邀请码"""
        response = client.post(
            "/api/v1/billing/invite/generate",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert len(data["code"]) == 8

    def test_list_my_invite_codes(self, client, token: str):
        """测试获取我的邀请码列表"""
        # 先生成一个邀请码
        client.post(
            "/api/v1/billing/invite/generate",
            headers={"Authorization": f"Bearer {token}"}
        )

        response = client.get(
            "/api/v1/billing/invite/my-codes",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0


class TestAdminAPI:
    """管理API端点测试"""

    def test_get_settings(self, client, token: str, admin_user: User):
        """测试获取系统设置"""
        response = client.get(
            "/api/v1/admin/settings",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "billing_enabled" in data

    def test_update_settings(self, client, db: Session, token: str, admin_user: User):
        """测试修改系统设置"""
        response = client.put(
            "/api/v1/admin/settings",
            json={"billing_enabled": "true", "price_per_use": "500"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        # 验证修改生效
        enabled = billing_service.is_billing_enabled(db)
        assert enabled is True

    def test_list_users_enhanced(self, client, db: Session, token: str, admin_user: User):
        """测试增强的用户列表"""
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "username" in data[0]
            assert "total_credits" in data[0]

    def test_grant_quota(self, client, db: Session, token: str, admin_user: User, test_user: User):
        """测试赠送额度"""
        response = client.post(
            f"/api/v1/admin/users/{test_user.id}/grant-quota",
            json={"count": 5},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        # 验证额度已增加
        quota = billing_service.get_user_quota(db, test_user.id)
        assert quota["total_credits"] == 5


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def test_user(db: Session):
    """创建测试用户"""
    user = User(
        username="testuser",
        hashed_password="hashed_password",
        is_active=True,
        is_approved=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user1(db: Session):
    """创建测试用户1"""
    user = User(
        username="user1",
        hashed_password="hashed_password",
        is_active=True,
        is_approved=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user2(db: Session):
    """创建测试用户2"""
    user = User(
        username="user2",
        hashed_password="hashed_password",
        is_active=True,
        is_approved=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db: Session):
    """创建管理员用户"""
    user = User(
        username="admin",
        hashed_password="hashed_password",
        is_active=True,
        is_approved=True,
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def token(client, admin_user):
    """获取管理员token"""
    from app.api.v1.auth import _hash
    admin_user.hashed_password = _hash("admin123")

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"},
    )
    return response.json()["access_token"]
