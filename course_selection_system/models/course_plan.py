"""
models/course_plan.py - 开课计划模型

映射 course_plan 表，存储每学期的开课记录，
包括教师、时间、地点、容量、先修课等信息。
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

from models.base import Base


class CoursePlan(Base):
    """开课计划模型。

    每个课程可在多个学期开课，产生不同的开课计划。
    包含授课教师、时间地点、容量限制、先修课要求等信息。
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
    time_slot = Column(
        String(50),
        comment="上课时间，如 周一1-2节",
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
        SAEnum("开课", "停课"),
        default="开课",
        comment="开课状态: 开课/停课",
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
            "time_slot": self.time_slot,
            "location": self.location,
            "capacity": self.capacity,
            "enrolled": self.enrolled,
            "prerequisite": self.prerequisite,
            "status": self.status,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }
