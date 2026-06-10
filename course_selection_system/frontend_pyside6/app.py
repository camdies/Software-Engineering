"""PySide6 application entry point."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from backend.models.base import DatabaseManager
from frontend_pyside6.login_window import LoginWindow
from frontend_pyside6.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
<<<<<<< Updated upstream
    app.setFont(QFont("Microsoft YaHei", 9))
=======
    app.setFont(QFont("Microsoft YaHei", 10))
    # 各处 STYLE 只设 font-size 不设 font-family 时
    # Qt 会把字体重置为系统默认，导致中文渲染失败。
    # 全局规则确保所有 widget 坚守 Microsoft YaHei。
    app.setStyleSheet("* { font-family: 'Microsoft YaHei'; }")
>>>>>>> Stashed changes
    try:
        DatabaseManager.get_instance().create_all_tables()
    except Exception as e:
        QMessageBox.critical(None, "启动失败", f"数据库连接失败: {e}")
        return

    main_window_ref = {"window": None}

    def on_login_success(role, user_id):
        main_window = MainWindow(role, user_id)
        main_window_ref["window"] = main_window
        main_window.show()

    login = LoginWindow()
    login.login_success.connect(on_login_success)
    login.show()
    sys.exit(app.exec())
