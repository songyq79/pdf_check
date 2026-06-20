"""
认证接口：登录、注册、获取当前用户、用户管理（管理员）
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User, get_db

router = APIRouter()

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── Pydantic 模型 ─────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    invite_code: Optional[str] = None


class SmsCodeRequest(BaseModel):
    phone: str


class SmsLoginRequest(BaseModel):
    phone: str
    code: str
    invite_code: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[str]
    is_admin: bool
    is_approved: bool
    is_active: bool
    phone: Optional[str] = None
    wechat_openid: Optional[str] = None
    nickname: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    invite_warning: Optional[str] = None


# ── 工具函数 ──────────────────────────────────────────────

def _hash(password: str) -> str:
    import bcrypt as _bcrypt
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def _verify(plain: str, hashed: str) -> bool:
    import bcrypt as _bcrypt
    try:
        return _bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def _create_token(data: dict, expires_minutes: int = None) -> str:
    exp = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=exp)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise credentials_exc
    return user


def require_approved(user: User = Depends(get_current_user)) -> User:
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="账号尚未审批，请联系管理员")
    return user


def require_admin(user: User = Depends(require_approved)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


# ── 接口 ──────────────────────────────────────────────────

@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    from loguru import logger
    user = db.query(User).filter(User.username == form.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    try:
        pwd_ok = _verify(form.password, user.hashed_password)
        logger.info(f"[auth] login user={form.username} pwd_ok={pwd_ok}")
    except Exception as e:
        logger.error(f"[auth] 密码验证异常 username={form.username}: {e}")
        raise HTTPException(status_code=500, detail="密码验证失败，请联系管理员")
    if not pwd_ok:
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="账号已被禁用")
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="账号尚未审批，请等待管理员审核")
    token = _create_token({"sub": user.username})
    return TokenOut(access_token=token)


@router.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if len(req.username) < 4 or len(req.username) > 20:
        raise HTTPException(status_code=400, detail="用户名长度需在4-20位之间")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if req.email and db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    user = User(
        username=req.username,
        email=req.email or None,
        hashed_password=_hash(req.password),
        is_approved=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 发放免费试用 + 处理邀请码
    _post_register(db, user.id, req.invite_code)

    return {"message": "注册申请已提交，请等待管理员审批"}


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# ── 管理员接口 ────────────────────────────────────────────

class CreateUserRequest(BaseModel):
    phone: str
    is_admin: bool = False


@router.post("/admin/users", response_model=UserOut, status_code=201)
def create_user(req: CreateUserRequest, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    import re, secrets
    if not re.match(r"^1[3-9]\d{9}$", req.phone):
        raise HTTPException(status_code=400, detail="手机号格式错误")
    if db.query(User).filter(User.phone == req.phone).first():
        raise HTTPException(status_code=400, detail="该手机号已注册")
    username = f"phone_{req.phone[-4:]}_{secrets.token_hex(3)}"
    user = User(
        username=username,
        phone=req.phone,
        hashed_password=_hash(secrets.token_hex(16)),
        is_approved=True,
        is_active=True,
        is_admin=req.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _post_register(db, user.id, None)
    return user


@router.get("/admin/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/admin/users/{user_id}/approve")
def approve_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_approved = True
    db.commit()
    return {"message": f"用户 {user.username} 已审批通过"}


@router.post("/admin/users/{user_id}/reject")
def reject_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = False
    db.commit()
    return {"message": f"用户 {user.username} 已拒绝"}


@router.post("/admin/users/{user_id}/restore")
def restore_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """恢复已拒绝的用户，使其可以再次使用系统"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_active = True
    db.commit()
    return {"message": f"用户 {user.username} 已恢复，可以重新申请审批"}


# ── 注册后处理（免费试用 + 邀请码）────────────────────────────


def _post_register(db: Session, user_id: int, invite_code: Optional[str] = None) -> Optional[str]:
    """注册后处理，返回邀请码警告信息（如有）"""
    from app.services.billing_service import ensure_free_trial, apply_invite_code
    from app.models.billing import InviteCode as InviteCodeModel
    ensure_free_trial(db, user_id)
    if invite_code:
        # 先检查是否是自己的邀请码，给出精确提示
        own_code = db.query(InviteCodeModel).filter(
            InviteCodeModel.code == invite_code,
            InviteCodeModel.owner_id == user_id,
        ).first()
        if own_code:
            return "邀请码无效，无法邀请自己"
        success = apply_invite_code(db, invite_code, user_id)
        if not success:
            return "邀请码无效或已被使用"
    return None


# ── 手机号登录/注册 ──────────────────────────────────────────


@router.post("/sms/send", summary="发送短信验证码")
def send_sms_code(req: SmsCodeRequest):
    import re
    if not re.match(r"^1[3-9]\d{9}$", req.phone):
        raise HTTPException(status_code=400, detail="手机号格式错误")
    from app.services.sms_service import send_code
    result = send_code(req.phone)
    if not result["success"]:
        raise HTTPException(status_code=429, detail=result["message"])
    return {"message": result["message"]}


@router.post("/sms/login", response_model=TokenOut, summary="手机号验证码登录/注册")
def sms_login(req: SmsLoginRequest, db: Session = Depends(get_db)):
    import re
    if not re.match(r"^1[3-9]\d{9}$", req.phone):
        raise HTTPException(status_code=400, detail="手机号格式错误")

    from app.services.sms_service import verify_code
    if not verify_code(req.phone, req.code):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    # 查找已有用户
    user = db.query(User).filter(User.phone == req.phone).first()
    if not user:
        # 自动注册
        import secrets
        user = User(
            username=f"phone_{req.phone[-4:]}_{secrets.token_hex(3)}",
            phone=req.phone,
            hashed_password=_hash(secrets.token_hex(16)),
            is_approved=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        invite_warning = _post_register(db, user.id, req.invite_code)

        if not user.is_active:
            raise HTTPException(status_code=400, detail="账号已被禁用")

        token = _create_token({"sub": user.username})
        return {"access_token": token, "token_type": "bearer", "invite_warning": invite_warning}

    if not user.is_active:
        raise HTTPException(status_code=400, detail="账号已被禁用")

    invite_warning = None
    if req.invite_code:
        from app.models.billing import InviteCode as InviteCodeModel
        own_code = db.query(InviteCodeModel).filter(
            InviteCodeModel.code == req.invite_code,
            InviteCodeModel.owner_id == user.id,
        ).first()
        if own_code:
            invite_warning = "邀请码无效，无法邀请自己"
        else:
            invite_warning = "邀请码仅在首次注册时有效，本次登录未应用"

    token = _create_token({"sub": user.username})
    return TokenOut(access_token=token, invite_warning=invite_warning)


# ── 微信扫码登录 ──────────────────────────────────────────────


@router.get("/wechat/url", summary="获取微信登录二维码URL")
def wechat_login_url():
    from app.services.oauth_service import get_wechat_login_url
    return {"url": get_wechat_login_url()}


@router.get("/wechat/callback", summary="微信登录回调")
def wechat_callback(code: str, state: str = "login", db: Session = Depends(get_db)):
    from app.services.oauth_service import wechat_code_to_user
    wx_user = wechat_code_to_user(code)
    if not wx_user:
        raise HTTPException(status_code=400, detail="微信授权失败")

    openid = wx_user["openid"]
    user = db.query(User).filter(User.wechat_openid == openid).first()
    if not user:
        import secrets
        user = User(
            username=f"wx_{secrets.token_hex(4)}",
            wechat_openid=openid,
            nickname=wx_user.get("nickname", ""),
            avatar=wx_user.get("avatar", ""),
            hashed_password=_hash(secrets.token_hex(16)),
            is_approved=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        # 从 state 中提取邀请码（格式: login_INVITECODE）
        invite_code = state.split("_", 1)[1] if "_" in state else None
        _post_register(db, user.id, invite_code)

    if not user.is_active:
        raise HTTPException(status_code=400, detail="账号已被禁用")

    token = _create_token({"sub": user.username})
    return TokenOut(access_token=token)


# ── 支付宝登录 ────────────────────────────────────────────────


@router.get("/alipay/url", summary="获取支付宝登录URL")
def alipay_login_url():
    from app.services.oauth_service import get_alipay_login_url
    return {"url": get_alipay_login_url()}


@router.get("/alipay/callback", summary="支付宝登录回调")
def alipay_callback(auth_code: str, state: str = "login", db: Session = Depends(get_db)):
    from app.services.oauth_service import alipay_code_to_user
    ali_user = alipay_code_to_user(auth_code)
    if not ali_user:
        raise HTTPException(status_code=400, detail="支付宝授权失败")

    uid = ali_user["uid"]
    user = db.query(User).filter(User.alipay_uid == uid).first()
    if not user:
        import secrets
        user = User(
            username=f"ali_{secrets.token_hex(4)}",
            alipay_uid=uid,
            nickname=ali_user.get("nickname", ""),
            avatar=ali_user.get("avatar", ""),
            hashed_password=_hash(secrets.token_hex(16)),
            is_approved=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        invite_code = state.split("_", 1)[1] if "_" in state else None
        _post_register(db, user.id, invite_code)

    if not user.is_active:
        raise HTTPException(status_code=400, detail="账号已被禁用")

    token = _create_token({"sub": user.username})
    return TokenOut(access_token=token)
