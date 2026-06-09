"""Teacher teaching info page - shows the teacher's course plans."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QComboBox, QPushButton, QTableWidget,
                                QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.controllers.teacher_controller import TeacherController

STYLE = """
QComboBox { padding: 6px 10px; border: 1px solid #bdbdbd; border-radius: 4px; font-size: 13px; background: white; }
QTableWidget { gridline-color: #e0e0e0; font-size: 13px; alternate-background-color: #fafafa; background-color: white; }
QTableWidget::item { padding: 6px; }
QHeaderView::section { background-color: #e3f2fd; color: #1565c0; padding: 8px 4px; font-weight: bold; border: none; border-right: 1px solid #bbdefb; border-bottom: 2px solid #1565c0; }
#primaryBtn { background-color: #2196f3; color: white; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#primaryBtn:hover { background-color: #1976d2; }
"""


class TeacherCoursesPage(QWidget):
    def __init__(self, parent=None, teacher_id=""):
        super().__init__(parent)
        self._main = parent
        self._controller = TeacherController()
        self._teacher_id = teacher_id or (
            parent._user_id if hasattr(parent, '_user_id') else "")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("我的任课信息")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1565c0;")
        layout.addWidget(title)

        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        filter_layout.addWidget(QLabel("学期:"))
        self._semester = QComboBox()
        self._semester.setEditable(True)
        self._semester.addItems(["全部", "2026-2027-1", "2026-2027-2", "2027-2028-1"])
        self._semester.setMinimumWidth(200)
        filter_layout.addWidget(self._semester)

        search_btn = QPushButton("查询")
        search_btn.setObjectName("primaryBtn")
        search_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(search_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Stats
        self._stats_label = QLabel("")
        self._stats_label.setStyleSheet("font-size: 13px; color: #616161; padding: 4px 0;")
        layout.addWidget(self._stats_label)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "计划ID", "课程代码", "学期", "时间", "地点", "容量", "已选"])
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
        data = self._controller.get_teaching_plans(self._teacher_id, semester)
        self._populate_table(data)
        total_students = sum(p.get("enrolled", 0) or 0 for p in data)
        self._stats_label.setText(f"共 {len(data)} 门课程 | 选课学生总计: {total_students} 人次")

    def _populate_table(self, data):
        self._table.setRowCount(len(data))
        for i, p in enumerate(data):
            self._table.setItem(i, 0, QTableWidgetItem(str(p.get("plan_id", ""))))
            self._table.setItem(i, 1, QTableWidgetItem(p.get("course_id", "")))
            self._table.setItem(i, 2, QTableWidgetItem(p.get("semester", "")))
            self._table.setItem(i, 3, QTableWidgetItem(p.get("time_slot", "") or ""))
            self._table.setItem(i, 4, QTableWidgetItem(p.get("location", "") or ""))
            capacity = p.get("capacity")
            self._table.setItem(i, 5, QTableWidgetItem(str(capacity) if capacity is not None else ""))
            enrolled = p.get("enrolled")
            self._table.setItem(i, 6, QTableWidgetItem(str(enrolled) if enrolled is not None else "0"))
