"""Student course selection page."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QComboBox, QPushButton, QTableWidget,
                                QTableWidgetItem, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.controllers.student_controller import StudentController
from backend.controllers.enrollment_controller import EnrollmentController


STYLE = """
QComboBox { padding: 6px 10px; border: 1px solid #bdbdbd; border-radius: 4px; font-size: 13px; background: white; }
QTableWidget { gridline-color: #e0e0e0; font-size: 13px; alternate-background-color: #fafafa; background-color: white; }
QTableWidget::item { padding: 6px; }
QHeaderView::section { background-color: #e3f2fd; color: #1565c0; padding: 8px 4px; font-weight: bold; border: none; border-right: 1px solid #bbdefb; border-bottom: 2px solid #1565c0; }
#primaryBtn { background-color: #2196f3; color: white; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#primaryBtn:hover { background-color: #1976d2; }
#secondaryBtn { background-color: #e0e0e0; color: #424242; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#secondaryBtn:hover { background-color: #bdbdbd; }
#successBtn { background-color: #4caf50; color: white; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#successBtn:hover { background-color: #388e3c; }
"""


class StudentEnrollPage(QWidget):
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

        title = QLabel("选课中心")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1565c0;")
        layout.addWidget(title)

        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        filter_layout.addWidget(QLabel("学期:"))
        self._semester = QComboBox()
        self._semester.setEditable(True)
        self._semester.addItems(["全部", "2026-2027-1", "2026-2027-2", "2027-2028-1"])
        self._semester.setMinimumWidth(200)
        filter_layout.addWidget(self._semester)

        search_btn = QPushButton("查询可选课程")
        search_btn.setObjectName("primaryBtn")
        search_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(search_btn)
        filter_layout.addStretch()

        self._hint_label = QLabel("")
        self._hint_label.setStyleSheet("font-size: 13px; color: #616161;")
        filter_layout.addWidget(self._hint_label)
        layout.addLayout(filter_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "代码", "名称", "学分", "教师", "时间", "地点", "余量/容量", "操作"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setStyleSheet(STYLE)
        layout.addWidget(self._table, 1)

    def load_data(self):
        semester = self._semester.currentText().strip()
        if semester == "全部":
            semester = None
        courses = self._student_ctrl.get_available_courses(semester)
        self._populate_table(courses)
        self._hint_label.setText(f"共 {len(courses)} 门可选课程")

    def _populate_table(self, courses):
        self._table.setRowCount(len(courses))
        for i, c in enumerate(courses):
            self._table.setItem(i, 0, QTableWidgetItem(c.get("course_id", "")))
            self._table.setItem(i, 1, QTableWidgetItem(c.get("course_name", "")))
            credit = c.get("credit")
            self._table.setItem(i, 2, QTableWidgetItem(str(credit) if credit else ""))
            self._table.setItem(i, 3, QTableWidgetItem(c.get("teacher_id", "")))
            self._table.setItem(i, 4, QTableWidgetItem(c.get("time_slot", "") or ""))
            self._table.setItem(i, 5, QTableWidgetItem(c.get("location", "") or ""))
            available = c.get("available", 0)
            capacity = c.get("capacity", 0)
            self._table.setItem(i, 6, QTableWidgetItem(f"{available}/{capacity}"))

            # Enroll button
            plan_id = c.get("plan_id")
            enroll_btn = QPushButton("选课")
            enroll_btn.setObjectName("successBtn")
            enroll_btn.setProperty("plan_id", plan_id)
            enroll_btn.clicked.connect(lambda checked, pid=plan_id: self._enroll(pid))
            self._table.setCellWidget(i, 7, enroll_btn)

    def _enroll(self, plan_id):
        reply = QMessageBox.question(self, "确认选课",
            f"确定要选择该课程吗？(计划ID: {plan_id})",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        result = self._enroll_ctrl.select_course(self._student_id, plan_id)
        if result.get("success"):
            QMessageBox.information(self, "成功", result.get("message", "选课成功！"))
            self.load_data()
        else:
            QMessageBox.warning(self, "选课失败", result.get("message", "选课失败"))
