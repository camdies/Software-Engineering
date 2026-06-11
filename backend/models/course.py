"""
models/course.py - 课程信息模型

映射 course 表，存储课程计划信息（课程代码、名称、学分等）。
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    DECIMAL,
    Enum as SAEnum,
    DateTime,
)
from sqlalchemy.orm import relationship

from backend.models.base import Base


class Course(Base):
    """课程信息模型。

    存储课程的基本信息，每个课程可以有多个开课计划(course_plan)。
    """

    __tablename__ = "course"

    course_id = Column(
        String(20),
        primary_key=True,
        comment="课程代码（主键）",
    )
    course_name = Column(
        String(100),
        nullable=False,
        comment="课程名称",
    )
    credit = Column(
        DECIMAL(3, 1),
        comment="学分数（0.5-20，0.5步进）",
    )
    hours = Column(
        Integer,
        comment="学时数",
    )
    exam_type = Column(
        SAEnum("考试", "考查"),
        comment="考核方式: 考试/考查",
    )
    department = Column(
        String(100),
        comment="开课院系",
    )
    description = Column(
        String(2000),
        comment="课程简介",
    )
    textbook = Column(
        String(200),
        comment="教材",
    )
    syllabus = Column(
        String(2000),
        comment="教学大纲",
    )
    instructor_intro = Column(
        String(500),
        comment="教师简介",
    )
    created_at = Column(
        DateTime,
        default=datetime.now,
        comment="记录创建时间",
    )

    # 关联关系
    course_plans = relationship("CoursePlan", back_populates="course")

    def __repr__(self):
        return (
            f"<Course(course_id={self.course_id!r}, "
            f"course_name={self.course_name!r})>"
        )

    def to_dict(self) -> dict:
        """将模型转为字典。

        Returns:
            dict: 包含课程基本信息的字典。
        """
        return {
            "course_id": self.course_id,
            "course_name": self.course_name,
            "credit": float(self.credit) if self.credit else None,
            "hours": self.hours,
            "exam_type": self.exam_type,
            "department": self.department,
            "description": self.description,
            "textbook": self.textbook,
            "syllabus": self.syllabus,
            "instructor_intro": self.instructor_intro,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }
