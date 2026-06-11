"""
models/password_reset_request.py - 密码重置申请模型

映射 password_reset_request 表，存储用户提交的密码重置申请。
由管理员在审核中心统一处理。
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Enum as SAEnum,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from backend.models.base import Base


class PasswordResetRequest(Base):
    """密码重置申请模型。

    用户在登录页面提交重置申请，管理员审核通过后生效。
    new_password 为 NULL 时表示重置为默认密码 123456。
    """

    __tablename__ = "password_reset_request"

    request_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="申请ID（主键，自增）",
    )
    user_id = Column(
        String(20),
        ForeignKey("user_account.user_id"),
        nullable=False,
        comment="申请用户账号",
    )
    new_password = Column(
        String(255),
        nullable=True,
        comment="申请的新密码哈希（NULL=重置为默认密码）",
    )
    reason = Column(
        String(200),
        comment="申请原因",
    )
    status = Column(
        SAEnum("待审核", "已通过", "已驳回"),
        default="待审核",
        comment="审核状态",
    )
    admin_id = Column(
        String(20),
        comment="处理该申请的管理员ID",
    )
    request_time = Column(
        DateTime,
        default=datetime.now,
        comment="申请提交时间",
    )
    process_time = Column(
        DateTime,
        comment="处理时间",
    )
    comment = Column(
        String(200),
        comment="管理员处理意见",
    )

    user = relationship("UserAccount", back_populates="password_reset_requests")

    def __repr__(self):
        return (
            f"<PasswordResetRequest(request_id={self.request_id}, "
            f"user_id={self.user_id!r}, status={self.status!r})>"
        )

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "reason": self.reason,
            "status": self.status,
            "admin_id": self.admin_id,
            "request_time": (
                self.request_time.isoformat() if self.request_time else None
            ),
            "process_time": (
                self.process_time.isoformat() if self.process_time else None
            ),
            "comment": self.comment,
        }
