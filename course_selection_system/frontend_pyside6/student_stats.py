"""Student academic statistics page."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QTableWidget, QTableWidgetItem,
                                QHeaderView, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.controllers.stats_controller import StatsController

STYLE = """
QTableWidget { gridline-color: #e0e0e0; font-size: 13px; alternate-background-color: #fafafa; background-color: white; }
QTableWidget::item { padding: 6px; }
QHeaderView::section { background-color: #e3f2fd; color: #1565c0; padding: 8px 4px; font-weight: bold; border: none; border-right: 1px solid #bbdefb; border-bottom: 2px solid #1565c0; }
#primaryBtn { background-color: #2196f3; color: white; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#primaryBtn:hover { background-color: #1976d2; }
#secondaryBtn { background-color: #e0e0e0; color: #424242; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#secondaryBtn:hover { background-color: #bdbdbd; }
"""


class StudentStatsPage(QWidget):
    def __init__(self, parent=None, student_id=""):
        super().__init__(parent)
        self._main = parent
        self._student_id = student_id or (
            parent._user_id if hasattr(parent, '_user_id') else "")
        self._stats_ctrl = StatsController()
        self._current_stats = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("学业统计")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1565c0;")
        layout.addWidget(title)

        # Top bar
        top_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新统计")
        refresh_btn.setObjectName("primaryBtn")
        refresh_btn.clicked.connect(self.load_data)
        top_layout.addWidget(refresh_btn)

        export_btn = QPushButton("导出Excel")
        export_btn.setObjectName("secondaryBtn")
        export_btn.clicked.connect(self._export)
        top_layout.addWidget(export_btn)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Summary cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)

        self._credits_label = QLabel("已修学分\n0.0")
        self._credits_label.setFont(QFont("Microsoft YaHei", 12))
        self._credits_label.setStyleSheet(
            "QLabel { background: #e3f2fd; color: #1565c0; padding: 16px 24px; "
            "border-radius: 8px; font-weight: bold; }")
        self._credits_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self._credits_label)

        self._gpa_label = QLabel("累计GPA\n0.00")
        self._gpa_label.setFont(QFont("Microsoft YaHei", 12))
        self._gpa_label.setStyleSheet(
            "QLabel { background: #e8f5e9; color: #2e7d32; padding: 16px 24px; "
            "border-radius: 8px; font-weight: bold; }")
        self._gpa_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self._gpa_label)

        self._failed_label = QLabel("未通过课程\n0 门")
        self._failed_label.setFont(QFont("Microsoft YaHei", 12))
        self._failed_label.setStyleSheet(
            "QLabel { background: #ffebee; color: #c62828; padding: 16px 24px; "
            "border-radius: 8px; font-weight: bold; }")
        self._failed_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self._failed_label)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Failed courses table
        failed_title = QLabel("未通过课程详情")
        failed_title.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
        failed_title.setStyleSheet("color: #c62828; padding-top: 8px;")
        layout.addWidget(failed_title)

        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["课程名称", "成绩", "学期"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setStyleSheet(STYLE)
        layout.addWidget(self._table, 1)

    def load_data(self):
        stats = self._stats_ctrl.get_academic_stats(self._student_id)
        self._current_stats = stats

        total_credits = stats.get("total_credits", 0)
        cumulative_gpa = stats.get("cumulative_gpa", 0)
        failed = stats.get("failed_courses", [])

        self._credits_label.setText(f"已修学分\n{total_credits}")
        self._gpa_label.setText(f"累计GPA\n{cumulative_gpa}")
        self._failed_label.setText(f"未通过课程\n{len(failed)} 门")

        self._table.setRowCount(len(failed))
        for i, f in enumerate(failed):
            self._table.setItem(i, 0, QTableWidgetItem(f.get("course_name", "")))
            score = f.get("score")
            score_item = QTableWidgetItem(str(score) if score is not None else "")
            score_item.setForeground(Qt.red)
            self._table.setItem(i, 1, score_item)
            self._table.setItem(i, 2, QTableWidgetItem(f.get("semester", "") or ""))

    def _export(self):
        if not self._current_stats:
            QMessageBox.warning(self, "提示", "请先刷新统计数据")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出Excel", "academic_stats.xlsx",
                                               "Excel Files (*.xlsx)")
        if not path:
            return
        self._stats_ctrl.export_stats_to_excel(self._current_stats, path)
        QMessageBox.information(self, "成功", f"已导出到 {path}")
