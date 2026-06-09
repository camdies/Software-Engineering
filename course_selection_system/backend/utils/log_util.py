"""
log_util.py - 日志工具封装

基于Python标准logging模块，提供统一的日志记录接口。
特性：
- 同时输出到控制台和按日期滚动的日志文件
- 日志文件每日滚动，保留30天
- 统一格式：[时间][级别][模块名][函数名:行号] 消息内容
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime

# 日志格式
LOG_FORMAT = (
    "[%(asctime)s][%(levelname)s][%(name)s]"
    "[%(funcName)s:%(lineno)d] %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 默认日志输出目录（3级: utils -> backend -> course_selection_system/logs）
_DEFAULT_LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "logs",
)


def get_logger(module_name: str) -> logging.Logger:
    """获取指定模块的logger实例。

    首次调用时为该模块配置控制台和文件handler，
    后续调用返回已配置的logger，避免重复添加handler。

    Args:
        module_name: 模块名称，用于日志标识和文件名。

    Returns:
        logging.Logger: 配置完成的logger实例。
    """
    logger = logging.getLogger(module_name)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 从系统配置读取日志级别，默认为INFO
    try:
        from backend.config.settings import Settings
        settings = Settings.get_instance()
        log_level_str = settings.log_level
        log_dir = settings.log_dir
        if not os.path.isabs(log_dir):
            log_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                log_dir,
            )
    except Exception:
        log_level_str = "INFO"
        log_dir = _DEFAULT_LOG_DIR

    level = getattr(logging, log_level_str.upper(), logging.INFO)
    logger.setLevel(level)

    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)

    # 创建formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件handler — 按日期滚动，保留30天
    log_file = os.path.join(log_dir, f"{module_name}.log")
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler.suffix = "%Y%m%d"
    logger.addHandler(file_handler)

    return logger
