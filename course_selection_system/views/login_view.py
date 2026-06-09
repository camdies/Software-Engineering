"""
views/login_view.py - 登录界面

基于PyQt5的登录窗口，提供用户ID、密码输入及登录/退出功能。
登录成功后根据角色跳转至对应主界面。
"""

from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QSpacerItem,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from controllers.auth_controller import AuthController


class LoginView(QWidget):
    """登录界面。

    窗口标题: 学生选课及成绩管理系统 - 登录
    包含用户ID输入框、密码输入框（密文）、登录按钮、退出按钮。
    登录成功信号携带角色信息，由主窗口处理页面跳转。
    """

    login_success = pyqtSignal(str, str)  # role, user_id

    def __init__(self):
        super().__init__()
        self.auth_controller = AuthController()
        self._init_ui()

    def _init_ui(self):
        """初始化登录界面UI。"""
        self.setWindowTitle("学生选课及成绩管理系统 - 登录")
        self.setFixedSize(420, 380)
        self.setObjectName("loginView")

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(50, 40, 50, 40)
        main_layout.setSpacing(15)

        # 标题
        title_label = QLabel("教务管理系统")
        title_label.setObjectName("loginTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("微软雅黑", 18, QFont.Bold))
        main_layout.addWidget(title_label)

        subtitle_label = QLabel("学生选课及成绩管理")
        subtitle_label.setObjectName("loginSubtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setFont(QFont("微软雅黑", 10))
        main_layout.addWidget(subtitle_label)

        main_layout.addSpacerItem(QSpacerItem(20, 20,
                                  QSizePolicy.Minimum, QSizePolicy.Fixed))

        # 用户ID输入区
        id_layout = QHBoxLayout()
        id_label = QLabel("用户ID")
        id_label.setFixedWidth(60)
        id_label.setFont(QFont("微软雅黑", 10))
        self.user_id_input = QLineEdit()
        self.user_id_input.setPlaceholderText("请输入学号/工号")
        self.user_id_input.setFont(QFont("微软雅黑", 10))
        self.user_id_input.setMinimumHeight(36)
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.user_id_input)
        main_layout.addLayout(id_layout)

        # 密码输入区
        pwd_layout = QHBoxLayout()
        pwd_label = QLabel("密  码")
        pwd_label.setFixedWidth(60)
        pwd_label.setFont(QFont("微软雅黑", 10))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont("微软雅黑", 10))
        self.password_input.setMinimumHeight(36)
        pwd_layout.addWidget(pwd_label)
        pwd_layout.addWidget(self.password_input)
        main_layout.addLayout(pwd_layout)

        # 提示标签
        self.hint_label = QLabel("")
        self.hint_label.setObjectName("loginHint")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setFont(QFont("微软雅黑", 9))
        main_layout.addWidget(self.hint_label)

        # 按钮区
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        self.login_btn = QPushButton("登 录")
        self.login_btn.setObjectName("loginBtn")
        self.login_btn.setMinimumHeight(38)
        self.login_btn.setFont(QFont("微软雅黑", 11))
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self._on_login)

        self.exit_btn = QPushButton("退 出")
        self.exit_btn.setObjectName("exitBtn")
        self.exit_btn.setMinimumHeight(38)
        self.exit_btn.setFont(QFont("微软雅黑", 11))
        self.exit_btn.setCursor(Qt.PointingHandCursor)
        self.exit_btn.clicked.connect(self.close)

        btn_layout.addWidget(self.login_btn)
        btn_layout.addWidget(self.exit_btn)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)
        self.setStyleSheet(self._get_stylesheet())

        # 绑定回车键
        self.password_input.returnPressed.connect(self._on_login)
        self.user_id_input.returnPressed.connect(
            self.password_input.setFocus
        )

    def _on_login(self):
        """处理登录按钮点击事件。

        调用 auth_controller.login() 进行验证，
        根据返回结果决定跳转或显示错误提示。
        """
        user_id = self.user_id_input.text().strip()
        password = self.password_input.text()

        if not user_id:
            self.hint_label.setText("请输入用户ID")
            self.hint_label.setStyleSheet("color: #f44336;")
            return
        if not password:
            self.hint_label.setText("请输入密码")
            self.hint_label.setStyleSheet("color: #f44336;")
            return

        result = self.auth_controller.login(user_id, password)

        if result["success"]:
            self.hint_label.setText("登录成功，正在跳转...")
            self.hint_label.setStyleSheet("color: #4caf50;")
            self.login_success.emit(result["role"], result["user_id"])
        else:
            msg = result["message"]
            if "密码错误" in msg or "尝试次数" in msg:
                self.hint_label.setText(msg)
                self.hint_label.setStyleSheet("color: #f44336;")
                self.password_input.clear()
                self.password_input.setFocus()
            elif "已锁定" in msg:
                QMessageBox.warning(self, "账号已锁定",
                                    "账号已锁定，请联系管理员")
                self.hint_label.setText("账号已锁定")
                self.hint_label.setStyleSheet("color: #f44336;")
            else:
                self.hint_label.setText(msg)
                self.hint_label.setStyleSheet("color: #f44336;")

    def _get_stylesheet(self) -> str:
        """返回登录界面的QSS样式表。"""
        return """
            #loginView {
                background-color: #f5f5f5;
            }
            #loginTitle {
                color: #1976d2;
            }
            #loginSubtitle {
                color: #757575;
            }
            QLineEdit {
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                padding: 5px 10px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #2196f3;
            }
            #loginBtn {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 4px;
            }
            #loginBtn:hover {
                background-color: #1976d2;
            }
            #loginBtn:pressed {
                background-color: #1565c0;
            }
            #exitBtn {
                background-color: #e0e0e0;
                color: #616161;
                border: none;
                border-radius: 4px;
            }
            #exitBtn:hover {
                background-color: #bdbdbd;
            }
        """
