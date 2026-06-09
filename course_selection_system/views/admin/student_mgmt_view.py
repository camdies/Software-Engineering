"""
views/admin/student_mgmt_view.py - 学生信息管理界面

管理员管理学生信息的视图，包含搜索、增删改查、分页、导出功能。
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QMessageBox,
    QSpacerItem,
    QSizePolicy,
    QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from utils.validator import validate_student_id, validate_contact, \
    validate_not_empty
from utils.log_util import get_logger

logger = get_logger("student_mgmt_view")


class StudentMgmtView(QWidget):
    """学生信息管理界面。

    功能: 搜索、新增、编辑、删除、分页浏览、导出Excel。
    表格列: 学号、姓名、专业、班级、联系方式、操作。
    """

    def __init__(self):
        super().__init__()
        self.current_page = 1
        self.page_size = 20
        self.total_records = 0
        self._init_ui()

    def _init_ui(self):
        """初始化UI布局。"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 标题
        title_label = QLabel("学生信息管理")
        title_label.setFont(QFont("微软雅黑", 16, QFont.Bold))
        title_label.setObjectName("pageTitle")
        main_layout.addWidget(title_label)

        # 搜索区
        search_frame = QFrame()
        search_frame.setObjectName("searchFrame")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(15, 10, 15, 10)

        search_layout.addWidget(QLabel("学号:"))
        self.search_id = QLineEdit()
        self.search_id.setPlaceholderText("输入学号搜索")
        self.search_id.setMinimumWidth(120)
        search_layout.addWidget(self.search_id)

        search_layout.addWidget(QLabel("姓名:"))
        self.search_name = QLineEdit()
        self.search_name.setPlaceholderText("输入姓名搜索")
        self.search_name.setMinimumWidth(120)
        search_layout.addWidget(self.search_name)

        search_layout.addWidget(QLabel("班级:"))
        self.search_class = QComboBox()
        self.search_class.setMinimumWidth(120)
        self.search_class.addItem("全部")
        search_layout.addWidget(self.search_class)

        self.search_btn = QPushButton("搜索")
        self.search_btn.setObjectName("primaryBtn")
        self.search_btn.setCursor(Qt.PointingHandCursor)
        search_layout.addWidget(self.search_btn)

        self.reset_btn = QPushButton("重置")
        self.reset_btn.setObjectName("secondaryBtn")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        search_layout.addWidget(self.reset_btn)

        search_layout.addStretch()
        main_layout.addWidget(search_frame)

        # 工具栏
        toolbar_layout = QHBoxLayout()

        self.add_btn = QPushButton("新增学生")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        toolbar_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("编辑学生")
        self.edit_btn.setObjectName("secondaryBtn")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        toolbar_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("删除学生")
        self.delete_btn.setObjectName("dangerBtn")
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        toolbar_layout.addWidget(self.delete_btn)

        self.export_btn = QPushButton("导出Excel")
        self.export_btn.setObjectName("secondaryBtn")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        toolbar_layout.addWidget(self.export_btn)

        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)

        # 数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["学号", "姓名", "专业", "班级", "联系方式", "操作"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setFont(QFont("微软雅黑", 9))
        main_layout.addWidget(self.table)

        # 分页控件
        page_layout = QHBoxLayout()

        self.prev_btn = QPushButton("上一页")
        self.prev_btn.setObjectName("secondaryBtn")
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        page_layout.addWidget(self.prev_btn)

        self.page_label = QLabel("第 1 页")
        self.page_label.setFont(QFont("微软雅黑", 9))
        page_layout.addWidget(self.page_label)

        self.next_btn = QPushButton("下一页")
        self.next_btn.setObjectName("secondaryBtn")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        page_layout.addWidget(self.next_btn)

        page_layout.addStretch()

        page_layout.addWidget(QLabel("每页条数:"))
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["10", "20", "50"])
        self.page_size_combo.setCurrentText("20")
        self.page_size_combo.setMinimumWidth(70)
        page_layout.addWidget(self.page_size_combo)

        main_layout.addLayout(page_layout)

        # 设置样式
        self.setStyleSheet(self._get_stylesheet())

    def _load_data(self):
        """加载表格数据（从数据库分页查询）。

        实际实现需调用 controller 方法加载数据。
        """
        # 占位 — 实际实现调用 controller 方法
        self.table.setRowCount(0)
        self.page_label.setText(f"第 {self.current_page} 页")

    def _on_search(self):
        """搜索按钮事件。"""
        self.current_page = 1
        self._load_data()

    def _on_reset(self):
        """重置搜索条件。"""
        self.search_id.clear()
        self.search_name.clear()
        self.search_class.setCurrentIndex(0)
        self.current_page = 1
        self._load_data()

    def _on_add(self):
        """新增学生按钮事件。"""
        dialog = StudentEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self._load_data()

    def _on_edit(self):
        """编辑学生按钮事件。"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要编辑的学生")
            return
        student_id = self.table.item(current_row, 0).text()
        dialog = StudentEditDialog(self, student_id=student_id)
        if dialog.exec_() == QDialog.Accepted:
            self._load_data()

    def _on_delete(self):
        """删除学生按钮事件 — 弹出二次确认对话框。"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要删除的学生")
            return
        student_id = self.table.item(current_row, 0).text()
        name = self.table.item(current_row, 1).text()

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除学生 {name}({student_id}) 吗？\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            # 调用 controller 执行删除
            self._load_data()

    def _on_export(self):
        """导出Excel按钮事件。"""
        # 调用 utils.export_util 导出
        pass

    def _get_stylesheet(self) -> str:
        """返回学生管理界面的QSS样式表。"""
        return """
            #pageTitle {
                color: #212121;
            }
            #searchFrame {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QLineEdit, QComboBox {
                border: 1px solid #bdbdbd;
                border-radius: 3px;
                padding: 4px 8px;
                background-color: white;
                min-height: 24px;
            }
            QLineEdit:focus {
                border: 1px solid #2196f3;
            }
            #primaryBtn {
                background-color: #2196f3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                min-height: 28px;
            }
            #primaryBtn:hover {
                background-color: #1976d2;
            }
            #secondaryBtn {
                background-color: #e0e0e0;
                color: #424242;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                min-height: 28px;
            }
            #secondaryBtn:hover {
                background-color: #bdbdbd;
            }
            #dangerBtn {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                min-height: 28px;
            }
            #dangerBtn:hover {
                background-color: #d32f2f;
            }
            QTableWidget {
                border: 1px solid #e0e0e0;
                gridline-color: #eeeeee;
                background-color: white;
                alternate-background-color: #fafafa;
            }
            QHeaderView::section {
                background-color: #e3f2fd;
                color: #1565c0;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #2196f3;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #bbdefb;
                color: #212121;
            }
        """


class StudentEditDialog(QDialog):
    """学生信息新增/编辑弹窗。

    包含字段: 学号、姓名、专业、班级、联系方式。
    学号唯一性校验（失焦时实时查询）。
    保存前进行完整校验，错误字段高亮红色边框。
    """

    def __init__(self, parent=None, student_id: str = None):
        super().__init__(parent)
        self.student_id = student_id
        self.is_edit = student_id is not None
        self._init_ui()

    def _init_ui(self):
        """初始化弹窗UI。"""
        self.setWindowTitle("编辑学生信息" if self.is_edit else "新增学生")
        self.setFixedSize(420, 350)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("请输入学号（6-20位字母/数字）")
        if self.is_edit:
            self.id_input.setText(self.student_id)
            self.id_input.setEnabled(False)  # 编辑时学号不可修改
        else:
            # 失焦时进行唯一性校验
            pass  # 实际实现: self.id_input.editingFinished.connect(self._check_unique)
        form_layout.addRow("学号:", self.id_input)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入姓名")
        form_layout.addRow("姓名:", self.name_input)

        self.major_input = QLineEdit()
        self.major_input.setPlaceholderText("请输入专业")
        form_layout.addRow("专业:", self.major_input)

        self.class_input = QLineEdit()
        self.class_input.setPlaceholderText("请输入班级")
        form_layout.addRow("班级:", self.class_input)

        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("请输入联系方式（手机/座机）")
        form_layout.addRow("联系方式:", self.contact_input)

        layout.addLayout(form_layout)
        layout.addSpacing(10)

        # 错误提示标签
        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setStyleSheet("color: #f44336;")
        layout.addWidget(self.error_label)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_save)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Ok).setText("保存")
        button_box.button(QDialogButtonBox.Cancel).setText("取消")
        layout.addWidget(button_box)

    def _on_save(self):
        """保存按钮事件 — 执行完整校验后保存。"""
        # 清除之前的错误样式
        self._clear_error_styles()

        # 非空校验
        for field, name in [
            (self.id_input, "学号"),
            (self.name_input, "姓名"),
        ]:
            valid, err = validate_not_empty(field.text(), name)
            if not valid:
                self._highlight_error(field)
                self.error_label.setText(err)
                return

        # 学号格式校验（仅新增时）
        if not self.is_edit:
            valid, err = validate_student_id(self.id_input.text())
            if not valid:
                self._highlight_error(self.id_input)
                self.error_label.setText(err)
                return

        # 联系方式校验
        contact = self.contact_input.text().strip()
        if contact:
            valid, err = validate_contact(contact)
            if not valid:
                self._highlight_error(self.contact_input)
                self.error_label.setText(err)
                return

        self.accept()

    def _highlight_error(self, widget: QLineEdit):
        """高亮错误字段（红色边框）。

        Args:
            widget: 有错误的输入框控件。
        """
        widget.setStyleSheet("border: 1px solid #f44336;")

    def _clear_error_styles(self):
        """清除所有错误高亮样式。"""
        default = "border: 1px solid #bdbdbd; border-radius: 3px; padding: 4px 8px;"
        for w in [self.id_input, self.name_input, self.major_input,
                  self.class_input, self.contact_input]:
            w.setStyleSheet(default)
