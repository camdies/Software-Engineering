"""Admin operation log viewer — filters, table, pagination."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QComboBox, QPushButton, QTableWidget,
                                QTableWidgetItem, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.controllers.admin_controller import AdminController

STYLE = """
QLineEdit, QComboBox {
    padding: 6px 10px;
    border: 1px solid #bdbdbd;
    border-radius: 4px;
    font-size: 13px;
    background: white;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #2196f3;
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
"""


class AdminLogsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._controller = AdminController()
        self._page = 1
        self._page_size = 50
        self._total = 0
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("操作日志")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1565c0;")
        layout.addWidget(title)

        # Filter bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        search_layout.addWidget(QLabel("用户ID:"))
        self._search_user = QLineEdit()
        self._search_user.setPlaceholderText("按用户ID搜索")
        self._search_user.setMaximumWidth(150)
        self._search_user.returnPressed.connect(self.load_data)
        search_layout.addWidget(self._search_user)

        search_layout.addWidget(QLabel("类型:"))
        self._search_type = QComboBox()
        self._search_type.addItems(["全部", "登录", "选课", "成绩", "系统"])
        self._search_type.setMaximumWidth(120)
        search_layout.addWidget(self._search_type)

        search_btn = QPushButton("查询")
        search_btn.setObjectName("primaryBtn")
        search_btn.clicked.connect(self.load_data)
        search_layout.addWidget(search_btn)

        reset_btn = QPushButton("重置")
        reset_btn.setObjectName("secondaryBtn")
        reset_btn.clicked.connect(self._reset_search)
        search_layout.addWidget(reset_btn)
        search_layout.addStretch()
        layout.addLayout(search_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "时间", "用户", "类型", "操作", "结果", "IP"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
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

    # ------------------------------------------------------------------ #
    #  Data loading
    # ------------------------------------------------------------------ #

    def load_data(self):
        user_id = self._search_user.text().strip() or None
        log_type = self._search_type.currentText().strip()
        if log_type == "全部":
            log_type = None
        result = self._controller.get_logs(
            page=self._page, page_size=self._page_size,
            user_id=user_id, log_type=log_type)
        self._total = result.get("total", 0)
        data = result.get("data", [])
        self._populate_table(data)
        total_pages = max(1, (self._total + self._page_size - 1) // self._page_size)
        self._page_label.setText(f"第 {self._page} 页 / 共 {total_pages} 页")
        self._prev_btn.setEnabled(self._page > 1)
        self._next_btn.setEnabled(self._page < total_pages)

    def _populate_table(self, data):
        self._table.setRowCount(len(data))
        for i, log in enumerate(data):
            log_time = log.get("log_time", "")
            if log_time:
                log_time = log_time.replace("T", " ")[:19]
            self._table.setItem(i, 0, QTableWidgetItem(log_time))
            self._table.setItem(i, 1, QTableWidgetItem(log.get("user_id", "")))
            self._table.setItem(i, 2, QTableWidgetItem(log.get("log_type", "")))
            self._table.setItem(i, 3, QTableWidgetItem(log.get("operation", "")))
            result_text = log.get("result", "")
            result_item = QTableWidgetItem(result_text)
            if result_text == "失败":
                result_item.setForeground(Qt.red)
            elif result_text == "成功":
                result_item.setForeground(Qt.darkGreen)
            self._table.setItem(i, 4, result_item)
            self._table.setItem(i, 5, QTableWidgetItem(log.get("ip_address", "") or ""))

    # ------------------------------------------------------------------ #
    #  Search / pagination helpers
    # ------------------------------------------------------------------ #

    def _reset_search(self):
        self._search_user.clear()
        self._search_type.setCurrentIndex(0)
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
