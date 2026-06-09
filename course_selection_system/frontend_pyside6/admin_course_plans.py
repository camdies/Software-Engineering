"""Admin course plan management page."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QComboBox, QPushButton, QTableWidget,
                                QTableWidgetItem, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.controllers.admin_controller import AdminController
from backend.models.base import DatabaseManager
from backend.models.course_plan import CoursePlan

STYLE = """
QLineEdit, QComboBox { padding: 6px 10px; border: 1px solid #bdbdbd; border-radius: 4px; font-size: 13px; background: white; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #2196f3; }
QTableWidget { gridline-color: #e0e0e0; font-size: 13px; alternate-background-color: #fafafa; background-color: white; }
QTableWidget::item { padding: 6px; }
QHeaderView::section { background-color: #e3f2fd; color: #1565c0; padding: 8px 4px; font-weight: bold; border: none; border-right: 1px solid #bbdefb; border-bottom: 2px solid #1565c0; }
#primaryBtn { background-color: #2196f3; color: white; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#primaryBtn:hover { background-color: #1976d2; }
#secondaryBtn { background-color: #e0e0e0; color: #424242; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#secondaryBtn:hover { background-color: #bdbdbd; }
#dangerBtn { background-color: #f44336; color: white; border: none; border-radius: 4px; padding: 7px 18px; font-size: 13px; }
#dangerBtn:hover { background-color: #d32f2f; }
"""


class CoursePlansPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._controller = AdminController()
        self._page = 1
        self._page_size = 20
        self._total = 0
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("开课计划管理")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1565c0;")
        layout.addWidget(title)

        # Search
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        search_layout.addWidget(QLabel("学期:"))
        self._search_semester = QComboBox()
        self._search_semester.setEditable(True)
        self._search_semester.addItems(["2026-2027-1", "2026-2027-2", "2027-2028-1"])
        self._search_semester.setMaximumWidth(200)
        search_layout.addWidget(self._search_semester)

        search_btn = QPushButton("搜索")
        search_btn.setObjectName("primaryBtn")
        search_btn.clicked.connect(self.load_data)
        search_layout.addWidget(search_btn)

        reset_btn = QPushButton("重置")
        reset_btn.setObjectName("secondaryBtn")
        reset_btn.clicked.connect(self._reset_search)
        search_layout.addWidget(reset_btn)
        search_layout.addStretch()

        # Toggle status button
        toggle_btn = QPushButton("开课/停课")
        toggle_btn.setObjectName("secondaryBtn")
        toggle_btn.clicked.connect(self._toggle_status)
        search_layout.addWidget(toggle_btn)
        layout.addLayout(search_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(["计划ID", "课程代码", "教师工号", "学期", "时间", "地点", "容量", "已选"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setStyleSheet(STYLE)
        layout.addWidget(self._table, 1)

        # Pagination
        page_layout = QHBoxLayout()
        page_layout.addStretch()
        self._prev_btn = QPushButton("< 上一页")
        self._prev_btn.setObjectName("secondaryBtn")
        self._prev_btn.clicked.connect(self._prev_page)
        page_layout.addWidget(self._prev_btn)
        self._page_label = QLabel("第 1 页 / 共 1 页")
        self._page_label.setStyleSheet("font-size: 13px; color: #616161; padding: 0 12px;")
        page_layout.addWidget(self._page_label)
        self._next_btn = QPushButton("下一页 >")
        self._next_btn.setObjectName("secondaryBtn")
        self._next_btn.clicked.connect(self._next_page)
        page_layout.addWidget(self._next_btn)
        page_layout.addStretch()
        layout.addLayout(page_layout)

    def load_data(self):
        semester = self._search_semester.currentText().strip() or None
        result = self._controller.get_course_plans(page=self._page, page_size=self._page_size, semester=semester)
        self._total = result.get("total", 0)
        data = result.get("data", [])
        self._populate_table(data)
        total_pages = max(1, (self._total + self._page_size - 1) // self._page_size)
        self._page_label.setText(f"第 {self._page} 页 / 共 {total_pages} 页")
        self._prev_btn.setEnabled(self._page > 1)
        self._next_btn.setEnabled(self._page < total_pages)

    def _populate_table(self, data):
        self._table.setRowCount(len(data))
        for i, p in enumerate(data):
            self._table.setItem(i, 0, QTableWidgetItem(str(p.get("plan_id", ""))))
            self._table.setItem(i, 1, QTableWidgetItem(p.get("course_id", "")))
            self._table.setItem(i, 2, QTableWidgetItem(p.get("teacher_id", "")))
            self._table.setItem(i, 3, QTableWidgetItem(p.get("semester", "")))
            self._table.setItem(i, 4, QTableWidgetItem(p.get("time_slot", "") or ""))
            self._table.setItem(i, 5, QTableWidgetItem(p.get("location", "") or ""))
            capacity = p.get("capacity")
            self._table.setItem(i, 6, QTableWidgetItem(str(capacity) if capacity is not None else ""))
            enrolled = p.get("enrolled")
            self._table.setItem(i, 7, QTableWidgetItem(str(enrolled) if enrolled is not None else "0"))

    def _reset_search(self):
        self._search_semester.setCurrentText("")
        self._page = 1
        self.load_data()

    def _prev_page(self):
        if self._page > 1:
            self._page -= 1
            self.load_data()

    def _next_page(self):
        total_pages = max(1, (self._total + self._page_size - 1) // self._page_size)
        if self._page < total_pages:
            self._page += 1
            self.load_data()

    def _toggle_status(self):
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个开课计划")
            return
        plan_id = int(self._table.item(row, 0).text())
        current_status = "开课"  # We need to check
        db = DatabaseManager.get_instance()
        try:
            with db.get_session() as session:
                plan = session.query(CoursePlan).filter_by(plan_id=plan_id).first()
                if plan is None:
                    QMessageBox.warning(self, "失败", "开课计划不存在")
                    return
                current_status = plan.status
                new_status = "停课" if plan.status == "开课" else "开课"
                plan.status = new_status
            QMessageBox.information(self, "成功", f"开课计划状态已切换为: {new_status}")
            self.load_data()
        except Exception as e:
            QMessageBox.warning(self, "失败", f"操作失败: {e}")
