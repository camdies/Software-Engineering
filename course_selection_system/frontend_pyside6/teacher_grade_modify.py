"""Teacher grade modification page - apply for grade changes."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QPushButton, QTableWidget,
                                QTableWidgetItem, QHeaderView, QMessageBox,
                                QSpinBox, QTextEdit)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.controllers.grade_controller import GradeController
from backend.models.base import DatabaseManager
from backend.models.grade import Grade
from backend.models.course_plan import CoursePlan
from backend.models.course import Course

STYLE = """
QLineEdit { padding: 6px 10px; border: 1px solid #bdbdbd; border-radius: 4px; font-size: 13px; background: white; }
QLineEdit:focus { border: 1px solid #2196f3; }
QSpinBox { padding: 6px 10px; border: 1px solid #bdbdbd; border-radius: 4px; font-size: 13px; background: white; }
QTextEdit { padding: 6px 10px; border: 1px solid #bdbdbd; border-radius: 4px; font-size: 13px; background: white; }
QTextEdit:focus { border: 1px solid #2196f3; }
QTableWidget { gridline-color: #e0e0e0; font-size: 13px; alternate-background-color: #fafafa; background-color: white; }
QTableWidget::item { padding: 6px; }
QHeaderView::section { background-color: #e3f2fd; color: #1565c0; padding: 8px 4px; font-weight: bold; border: none; border-right: 1px solid #bbdefb; border-bottom: 2px solid #1565c0; }
#primaryBtn { background-color: #2196f3; color: white; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#primaryBtn:hover { background-color: #1976d2; }
#secondaryBtn { background-color: #e0e0e0; color: #424242; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#secondaryBtn:hover { background-color: #bdbdbd; }
#warnBtn { background-color: #ff9800; color: white; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#warnBtn:hover { background-color: #f57c00; }
"""


class TeacherGradeModifyPage(QWidget):
    def __init__(self, parent=None, teacher_id=""):
        super().__init__(parent)
        self._main = parent
        self._teacher_id = teacher_id or (
            parent._user_id if hasattr(parent, '_user_id') else "")
        self._controller = GradeController()
        self._db = DatabaseManager.get_instance()
        self._selected_grade_id = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("成绩修改申请")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1565c0;")
        layout.addWidget(title)

        # Search
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        search_layout.addWidget(QLabel("学号:"))
        self._search_student = QLineEdit()
        self._search_student.setPlaceholderText("输入学生学号")
        self._search_student.setMaximumWidth(180)
        search_layout.addWidget(self._search_student)

        search_layout.addWidget(QLabel("计划ID:"))
        self._search_plan = QLineEdit()
        self._search_plan.setPlaceholderText("输入开课计划ID")
        self._search_plan.setMaximumWidth(120)
        search_layout.addWidget(self._search_plan)

        search_btn = QPushButton("查询成绩")
        search_btn.setObjectName("primaryBtn")
        search_btn.clicked.connect(self._search_grades)
        search_layout.addWidget(search_btn)
        search_layout.addStretch()
        layout.addLayout(search_layout)

        # Pending modifications table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "成绩ID", "学号", "课程", "当前成绩", "状态", "修改原因"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setStyleSheet(STYLE)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table, 1)

        # Modify form
        form_layout = QHBoxLayout()
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("新成绩:"))
        self._new_score = QSpinBox()
        self._new_score.setRange(0, 100)
        self._new_score.setValue(0)
        self._new_score.setFixedWidth(80)
        form_layout.addWidget(self._new_score)

        form_layout.addWidget(QLabel("修改原因:"))
        self._reason = QTextEdit()
        self._reason.setMaximumHeight(60)
        self._reason.setPlaceholderText("请输入修改原因（必填）")
        form_layout.addWidget(self._reason, 1)

        submit_btn = QPushButton("提交修改申请")
        submit_btn.setObjectName("warnBtn")
        submit_btn.clicked.connect(self._submit_modification)
        form_layout.addWidget(submit_btn)
        layout.addLayout(form_layout)

        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新列表")
        refresh_btn.setObjectName("secondaryBtn")
        refresh_btn.clicked.connect(self._refresh_pending)
        refresh_layout.addWidget(refresh_btn)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)

        self._selected_grade_id = None

    def load_data(self):
        self._refresh_pending()

    def _on_selection_changed(self):
        row = self._table.currentRow()
        if row < 0:
            self._selected_grade_id = None
            return
        self._selected_grade_id = int(self._table.item(row, 0).text())
        current_score = self._table.item(row, 3).text()
        try:
            self._new_score.setValue(int(current_score) if current_score else 0)
        except ValueError:
            self._new_score.setValue(0)

    def _search_grades(self):
        student_id = self._search_student.text().strip()
        plan_id_str = self._search_plan.text().strip()
        if not student_id:
            QMessageBox.warning(self, "提示", "请输入学号")
            return
        try:
            with self._db.get_session() as session:
                q = session.query(Grade).filter(Grade.student_id == student_id)
                if plan_id_str:
                    try:
                        q = q.filter(Grade.plan_id == int(plan_id_str))
                    except ValueError:
                        pass
                # Only show grades from this teacher's plans
                grades = []
                for g in q.all():
                    plan = session.query(CoursePlan).filter_by(plan_id=g.plan_id).first()
                    if plan and plan.teacher_id == self._teacher_id:
                        course = session.query(Course).filter_by(course_id=plan.course_id).first()
                        grades.append({
                            "grade_id": g.grade_id,
                            "student_id": g.student_id,
                            "course_name": course.course_name if course else str(g.plan_id),
                            "score": g.score,
                            "status": g.status,
                            "reason": g.modify_reason or "",
                        })
                self._populate_table(grades)
                if not grades:
                    QMessageBox.information(self, "提示", "未找到相关成绩记录")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"查询失败: {e}")

    def _refresh_pending(self):
        try:
            with self._db.get_session() as session:
                grades = session.query(Grade).join(
                    CoursePlan, Grade.plan_id == CoursePlan.plan_id
                ).filter(
                    CoursePlan.teacher_id == self._teacher_id,
                    Grade.status.in_(["待审核", "已更正"])
                ).all()
                data = []
                for g in grades:
                    plan = session.query(CoursePlan).filter_by(plan_id=g.plan_id).first()
                    course = session.query(Course).filter_by(course_id=plan.course_id).first() if plan else None
                    data.append({
                        "grade_id": g.grade_id,
                        "student_id": g.student_id,
                        "course_name": course.course_name if course else str(g.plan_id),
                        "score": g.score,
                        "status": g.status,
                        "reason": g.modify_reason or "",
                    })
                self._populate_table(data)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"刷新失败: {e}")

    def _populate_table(self, data):
        self._table.setRowCount(len(data))
        for i, d in enumerate(data):
            self._table.setItem(i, 0, QTableWidgetItem(str(d["grade_id"])))
            self._table.setItem(i, 1, QTableWidgetItem(d["student_id"]))
            self._table.setItem(i, 2, QTableWidgetItem(d["course_name"]))
            self._table.setItem(i, 3, QTableWidgetItem(str(d["score"] or "")))
            status_item = QTableWidgetItem(d["status"] or "")
            if d["status"] == "待审核":
                status_item.setForeground(Qt.darkYellow)
            elif d["status"] == "已更正":
                status_item.setForeground(Qt.darkGreen)
            self._table.setItem(i, 4, status_item)
            self._table.setItem(i, 5, QTableWidgetItem(d["reason"]))

    def _submit_modification(self):
        if self._selected_grade_id is None:
            QMessageBox.warning(self, "提示", "请先从上表中选择一条成绩记录")
            return
        reason = self._reason.toPlainText().strip()
        if not reason:
            QMessageBox.warning(self, "提示", "请输入修改原因")
            self._reason.setFocus()
            return
        new_score = self._new_score.value()

        reply = QMessageBox.question(self, "确认提交",
            f"确认申请修改成绩为 {new_score} 分?\n原因: {reason}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        result = self._controller.apply_grade_modify(
            self._teacher_id, self._selected_grade_id, new_score, reason)
        if result.get("success"):
            QMessageBox.information(self, "成功", result.get("message", "申请已提交"))
            self._reason.clear()
            self._refresh_pending()
        else:
            QMessageBox.warning(self, "失败", result.get("message", "操作失败"))
