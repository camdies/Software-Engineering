"""Unified main window for all roles (admin, teacher, student)."""

from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                                QListWidget, QListWidgetItem, QStackedWidget,
                                QLabel, QStatusBar, QSplitter, QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

from backend.controllers.auth_controller import AuthController

SIDEBAR_STYLE = """
QListWidget {
    background-color: #ffffff;
    border: none;
    border-right: 1px solid #e0e0e0;
    font-size: 13px;
}
QListWidget::item {
    padding: 12px 20px;
    border-bottom: 1px solid #f5f5f5;
}
QListWidget::item:hover {
    background-color: #e3f2fd;
    color: #1565c0;
}
QListWidget::item:selected {
    background-color: #2196f3;
    color: white;
}
"""


class MainWindow(QMainWindow):
    def __init__(self, role: str, user_id: str):
        super().__init__()
        self._role = role
        self._user_id = user_id
        self._auth = AuthController()
        self._pages = {}  # sidebar item name -> widget

        self._init_ui()
        self._build_sidebar()
        self._build_content()

        # Select first item
        if self._sidebar.count() > 0:
            self._sidebar.setCurrentRow(0)
            item = self._sidebar.item(0)
            if item and item.flags() & Qt.ItemIsSelectable:
                self._on_sidebar_changed(item)

    def _init_ui(self):
        titles = {"admin": "管理员", "teacher": "教师", "student": "学生"}
        title = titles.get(self._role, self._role)
        self.setWindowTitle(f"学生选课及成绩管理系统 - {title}端 - {self._user_id}")
        self.setMinimumSize(1100, 700)

        screen = self.screen().availableGeometry()
        self.resize(int(screen.width() * 0.75), int(screen.height() * 0.75))
        self.move((screen.width() - self.width()) // 2,
                  (screen.height() - self.height()) // 2)

        central = QWidget()
        self.setCentralWidget(central)

        # Main layout: sidebar + content
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background: #e0e0e0; }")

        # Sidebar
        self._sidebar = QListWidget()
        self._sidebar.setFixedWidth(220)
        self._sidebar.setStyleSheet(SIDEBAR_STYLE)
        self._sidebar.setSpacing(0)
        self._sidebar.currentItemChanged.connect(self._on_sidebar_changed)

        # Content stack
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background-color: #fafafa;")

        splitter.addWidget(self._sidebar)
        splitter.addWidget(self._stack)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(splitter)

        # Status bar
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet("QStatusBar { background: #e3f2fd; color: #1565c0; font-size: 12px; }")
        self._status_bar.showMessage(f"当前用户: {self._user_id} | 角色: {title}")
        self.setStatusBar(self._status_bar)

    def _add_category(self, text):
        item = QListWidgetItem(text)
        item.setFlags(Qt.NoItemFlags)
        font = QFont("Microsoft YaHei", 10, QFont.Bold)
        item.setFont(font)
        item.setForeground(Qt.gray)
        item.setSizeHint(QSize(0, 36))
        self._sidebar.addItem(item)

    def _add_item(self, text):
        item = QListWidgetItem("    " + text)
        item.setData(Qt.UserRole, text)
        item.setSizeHint(QSize(0, 42))
        self._sidebar.addItem(item)

    def _build_sidebar(self):
        if self._role == "admin":
            self._add_category("人员管理")
            self._add_item("学生管理")
            self._add_item("教师管理")
            self._add_category("课程管理")
            self._add_item("课程信息")
            self._add_item("开课计划")
            self._add_category("选课管理")
            self._add_item("时段控制")
            self._add_item("选课统计")
            self._add_category("成绩管理")
            self._add_item("成绩审核")
            self._add_category("系统管理")
            self._add_item("操作日志")
        elif self._role == "teacher":
            self._add_item("任课信息")
            self._add_item("成绩录入")
            self._add_item("成绩修改申请")
            self._add_item("统计分析")
        elif self._role == "student":
            self._add_item("选课中心")
            self._add_item("已选课程")
            self._add_item("成绩查询")
            self._add_item("学业统计")

    def _build_content(self):
        from frontend_pyside6.admin_students import AdminStudentsPage
        from frontend_pyside6.admin_teachers import AdminTeachersPage
        from frontend_pyside6.admin_courses import AdminCoursesPage
        from frontend_pyside6.admin_course_plans import CoursePlansPage
        from frontend_pyside6.admin_enrollment_control import EnrollmentControlPage
        from frontend_pyside6.admin_enrollment_stats import EnrollmentStatsPage
        from frontend_pyside6.admin_grade_audit import AdminGradeAuditPage
        from frontend_pyside6.admin_logs import AdminLogsPage
        from frontend_pyside6.teacher_courses import TeacherCoursesPage
        from frontend_pyside6.teacher_grades import TeacherGradesPage
        from frontend_pyside6.teacher_grade_modify import TeacherGradeModifyPage
        from frontend_pyside6.teacher_stats import TeacherStatsPage
        from frontend_pyside6.student_enroll import StudentEnrollPage
        from frontend_pyside6.student_my_courses import StudentMyCoursesPage
        from frontend_pyside6.student_grades import StudentGradesPage
        from frontend_pyside6.student_stats import StudentStatsPage

        if self._role == "admin":
            self._add_page("学生管理", AdminStudentsPage(self))
            self._add_page("教师管理", AdminTeachersPage(self))
            self._add_page("课程信息", AdminCoursesPage(self))
            self._add_page("开课计划", CoursePlansPage(self))
            self._add_page("时段控制", EnrollmentControlPage(self))
            self._add_page("选课统计", EnrollmentStatsPage(self))
            self._add_page("成绩审核", AdminGradeAuditPage(self))
            self._add_page("操作日志", AdminLogsPage(self))
        elif self._role == "teacher":
            self._add_page("任课信息", TeacherCoursesPage(self))
            self._add_page("成绩录入", TeacherGradesPage(self))
            self._add_page("成绩修改申请", TeacherGradeModifyPage(self))
            self._add_page("统计分析", TeacherStatsPage(self))
        elif self._role == "student":
            self._add_page("选课中心", StudentEnrollPage(self))
            self._add_page("已选课程", StudentMyCoursesPage(self))
            self._add_page("成绩查询", StudentGradesPage(self))
            self._add_page("学业统计", StudentStatsPage(self))

    def _add_page(self, name, widget):
        self._pages[name] = widget
        self._stack.addWidget(widget)

    def _on_sidebar_changed(self, current, previous=None):
        if current is None:
            return
        name = current.data(Qt.UserRole)
        if name and name in self._pages:
            widget = self._pages[name]
            self._stack.setCurrentWidget(widget)
            if hasattr(widget, "load_data"):
                widget.load_data()

    def closeEvent(self, event):
        try:
            self._auth.logout(self._user_id)
        except Exception:
            pass
        super().closeEvent(event)
