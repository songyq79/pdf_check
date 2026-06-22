"""
机构管理业务逻辑（B端）。
建机构、批量导入学生、学生审批、导师绑定。
学生账号创建即设 institution_id + user_type=institution_student（配额走机构池）。
"""

import secrets
from datetime import datetime
from typing import List, Optional

import bcrypt
from loguru import logger
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.institution import Institution, InstitutionStudent


def _gen_invite_code() -> str:
    return secrets.token_hex(4).upper()  # 8 位


def _hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


# ── 机构 ──────────────────────────────────────────────────────

def create_institution(db: Session, name: str, domain: str = "",
                       subscription_level: str = "small",
                       quota_total: int = 0,
                       admin_user_id: Optional[int] = None,
                       admin_username: str = "",
                       admin_password: str = "") -> Institution:
    """
    创建机构。指派机构管理员有两种方式（admin_username 优先）：
      - admin_username(+admin_password)：账号不存在则当场创建并设为管理员，存在则提升。
      - admin_user_id：把已存在的用户提升为机构管理员。
    返回的 Institution 上附带 _admin_info（dict）供 API 回显。
    """
    code = _gen_invite_code()
    while db.query(Institution).filter(Institution.invite_code == code).first():
        code = _gen_invite_code()
    inst = Institution(
        name=name, domain=domain or None, subscription_level=subscription_level,
        quota_total=quota_total, quota_used=0, invite_code=code,
        is_active=True,
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)

    # 解析/创建管理员账号
    admin = None
    admin_created = False
    admin_username = (admin_username or "").strip()
    if admin_username:
        admin = db.query(User).filter(User.username == admin_username).first()
        if not admin:
            if not admin_password:
                admin_password = secrets.token_hex(6)
            admin = User(
                username=admin_username, hashed_password=_hash_pw(admin_password),
                is_active=True, is_approved=True,
            )
            db.add(admin)
            db.flush()
            admin_created = True
    elif admin_user_id:
        admin = db.query(User).filter(User.id == admin_user_id).first()

    admin_info = None
    if admin:
        admin.institution_id = inst.id
        admin.user_type = "institution_admin"
        inst.admin_user_ids = str(admin.id)
        db.commit()
        admin_info = {"id": admin.id, "username": admin.username, "created": admin_created}

    inst._admin_info = admin_info  # 临时属性，仅供本次响应
    logger.info(f"[inst] 创建机构 id={inst.id} name={name} invite={code} admin={admin_info}")
    return inst


def get_institution(db: Session, institution_id: int) -> Optional[Institution]:
    return db.query(Institution).filter(Institution.id == institution_id).first()


def list_institutions(db: Session) -> List[dict]:
    """列出所有机构（系统管理员）。附带各机构管理员账号信息。"""
    rows = db.query(Institution).order_by(Institution.id.desc()).all()
    out = []
    for inst in rows:
        admins = []
        if inst.admin_user_ids:
            for aid in str(inst.admin_user_ids).split(","):
                aid = aid.strip()
                if not aid:
                    continue
                u = db.query(User).filter(User.id == int(aid)).first()
                if u:
                    admins.append({"id": u.id, "username": u.username})
        out.append({
            "id": inst.id, "name": inst.name, "domain": inst.domain,
            "subscription_level": inst.subscription_level,
            "quota_total": inst.quota_total, "quota_used": inst.quota_used,
            "quota_remaining": inst.quota_remaining,
            "student_count": inst.student_count, "invite_code": inst.invite_code,
            "is_active": inst.is_active, "admins": admins,
        })
    return out


def get_by_invite(db: Session, invite_code: str) -> Optional[Institution]:
    return db.query(Institution).filter(
        Institution.invite_code == (invite_code or "").strip().upper(),
        Institution.is_active == True,
    ).first()


def register_student_by_invite(db: Session, invite_code: str, username: str, password: str,
                               student_id: str = "", college: str = "",
                               grade: str = "", major: str = "") -> dict:
    """
    学生用邀请码自助注册。创建 User(institution_student, 待审批) +
    InstitutionStudent(status=pending)。需机构管理员审批后方可使用。
    """
    inst = get_by_invite(db, invite_code)
    if not inst:
        return {"ok": False, "error": "邀请码无效或机构已停用"}
    username = (username or "").strip()
    if not username or not password:
        return {"ok": False, "error": "用户名/密码不能为空"}
    if db.query(User).filter(User.username == username).first():
        return {"ok": False, "error": "用户名已存在"}

    u = User(
        username=username, hashed_password=_hash_pw(password),
        is_active=True, is_approved=False,           # 待机构管理员审批
        institution_id=inst.id, user_type="institution_student",
    )
    db.add(u)
    db.flush()
    db.add(InstitutionStudent(
        institution_id=inst.id, user_id=u.id, student_id=student_id or None,
        college=college or None, grade=grade or None, major=major or None,
        status="pending",
    ))
    db.commit()
    logger.info(f"[inst] 学生自助注册 机构={inst.id} user={u.id} 待审批")
    return {"ok": True, "user_id": u.id, "institution_name": inst.name, "status": "pending"}


# ── 学生 ──────────────────────────────────────────────────────

def import_students(db: Session, institution_id: int, students: List[dict]) -> dict:
    """
    批量导入学生。每条 students[i]: {username, password?, student_id, college, grade, major}
    创建 User(approved, institution_student) + InstitutionStudent(approved)。
    用户名重复则跳过。返回统计。
    """
    created, skipped = 0, 0
    default_pw_hash = None
    for s in students:
        username = (s.get("username") or s.get("student_id") or "").strip()
        if not username:
            skipped += 1
            continue
        if db.query(User).filter(User.username == username).first():
            skipped += 1
            continue
        pw = s.get("password") or secrets.token_hex(6)
        u = User(
            username=username,
            hashed_password=_hash_pw(pw),
            is_active=True, is_approved=True,
            institution_id=institution_id,
            user_type="institution_student",
        )
        db.add(u)
        db.flush()  # 取 u.id
        db.add(InstitutionStudent(
            institution_id=institution_id, user_id=u.id,
            student_id=s.get("student_id"), college=s.get("college"),
            grade=s.get("grade"), major=s.get("major"),
            status="approved",
        ))
        created += 1
    # 更新机构学生数
    inst = get_institution(db, institution_id)
    if inst:
        inst.student_count = db.query(InstitutionStudent).filter(
            InstitutionStudent.institution_id == institution_id).count() + created
    db.commit()
    logger.info(f"[inst] 导入学生 机构={institution_id} 新增={created} 跳过={skipped}")
    return {"created": created, "skipped": skipped}


def list_students(db: Session, institution_id: int, status: Optional[str] = None) -> List[dict]:
    q = db.query(InstitutionStudent).filter(InstitutionStudent.institution_id == institution_id)
    if status:
        q = q.filter(InstitutionStudent.status == status)
    rows = q.all()
    out = []
    for r in rows:
        u = db.query(User).filter(User.id == r.user_id).first()
        out.append({
            "user_id": r.user_id,
            "username": u.username if u else None,
            "student_id": r.student_id, "college": r.college,
            "grade": r.grade, "major": r.major,
            "advisor_id": r.advisor_id, "status": r.status,
        })
    return out


def approve_student(db: Session, institution_id: int, user_id: int) -> bool:
    r = db.query(InstitutionStudent).filter(
        InstitutionStudent.institution_id == institution_id,
        InstitutionStudent.user_id == user_id,
    ).first()
    if not r:
        return False
    r.status = "approved"
    u = db.query(User).filter(User.id == user_id).first()
    if u:
        u.is_approved = True
    db.commit()
    return True


def assign_advisor(db: Session, institution_id: int, student_user_id: int, advisor_id: int) -> bool:
    r = db.query(InstitutionStudent).filter(
        InstitutionStudent.institution_id == institution_id,
        InstitutionStudent.user_id == student_user_id,
    ).first()
    if not r:
        return False
    r.advisor_id = advisor_id
    db.commit()
    return True


# ── 统计（管理控制台）──────────────────────────────────────────

def dashboard_stats(db: Session, institution_id: int) -> dict:
    """机构使用统计：学生数、配额、按功能/学院/日期聚合（基于 UsageRecord）。"""
    from datetime import timedelta
    from sqlalchemy import func
    from app.models.billing import UsageRecord

    inst = get_institution(db, institution_id)
    students = db.query(InstitutionStudent).filter(
        InstitutionStudent.institution_id == institution_id).all()
    approved = sum(1 for s in students if s.status == "approved")

    # 本机构成员 user_id 列表
    member_ids = [u.id for u in db.query(User.id).filter(User.institution_id == institution_id).all()]

    def _usage_q():
        return db.query(UsageRecord).filter(UsageRecord.user_id.in_(member_ids)) if member_ids else None

    # 按功能
    by_action = {}
    by_college = {}
    trend = {}
    total_usage = 0
    if member_ids:
        rows = db.query(UsageRecord.action, func.count(UsageRecord.id)).filter(
            UsageRecord.user_id.in_(member_ids)).group_by(UsageRecord.action).all()
        by_action = {a: c for a, c in rows}
        total_usage = sum(by_action.values())

        # 按学院（join InstitutionStudent）
        crows = db.query(InstitutionStudent.college, func.count(UsageRecord.id)).join(
            UsageRecord, UsageRecord.user_id == InstitutionStudent.user_id).filter(
            InstitutionStudent.institution_id == institution_id).group_by(
            InstitutionStudent.college).all()
        by_college = {(c or "未分院系"): n for c, n in crows}

        # 近 30 天趋势（按日）
        cutoff = datetime.utcnow() - timedelta(days=30)
        trows = db.query(func.date(UsageRecord.created_at), func.count(UsageRecord.id)).filter(
            UsageRecord.user_id.in_(member_ids), UsageRecord.created_at >= cutoff).group_by(
            func.date(UsageRecord.created_at)).all()
        trend = {str(d): n for d, n in trows}

    return {
        "students": {"total": len(students), "approved": approved, "pending": len(students) - approved},
        "quota": {
            "total": inst.quota_total if inst else 0,
            "used": inst.quota_used if inst else 0,
            "remaining": inst.quota_remaining if inst else 0,
        },
        "total_usage": total_usage,
        "usage_by_action": by_action,
        "usage_by_college": by_college,
        "usage_trend": trend,
    }


def export_usage_csv(db: Session, institution_id: int) -> str:
    """导出按学生的使用量 CSV（管理员下载，Excel 可开）。"""
    import csv
    import io
    from sqlalchemy import func
    from app.models.billing import UsageRecord

    rows = list_students(db, institution_id)
    # 每个学生的使用次数
    usage_map = {}
    member_ids = [r["user_id"] for r in rows]
    if member_ids:
        urows = db.query(UsageRecord.user_id, func.count(UsageRecord.id)).filter(
            UsageRecord.user_id.in_(member_ids)).group_by(UsageRecord.user_id).all()
        usage_map = {uid: c for uid, c in urows}

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["学号", "用户名", "学院", "年级", "专业", "状态", "使用次数"])
    for r in rows:
        w.writerow([r.get("student_id") or "", r.get("username") or "", r.get("college") or "",
                    r.get("grade") or "", r.get("major") or "", r.get("status") or "",
                    usage_map.get(r["user_id"], 0)])
    return buf.getvalue()
