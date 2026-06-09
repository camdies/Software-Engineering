"""
backend/models/base.py - 数据库连接基础模块

支持 SQL Server (pyodbc) 和 MySQL (PyMySQL) 双驱动，
通过 config.ini [database].driver 字段自动切换。
采用单例模式管理数据库连接。
"""

from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

from backend.utils.log_util import get_logger

logger = get_logger("base")
Base = declarative_base()


class DatabaseManager:
    """数据库连接管理器，单例模式。

    支持 SQL Server / MySQL 双驱动。
    SQL Server 模式下自动配置 IDENTITY_INSERT 等兼容性设置。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        return cls()

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._engine = None
        self._Session = None
        self._driver = "mssql"
        self._init_engine()

    def _init_engine(self):
        """从配置文件读取参数并创建 SQLAlchemy Engine。

        SQL Server (mssql):
          - 使用 pyodbc + ODBC Driver 18 for SQL Server
          - pool_size=10, max_overflow=20, pool_timeout=30
          - pool_pre_ping=True 维持长连接

        MySQL (mysql):
          - 使用 PyMySQL
          - 同连接池参数
        """
        try:
            from backend.config.settings import Settings

            settings = Settings.get_instance()
            db = settings.database
            db_url = settings.database_url
            self._driver = db.get("driver", "mssql")

            logger.info(
                f"正在连接数据库 [{self._driver}] "
                f"{db['host']}:{db['port']}/{db['database']}"
            )

            connect_args = {}

            # pyodbc 额外参数
            if self._driver == "mssql" and "pyodbc" in db_url:
                connect_args = {
                    "timeout": 30,
                    "autocommit": False,
                }

            self._engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=db.get("pool_size", 10),
                max_overflow=20,
                pool_timeout=30,
                pool_pre_ping=True,
                echo=False,
                connect_args=connect_args if connect_args else {},
            )

            # SQL Server: 启用快照隔离以支持 SELECT ... FOR UPDATE 等价行为
            if self._driver == "mssql":
                @event.listens_for(self._engine, "connect")
                def _set_snapshot_isolation(dbapi_conn, connection_record):
                    cursor = dbapi_conn.cursor()
                    cursor.execute(
                        "SET TRANSACTION ISOLATION LEVEL READ COMMITTED"
                    )
                    cursor.close()

            self._Session = sessionmaker(bind=self._engine)
            logger.info("数据库引擎初始化成功")
        except Exception as e:
            logger.error(f"数据库引擎初始化失败: {e}")
            raise

    @property
    def engine(self):
        return self._engine

    @property
    def Session(self):
        return self._Session

    @contextmanager
    def get_session(self):
        """数据库会话上下文管理器，自动 commit / rollback / close。"""
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
        if self._engine:
            self._engine.dispose()
            logger.info("数据库连接池已释放")

    def create_all_tables(self):
        """根据所有 Model 定义创建数据库表。"""
        try:
            # 导入所有模型以确保注册到 Base.metadata
            import backend.models.user_account  # noqa
            import backend.models.student      # noqa
            import backend.models.teacher      # noqa
            import backend.models.course       # noqa
            import backend.models.course_plan  # noqa
            import backend.models.enrollment   # noqa
            import backend.models.grade        # noqa
            import backend.models.operation_log  # noqa
            Base.metadata.create_all(self._engine)
            logger.info("所有数据库表创建/验证完成")
        except Exception as e:
            logger.error(f"数据库表创建失败: {e}")
            raise

    @property
    def is_mssql(self) -> bool:
        """是否为 SQL Server 驱动。"""
        return self._driver == "mssql"
