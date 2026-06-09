"""Admin grade audit page — approve/reject pending grade modifications."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QPushButton, QTableWidget,
                                QTableWidgetItem, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.controllers.grade_controller import GradeController
from backend.models.base import DatabaseManager
from backend.models.grade import Grade
from backend.models.course_plan import CoursePlan
from backend.models.course import Course

STYLE = """
QLineEdit {
    padding: 6px 10px;
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    font-size: 13px;
    background: white;
}
QLineEdit:focus { border: 1px solid #2196f3; }
QTableWidget {
    gridline-color: #e0e0e0;
    font-size: 13px;
    alternate-background-color: #fafafa;
    background-color: white;
}
QTableWidget::item { padding: 6px; }
QHeaderView::section {
    background-color: #e3f2fd;
    color: #1565c0;
    padding: 8px 4px;
    font-weight: bold;
    border: none;
    border-right: 1px solid #bbdefb;
    border-bottom: 2px solid #1565c0;
}
#approveBtn {
    background-color: #4caf50;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 7px 18px;
    font-size: 13px;
}
#approveBtn:hover { background-color: #388e3c; }
#rejectBtn {
    background-color: #f44336;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 7px 18px;
    font-size: 13px;
}
#rejectBtn:hover { background-color: #d32f2f; }
#secondaryBtn {
    background-color: #e0e0e0;
    color: #424242;
    border: none;
    border-radius: 4px;
    padding: 7px 18px;
    font-size: 13px;
}
#secondaryBtn:hover { background-color: #bdbdbd; }
"""


class AdminGradeAuditPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._main = parent
        self._controller = GradeController()
        self._db = DatabaseManager.get_instance()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("成绩审核")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1565c0;")
        layout.addWidget(title)

        # Refresh bar
        refresh_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新列表")
        refresh_btn.setObjectName("secondaryBtn")
        refresh_btn.clicked.connect(self.load_data)
        refresh_layout.addWidget(refresh_btn)

        self._count_label = QLabel("")
        self._count_label.setStyleSheet("font-size: 13px; color: #616161;")
        refresh_layout.addWidget(self._count_label)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)

        # Table: ID, 学号, 计划ID, 原成绩, 修改原因
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "成绩ID", "学号", "课程", "原成绩", "申请新成绩", "原因"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setStyleSheet(STYLE)
        layout.addWidget(self._table, 1)

        # Action area
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        action_layout.addWidget(QLabel("审核意见:"))
        self._comment_edit = QLineEdit()
        self._comment_edit.setPlaceholderText("可选，填写审核意见")
        action_layout.addWidget(self._comment_edit, 1)

        approve_btn = QPushButton("通过")
        approve_btn.setObjectName("approveBtn")
        approve_btn.clicked.connect(lambda: self._audit("approve"))
        action_layout.addWidget(approve_btn)

        reject_btn = QPushButton("驳回")
        reject_btn.setObjectName("rejectBtn")
        reject_btn.clicked.connect(lambda: self._audit("reject"))
        action_layout.addWidget(reject_btn)
        layout.addLayout(action_layout)

    # ------------------------------------------------------------------ #
    #  Data loading
    # ------------------------------------------------------------------ #

    def load_data(self):
        try:
            with self._db.get_session() as session:
                grades = session.query(Grade).filter(Grade.status == "待审核").all()
                data = []
                for g in grades:
                    plan = session.query(CoursePlan).filter_by(plan_id=g.plan_id).first()
                    course = session.query(Course).filter_by(
                        course_id=plan.course_id).first() if plan else None
                    # Extract new score from modify_reason
                    import re
                    new_score = ""
                    if g.modify_reason:
                        m = re.search(r'修改为(\d+)', g.modify_reason)
                        if m:
                            new_score = m.group(1)
                    data.append({
                        "grade_id": g.grade_id,
                        "student_id": g.student_id,
                        "course_name": course.course_name if course else str(g.plan_id),
                        "original_score": g.score,
                        "new_score": new_score,
                        "reason": g.modify_reason or "",
                    })
                self._populate_table(data)
                self._count_label.setText(f"共 {len(data)} 条待审核记录")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载数据失败: {e}")

    def _populate_table(self, data):
        self._table.setRowCount(len(data))
        for i, d in enumerate(data):
            self._table.setItem(i, 0, QTableWidgetItem(str(d["grade_id"])))
            self._table.setItem(i, 1, QTableWidgetItem(d["student_id"]))
            self._table.setItem(i, 2, QTableWidgetItem(d["course_name"]))
            self._table.setItem(i, 3, QTableWidgetItem(str(d["original_score"] or "")))
            self._table.setItem(i, 4, QTableWidgetItem(d["new_score"]))
            self._table.setItem(i, 5, QTableWidgetItem(d["reason"]))

    # ------------------------------------------------------------------ #
    #  Audit actions
    # ------------------------------------------------------------------ #

    def _get_selected_grade_id(self):
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一条记录")
            return None
        return int(self._table.item(row, 0).text())

    def _audit(self, action):
        grade_id = self._get_selected_grade_id()
        if grade_id is None:
            return
        comment = self._comment_edit.text().strip()
        admin_id = self._main._user_id if hasattr(self._main, '_user_id') else "admin"

        action_names = {"approve": "通过", "reject": "驳回"}
        reply = QMessageBox.question(self, "确认操作",
            f"确定要{action_names[action]}该成绩修改申请吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        result = self._controller.audit_grade(admin_id, grade_id, action, comment)
        if result.get("success"):
            QMessageBox.information(self, "成功", result.get("message", "操作成功"))
            self._comment_edit.clear()
            self.load_data()
        else:
            QMessageBox.warning(self, "失败", result.get("message", "操作失败"))
