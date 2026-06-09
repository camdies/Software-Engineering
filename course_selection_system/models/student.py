"""
models/student.py - 学生信息模型

映射 student 表，存储学生基本信息。
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from models.base import Base


class Student(Base):
    """学生信息模型。

    存储学生的基本信息，与user_account表通过student_id关联。
    """

    __tablename__ = "student"

    student_id = Column(
        String(20),
        ForeignKey("user_account.user_id", ondelete="CASCADE",
                   onupdate="CASCADE"),
        primary_key=True,
        comment="学生学号（主键，外键关联user_account）",
    )
    name = Column(
        String(50),
        nullable=False,
        comment="学生姓名",
    )
    major = Column(
        String(100),
        comment="主修专业",
    )
    class_name = Column(
        String(50),
        comment="所在班级",
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
    account = relationship("UserAccount", back_populates="student")
    enrollments = relationship("Enrollment", back_populates="student")
    grades = relationship("Grade", back_populates="student")

    def __repr__(self):
        return (
            f"<Student(student_id={self.student_id!r}, name={self.name!r})>"
        )

    def to_dict(self) -> dict:
        """将模型转为字典。

        Returns:
            dict: 包含学生基本信息的字典。
        """
        return {
            "student_id": self.student_id,
            "name": self.name,
            "major": self.major,
            "class_name": self.class_name,
            "contact": self.contact,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }
