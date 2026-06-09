"""Admin enrollment statistics page."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QComboBox, QPushButton, QTableWidget,
                                QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.models.base import DatabaseManager
from backend.models.course_plan import CoursePlan
from backend.models.enrollment import Enrollment
from backend.models.student import Student
from backend.models.course import Course

STYLE = """
QComboBox { padding: 6px 10px; border: 1px solid #bdbdbd; border-radius: 4px; font-size: 13px; background: white; }
QTableWidget { gridline-color: #e0e0e0; font-size: 13px; alternate-background-color: #fafafa; background-color: white; }
QTableWidget::item { padding: 6px; }
QHeaderView::section { background-color: #e3f2fd; color: #1565c0; padding: 8px 4px; font-weight: bold; border: none; border-right: 1px solid #bbdefb; border-bottom: 2px solid #1565c0; }
#primaryBtn { background-color: #2196f3; color: white; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#primaryBtn:hover { background-color: #1976d2; }
#secondaryBtn { background-color: #e0e0e0; color: #424242; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#secondaryBtn:hover { background-color: #bdbdbd; }
QLabel.stat { font-size: 14px; color: #424242; padding: 4px 16px; }
"""


class EnrollmentStatsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = DatabaseManager.get_instance()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("选课统计")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1565c0;")
        layout.addWidget(title)

        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        filter_layout.addWidget(QLabel("学期:"))
        self._semester = QComboBox()
        self._semester.setEditable(True)
        self._semester.addItems(["2026-2027-1", "2026-2027-2", "2027-2028-1"])
        self._semester.setMinimumWidth(200)
        filter_layout.addWidget(self._semester)

        self._course_plan = QComboBox()
        self._course_plan.setMinimumWidth(250)
        self._course_plan.setPlaceholderText("选择开课计划...")
        filter_layout.addWidget(self._course_plan)

        search_btn = QPushButton("查询")
        search_btn.setObjectName("primaryBtn")
        search_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(search_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Summary stats
        stats_layout = QHBoxLayout()
        self._total_plans = QLabel("开课数: -")
        self._total_plans.setObjectName("stat")
        self._total_plans.setProperty("class", "stat")
        self._total_plans.setStyleSheet("QLabel { font-size: 14px; color: #424242; padding: 4px 16px; }")

        self._total_enrolled = QLabel("选课人次: -")
        self._total_enrolled.setStyleSheet("QLabel { font-size: 14px; color: #424242; padding: 4px 16px; }")

        self._avg_fill = QLabel("平均满座率: -")
        self._avg_fill.setStyleSheet("QLabel { font-size: 14px; color: #424242; padding: 4px 16px; }")

        stats_layout.addWidget(self._total_plans)
        stats_layout.addWidget(self._total_enrolled)
        stats_layout.addWidget(self._avg_fill)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "计划ID", "课程名称", "教师工号", "学期", "容量", "已选", "满座率"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setStyleSheet(STYLE)
        layout.addWidget(self._table, 1)

        # Connect semester change to reload plans
        self._semester.currentTextChanged.connect(self._load_plans)

    def _load_plans(self):
        semester = self._semester.currentText().strip()
        self._course_plan.clear()
        if not semester:
            return
        try:
            with self._db.get_session() as session:
                plans = session.query(CoursePlan).filter(
                    CoursePlan.semester == semester).all()
                plan_map = {}
                for p in plans:
                    course = session.query(Course).filter_by(course_id=p.course_id).first()
                    label = f"[{p.plan_id}] {course.course_name if course else p.course_id} ({p.time_slot or ''})"
                    self._course_plan.addItem(label, p.plan_id)
                    plan_map[p.plan_id] = label
        except Exception:
            pass

    def load_data(self):
        semester = self._semester.currentText().strip()
        if not semester:
            return
        try:
            with self._db.get_session() as session:
                plans = session.query(CoursePlan).filter(
                    CoursePlan.semester == semester).all()
                data = []
                total_capacity = 0
                total_enrolled = 0
                for p in plans:
                    course = session.query(Course).filter_by(course_id=p.course_id).first()
                    capacity = p.capacity or 0
                    enrolled = p.enrolled or 0
                    fill_rate = f"{enrolled / capacity * 100:.1f}%" if capacity > 0 else "N/A"
                    data.append({
                        "plan_id": p.plan_id,
                        "course_name": course.course_name if course else p.course_id,
                        "teacher_id": p.teacher_id,
                        "semester": p.semester,
                        "capacity": capacity,
                        "enrolled": enrolled,
                        "fill_rate": fill_rate,
                    })
                    total_capacity += capacity
                    total_enrolled += enrolled

                self._populate_table(data)
                self._total_plans.setText(f"开课数: {len(data)}")
                self._total_enrolled.setText(f"选课人次: {total_enrolled}")
                avg = f"{total_enrolled / total_capacity * 100:.1f}%" if total_capacity > 0 else "N/A"
                self._avg_fill.setText(f"平均满座率: {avg}")
        except Exception as e:
            pass

    def _populate_table(self, data):
        self._table.setRowCount(len(data))
        for i, d in enumerate(data):
            self._table.setItem(i, 0, QTableWidgetItem(str(d["plan_id"])))
            self._table.setItem(i, 1, QTableWidgetItem(d["course_name"]))
            self._table.setItem(i, 2, QTableWidgetItem(d["teacher_id"]))
            self._table.setItem(i, 3, QTableWidgetItem(d["semester"]))
            self._table.setItem(i, 4, QTableWidgetItem(str(d["capacity"])))
            self._table.setItem(i, 5, QTableWidgetItem(str(d["enrolled"])))
            self._table.setItem(i, 6, QTableWidgetItem(d["fill_rate"]))
