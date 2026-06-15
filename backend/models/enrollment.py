"""
models/enrollment.py - 选课记录模型

映射 enrollment 表，存储学生选课/退课记录。
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Index,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from backend.models.base import Base


class Enrollment(Base):
    """选课记录模型。

    记录每位学生的选课与退课历史。
    一个学生可选多门课，每门课对应唯一的开课计划。
    """

    __tablename__ = "enrollment"

    enroll_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="选课记录ID（主键，自增）",
    )
    student_id = Column(
        String(20),
        ForeignKey("student.student_id", ondelete="CASCADE",
                   onupdate="CASCADE"),
        nullable=False,
        comment="学生学号（外键关联student）",
    )
    plan_id = Column(
        Integer,
        ForeignKey("course_plan.plan_id", ondelete="RESTRICT",
                   onupdate="CASCADE"),
        nullable=False,
        comment="开课计划ID（外键关联course_plan）",
    )
    enroll_time = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        comment="选课时间",
    )
    status = Column(
        String(10),
        default="已选",
        comment="选课状态: 已选/已退",
    )
    created_at = Column(
        DateTime,
        default=datetime.now,
        comment="记录创建时间",
    )

    # 关联关系
    student = relationship("Student", back_populates="enrollments")
    course_plan = relationship("CoursePlan", back_populates="enrollments")

    # 联合唯一索引，防止同一学生重复选同一开课计划
    __table_args__ = (
        Index("idx_enrollment_student_plan", "student_id", "plan_id",
              unique=True),
    )

    def __repr__(self):
        return (
            f"<Enrollment(enroll_id={self.enroll_id}, "
            f"student_id={self.student_id!r}, plan_id={self.plan_id}, "
            f"status={self.status!r})>"
        )

    def to_dict(self) -> dict:
        """将模型转为字典。

        Returns:
            dict: 包含选课记录基本信息的字典。
        """
        return {
            "enroll_id": self.enroll_id,
            "student_id": self.student_id,
            "plan_id": self.plan_id,
            "enroll_time": (
                self.enroll_time.isoformat() if self.enroll_time else None
            ),
            "status": self.status,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }
