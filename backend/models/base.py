"""
backend/models/base.py - 数据库连接基础模块

支持 MySQL (PyMySQL) 和 SQL Server (pyodbc) 双驱动，
通过 config.ini [database].driver 字段自动切换（默认 mysql）。
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
        self._driver = "mysql"
        try:
            self._ensure_models_loaded()
            self._init_engine()
            self._upgrade_existing_schema()
        except Exception:
            if self._engine is not None:
                self._engine.dispose()
            # A transient database or migration failure must be retryable.
            self._initialized = False
            raise

    def _upgrade_existing_schema(self):
        """Bring persistent installations in sync before any ORM query."""
        from backend.config.schema_upgrade import ensure_schema_current

        ensure_schema_current(self._engine, self._driver)
        logger.info("数据库结构检查/升级完成")

    def _ensure_models_loaded(self):
        """Import all models so string-based relationship() references resolve.

        SQLAlchemy's declarative_base lazily configures mappers.  String-based
        relationship("OtherModel") lookups fail at query-time if OtherModel
        hasn't been imported yet.  Importing the full model tree here guarantees
        every relationship is resolvable before any controller runs a query.
        """
        import backend.models.user_account  # noqa: F401
        import backend.models.student       # noqa: F401
        import backend.models.teacher       # noqa: F401
        import backend.models.course        # noqa: F401
        import backend.models.course_plan   # noqa: F401
        import backend.models.enrollment    # noqa: F401
        import backend.models.grade         # noqa: F401
        import backend.models.operation_log # noqa: F401
        import backend.models.class_period  # noqa: F401
        import backend.models.semester_config # noqa: F401
        import backend.models.password_reset_request # noqa: F401

    def _init_engine(self):
        """从配置文件读取参数并创建 SQLAlchemy Engine。

        MySQL (mysql):
          - 使用 PyMySQL + utf8mb4
          - pool_size=10, max_overflow=20, pool_timeout=10
          - pool_pre_ping=True 维持长连接

        SQL Server (mssql):
          - 使用 pyodbc + ODBC Driver 18 for SQL Server
          - 同连接池参数
          - 自动设置 READ COMMITTED 隔离级别
        """
        try:
            from backend.config.settings import Settings

            settings = Settings.get_instance()
            db = settings.database
            db_url = settings.database_url
            self._driver = db.get("driver", "mysql")

            logger.info(
                f"正在连接数据库 [{self._driver}] "
                f"{db['host']}:{db['port']}/{db['database']}"
            )

            connect_args = {}

            # MySQL: 强制 utf8mb4 字符集，避免中文乱码
            if self._driver == "mysql":
                connect_args = {"charset": "utf8mb4"}

            # pyodbc 额外参数
            if self._driver == "mssql" and "pyodbc" in db_url:
                connect_args = {
                    "timeout": 5,
                    "login_timeout": 5,
                }

            self._engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=db.get("pool_size", 10),
                max_overflow=20,
                pool_timeout=10,
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
            Base.metadata.create_all(self._engine)
            logger.info("所有数据库表创建/验证完成")
        except Exception as e:
            logger.error(f"数据库表创建失败: {e}")
            raise

    @property
    def is_mssql(self) -> bool:
        """是否为 SQL Server 驱动。"""
        return self._driver == "mssql"
