"""
db_util.py - 数据库连接池管理

封装数据库连接池的获取与释放，为各控制器提供便捷的数据库操作接口。
"""

from backend.models.base import DatabaseManager
from backend.utils.log_util import get_logger

logger = get_logger("db_util")


def get_db_session():
    """获取数据库会话上下文管理器。

    使用示例:
        with get_db_session() as session:
            result = session.query(User).all()

    Returns:
        数据库会话上下文管理器。
    """
    return DatabaseManager.get_instance().get_session()
