"""Login window for the course selection system."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QPushButton, QSpacerItem, QSizePolicy,
                                QMessageBox)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from backend.controllers.auth_controller import AuthController

STYLE = """
QWidget#loginWidget {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #e3f2fd, stop:1 #bbdefb);
}
QLineEdit {
    padding: 10px 14px;
    border: 1px solid #bdbdbd;
    border-radius: 6px;
    font-size: 13px;
    background: white;
}
QLineEdit:focus {
    border: 1px solid #2196f3;
}
#loginBtn {
    background-color: #2196f3;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px;
    font-size: 14px;
    font-weight: bold;
}
#loginBtn:hover {
    background-color: #1976d2;
}
#loginBtn:pressed {
    background-color: #1565c0;
}
#exitBtn {
    background-color: #e0e0e0;
    color: #424242;
    border: none;
    border-radius: 6px;
    padding: 10px;
    font-size: 14px;
}
#exitBtn:hover {
    background-color: #bdbdbd;
}
#hintLabel {
    font-size: 12px;
    padding: 4px;
}
"""


class LoginWindow(QWidget):
    login_success = Signal(str, str)  # role, user_id

    def __init__(self):
        super().__init__()
        self._auth = AuthController()
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("学生选课及成绩管理系统 - 登录")
        self.setFixedSize(420, 380)
        self.setObjectName("loginWidget")
        self.setStyleSheet(STYLE)

        # Center on screen
        screen = self.screen().availableGeometry()
        x = (screen.width() - 420) // 2
        y = (screen.height() - 380) // 2
        self.move(x, y)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(12)

        # Title
        title = QLabel("教务管理系统")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title.setStyleSheet("color: #1976d2;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Subtitle
        sub = QLabel("学生选课及成绩管理")
        sub.setFont(QFont("Microsoft YaHei", 10))
        sub.setStyleSheet("color: #757575;")
        sub.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(sub)

        main_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # User ID
        self._user_id_edit = QLineEdit()
        self._user_id_edit.setPlaceholderText("请输入学号/工号")
        self._user_id_edit.setMinimumHeight(40)
        main_layout.addWidget(self._user_id_edit)

        # Password
        self._password_edit = QLineEdit()
        self._password_edit.setPlaceholderText("请输入密码")
        self._password_edit.setEchoMode(QLineEdit.Password)
        self._password_edit.setMinimumHeight(40)
        self._password_edit.returnPressed.connect(self._do_login)
        main_layout.addWidget(self._password_edit)

        # Hint label
        self._hint_label = QLabel("")
        self._hint_label.setObjectName("hintLabel")
        self._hint_label.setAlignment(Qt.AlignCenter)
        self._hint_label.setWordWrap(True)
        main_layout.addWidget(self._hint_label)

        main_layout.addSpacerItem(QSpacerItem(0, 6, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)

        self._login_btn = QPushButton("登 录")
        self._login_btn.setObjectName("loginBtn")
        self._login_btn.setMinimumHeight(40)
        self._login_btn.setCursor(Qt.PointingHandCursor)
        self._login_btn.clicked.connect(self._do_login)

        self._exit_btn = QPushButton("退 出")
        self._exit_btn.setObjectName("exitBtn")
        self._exit_btn.setMinimumHeight(40)
        self._exit_btn.setCursor(Qt.PointingHandCursor)
        self._exit_btn.clicked.connect(self.close)

        btn_layout.addWidget(self._login_btn)
        btn_layout.addWidget(self._exit_btn)
        main_layout.addLayout(btn_layout)

    def _do_login(self):
        user_id = self._user_id_edit.text().strip()
        password = self._password_edit.text()

        if not user_id:
            self._show_hint("请输入学号/工号", "red")
            self._user_id_edit.setFocus()
            return
        if not password:
            self._show_hint("请输入密码", "red")
            self._password_edit.setFocus()
            return

        self._login_btn.setEnabled(False)
        self._show_hint("登录中...", "#1565c0")

        result = self._auth.login(user_id, password)

        if result["success"]:
            self._show_hint("登录成功，正在跳转...", "green")
            QTimer.singleShot(400, lambda: self._emit_login(result["role"], result["user_id"]))
        else:
            self._login_btn.setEnabled(True)
            msg = result.get("message", "登录失败")
            if "锁定" in msg:
                QMessageBox.warning(self, "账号锁定", "账号已锁定，请联系管理员")
                self._show_hint("账号已锁定", "red")
            else:
                self._show_hint(msg, "red")
                self._password_edit.setFocus()
                self._password_edit.selectAll()

    def _emit_login(self, role, user_id):
        self._login_btn.setEnabled(True)
        self.login_success.emit(role, user_id)
        self.close()

    def _show_hint(self, text, color):
        self._hint_label.setText(text)
        self._hint_label.setStyleSheet(f"color: {color};")
