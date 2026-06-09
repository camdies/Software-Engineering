"""
models/base.py - 数据库连接基础模块

提供SQLAlchemy Engine、Session工厂及数据库会话上下文管理器。
采用单例模式管理数据库连接，从config/config.ini读取数据库配置。
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

from utils.log_util import get_logger

logger = get_logger("base")

Base = declarative_base()


class DatabaseManager:
    """数据库连接管理器，实现单例模式。

    管理SQLAlchemy Engine和Session工厂的生命周期，
    提供带事务控制的会话上下文管理器。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        """获取数据库管理器单例实例。

        Returns:
            DatabaseManager: 全局唯一的数据库管理器实例。
        """
        return cls()

    def __init__(self):
        """初始化数据库连接引擎和Session工厂。"""
        if self._initialized:
            return
        self._initialized = True
        self._engine = None
        self._Session = None
        self._init_engine()

    def _init_engine(self):
        """从配置文件读取参数并创建SQLAlchemy Engine。

        连接池配置:
            pool_size=10: 常驻连接数
            max_overflow=20: 最大溢出连接数
            pool_timeout=30: 等待可用连接的超时秒数
        """
        try:
            from config.settings import Settings

            settings = Settings.get_instance()
            db = settings.database
            db_url = settings.database_url

            logger.info(
                f"正在连接数据库 {db['host']}:{db['port']}/{db['database']}"
            )

            self._engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=db.get("pool_size", 10),
                max_overflow=20,
                pool_timeout=30,
                pool_pre_ping=True,  # 连接前检测可用性
                echo=False,
            )

            self._Session = sessionmaker(bind=self._engine)
            logger.info("数据库引擎初始化成功")
        except Exception as e:
            logger.error(f"数据库引擎初始化失败: {e}")
            raise

    @property
    def engine(self):
        """SQLAlchemy Engine实例。"""
        return self._engine

    @property
    def Session(self):
        """SQLAlchemy Session工厂。"""
        return self._Session

    @contextmanager
    def get_session(self):
        """提供数据库会话上下文管理器，自动处理事务提交/回滚/关闭。

        使用示例:
            db_mgr = DatabaseManager.get_instance()
            with db_mgr.get_session() as session:
                user = session.query(User).filter_by(id=1).first()

        事务控制:
            - 正常退出: 自动commit
            - 异常退出: 自动rollback，记录异常日志并重新抛出
            - 最终: 自动close释放连接回连接池

        Yields:
            Session: SQLAlchemy会话对象。

        Raises:
            Exception: 数据库操作异常，已自动回滚。
        """
        session = self._Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库事务异常，已回滚: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def dispose(self):
        """释放数据库连接池所有连接。

        通常在应用关闭时调用，确保连接资源被正确释放。
        """
        if self._engine:
            self._engine.dispose()
            logger.info("数据库连接池已释放")

    def create_all_tables(self):
        """根据所有Model定义创建数据库表。

        仅在首次初始化或表结构变更时调用。
        """
        try:
            Base.metadata.create_all(self._engine)
            logger.info("所有数据库表创建/验证完成")
        except Exception as e:
            logger.error(f"数据库表创建失败: {e}")
            raise
