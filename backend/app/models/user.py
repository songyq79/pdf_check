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
    # 本地开发：把 DATABASE_URL 中的相对路径解析成绝对路径，不依赖 CWD，
    # 但保留 DATABASE_URL 里配置的实际文件名（此前曾被写死成 app.db，
    # 导致 DATABASE_URL=sqlite:///./storage/xxx.db 这类自定义文件名被忽略）。
    _raw_path = _url.split("sqlite:///", 1)[-1] if "sqlite:///" in _url else "storage/app.db"
    _candidate = Path(_raw_path)
    _db_file = _candidate if _candidate.is_absolute() else (Path(__file__).parent.parent.parent / _candidate)
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
    # Phase 2 多租户：个人用户 institution_id 为空、user_type=individual（不影响 C端）
    institution_id = Column(Integer, index=True, nullable=True)
    user_type = Column(String(30), default="individual")  # individual/institution_student/institution_admin/super_admin
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """创建表，并确保存在默认管理员账号和系统配置"""
    import app.models.billing      # noqa: F401 — 确保计费表被创建
    import app.models.local_paper  # noqa: F401 — 确保本地论文表被创建
    import app.models.phase1       # noqa: F401 — Phase 1 选题评估/文献综述/期刊库
    import app.models.institution  # noqa: F401 — Phase 2 机构/机构学生表

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 默认管理员：仅在首次(账号不存在时)创建，之后绝不覆盖已有密码。
        # 初始密码取自 settings.ADMIN_INITIAL_PASSWORD（生产环境务必在 .env 中设置）。
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            import bcrypt as _bcrypt
            _pw = (settings.ADMIN_INITIAL_PASSWORD or "admin123").encode()
            hashed = _bcrypt.hashpw(_pw, _bcrypt.gensalt()).decode()
            db.add(User(
                username="admin",
                hashed_password=hashed,
                is_active=True,
                is_approved=True,
                is_admin=True,
            ))
            db.commit()

        # 增量迁移：orders 表新增 refund_amount_cents 列（旧库升级）
        try:
            db.execute(text("ALTER TABLE orders ADD COLUMN refund_amount_cents INTEGER"))
            db.commit()
        except Exception:
            db.rollback()  # 列已存在，忽略

        # 增量迁移：users 表新增 Phase 2 多租户列（旧库升级，幂等）
        for _ddl in (
            "ALTER TABLE users ADD COLUMN institution_id INTEGER",
            "ALTER TABLE users ADD COLUMN user_type VARCHAR(30) DEFAULT 'individual'",
        ):
            try:
                db.execute(text(_ddl))
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
