"""
B端高校机构版数据模型（Phase 2）。
Institution（机构）+ InstitutionStudent（机构-学生-导师绑定）。
机构配额池：quota_total/quota_used，机构学生消耗走此池（见 billing_service 路由）。
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index

from app.models.user import Base


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    domain = Column(String(100), index=True, nullable=True)      # 校域邮箱后缀，如 pku.edu.cn
    subscription_level = Column(String(20), default="small")      # small / medium / large
    quota_total = Column(Integer, default=0)                      # 机构配额池总量
    quota_used = Column(Integer, default=0)                       # 已消耗
    student_count = Column(Integer, default=0)                    # 已开通学生数
    invite_code = Column(String(20), unique=True, index=True, nullable=True)  # 学生注册邀请码
    admin_user_ids = Column(String(500), nullable=True)          # 机构管理员 user_id，逗号分隔
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)                  # 年费到期

    @property
    def quota_remaining(self) -> int:
        return max(0, (self.quota_total or 0) - (self.quota_used or 0))


class InstitutionStudent(Base):
    __tablename__ = "institution_students"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    student_id = Column(String(50), nullable=True)                # 学号
    college = Column(String(100), nullable=True)                  # 学院
    grade = Column(String(20), nullable=True)                     # 年级
    major = Column(String(100), nullable=True)                    # 专业
    advisor_id = Column(Integer, nullable=True)                   # 导师 user_id
    status = Column(String(20), default="pending")               # pending / approved
    created_at = Column(DateTime, default=datetime.utcnow)


# 机构内按学院/年级筛选学生（管理控制台统计路径）
Index("ix_inst_students_inst_college", InstitutionStudent.institution_id, InstitutionStudent.college)
