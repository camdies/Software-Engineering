"""
models/class_period.py - 上课节次时间表模型

映射 class_period 表，定义每天11节课的固定时间安排。
"""

from sqlalchemy import Column, Integer, String

from backend.models.base import Base


class ClassPeriod(Base):
    """每天上课节次时间表。

    提供固定的11节课时间安排（8:30-21:20）。
    """

    __tablename__ = "class_period"

    period_id = Column(
        Integer,
        primary_key=True,
        comment="节次编号 (1-11)",
    )
    period_name = Column(
        String(10),
        nullable=False,
        comment="节次名称（第一节-第十一节）",
    )
    start_time = Column(
        String(10),
        nullable=False,
        comment="开始时间（HH:MM）",
    )
    end_time = Column(
        String(10),
        nullable=False,
        comment="结束时间（HH:MM）",
    )
    description = Column(
        String(50),
        comment="时段描述（上午/下午/晚上）",
    )

    def __repr__(self):
        return f"<ClassPeriod(period_id={self.period_id}, {self.start_time}-{self.end_time})>"

    def to_dict(self) -> dict:
        return {
            "period_id": self.period_id,
            "period_name": self.period_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "description": self.description,
            "time_range": f"{self.start_time}-{self.end_time}",
        }
