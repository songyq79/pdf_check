"""
用户模型 - SQLite + SQLAlchemy
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path

from app.config import settings

_url = settings.DATABASE_URL

if _url.startswith("sqlite"):
    # 本地开发：固定用绝对路径，不依赖 CWD
    _db_file = Path(__file__).parent.parent.parent / "storage" / "app.db"
    _db_file.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{_db_file}",
        connect_args={"check_same_thread": False},
    )
else:
    # 云部署：MySQL（pool_pre_ping 防止连接超时后报错）
    engine = create_engine(
        _url,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)   # 管理员审批
    is_admin = Column(Boolean, default=False)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    wechat_openid = Column(String(100), unique=True, index=True, nullable=True)
    alipay_uid = Column(String(100), unique=True, index=True, nullable=True)
    nickname = Column(String(50), nullable=True)
    avatar = Column(String(500), nullable=True)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """创建表，并确保存在默认管理员账号和系统配置"""
    import app.models.billing      # noqa: F401 — 确保计费表被创建
    import app.models.local_paper  # noqa: F401 — 确保本地论文表被创建
    import app.models.phase1       # noqa: F401 — Phase 1 选题评估/文献综述/期刊库

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 默认管理员
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            import bcrypt as _bcrypt
            hashed = _bcrypt.hashpw(b"admin123", _bcrypt.gensalt()).decode()
            db.add(User(
                username="admin",
                hashed_password=hashed,
                is_active=True,
                is_approved=True,
                is_admin=True,
            ))
            db.commit()
        else:
            # 每次启动强制用当前 bcrypt 重新生成 admin 密码，避免版本不兼容
            import bcrypt as _bcrypt
            admin.hashed_password = _bcrypt.hashpw(b"admin123", _bcrypt.gensalt()).decode()
            db.commit()

        # 增量迁移：orders 表新增 refund_amount_cents 列（旧库升级）
        try:
            db.execute(text("ALTER TABLE orders ADD COLUMN refund_amount_cents INTEGER"))
            db.commit()
        except Exception:
            db.rollback()  # 列已存在，忽略

        # 初始化默认系统配置
        from app.models.billing import SystemConfig
        defaults = {
            "billing_enabled": "false",
            "price_per_use": "300",
            "price_monthly": "9900",
            "free_trial_count": "1",
            "referral_reward_count": "3",
        }
        for key, value in defaults.items():
            existing = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if not existing:
                db.add(SystemConfig(key=key, value=value))
        db.commit()
    finally:
        db.close()


def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
