"""
main.py - 程序入口

初始化数据库连接，创建登录窗口，根据用户角色引导至对应主界面。
"""

import sys
import os

# 确保项目根目录在sys.path中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

from models.base import DatabaseManager
from views.login_view import LoginView
from utils.log_util import get_logger

logger = get_logger("main")


class Application:
    """应用程序主类，管理窗口生命周期和页面路由。"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setAttribute(Qt.AA_EnableHighDpiScaling, True)

        # 设置全局默认字体
        from PyQt5.QtGui import QFont
        font = QFont("微软雅黑", 9)
        self.app.setFont(font)

        # 初始化数据库连接
        try:
            db_mgr = DatabaseManager.get_instance()
            db_mgr.create_all_tables()
            logger.info("数据库连接初始化成功")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            QMessageBox.critical(
                None, "启动失败",
                f"数据库连接失败，请检查配置文件:\n{str(e)}"
            )
            sys.exit(1)

        # 创建登录界面
        self.login_view = LoginView()
        self.login_view.login_success.connect(self._on_login_success)
        self.login_view.show()

        self.current_window = None

    def _on_login_success(self, role: str, user_id: str):
        """登录成功后根据角色跳转到对应主界面。

        Args:
            role: 用户角色（admin/teacher/student）。
            user_id: 用户ID。
        """
        self.login_view.close()

        if role == "admin":
            from views.admin.admin_main_view import AdminMainView
            self.current_window = AdminMainView(user_id)
        elif role == "teacher":
            # 教师主界面——后续实现
            from PyQt5.QtWidgets import QMainWindow, QLabel
            self.current_window = QMainWindow()
            self.current_window.setWindowTitle("教师主界面")
            self.current_window.resize(800, 600)
            label = QLabel(f"教师 {user_id} - 功能开发中")
            label.setAlignment(Qt.AlignCenter)
            self.current_window.setCentralWidget(label)
        elif role == "student":
            # 学生主界面——后续实现
            from PyQt5.QtWidgets import QMainWindow, QLabel
            self.current_window = QMainWindow()
            self.current_window.setWindowTitle("学生主界面")
            self.current_window.resize(800, 600)
            label = QLabel(f"学生 {user_id} - 功能开发中")
            label.setAlignment(Qt.AlignCenter)
            self.current_window.setCentralWidget(label)
        else:
            logger.error(f"未知角色: {role}")
            return

        self.current_window.show()

    def run(self):
        """启动应用程序事件循环。"""
        logger.info("应用程序启动")
        exit_code = self.app.exec_()
        # 清理数据库连接
        try:
            DatabaseManager.get_instance().dispose()
        except Exception:
            pass
        logger.info("应用程序退出")
        sys.exit(exit_code)


if __name__ == "__main__":
    app = Application()
    app.run()
