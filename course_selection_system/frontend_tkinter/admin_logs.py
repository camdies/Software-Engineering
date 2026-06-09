"""
frontend_tkinter/admin_logs.py - Operation Log Viewer.

Provides filtering and paginated viewing of operation logs
via AdminController.get_logs().
"""

import tkinter as tk
from tkinter import ttk, messagebox

from backend.controllers.admin_controller import AdminController

# Colour theme
COLOR_PRIMARY = "#2196F3"
COLOR_PRIMARY_HOVER = "#1976D2"
COLOR_BG = "#FAFAFA"
COLOR_TEXT = "#212121"


class AdminLogsPage(tk.Frame):
    """Operation log viewer page embedded in the admin content area."""

    def __init__(self, master, admin_id):
        """Initialise the log viewer page.

        Args:
            master: Parent widget.
            admin_id (str): The admin user ID.
        """
        super().__init__(master, bg=COLOR_BG)
        self.admin_id = admin_id
        self.controller = AdminController()
        self.current_page = 1
        self.page_size = 50
        self.total_records = 0

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        title_frame = tk.Frame(self, bg=COLOR_BG)
        title_frame.pack(fill=tk.X, padx=16, pady=(12, 8))
        tk.Label(
            title_frame, text="操作日志", font=("微软雅黑", 14, "bold"),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).pack(side=tk.LEFT)

        # Filter bar
        filter_frame = tk.Frame(self, bg=COLOR_BG, height=44)
        filter_frame.pack(fill=tk.X, padx=16, pady=(0, 8))
        filter_frame.pack_propagate(False)

        tk.Label(
            filter_frame, text="用户ID:", font=("微软雅黑", 10), bg=COLOR_BG,
        ).pack(side=tk.LEFT, padx=(0, 4))
        self.entry_user_id = tk.Entry(
            filter_frame, font=("微软雅黑", 10), width=14,
            relief=tk.SOLID, borderwidth=1,
        )
        self.entry_user_id.pack(side=tk.LEFT, padx=(0, 12))

        tk.Label(
            filter_frame, text="类型:", font=("微软雅黑", 10), bg=COLOR_BG,
        ).pack(side=tk.LEFT, padx=(0, 4))
        self.combo_log_type = ttk.Combobox(
            filter_frame, values=["", "登录", "选课", "成绩", "系统"],
            font=("微软雅黑", 10), width=8, state="readonly",
        )
        self.combo_log_type.pack(side=tk.LEFT, padx=(0, 16))

        tk.Button(
            filter_frame, text="搜索", font=("微软雅黑", 10),
            bg=COLOR_PRIMARY, fg="white",
            activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
            relief=tk.FLAT, cursor="hand2",
            command=self._do_search,
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(
            filter_frame, text="重置", font=("微软雅黑", 10),
            bg="#E0E0E0", fg=COLOR_TEXT, relief=tk.FLAT, cursor="hand2",
            command=self._do_reset,
        ).pack(side=tk.LEFT)

        # Treeview
        tree_frame = tk.Frame(self, bg=COLOR_BG)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 6))

        columns = ("log_time", "user_id", "log_type", "operation", "result", "ip_address")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="browse",
        )

        col_headers = {
            "log_time": "时间", "user_id": "用户", "log_type": "类型",
            "operation": "操作", "result": "结果", "ip_address": "IP",
        }
        col_widths = {"log_time": 170, "user_id": 100, "log_type": 60,
                      "operation": 260, "result": 60, "ip_address": 130}

        for col in columns:
            self.tree.heading(col, text=col_headers.get(col, col))
            self.tree.column(col, width=col_widths.get(col, 100), anchor=tk.CENTER,
                             minwidth=60)
        self.tree.column("operation", anchor=tk.W)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        style = ttk.Style()
        style.configure("Treeview", font=("微软雅黑", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))

        # Pagination
        pager = tk.Frame(self, bg=COLOR_BG, height=40)
        pager.pack(fill=tk.X, padx=16, pady=(0, 8))
        pager.pack_propagate(False)

        tk.Button(
            pager, text="上一页", font=("微软雅黑", 10),
            bg="#E0E0E0", fg=COLOR_TEXT, relief=tk.FLAT, cursor="hand2",
            command=self._prev_page,
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.lbl_page = tk.Label(
            pager, text="第 1 页", font=("微软雅黑", 10),
            bg=COLOR_BG, fg=COLOR_TEXT,
        )
        self.lbl_page.pack(side=tk.LEFT, padx=(0, 16))

        tk.Button(
            pager, text="下一页", font=("微软雅黑", 10),
            bg="#E0E0E0", fg=COLOR_TEXT, relief=tk.FLAT, cursor="hand2",
            command=self._next_page,
        ).pack(side=tk.LEFT, padx=(0, 24))

        tk.Label(
            pager, text="每页条数:", font=("微软雅黑", 10), bg=COLOR_BG,
        ).pack(side=tk.LEFT, padx=(0, 4))

        self.combo_page_size = ttk.Combobox(
            pager, values=["20", "50", "100"], font=("微软雅黑", 10),
            width=4, state="readonly",
        )
        self.combo_page_size.set(str(self.page_size))
        self.combo_page_size.pack(side=tk.LEFT)
        self.combo_page_size.bind("<<ComboboxSelected>>", self._on_page_size_change)

        self.lbl_total = tk.Label(
            pager, text="共 0 条", font=("微软雅黑", 10),
            bg=COLOR_BG, fg=COLOR_TEXT,
        )
        self.lbl_total.pack(side=tk.RIGHT)

    def _load_data(self):
        user_id = self.entry_user_id.get().strip() or None
        log_type = self.combo_log_type.get().strip() or None

        result = self.controller.get_logs(
            page=self.current_page, page_size=self.page_size,
            user_id=user_id, log_type=log_type,
        )
        self.total_records = result.get("total", 0)
        data = result.get("data", [])

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in data:
            self.tree.insert("", tk.END, values=(
                row.get("log_time", ""),
                row.get("user_id", ""),
                row.get("log_type", ""),
                row.get("operation", ""),
                row.get("result", ""),
                row.get("ip_address", ""),
            ))

        total_pages = max(1, (self.total_records + self.page_size - 1) // self.page_size)
        self.lbl_page.config(text=f"第 {self.current_page}/{total_pages} 页")
        self.lbl_total.config(text=f"共 {self.total_records} 条")

    def _do_search(self):
        self.current_page = 1
        self._load_data()

    def _do_reset(self):
        self.entry_user_id.delete(0, tk.END)
        self.combo_log_type.set("")
        self.current_page = 1
        self._load_data()

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._load_data()

    def _next_page(self):
        total_pages = max(1, (self.total_records + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self._load_data()

    def _on_page_size_change(self, event):
        try:
            self.page_size = int(self.combo_page_size.get())
        except ValueError:
            self.page_size = 50
        self.current_page = 1
        self._load_data()
