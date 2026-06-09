"""
auth_util.py - 密码加密与验证工具

使用bcrypt算法对用户密码进行哈希加密和验证，
bcrypt内置salt机制，每次加密结果均不同。
"""

import bcrypt

from backend.utils.log_util import get_logger

logger = get_logger("auth_util")


def hash_password(password: str) -> str:
    """对明文密码进行bcrypt哈希加密。

    Args:
        password: 明文密码字符串。

    Returns:
        str: bcrypt哈希后的密码字符串（60字符）。

    Raises:
        ValueError: password为空时抛出。
    """
    if not password:
        logger.error("密码为空，无法进行哈希加密")
        raise ValueError("密码不能为空")
    try:
        # 将密码转为bytes，使用bcrypt生成salt并进行哈希
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")
    except Exception as e:
        logger.error(f"密码哈希加密失败: {e}")
        raise


def verify_password(password: str, hashed: str) -> bool:
    """验证明文密码与哈希值是否匹配。

    Args:
        password: 明文密码字符串。
        hashed: 数据库中存储的bcrypt哈希值。

    Returns:
        bool: 匹配返回True，否则返回False。
    """
    if not password or not hashed:
        logger.warning("密码验证参数不完整")
        return False
    try:
        password_bytes = password.encode("utf-8")
        hashed_bytes = hashed.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"密码验证过程异常: {e}")
        return False
