"""
models/semester_config.py - 学期配置模型

映射 semester_config 表，管理学期参数和选课开关。
"""

from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date, DateTime

from backend.models.base import Base


class SemesterConfig(Base):
    """学期配置模型。

    管理学期总周数、起止日期、选课开关等全局配置。
    """

    __tablename__ = "semester_config"

    config_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="配置ID（主键，自增）",
    )
    semester = Column(
        String(20),
        nullable=False,
        comment="学期标识，如 2026-2027-1",
    )
    total_weeks = Column(
        Integer,
        nullable=False,
        default=20,
        comment="学期总周数（默认20周）",
    )
    start_date = Column(
        Date,
        comment="学期开始日期",
    )
    end_date = Column(
        Date,
        comment="学期结束日期",
    )
    is_current = Column(
        Integer,
        nullable=False,
        default=0,
        comment="是否为当前学期（1=是，0=否）",
    )
    enrollment_open = Column(
        Integer,
        nullable=False,
        default=0,
        comment="选课是否开放（1=是，0=否）",
    )
    enroll_start = Column(
        DateTime,
        comment="选课开始时间",
    )
    enroll_end = Column(
        DateTime,
        comment="选课结束时间",
    )
    created_at = Column(
        DateTime,
        default=datetime.now,
        comment="记录创建时间",
    )

    def __repr__(self):
        return (f"<SemesterConfig(semester={self.semester!r}, "
                f"weeks={self.total_weeks}, current={self.is_current})>")

    def to_dict(self) -> dict:
        return {
            "config_id": self.config_id,
            "semester": self.semester,
            "total_weeks": self.total_weeks,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_current": bool(self.is_current),
            "enrollment_open": bool(self.enrollment_open),
            "enroll_start": self.enroll_start.isoformat() if self.enroll_start else None,
            "enroll_end": self.enroll_end.isoformat() if self.enroll_end else None,
        }
