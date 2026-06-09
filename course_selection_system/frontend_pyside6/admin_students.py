"""Admin student management page - full CRUD with search, pagination, export."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QComboBox, QPushButton, QTableWidget,
                                QTableWidgetItem, QHeaderView, QDialog,
                                QFormLayout, QMessageBox, QFileDialog, QSpacerItem,
                                QSizePolicy)
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
#dangerBtn {
    background-color: #f44336;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 7px 18px;
    font-size: 13px;
}
#dangerBtn:hover { background-color: #d32f2f; }
QComboBox {
    min-width: 120px;
}
"""


class AdminStudentsPage(QWidget):
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

        # Title
        title = QLabel("学生管理")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1565c0;")
        layout.addWidget(title)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        search_layout.addWidget(QLabel("学号:"))
        self._search_id = QLineEdit()
        self._search_id.setPlaceholderText("按学号搜索")
        self._search_id.setMaximumWidth(150)
        self._search_id.returnPressed.connect(self.load_data)
        search_layout.addWidget(self._search_id)

        search_layout.addWidget(QLabel("姓名:"))
        self._search_name = QLineEdit()
        self._search_name.setPlaceholderText("按姓名搜索")
        self._search_name.setMaximumWidth(150)
        self._search_name.returnPressed.connect(self.load_data)
        search_layout.addWidget(self._search_name)

        search_layout.addWidget(QLabel("班级:"))
        self._search_class = QComboBox()
        self._search_class.setEditable(True)
        self._search_class.setMaximumWidth(150)
        search_layout.addWidget(self._search_class)

        search_btn = QPushButton("搜索")
        search_btn.setObjectName("primaryBtn")
        search_btn.clicked.connect(self.load_data)
        search_layout.addWidget(search_btn)

        reset_btn = QPushButton("重置")
        reset_btn.setObjectName("secondaryBtn")
        reset_btn.clicked.connect(self._reset_search)
        search_layout.addWidget(reset_btn)

        search_layout.addStretch()
        layout.addLayout(search_layout)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        add_btn = QPushButton("+ 新增")
        add_btn.setObjectName("primaryBtn")
        add_btn.clicked.connect(self._add_student)
        toolbar.addWidget(add_btn)

        edit_btn = QPushButton("编辑")
        edit_btn.setObjectName("secondaryBtn")
        edit_btn.clicked.connect(self._edit_student)
        toolbar.addWidget(edit_btn)

        del_btn = QPushButton("删除")
        del_btn.setObjectName("dangerBtn")
        del_btn.clicked.connect(self._delete_student)
        toolbar.addWidget(del_btn)

        export_btn = QPushButton("导出Excel")
        export_btn.setObjectName("secondaryBtn")
        export_btn.clicked.connect(self._export)
        toolbar.addWidget(export_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["学号", "姓名", "专业", "班级", "联系方式"])
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

        # Store buttons as list for later (internal reference)
        self._btn_list = [add_btn, edit_btn, del_btn, export_btn, self._prev_btn, self._next_btn]

    def load_data(self):
        sid = self._search_id.text().strip() or None
        sname = self._search_name.text().strip() or None
        cname = self._search_class.currentText().strip() or None
        result = self._controller.get_students(
            page=self._page, page_size=self._page_size,
            student_id=sid, name=sname, class_name=cname)
        self._total = result.get("total", 0)
        data = result.get("data", [])
        self._populate_table(data)
        total_pages = max(1, (self._total + self._page_size - 1) // self._page_size)
        self._page_label.setText(f"第 {self._page} 页 / 共 {total_pages} 页")
        self._prev_btn.setEnabled(self._page > 1)
        self._next_btn.setEnabled(self._page < total_pages)

    def _populate_table(self, data):
        self._table.setRowCount(len(data))
        for i, s in enumerate(data):
            self._table.setItem(i, 0, QTableWidgetItem(s.get("student_id", "")))
            self._table.setItem(i, 1, QTableWidgetItem(s.get("name", "")))
            self._table.setItem(i, 2, QTableWidgetItem(s.get("major", "") or ""))
            self._table.setItem(i, 3, QTableWidgetItem(s.get("class_name", "") or ""))
            self._table.setItem(i, 4, QTableWidgetItem(s.get("contact", "") or ""))

    def _reset_search(self):
        self._search_id.clear()
        self._search_name.clear()
        self._search_class.setCurrentText("")
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

    def _get_selected_id(self):
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一行")
            return None
        return self._table.item(row, 0).text()

    def _add_student(self):
        dlg = StudentDialog(self, mode="add")
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            result = self._controller.create_student(**data)
            if result.get("success"):
                QMessageBox.information(self, "成功", result.get("message", "创建成功"))
                self.load_data()
            else:
                QMessageBox.warning(self, "失败", result.get("message", "创建失败"))

    def _edit_student(self):
        sid = self._get_selected_id()
        if sid is None:
            return
        row = self._table.currentRow()
        existing = {
            "student_id": sid,
            "name": self._table.item(row, 1).text(),
            "major": self._table.item(row, 2).text(),
            "class_name": self._table.item(row, 3).text(),
            "contact": self._table.item(row, 4).text(),
        }
        dlg = StudentDialog(self, mode="edit", data=existing)
        if dlg.exec() == QDialog.Accepted:
            update_data = dlg.get_data()
            update_data.pop("student_id", None)
            result = self._controller.update_student(sid, **update_data)
            if result.get("success"):
                QMessageBox.information(self, "成功", result.get("message", "更新成功"))
                self.load_data()
            else:
                QMessageBox.warning(self, "失败", result.get("message", "更新失败"))

    def _delete_student(self):
        sid = self._get_selected_id()
        if sid is None:
            return
        name = self._table.item(self._table.currentRow(), 1).text()
        reply = QMessageBox.question(self, "确认删除",
            f"确定要删除学生 {name}({sid}) 吗？\n此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            result = self._controller.delete_student(sid)
            if result.get("success"):
                QMessageBox.information(self, "成功", result.get("message", "删除成功"))
                self.load_data()
            else:
                QMessageBox.warning(self, "失败", result.get("message", "删除失败"))

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出Excel", "students.xlsx",
                                               "Excel Files (*.xlsx)")
        if not path:
            return
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "学生列表"
        headers = ["学号", "姓名", "专业", "班级", "联系方式"]
        ws.append(headers)
        for row in range(self._table.rowCount()):
            ws.append([self._table.item(row, c).text() if self._table.item(row, c) else ""
                       for c in range(self._table.columnCount())])
        wb.save(path)
        QMessageBox.information(self, "成功", f"已导出到 {path}")


class StudentDialog(QDialog):
    def __init__(self, parent, mode="add", data=None):
        super().__init__(parent)
        self._mode = mode
        self.setWindowTitle("新增学生" if mode == "add" else "编辑学生")
        self.setFixedSize(400, 350)
        self._init_ui(data or {})

    def _init_ui(self, data):
        layout = QFormLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        style = "QLineEdit { padding: 6px 10px; border: 1px solid #bdbdbd; border-radius: 4px; }"

        self._id_edit = QLineEdit()
        self._id_edit.setText(data.get("student_id", ""))
        self._id_edit.setStyleSheet(style)
        if self._mode == "edit":
            self._id_edit.setEnabled(False)
        layout.addRow("学号:", self._id_edit)

        self._name_edit = QLineEdit()
        self._name_edit.setText(data.get("name", ""))
        self._name_edit.setStyleSheet(style)
        layout.addRow("姓名:", self._name_edit)

        self._major_edit = QLineEdit()
        self._major_edit.setText(data.get("major", ""))
        self._major_edit.setStyleSheet(style)
        layout.addRow("专业:", self._major_edit)

        self._class_edit = QLineEdit()
        self._class_edit.setText(data.get("class_name", ""))
        self._class_edit.setStyleSheet(style)
        layout.addRow("班级:", self._class_edit)

        self._contact_edit = QLineEdit()
        self._contact_edit.setText(data.get("contact", ""))
        self._contact_edit.setStyleSheet(style)
        layout.addRow("联系方式:", self._contact_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(
            "QPushButton { background: #2196f3; color: white; border: none; "
            "border-radius: 4px; padding: 8px 24px; } QPushButton:hover { background: #1976d2; }")
        save_btn.clicked.connect(self._validate_and_accept)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(
            "QPushButton { background: #e0e0e0; border: none; border-radius: 4px; "
            "padding: 8px 24px; } QPushButton:hover { background: #bdbdbd; }")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def _validate_and_accept(self):
        valid = True
        fields = [
            (self._id_edit, bool(self._id_edit.text().strip())),
            (self._name_edit, bool(self._name_edit.text().strip())),
        ]
        for field, ok in fields:
            if not ok:
                field.setStyleSheet(
                    "QLineEdit { padding: 6px 10px; border: 2px solid #f44336; border-radius: 4px; }")
                valid = False
            else:
                field.setStyleSheet(
                    "QLineEdit { padding: 6px 10px; border: 1px solid #bdbdbd; border-radius: 4px; }")
        if valid:
            self.accept()

    def get_data(self):
        return {
            "student_id": self._id_edit.text().strip(),
            "name": self._name_edit.text().strip(),
            "major": self._major_edit.text().strip() or None,
            "class_name": self._class_edit.text().strip() or None,
            "contact": self._contact_edit.text().strip() or None,
        }
