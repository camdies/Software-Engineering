"""
settings.py - 配置读取模块

从 config.ini 读取数据库连接、系统参数、选课时段等配置，
对外提供统一的配置访问接口。
"""

import os
import configparser


class Settings:
    """系统配置管理类，封装 config.ini 的读取逻辑。

    采用懒加载模式，首次访问时读取配置文件，
    后续调用使用缓存的配置实例。
    """

    _instance = None
    _config = None

    @classmethod
    def get_instance(cls) -> "Settings":
        """获取Settings单例实例。"""
        if cls._instance is None:
            cls._instance = Settings()
        return cls._instance

    def __init__(self):
        """初始化配置对象，读取config.ini文件。"""
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
            dict: 包含 host, port, user, password, database, pool_size 键。
        """
        return {
            "host": self._config.get("database", "host", fallback="localhost"),
            "port": self._config.getint("database", "port", fallback=3306),
            "user": self._config.get("database", "user", fallback="root"),
            "password": self._config.get("database", "password", fallback=""),
            "database": self._config.get("database", "database",
                                          fallback="course_management_db"),
            "pool_size": self._config.getint("database", "pool_size",
                                             fallback=10),
        }

    @property
    def database_url(self) -> str:
        """生成SQLAlchemy数据库连接URL。

        Returns:
            str: MySQL连接字符串。
        """
        db = self.database
        return (
            f"mysql+pymysql://{db['user']}:{db['password']}"
            f"@{db['host']}:{db['port']}/{db['database']}"
            "?charset=utf8mb4"
        )

    @property
    def log_level(self) -> str:
        """系统日志级别。"""
        return self._config.get("system", "log_level", fallback="INFO")

    @property
    def log_dir(self) -> str:
        """日志文件存放目录。"""
        return self._config.get("system", "log_dir", fallback="logs")

    @property
    def backup_dir(self) -> str:
        """数据备份目录。"""
        return self._config.get("system", "backup_dir", fallback="backup")

    @property
    def backup_retain_days(self) -> int:
        """备份文件保留天数。"""
        return self._config.getint("system", "backup_retain_days", fallback=30)

    @property
    def session_timeout(self) -> int:
        """会话超时时间（秒）。"""
        return self._config.getint("system", "session_timeout", fallback=3600)

    @property
    def max_login_attempts(self) -> int:
        """最大登录失败尝试次数。"""
        return self._config.getint("system", "max_login_attempts", fallback=5)

    @property
    def enrollment_is_open(self) -> bool:
        """选课系统是否开放。"""
        return self._config.getboolean("enrollment", "is_open", fallback=False)

    @property
    def enrollment_open_time(self) -> str:
        """选课开放开始时间。"""
        return self._config.get("enrollment", "open_time", fallback="")

    @property
    def enrollment_close_time(self) -> str:
        """选课开放结束时间。"""
        return self._config.get("enrollment", "close_time", fallback="")
