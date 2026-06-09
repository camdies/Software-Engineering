"""Student my enrolled courses page."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QTableWidget, QTableWidgetItem,
                                QHeaderView, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.controllers.student_controller import StudentController
from backend.controllers.enrollment_controller import EnrollmentController

STYLE = """
QTableWidget { gridline-color: #e0e0e0; font-size: 13px; alternate-background-color: #fafafa; background-color: white; }
QTableWidget::item { padding: 6px; }
QHeaderView::section { background-color: #e3f2fd; color: #1565c0; padding: 8px 4px; font-weight: bold; border: none; border-right: 1px solid #bbdefb; border-bottom: 2px solid #1565c0; }
#primaryBtn { background-color: #2196f3; color: white; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#primaryBtn:hover { background-color: #1976d2; }
#dangerBtn { background-color: #f44336; color: white; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#dangerBtn:hover { background-color: #d32f2f; }
"""


class StudentMyCoursesPage(QWidget):
    def __init__(self, parent=None, student_id=""):
        super().__init__(parent)
        self._main = parent
        self._student_id = student_id or (
            parent._user_id if hasattr(parent, '_user_id') else "")
        self._student_ctrl = StudentController()
        self._enroll_ctrl = EnrollmentController()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("已选课程")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1565c0;")
        layout.addWidget(title)

        # Refresh bar
        top_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新")
        refresh_btn.setObjectName("primaryBtn")
        refresh_btn.clicked.connect(self.load_data)
        top_layout.addWidget(refresh_btn)
        top_layout.addStretch()

        self._count_label = QLabel("")
        self._count_label.setStyleSheet("font-size: 13px; color: #616161;")
        top_layout.addWidget(self._count_label)
        layout.addLayout(top_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "课程代码", "课程名称", "学分", "上课时间", "选课时间", "操作"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setStyleSheet(STYLE)
        layout.addWidget(self._table, 1)

    def load_data(self):
        courses = self._student_ctrl.get_my_courses(self._student_id)
        self._populate_table(courses)
        self._count_label.setText(f"共 {len(courses)} 门课程")

    def _populate_table(self, courses):
        self._table.setRowCount(len(courses))
        for i, c in enumerate(courses):
            self._table.setItem(i, 0, QTableWidgetItem(c.get("course_id", "")))
            self._table.setItem(i, 1, QTableWidgetItem(c.get("course_name", "")))
            credit = c.get("credit")
            self._table.setItem(i, 2, QTableWidgetItem(str(credit) if credit else ""))
            self._table.setItem(i, 3, QTableWidgetItem(c.get("time_slot", "") or ""))
            enroll_time = c.get("enroll_time", "")
            if enroll_time:
                # Shorten the ISO format
                enroll_time = enroll_time.replace("T", " ")[:19]
            self._table.setItem(i, 4, QTableWidgetItem(enroll_time))

            plan_id = c.get("plan_id")
            drop_btn = QPushButton("退课")
            drop_btn.setObjectName("dangerBtn")
            drop_btn.clicked.connect(lambda checked, pid=plan_id: self._drop(pid))
            self._table.setCellWidget(i, 5, drop_btn)

    def _drop(self, plan_id):
        reply = QMessageBox.question(self, "确认退课",
            f"确定要退选该课程吗？(计划ID: {plan_id})\n\n退课后不可恢复。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        result = self._enroll_ctrl.drop_course(self._student_id, plan_id)
        if result.get("success"):
            QMessageBox.information(self, "成功", result.get("message", "退课成功！"))
            self.load_data()
        else:
            QMessageBox.warning(self, "退课失败", result.get("message", "退课失败"))
