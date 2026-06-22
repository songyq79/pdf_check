"""
机构管理 API（B端）。
- 建机构：系统管理员（is_admin）
- 学生导入/审批/导师绑定/机构信息：机构管理员（user_type=institution_admin）
"""

from typing import List, Optional, Tuple

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.user import User, get_db
from app.models.institution import Institution
from app.api.v1.auth import get_current_user
from app.services import institution_service as svc

router = APIRouter()


# ── 权限依赖 ──────────────────────────────────────────────────

def require_system_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, "需要系统管理员权限")
    return user


def require_inst_admin(
    institution_id: Optional[int] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Tuple[User, Institution]:
    """
    机构管理员 + 其所属机构。
    系统管理员（is_admin）可通过 query 参数 institution_id 查看/管理任意机构。
    机构管理员忽略 institution_id，始终只能操作自己绑定的机构。
    """
    # 系统管理员：可指定机构
    if user.is_admin and institution_id:
        inst = svc.get_institution(db, institution_id)
        if not inst:
            raise HTTPException(404, "机构不存在")
        return user, inst
    # 机构管理员：只能操作自己的机构
    if user.user_type not in ("institution_admin", "super_admin") and not user.is_admin:
        raise HTTPException(403, "需要机构管理员权限")
    if not user.institution_id:
        raise HTTPException(400, "当前账号未绑定机构（系统管理员请从机构列表点「进入控制台」）")
    inst = svc.get_institution(db, user.institution_id)
    if not inst:
        raise HTTPException(404, "机构不存在")
    return user, inst


# ── 请求体 ────────────────────────────────────────────────────

class CreateInstitutionReq(BaseModel):
    name: str
    domain: str = ""
    subscription_level: str = "small"
    quota_total: int = 0
    admin_user_id: Optional[int] = None
    admin_username: str = ""      # 优先：账号不存在则当场创建并设为管理员
    admin_password: str = ""


class StudentItem(BaseModel):
    username: str = ""
    password: Optional[str] = None
    student_id: Optional[str] = None
    college: Optional[str] = None
    grade: Optional[str] = None
    major: Optional[str] = None


class ImportStudentsReq(BaseModel):
    students: List[StudentItem]


class AssignAdvisorReq(BaseModel):
    student_user_id: int
    advisor_id: int


class RegisterStudentReq(BaseModel):
    invite_code: str
    username: str
    password: str
    student_id: str = ""
    college: str = ""
    grade: str = ""
    major: str = ""


# ── 端点 ──────────────────────────────────────────────────────

@router.post("/create", summary="创建机构（系统管理员）")
def create_institution(req: CreateInstitutionReq, _: User = Depends(require_system_admin),
                       db: Session = Depends(get_db)):
    inst = svc.create_institution(
        db, name=req.name, domain=req.domain,
        subscription_level=req.subscription_level,
        quota_total=req.quota_total, admin_user_id=req.admin_user_id,
        admin_username=req.admin_username, admin_password=req.admin_password,
    )
    return {
        "id": inst.id, "name": inst.name, "invite_code": inst.invite_code,
        "quota_total": inst.quota_total, "subscription_level": inst.subscription_level,
        "admin": getattr(inst, "_admin_info", None),
    }


@router.get("/list", summary="所有机构列表（系统管理员）")
def list_institutions(_: User = Depends(require_system_admin), db: Session = Depends(get_db)):
    return {"institutions": svc.list_institutions(db)}


@router.get("/info", summary="当前机构信息（机构管理员）")
def institution_info(ctx: Tuple[User, Institution] = Depends(require_inst_admin)):
    _, inst = ctx
    return {
        "id": inst.id, "name": inst.name, "domain": inst.domain,
        "subscription_level": inst.subscription_level,
        "quota_total": inst.quota_total, "quota_used": inst.quota_used,
        "quota_remaining": inst.quota_remaining,
        "student_count": inst.student_count, "invite_code": inst.invite_code,
        "is_active": inst.is_active,
    }


@router.post("/students/import", summary="批量导入学生（机构管理员）")
def import_students(req: ImportStudentsReq, ctx: Tuple[User, Institution] = Depends(require_inst_admin),
                    db: Session = Depends(get_db)):
    _, inst = ctx
    result = svc.import_students(db, inst.id, [s.model_dump() for s in req.students])
    return result


@router.get("/students", summary="机构学生列表（机构管理员）")
def list_students(status: Optional[str] = None,
                  ctx: Tuple[User, Institution] = Depends(require_inst_admin),
                  db: Session = Depends(get_db)):
    _, inst = ctx
    return {"students": svc.list_students(db, inst.id, status)}


@router.post("/students/{user_id}/approve", summary="审批学生（机构管理员）")
def approve_student(user_id: int, ctx: Tuple[User, Institution] = Depends(require_inst_admin),
                    db: Session = Depends(get_db)):
    _, inst = ctx
    if not svc.approve_student(db, inst.id, user_id):
        raise HTTPException(404, "该学生不在本机构")
    return {"ok": True}


@router.post("/advisor/assign", summary="绑定导师（机构管理员）")
def assign_advisor(req: AssignAdvisorReq, ctx: Tuple[User, Institution] = Depends(require_inst_admin),
                   db: Session = Depends(get_db)):
    _, inst = ctx
    if not svc.assign_advisor(db, inst.id, req.student_user_id, req.advisor_id):
        raise HTTPException(404, "该学生不在本机构")
    return {"ok": True}


@router.post("/register-student", summary="学生用邀请码自助注册（公开，需后续审批）")
def register_student(req: RegisterStudentReq, db: Session = Depends(get_db)):
    result = svc.register_student_by_invite(
        db, invite_code=req.invite_code, username=req.username, password=req.password,
        student_id=req.student_id, college=req.college, grade=req.grade, major=req.major,
    )
    if not result.get("ok"):
        raise HTTPException(400, result.get("error", "注册失败"))
    return result


@router.get("/my", summary="当前学生的机构信息（机构学生）")
def my_institution(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.institution_id:
        raise HTTPException(404, "当前账号未绑定机构")
    inst = svc.get_institution(db, user.institution_id)
    if not inst:
        raise HTTPException(404, "机构不存在")
    return {
        "institution_name": inst.name,
        "user_type": user.user_type,
        "quota_source": "institution",
        "quota_remaining": inst.quota_remaining,
        "quota_total": inst.quota_total,
        "is_approved": user.is_approved,
    }


@router.get("/dashboard", summary="机构使用统计面板（机构管理员）")
def dashboard(ctx: Tuple[User, Institution] = Depends(require_inst_admin),
              db: Session = Depends(get_db)):
    _, inst = ctx
    return svc.dashboard_stats(db, inst.id)


@router.get("/report.csv", summary="导出机构使用量报表 CSV（机构管理员）")
def export_report(ctx: Tuple[User, Institution] = Depends(require_inst_admin),
                  db: Session = Depends(get_db)):
    _, inst = ctx
    csv_text = svc.export_usage_csv(db, inst.id)
    # ﻿ BOM 让 Excel 正确识别 UTF-8 中文
    content = ("﻿" + csv_text).encode("utf-8")
    fname = f"institution_{inst.id}_usage_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )
