"""
models/user_account.py - 用户账号模型

映射 user_account 表，存储系统登录账号信息，
支持 admin / teacher / student 三种角色。
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Enum as SAEnum,
    DateTime,
    Integer,
)
from sqlalchemy.orm import relationship

from backend.models.base import Base


class UserAccount(Base):
    """用户账号模型。

    存储所有用户的登录凭证和账户状态信息。
    角色枚举: admin(管理员), teacher(教师), student(学生)。
    账户锁定机制: 密码错误累计5次后自动锁定。
    """

    __tablename__ = "user_account"

    user_id = Column(
        String(20),
        primary_key=True,
        comment="用户账号（主键）",
    )
    password_hash = Column(
        String(255),
        nullable=False,
        comment="bcrypt密码哈希",
    )
    role = Column(
        String(10),
        nullable=False,
        comment="用户角色: admin/teacher/student",
    )
    last_login = Column(
        DateTime,
        comment="最后登录时间",
    )
    is_locked = Column(
        Integer,
        default=0,
        comment="账户锁定: 0未锁定 1已锁定",
    )
    login_fail_count = Column(
        Integer,
        default=0,
        comment="连续登录失败次数",
    )
    token_version = Column(
        Integer,
        nullable=False,
        default=0,
        comment="JWT 撤销版本；账号安全状态变更时递增",
    )
    created_at = Column(
        DateTime,
        default=datetime.now,
        comment="记录创建时间",
    )

    # 关联关系
    student = relationship("Student", back_populates="account", uselist=False)
    teacher = relationship("Teacher", back_populates="account", uselist=False)

    def __repr__(self):
        return (
            f"<UserAccount(user_id={self.user_id!r}, "
            f"role={self.role!r}, is_locked={self.is_locked})>"
        )

    def to_dict(self) -> dict:
        """将模型转为字典。

        Returns:
            dict: 包含用户基本信息的字典（不包含密码哈希）。
        """
        return {
            "user_id": self.user_id,
            "role": self.role,
            "last_login": (
                self.last_login.isoformat() if self.last_login else None
            ),
            "is_locked": self.is_locked,
            "login_fail_count": self.login_fail_count,
            "token_version": self.token_version,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }
