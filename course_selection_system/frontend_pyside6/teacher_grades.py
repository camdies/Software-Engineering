"""Teacher grade entry page — record and batch-import grades."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QComboBox, QPushButton, QTableWidget,
                                QTableWidgetItem, QHeaderView, QMessageBox,
                                QFileDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.controllers.teacher_controller import TeacherController
from backend.controllers.grade_controller import GradeController

STYLE = """
QComboBox {
    padding: 6px 10px;
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    font-size: 13px;
    background: white;
}
QTableWidget {
    gridline-color: #e0e0e0;
    font-size: 13px;
    alternate-background-color: #fafafa;
    background-color: white;
}
QTableWidget::item {
    padding: 6px;
}
QHeaderView::section {
    background-color: #e3f2fd;
    color: #1565c0;
    padding: 8px 4px;
    font-weight: bold;
    border: none;
    border-right: 1px solid #bbdefb;
    border-bottom: 2px solid #1565c0;
}
#primaryBtn {
    background-color: #2196f3;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 7px 18px;
    font-size: 13px;
}
#primaryBtn:hover { background-color: #1976d2; }
#secondaryBtn {
    background-color: #e0e0e0;
    color: #424242;
    border: none;
    border-radius: 4px;
    padding: 7px 18px;
    font-size: 13px;
}
#secondaryBtn:hover { background-color: #bdbdbd; }
#successBtn {
    background-color: #4caf50;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 7px 18px;
    font-size: 13px;
}
#successBtn:hover { background-color: #388e3c; }
"""


class TeacherGradesPage(QWidget):
    def __init__(self, parent=None, teacher_id=""):
        super().__init__(parent)
        self._main = parent
        self._teacher_id = teacher_id or (
            parent._user_id if hasattr(parent, '_user_id') else "")
        self._teacher_ctrl = TeacherController()
        self._grade_ctrl = GradeController()
        self._plans = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("成绩录入")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1565c0;")
        layout.addWidget(title)

        # Course selection
        sel_layout = QHBoxLayout()
        sel_layout.setSpacing(10)
        sel_layout.addWidget(QLabel("选择课程:"))
        self._course_combo = QComboBox()
        self._course_combo.setMinimumWidth(350)
        self._course_combo.currentIndexChanged.connect(self._on_course_changed)
        sel_layout.addWidget(self._course_combo)
        sel_layout.addStretch()

        refresh_plans_btn = QPushButton("刷新课程列表")
        refresh_plans_btn.setObjectName("secondaryBtn")
        refresh_plans_btn.clicked.connect(self._load_plans)
        sel_layout.addWidget(refresh_plans_btn)
        layout.addLayout(sel_layout)

        # Table: 学号, 姓名, 班级, 成绩
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["学号", "姓名", "班级", "成绩"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setStyleSheet(STYLE)
        layout.addWidget(self._table, 1)

        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)

        save_btn = QPushButton("保存成绩")
        save_btn.setObjectName("successBtn")
        save_btn.clicked.connect(self._save_grades)
        action_layout.addWidget(save_btn)

        batch_btn = QPushButton("批量导入 (Excel)")
        batch_btn.setObjectName("primaryBtn")
        batch_btn.clicked.connect(self._batch_import)
        action_layout.addWidget(batch_btn)

        action_layout.addStretch()

        self._result_label = QLabel("")
        self._result_label.setStyleSheet("font-size: 13px; padding: 4px 8px;")
        action_layout.addWidget(self._result_label)
        layout.addLayout(action_layout)

        # Load plans on init
        self._load_plans()

    # ------------------------------------------------------------------ #
    #  Course plan loading
    # ------------------------------------------------------------------ #

    def _load_plans(self):
        self._plans = self._teacher_ctrl.get_teaching_plans(self._teacher_id)
        self._course_combo.clear()
        for p in self._plans:
            label = (f"[{p.get('plan_id')}] {p.get('course_id')} - "
                     f"{p.get('semester', '')} ({p.get('time_slot', '')})")
            self._course_combo.addItem(label, p.get("plan_id"))

    def load_data(self):
        self._load_plans()

    # ------------------------------------------------------------------ #
    #  Student table for selected course
    # ------------------------------------------------------------------ #

    def _on_course_changed(self, idx):
        if idx < 0:
            return
        plan_id = self._course_combo.itemData(idx)
        if plan_id is None:
            return
        students = self._teacher_ctrl.get_enrolled_students(plan_id)
        self._populate_table(students)

    def _populate_table(self, students):
        self._table.setRowCount(len(students))
        for i, s in enumerate(students):
            self._table.setItem(i, 0, QTableWidgetItem(s.get("student_id", "")))
            self._table.setItem(i, 1, QTableWidgetItem(s.get("name", "")))
            self._table.setItem(i, 2, QTableWidgetItem(s.get("class_name", "") or ""))
            score_item = QTableWidgetItem("")
            self._table.setItem(i, 3, score_item)

    # ------------------------------------------------------------------ #
    #  Save grades
    # ------------------------------------------------------------------ #

    def _save_grades(self):
        if self._course_combo.currentIndex() < 0:
            QMessageBox.warning(self, "提示", "请先选择课程")
            return
        plan_id = self._course_combo.itemData(self._course_combo.currentIndex())
        success_count = 0
        fail_count = 0
        for row in range(self._table.rowCount()):
            student_id = self._table.item(row, 0).text()
            score_text = self._table.item(row, 3).text().strip()
            if not score_text:
                continue
            try:
                score = int(score_text)
            except ValueError:
                QMessageBox.warning(self, "格式错误",
                    f"第{row + 1}行 {student_id} 的成绩格式不正确: {score_text}")
                fail_count += 1
                continue
            result = self._grade_ctrl.record_grade(
                self._teacher_id, student_id, plan_id, score)
            if result.get("success"):
                success_count += 1
            else:
                fail_count += 1
        self._result_label.setText(
            f"录入完成: 成功 {success_count} 条, 失败 {fail_count} 条")
        self._result_label.setStyleSheet(
            f"font-size: 13px; padding: 4px 8px; "
            f"color: {'#4caf50' if fail_count == 0 else '#f44336'};")

    # ------------------------------------------------------------------ #
    #  Batch import
    # ------------------------------------------------------------------ #

    def _batch_import(self):
        if self._course_combo.currentIndex() < 0:
            QMessageBox.warning(self, "提示", "请先选择课程")
            return
        plan_id = self._course_combo.itemData(self._course_combo.currentIndex())
        path, _ = QFileDialog.getOpenFileName(
            self, "选择成绩文件", "", "Excel Files (*.xlsx)")
        if not path:
            return
        result = self._grade_ctrl.batch_record_grade(
            self._teacher_id, plan_id, path)
        msg = (f"批量导入完成:\n成功: {result.get('success_count', 0)} 条\n"
               f"失败: {result.get('fail_count', 0)} 条")
        fail_list = result.get("fail_list", [])
        if fail_list:
            details = "\n".join(
                f"  行{f.get('row', '?')} {f.get('student_id', '?')}: "
                f"{f.get('reason', '')}"
                for f in fail_list[:10])
            if len(fail_list) > 10:
                details += f"\n  ... 共 {len(fail_list)} 条失败"
            msg += f"\n\n失败详情:\n{details}"
        QMessageBox.information(self, "批量导入结果", msg)
        # Refresh student list
        self._on_course_changed(self._course_combo.currentIndex())
