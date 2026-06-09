"""Student grade query page."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QTableWidget, QTableWidgetItem,
                                QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.controllers.student_controller import StudentController

STYLE = """
QTableWidget { gridline-color: #e0e0e0; font-size: 13px; alternate-background-color: #fafafa; background-color: white; }
QTableWidget::item { padding: 6px; }
QHeaderView::section { background-color: #e3f2fd; color: #1565c0; padding: 8px 4px; font-weight: bold; border: none; border-right: 1px solid #bbdefb; border-bottom: 2px solid #1565c0; }
#primaryBtn { background-color: #2196f3; color: white; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#primaryBtn:hover { background-color: #1976d2; }
"""


class StudentGradesPage(QWidget):
    def __init__(self, parent=None, student_id=""):
        super().__init__(parent)
        self._main = parent
        self._student_id = student_id or (
            parent._user_id if hasattr(parent, '_user_id') else "")
        self._student_ctrl = StudentController()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("成绩查询")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1565c0;")
        layout.addWidget(title)

        # Top bar
        top_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新")
        refresh_btn.setObjectName("primaryBtn")
        refresh_btn.clicked.connect(self.load_data)
        top_layout.addWidget(refresh_btn)
        top_layout.addStretch()

        self._gpa_label = QLabel("")
        self._gpa_label.setStyleSheet("font-size: 14px; color: #1565c0; font-weight: bold;")
        top_layout.addWidget(self._gpa_label)
        layout.addLayout(top_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "课程名称", "学分", "成绩", "绩点", "学期", "状态"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setStyleSheet(STYLE)
        layout.addWidget(self._table, 1)

    def load_data(self):
        grades = self._student_ctrl.get_my_grades(self._student_id)
        self._populate_table(grades)

        # Calculate GPA
        if grades:
            total_points = 0.0
            total_credits = 0.0
            for g in grades:
                credit = g.get("credit", 0)
                gpa = g.get("gpa_point", 0) or 0
                score = g.get("score")
                if score is not None and score >= 60:
                    total_points += float(gpa) * float(credit)
                    total_credits += float(credit)
            gpa_val = total_points / total_credits if total_credits > 0 else 0.0
            self._gpa_label.setText(f"加权GPA: {gpa_val:.2f} | 已修学分: {total_credits:.1f}")

    def _populate_table(self, grades):
        self._table.setRowCount(len(grades))
        for i, g in enumerate(grades):
            self._table.setItem(i, 0, QTableWidgetItem(g.get("course_name", "")))
            credit = g.get("credit")
            self._table.setItem(i, 1, QTableWidgetItem(str(credit) if credit else ""))
            score = g.get("score")
            score_item = QTableWidgetItem(str(score) if score is not None else "")
            if score is not None and score < 60:
                score_item.setForeground(Qt.red)
            self._table.setItem(i, 2, score_item)
            gpa_p = g.get("gpa_point")
            self._table.setItem(i, 3, QTableWidgetItem(str(gpa_p) if gpa_p is not None else ""))
            self._table.setItem(i, 4, QTableWidgetItem(g.get("semester", "")))
            status = g.get("status", "")
            status_item = QTableWidgetItem(status or "")
            if status == "待审核":
                status_item.setForeground(Qt.darkYellow)
            elif status == "已更正":
                status_item.setForeground(Qt.darkGreen)
            self._table.setItem(i, 5, status_item)
