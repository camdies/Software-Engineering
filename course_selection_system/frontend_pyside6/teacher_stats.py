"""Teacher statistics page — class performance summary and rank list."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QComboBox, QPushButton, QTableWidget,
                                QTableWidgetItem, QHeaderView, QMessageBox,
                                QFileDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.controllers.teacher_controller import TeacherController
from backend.controllers.stats_controller import StatsController

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
"""

STAT_LABEL_STYLE = (
    "font-size: 14px; color: #424242; padding: 6px 16px; "
    "background: #e3f2fd; border-radius: 6px;"
)


class TeacherStatsPage(QWidget):
    def __init__(self, parent=None, teacher_id=""):
        super().__init__(parent)
        self._main = parent
        self._teacher_id = teacher_id or (
            parent._user_id if hasattr(parent, '_user_id') else "")
        self._teacher_ctrl = TeacherController()
        self._stats_ctrl = StatsController()
        self._plans = []
        self._current_stats = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("统计分析")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1565c0;")
        layout.addWidget(title)

        # Course selection
        sel_layout = QHBoxLayout()
        sel_layout.setSpacing(10)
        sel_layout.addWidget(QLabel("选择课程:"))
        self._plan_combo = QComboBox()
        self._plan_combo.setMinimumWidth(350)
        sel_layout.addWidget(self._plan_combo)

        load_btn = QPushButton("加载数据")
        load_btn.setObjectName("primaryBtn")
        load_btn.clicked.connect(self.load_stats)
        sel_layout.addWidget(load_btn)

        export_btn = QPushButton("导出Excel")
        export_btn.setObjectName("secondaryBtn")
        export_btn.clicked.connect(self._export)
        sel_layout.addWidget(export_btn)
        sel_layout.addStretch()
        layout.addLayout(sel_layout)

        # Summary stats
        stats_wrap = QHBoxLayout()
        stats_wrap.setSpacing(16)

        self._avg_label = QLabel("平均分: -")
        self._avg_label.setStyleSheet(STAT_LABEL_STYLE)
        stats_wrap.addWidget(self._avg_label)

        self._max_label = QLabel("最高分: -")
        self._max_label.setStyleSheet(STAT_LABEL_STYLE)
        stats_wrap.addWidget(self._max_label)

        self._min_label = QLabel("最低分: -")
        self._min_label.setStyleSheet(STAT_LABEL_STYLE)
        stats_wrap.addWidget(self._min_label)

        self._pass_rate_label = QLabel("及格率: -")
        self._pass_rate_label.setStyleSheet(STAT_LABEL_STYLE)
        stats_wrap.addWidget(self._pass_rate_label)

        stats_wrap.addStretch()
        layout.addLayout(stats_wrap)

        # Rank table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["排名", "学号", "姓名", "成绩"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setStyleSheet(STYLE)
        layout.addWidget(self._table, 1)

        # Load plans
        self._load_plans()

    # ------------------------------------------------------------------ #
    #  Plan loading
    # ------------------------------------------------------------------ #

    def _load_plans(self):
        self._plans = self._teacher_ctrl.get_teaching_plans(self._teacher_id)
        self._plan_combo.clear()
        for p in self._plans:
            label = f"[{p.get('plan_id')}] {p.get('course_id')} - {p.get('semester', '')}"
            self._plan_combo.addItem(label, p.get("plan_id"))

    def load_data(self):
        self._load_plans()

    # ------------------------------------------------------------------ #
    #  Stats loading
    # ------------------------------------------------------------------ #

    def load_stats(self):
        if self._plan_combo.currentIndex() < 0:
            QMessageBox.warning(self, "提示", "请先选择课程")
            return
        plan_id = self._plan_combo.itemData(self._plan_combo.currentIndex())
        stats = self._stats_ctrl.get_class_stats(self._teacher_id, plan_id)
        self._current_stats = stats

        self._avg_label.setText(f"平均分: {stats.get('avg_score', 0)}")
        self._max_label.setText(f"最高分: {stats.get('max_score', 0)}")
        self._min_label.setText(f"最低分: {stats.get('min_score', 0)}")
        pass_rate = stats.get("pass_rate", 0)
        self._pass_rate_label.setText(f"及格率: {pass_rate * 100:.1f}%")

        rank_list = stats.get("rank_list", [])
        self._table.setRowCount(len(rank_list))
        for i, r in enumerate(rank_list):
            self._table.setItem(i, 0, QTableWidgetItem(str(r.get("rank", i + 1))))
            self._table.setItem(i, 1, QTableWidgetItem(r.get("student_id", "")))
            self._table.setItem(i, 2, QTableWidgetItem(r.get("name", "")))
            self._table.setItem(i, 3, QTableWidgetItem(str(r.get("score", ""))))

    # ------------------------------------------------------------------ #
    #  Export
    # ------------------------------------------------------------------ #

    def _export(self):
        if not self._current_stats:
            QMessageBox.warning(self, "提示", "请先加载统计数据")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出Excel", "stats.xlsx", "Excel Files (*.xlsx)")
        if not path:
            return
        success = self._stats_ctrl.export_stats_to_excel(
            self._current_stats, path)
        if success:
            QMessageBox.information(self, "成功", f"已导出到 {path}")
        else:
            QMessageBox.warning(self, "失败", "导出失败，请重试")
