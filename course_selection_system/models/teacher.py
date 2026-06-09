"""
models/teacher.py - 教师信息模型

映射 teacher 表，存储教师基本信息。
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from models.base import Base


class Teacher(Base):
    """教师信息模型。

    存储教师的基本信息，与user_account表通过teacher_id关联。
    """

    __tablename__ = "teacher"

    teacher_id = Column(
        String(20),
        ForeignKey("user_account.user_id", ondelete="CASCADE",
                   onupdate="CASCADE"),
        primary_key=True,
        comment="教师工号（主键，外键关联user_account）",
    )
    name = Column(
        String(50),
        nullable=False,
        comment="教师姓名",
    )
    college = Column(
        String(100),
        comment="所属学院",
    )
    contact = Column(
        String(20),
        comment="联系方式",
    )
    created_at = Column(
        DateTime,
        default=datetime.now,
        comment="记录创建时间",
    )

    # 关联关系
    account = relationship("UserAccount", back_populates="teacher")
    course_plans = relationship("CoursePlan", back_populates="teacher")

    def __repr__(self):
        return (
            f"<Teacher(teacher_id={self.teacher_id!r}, name={self.name!r})>"
        )

    def to_dict(self) -> dict:
        """将模型转为字典。

        Returns:
            dict: 包含教师基本信息的字典。
        """
        return {
            "teacher_id": self.teacher_id,
            "name": self.name,
            "college": self.college,
            "contact": self.contact,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }
