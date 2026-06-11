"""
models/course_plan.py - 开课计划模型

映射 course_plan 表，存储每学期的开课记录。
教师提交申请，管理员审核通过后学生方可选课。
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Index,
    Enum as SAEnum,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from backend.models.base import Base


class CoursePlan(Base):
    """开课计划模型（教师申请制）。

    教师提交开课申请，管理员审核通过后生效。
    使用 weekday + period_start + period_count 精确描述上课时间。
    start_week + end_week 定义教学周范围（1-20）。
    """

    __tablename__ = "course_plan"

    plan_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="开课计划ID（主键，自增）",
    )
    course_id = Column(
        String(20),
        ForeignKey("course.course_id", ondelete="RESTRICT",
                   onupdate="CASCADE"),
        nullable=False,
        comment="课程代码（外键关联course）",
    )
    teacher_id = Column(
        String(20),
        ForeignKey("teacher.teacher_id", ondelete="RESTRICT",
                   onupdate="CASCADE"),
        nullable=False,
        comment="教师工号（外键关联teacher）",
    )
    semester = Column(
        String(20),
        nullable=False,
        comment="开课学期，如 2026-2027-1",
    )
    weekday = Column(
        Integer,
        nullable=False,
        comment="上课日: 1=周一 ... 7=周日",
    )
    period_start = Column(
        Integer,
        nullable=False,
        comment="起始节次 (1-11)",
    )
    period_count = Column(
        Integer,
        nullable=False,
        default=2,
        comment="持续节数 (1-11)",
    )
    start_week = Column(
        Integer,
        nullable=False,
        default=1,
        comment="起始教学周 (1-20)",
    )
    end_week = Column(
        Integer,
        nullable=False,
        default=20,
        comment="结束教学周 (1-20)",
    )
    location = Column(
        String(100),
        comment="上课地点",
    )
    capacity = Column(
        Integer,
        comment="课程容量上限",
    )
    enrolled = Column(
        Integer,
        default=0,
        comment="已选人数",
    )
    prerequisite = Column(
        String(200),
        comment="先修课程代码，多个以逗号分隔",
    )
    status = Column(
        SAEnum("待审核", "已通过", "已驳回", "已停课"),
        default="待审核",
        comment="审核状态: 待审核/已通过/已驳回/已停课",
    )
    audit_comment = Column(
        String(500),
        comment="审核意见",
    )
    created_at = Column(
        DateTime,
        default=datetime.now,
        comment="记录创建时间",
    )

    # 关联关系
    course = relationship("Course", back_populates="course_plans")
    teacher = relationship("Teacher", back_populates="course_plans")
    enrollments = relationship("Enrollment", back_populates="course_plan")
    grades = relationship("Grade", back_populates="course_plan")

    # 联合索引
    __table_args__ = (
        Index("idx_course_semester", "course_id", "semester"),
        Index("idx_course_plan_status", "status"),
    )

    @property
    def time_slot_display(self) -> str:
        """生成人类可读的上课时间描述。

        Returns:
            str: 如 '周一 1-2节 (第1-18周)'
        """
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        w = weekdays[self.weekday - 1] if 1 <= self.weekday <= 7 else "未知"
        return (
            f"{w} {self.period_start}-"
            f"{self.period_start + self.period_count - 1}节 "
            f"(第{self.start_week}-{self.end_week}周)"
        )

    def __repr__(self):
        return (
            f"<CoursePlan(plan_id={self.plan_id}, "
            f"course_id={self.course_id!r}, semester={self.semester!r})>"
        )

    def to_dict(self) -> dict:
        """将模型转为字典。

        Returns:
            dict: 包含开课计划基本信息的字典。
        """
        return {
            "plan_id": self.plan_id,
            "course_id": self.course_id,
            "teacher_id": self.teacher_id,
            "semester": self.semester,
            "weekday": self.weekday,
            "period_start": self.period_start,
            "period_count": self.period_count,
            "start_week": self.start_week,
            "end_week": self.end_week,
            "time_slot": self.time_slot_display,
            "location": self.location,
            "capacity": self.capacity,
            "enrolled": self.enrolled,
            "prerequisite": self.prerequisite,
            "status": self.status,
            "audit_comment": self.audit_comment,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }
