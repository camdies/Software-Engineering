"""
models/operation_log.py - 操作日志模型

映射 operation_log 表，记录系统中所有关键操作的审计日志。
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Index,
    Enum as SAEnum,
    DateTime,
)
from backend.models.base import Base


class OperationLog(Base):
    """操作日志模型。

    记录系统中所有关键操作（登录、选课、成绩录入、系统操作等），
    用于审计追溯和问题排查。
    """

    __tablename__ = "operation_log"

    log_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="日志ID（主键，自增）",
    )
    user_id = Column(
        String(20),
        nullable=False,
        comment="操作用户ID",
    )
    log_type = Column(
        SAEnum("登录", "选课", "成绩", "系统"),
        nullable=False,
        comment="操作类型: 登录/选课/成绩/系统",
    )
    operation = Column(
        String(200),
        nullable=False,
        comment="操作描述",
    )
    result = Column(
        SAEnum("成功", "失败"),
        nullable=False,
        comment="操作结果: 成功/失败",
    )
    log_time = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        comment="操作时间",
    )
    ip_address = Column(
        String(50),
        comment="操作IP地址",
    )
    created_at = Column(
        DateTime,
        default=datetime.now,
        comment="记录创建时间",
    )

    # 联合索引
    __table_args__ = (
        Index("idx_log_user_time", "user_id", "log_time"),
    )

    def __repr__(self):
        return (
            f"<OperationLog(log_id={self.log_id}, "
            f"user_id={self.user_id!r}, log_type={self.log_type!r}, "
            f"result={self.result!r})>"
        )

    def to_dict(self) -> dict:
        """将模型转为字典。

        Returns:
            dict: 包含操作日志基本信息的字典。
        """
        return {
            "log_id": self.log_id,
            "user_id": self.user_id,
            "log_type": self.log_type,
            "operation": self.operation,
            "result": self.result,
            "log_time": self.log_time.isoformat() if self.log_time else None,
            "ip_address": self.ip_address,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }
