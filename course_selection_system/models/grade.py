"""
models/grade.py - 成绩记录模型

映射 grade 表，存储学生的课程成绩和绩点信息。
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Index,
    DECIMAL,
    Enum as SAEnum,
    DateTime,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from models.base import Base


class Grade(Base):
    """成绩记录模型。

    存储每位学生在每门课程中的成绩和对应绩点，
    支持成绩审核和更正流程。
    """

    __tablename__ = "grade"

    grade_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="成绩记录ID（主键，自增）",
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
    score = Column(
        Integer,
        CheckConstraint("score >= 0 AND score <= 100"),
        comment="百分制成绩（0-100）",
    )
    gpa_point = Column(
        DECIMAL(3, 2),
        comment="对应绩点（0.00-4.00）",
    )
    record_time = Column(
        DateTime,
        default=datetime.now,
        comment="成绩录入时间",
    )
    status = Column(
        SAEnum("正常", "待审核", "已更正"),
        default="正常",
        comment="成绩状态: 正常/待审核/已更正",
    )
    modify_reason = Column(
        String(500),
        comment="成绩修改原因",
    )
    created_at = Column(
        DateTime,
        default=datetime.now,
        comment="记录创建时间",
    )

    # 关联关系
    student = relationship("Student", back_populates="grades")
    course_plan = relationship("CoursePlan", back_populates="grades")

    # 联合索引
    __table_args__ = (
        Index("idx_grade_student_plan", "student_id", "plan_id"),
    )

    def __repr__(self):
        return (
            f"<Grade(grade_id={self.grade_id}, "
            f"student_id={self.student_id!r}, score={self.score}, "
            f"status={self.status!r})>"
        )

    def to_dict(self) -> dict:
        """将模型转为字典。

        Returns:
            dict: 包含成绩记录基本信息的字典。
        """
        return {
            "grade_id": self.grade_id,
            "student_id": self.student_id,
            "plan_id": self.plan_id,
            "score": self.score,
            "gpa_point": float(self.gpa_point) if self.gpa_point else None,
            "record_time": (
                self.record_time.isoformat() if self.record_time else None
            ),
            "status": self.status,
            "modify_reason": self.modify_reason,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }
