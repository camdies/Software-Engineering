"""
backend/config/settings.py - 配置读取模块

支持 SQL Server 和 MySQL 双驱动，通过 config.ini [database] 段中的
driver 字段自动切换（默认 mssql）。
"""

import os
import configparser


class Settings:
    """系统配置管理类，单例模式。"""

    _instance = None
    _config = None

    @classmethod
    def get_instance(cls) -> "Settings":
        if cls._instance is None:
            cls._instance = Settings()
        return cls._instance

    def __init__(self):
        if self._config is not None:
            return
        self._config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), "config.ini")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        self._config.read(config_path, encoding="utf-8")

    @property
    def database(self) -> dict:
        """返回数据库连接参数。

        Returns:
            dict: host, port, driver(mssql|mysql), user, password, database, pool_size
        """
        return {
            "driver": self._config.get("database", "driver", fallback="mssql"),
            "host": self._config.get("database", "host", fallback="localhost"),
            "port": self._config.getint("database", "port", fallback=1433),
            "user": self._config.get("database", "user", fallback="sa"),
            "password": self._config.get("database", "password", fallback=""),
            "database": self._config.get("database", "database",
                                          fallback="CourseManagementDB"),
            "pool_size": self._config.getint("database", "pool_size", fallback=10),
        }

    @property
    def database_url(self) -> str:
        """生成 SQLAlchemy 数据库连接 URL。

        根据 driver 字段自动生成 SQL Server 或 MySQL 连接字符串。

        SQL Server (ODBC Driver 18):
          mssql+pyodbc://user:pass@host:port/db?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes

        SQL Server (pymssql fallback):
          mssql+pymssql://user:pass@host:port/db?charset=utf8

        MySQL:
          mysql+pymysql://user:pass@host:port/db?charset=utf8mb4

        Returns:
            str: 数据库连接字符串。
        """
        db = self.database
        driver = db.get("driver", "mssql")

        if driver == "mysql":
            return (
                f"mysql+pymysql://{db['user']}:{db['password']}"
                f"@{db['host']}:{db['port']}/{db['database']}"
                "?charset=utf8mb4"
            )

        # 默认 SQL Server — 优先使用 pyodbc + ODBC Driver 18
        return (
            f"mssql+pyodbc://{db['user']}:{db['password']}"
            f"@{db['host']}:{db['port']}/{db['database']}"
            "?driver=ODBC+Driver+18+for+SQL+Server"
            "&TrustServerCertificate=yes"
            "&Encrypt=yes"
        )

    @property
    def log_level(self) -> str:
        return self._config.get("system", "log_level", fallback="INFO")

    @property
    def log_dir(self) -> str:
        return self._config.get("system", "log_dir", fallback="logs")

    @property
    def backup_dir(self) -> str:
        return self._config.get("system", "backup_dir", fallback="backup")

    @property
    def backup_retain_days(self) -> int:
        return self._config.getint("system", "backup_retain_days", fallback=30)

    @property
    def session_timeout(self) -> int:
        return self._config.getint("system", "session_timeout", fallback=3600)

    @property
    def max_login_attempts(self) -> int:
        return self._config.getint("system", "max_login_attempts", fallback=5)

    @property
    def enrollment_is_open(self) -> bool:
        return self._config.getboolean("enrollment", "is_open", fallback=False)

    @property
    def enrollment_open_time(self) -> str:
        return self._config.get("enrollment", "open_time", fallback="")

    @property
    def enrollment_close_time(self) -> str:
        return self._config.get("enrollment", "close_time", fallback="")
