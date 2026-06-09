"""
views/admin/admin_main_view.py - 管理员主界面

基于QMainWindow的管理员主窗口，包含左侧导航栏和右侧内容区，
通过QStackedWidget实现页面切换。
"""

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QLabel,
    QPushButton,
    QStatusBar,
    QSplitter,
    QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

from controllers.auth_controller import AuthController


class AdminMainView(QMainWindow):
    """管理员主界面。

    左侧导航栏包含: 人员管理、课程管理、选课管理、成绩管理、系统管理。
    右侧为QStackedWidget，根据导航选择切换对应子界面。
    顶部状态栏显示: 当前用户、登录时间、退出按钮。
    """

    logout_signal = pyqtSignal()

    NAV_ITEMS = [
        ("人员管理", [
            ("student_mgmt", "学生管理"),
            ("teacher_mgmt", "教师管理"),
        ]),
        ("课程管理", [
            ("course_mgmt", "课程信息"),
            ("course_plan", "开课计划"),
        ]),
        ("选课管理", [
            ("enrollment_ctrl", "时段控制"),
            ("enrollment_stats", "选课统计"),
        ]),
        ("成绩管理", [
            ("grade_audit", "成绩审核"),
        ]),
        ("系统管理", [
            ("backup", "数据备份"),
            ("log_view", "操作日志"),
        ]),
    ]

    def __init__(self, user_id: str):
        super().__init__()
        self.user_id = user_id
        self.auth_controller = AuthController()
        self._init_ui()

    def _init_ui(self):
        """初始化管理员主界面。"""
        self.setWindowTitle("学生选课及成绩管理系统 - 管理员")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 680)

        # 居中显示
        screen = self.screen().availableGeometry()
        self.move(
            (screen.width() - 1280) // 2,
            (screen.height() - 800) // 2,
        )

        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧导航栏
        nav_widget = QWidget()
        nav_widget.setObjectName("navPanel")
        nav_widget.setFixedWidth(220)
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)

        # 导航标题
        nav_title = QLabel("管理菜单")
        nav_title.setObjectName("navTitle")
        nav_title.setAlignment(Qt.AlignCenter)
        nav_title.setFont(QFont("微软雅黑", 13, QFont.Bold))
        nav_title.setMinimumHeight(50)
        nav_title.setStyleSheet(
            "background-color: #1565c0; color: white; padding: 10px;"
        )
        nav_layout.addWidget(nav_title)

        # 导航列表
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        self.nav_list.setFont(QFont("微软雅黑", 10))
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)

        for category, items in self.NAV_ITEMS:
            # 分类标题（不可点击）
            cat_item = QListWidgetItem(category)
            cat_item.setFlags(Qt.NoItemFlags)
            cat_item.setFont(QFont("微软雅黑", 9, QFont.Bold))
            cat_item.setForeground(Qt.gray)
            self.nav_list.addItem(cat_item)

            for item_id, item_name in items:
                tab_item = QListWidgetItem(f"  {item_name}")
                tab_item.setData(Qt.UserRole, item_id)
                self.nav_list.addItem(tab_item)

        nav_layout.addWidget(self.nav_list)

        # 退出按钮
        logout_btn = QPushButton("退出登录")
        logout_btn.setObjectName("logoutBtn")
        logout_btn.setFont(QFont("微软雅黑", 10))
        logout_btn.setMinimumHeight(40)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self._on_logout)
        nav_layout.addWidget(logout_btn)

        # 右侧内容区
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentArea")

        # 添加占位页面（实际页面后续通过 set_page 方法注入）
        placeholder = QLabel("请选择管理功能")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setFont(QFont("微软雅黑", 14))
        self.content_stack.addWidget(placeholder)

        # 使用QSplitter分割布局
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(nav_widget)
        splitter.addWidget(self.content_stack)
        splitter.setStretchFactor(0, 0)  # 导航栏不拉伸
        splitter.setStretchFactor(1, 1)  # 内容区拉伸

        main_layout.addWidget(splitter)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status_bar()

        self.setStyleSheet(self._get_stylesheet())

        # 默认选中第一个可点击项
        self.nav_list.setCurrentRow(1)

    def _on_nav_changed(self, index: int):
        """导航栏切换事件处理。

        Args:
            index: 选中的行索引。
        """
        item = self.nav_list.item(index)
        if item is None:
            return
        page_id = item.data(Qt.UserRole)
        if page_id is None:
            return
        self._switch_page(page_id)

    def _switch_page(self, page_id: str):
        """切换到指定的子界面。

        Args:
            page_id: 子界面标识符（与NAV_ITEMS中定义一致）。
        """
        # 查找对应的QWidget
        for i in range(self.content_stack.count()):
            widget = self.content_stack.widget(i)
            if widget.objectName() == f"page_{page_id}":
                self.content_stack.setCurrentWidget(widget)
                return
        # 未找到对应页面，显示提示
        self.status_bar.showMessage(f"页面 {page_id} 尚未实现", 3000)

    def register_page(self, page_id: str, widget: QWidget):
        """注册子界面到内容区。

        Args:
            page_id: 子界面标识符。
            widget: 子界面QWidget实例。
        """
        widget.setObjectName(f"page_{page_id}")
        self.content_stack.addWidget(widget)

    def _on_logout(self):
        """退出登录按钮点击事件。"""
        reply = QMessageBox.question(
            self, "确认退出", "确定要退出登录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.auth_controller.logout(self.user_id)
            self.logout_signal.emit()
            self.close()

    def _update_status_bar(self):
        """更新状态栏信息。"""
        self.status_bar.showMessage(
            f"当前用户: {self.user_id} (管理员)  |  欢迎使用教务管理系统"
        )

    def closeEvent(self, event):
        """窗口关闭事件，清理资源。"""
        self.auth_controller.logout(self.user_id)
        event.accept()

    def _get_stylesheet(self) -> str:
        """返回管理员主界面的QSS样式表。"""
        return """
            #navPanel {
                background-color: #fafafa;
                border-right: 1px solid #e0e0e0;
            }
            #navList {
                border: none;
                background-color: #fafafa;
                outline: none;
            }
            #navList::item {
                padding: 8px 15px;
                border-bottom: none;
            }
            #navList::item:selected {
                background-color: #e3f2fd;
                color: #1565c0;
                font-weight: bold;
            }
            #contentArea {
                background-color: white;
            }
            #logoutBtn {
                background-color: #e53935;
                color: white;
                border: none;
                margin: 5px 10px;
                border-radius: 4px;
            }
            #logoutBtn:hover {
                background-color: #c62828;
            }
            QStatusBar {
                background-color: #f5f5f5;
                border-top: 1px solid #e0e0e0;
            }
            QSplitter::handle {
                background-color: #e0e0e0;
                width: 1px;
            }
        """
