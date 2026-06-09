"""
frontend_tkinter/admin_students.py - Student Management Page.

Provides search, pagination, and CRUD operations for student records
via the AdminController backend.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from backend.controllers.admin_controller import AdminController
from backend.utils.validator import validate_student_id, validate_contact

# Colour theme
COLOR_PRIMARY = "#2196F3"
COLOR_PRIMARY_HOVER = "#1976D2"
COLOR_BG = "#FAFAFA"
COLOR_TEXT = "#212121"
COLOR_ERROR = "#F44336"
COLOR_BORDER = "#E0E0E0"


class AdminStudentsPage(tk.Frame):
    """Student management page embedded in the admin content area."""

    def __init__(self, master, admin_id):
        """Initialise the student management page.

        Args:
            master: Parent widget.
            admin_id (str): The admin user ID (for logging).
        """
        super().__init__(master, bg=COLOR_BG)
        self.admin_id = admin_id
        self.controller = AdminController()
        self.current_page = 1
        self.page_size = 20
        self.total_records = 0

        self._build_ui()
        self._load_data()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        """Build the full student management layout."""
        # Title
        title_frame = tk.Frame(self, bg=COLOR_BG)
        title_frame.pack(fill=tk.X, padx=16, pady=(12, 8))
        tk.Label(
            title_frame, text="学生管理", font=("微软雅黑", 14, "bold"),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).pack(side=tk.LEFT)

        # Search bar
        self._build_search_bar()

        # Toolbar
        self._build_toolbar()

        # Treeview table
        self._build_treeview()

        # Pagination bar
        self._build_pagination()

    def _build_search_bar(self):
        """Build the search filter bar."""
        search_frame = tk.Frame(self, bg=COLOR_BG, height=44)
        search_frame.pack(fill=tk.X, padx=16, pady=(0, 8))
        search_frame.pack_propagate(False)

        tk.Label(
            search_frame, text="学号:", font=("微软雅黑", 10),
            bg=COLOR_BG,
        ).pack(side=tk.LEFT, padx=(0, 4))

        self.entry_search_id = tk.Entry(
            search_frame, font=("微软雅黑", 10), width=14,
            relief=tk.SOLID, borderwidth=1,
        )
        self.entry_search_id.pack(side=tk.LEFT, padx=(0, 12))

        tk.Label(
            search_frame, text="姓名:", font=("微软雅黑", 10),
            bg=COLOR_BG,
        ).pack(side=tk.LEFT, padx=(0, 4))

        self.entry_search_name = tk.Entry(
            search_frame, font=("微软雅黑", 10), width=12,
            relief=tk.SOLID, borderwidth=1,
        )
        self.entry_search_name.pack(side=tk.LEFT, padx=(0, 12))

        tk.Label(
            search_frame, text="班级:", font=("微软雅黑", 10),
            bg=COLOR_BG,
        ).pack(side=tk.LEFT, padx=(0, 4))

        self.combo_search_class = ttk.Combobox(
            search_frame, font=("微软雅黑", 10), width=12, state="normal",
        )
        self.combo_search_class.pack(side=tk.LEFT, padx=(0, 16))

        tk.Button(
            search_frame, text="搜索", font=("微软雅黑", 10),
            bg=COLOR_PRIMARY, fg="white",
            activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
            relief=tk.FLAT, cursor="hand2",
            command=self._do_search,
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            search_frame, text="重置", font=("微软雅黑", 10),
            bg="#E0E0E0", fg=COLOR_TEXT,
            relief=tk.FLAT, cursor="hand2",
            command=self._do_reset,
        ).pack(side=tk.LEFT)

    def _build_toolbar(self):
        """Build the CRUD toolbar."""
        toolbar = tk.Frame(self, bg=COLOR_BG, height=36)
        toolbar.pack(fill=tk.X, padx=16, pady=(0, 6))
        toolbar.pack_propagate(False)

        buttons = [
            ("新增", self._do_add),
            ("编辑", self._do_edit),
            ("删除", self._do_delete),
            ("导出", self._do_export),
        ]

        for text, cmd in buttons:
            tk.Button(
                toolbar, text=text, font=("微软雅黑", 10),
                bg=COLOR_PRIMARY, fg="white",
                activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
                relief=tk.FLAT, cursor="hand2", width=8,
                command=cmd,
            ).pack(side=tk.LEFT, padx=(0, 8))

    def _build_treeview(self):
        """Build the student table treeview."""
        tree_frame = tk.Frame(self, bg=COLOR_BG)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 6))

        columns = ("student_id", "name", "major", "class_name", "contact")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            selectmode="browse",
        )

        # Column headers (Chinese)
        col_headers = {
            "student_id": "学号",
            "name": "姓名",
            "major": "专业",
            "class_name": "班级",
            "contact": "联系方式",
        }
        col_widths = {"student_id": 140, "name": 120, "major": 180,
                      "class_name": 140, "contact": 160}

        for col in columns:
            self.tree.heading(col, text=col_headers.get(col, col))
            self.tree.column(col, width=col_widths.get(col, 120), anchor=tk.CENTER,
                             minwidth=60)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Style
        style = ttk.Style()
        style.configure("Treeview", font=("微软雅黑", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))

    def _build_pagination(self):
        """Build the pagination controls."""
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
            pager, text="每页条数:", font=("微软雅黑", 10),
            bg=COLOR_BG,
        ).pack(side=tk.LEFT, padx=(0, 4))

        self.combo_page_size = ttk.Combobox(
            pager, values=["10", "20", "50"], font=("微软雅黑", 10),
            width=4, state="readonly",
        )
        self.combo_page_size.set(str(self.page_size))
        self.combo_page_size.pack(side=tk.LEFT)
        self.combo_page_size.bind("<<ComboboxSelected>>", self._on_page_size_change)

        # Total count label
        self.lbl_total = tk.Label(
            pager, text="共 0 条", font=("微软雅黑", 10),
            bg=COLOR_BG, fg=COLOR_TEXT,
        )
        self.lbl_total.pack(side=tk.RIGHT)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _get_search_params(self):
        """Gather current search filter values.

        Returns:
            dict: Search parameters.
        """
        return {
            "student_id": self.entry_search_id.get().strip() or None,
            "name": self.entry_search_name.get().strip() or None,
            "class_name": self.combo_search_class.get().strip() or None,
        }

    def _load_data(self):
        """Fetch data from the controller and populate the treeview."""
        params = self._get_search_params()
        result = self.controller.get_students(
            page=self.current_page,
            page_size=self.page_size,
            **params,
        )
        self.total_records = result.get("total", 0)
        data = result.get("data", [])

        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in data:
            self.tree.insert("", tk.END, values=(
                row.get("student_id", ""),
                row.get("name", ""),
                row.get("major", ""),
                row.get("class_name", ""),
                row.get("contact", ""),
            ))

        # Update pagination labels
        total_pages = max(1, (self.total_records + self.page_size - 1) // self.page_size)
        self.lbl_page.config(text=f"第 {self.current_page}/{total_pages} 页")
        self.lbl_total.config(text=f"共 {self.total_records} 条")

    # ------------------------------------------------------------------
    # Search / Pagination actions
    # ------------------------------------------------------------------

    def _do_search(self):
        """Trigger search with current filters."""
        self.current_page = 1
        self._load_data()

    def _do_reset(self):
        """Reset all search filters and reload."""
        self.entry_search_id.delete(0, tk.END)
        self.entry_search_name.delete(0, tk.END)
        self.combo_search_class.set("")
        self.current_page = 1
        self._load_data()

    def _prev_page(self):
        """Go to the previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self._load_data()

    def _next_page(self):
        """Go to the next page."""
        total_pages = max(1, (self.total_records + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self._load_data()

    def _on_page_size_change(self, event):
        """Handle page size combobox change."""
        try:
            self.page_size = int(self.combo_page_size.get())
        except ValueError:
            self.page_size = 20
        self.current_page = 1
        self._load_data()

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------

    def _get_selected_student(self):
        """Get the currently selected student's data.

        Returns:
            dict or None: Selected student record with keys matching tree columns.
        """
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个学生")
            return None
        values = self.tree.item(selection[0], "values")
        return {
            "student_id": values[0],
            "name": values[1],
            "major": values[2],
            "class_name": values[3],
            "contact": values[4],
        }

    def _do_add(self):
        """Open the add student dialog."""
        dialog = StudentFormDialog(self, title="新增学生")
        self.wait_window(dialog)
        if dialog.result:
            r = self.controller.create_student(**dialog.result)
            if r.get("success"):
                messagebox.showinfo("成功", r.get("message", "学生创建成功"))
                self._load_data()
            else:
                messagebox.showerror("错误", r.get("message", "创建失败"))

    def _do_edit(self):
        """Open the edit student dialog."""
        student = self._get_selected_student()
        if student is None:
            return
        dialog = StudentFormDialog(self, title="编辑学生", initial=student)
        self.wait_window(dialog)
        if dialog.result:
            sid = dialog.result.pop("student_id")
            r = self.controller.update_student(sid, **dialog.result)
            if r.get("success"):
                messagebox.showinfo("成功", r.get("message", "学生信息更新成功"))
                self._load_data()
            else:
                messagebox.showerror("错误", r.get("message", "更新失败"))

    def _do_delete(self):
        """Delete the selected student after confirmation."""
        student = self._get_selected_student()
        if student is None:
            return
        sid = student["student_id"]
        if not messagebox.askyesno("确认删除", f"确定要删除学生 {sid} ({student['name']}) 吗？\n\n这将同时删除其账号信息。"):
            return
        r = self.controller.delete_student(sid)
        if r.get("success"):
            messagebox.showinfo("成功", r.get("message", "学生删除成功"))
            self._load_data()
        else:
            messagebox.showerror("错误", r.get("message", "删除失败"))

    def _do_export(self):
        """Export student list to a CSV/Excel file."""
        file_path = filedialog.asksaveasfilename(
            title="导出学生数据",
            defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
        )
        if not file_path:
            return
        try:
            import csv
            result = self.controller.get_students(page=1, page_size=9999)
            data = result.get("data", [])
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["学号", "姓名", "专业", "班级", "联系方式"])
                for row in data:
                    writer.writerow([
                        row.get("student_id", ""),
                        row.get("name", ""),
                        row.get("major", ""),
                        row.get("class_name", ""),
                        row.get("contact", ""),
                    ])
            messagebox.showinfo("成功", f"已导出 {len(data)} 条记录")
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))


class StudentFormDialog(tk.Toplevel):
    """Dialog for adding or editing a student."""

    def __init__(self, master, title="学生信息", initial=None):
        """Initialise the student form dialog.

        Args:
            master: Parent widget.
            title (str): Dialog title.
            initial (dict): Initial values for editing (None for add).
        """
        super().__init__(master)
        self.title(title)
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.result = None
        self.initial = initial or {}
        self.is_edit = initial is not None

        self._win_width = 400
        self._win_height = 320
        self._center_window()

        self._build_ui()
        self._fill_initial()

    def _center_window(self):
        """Centre the dialog on its parent."""
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - self._win_width) // 2
        y = (screen_h - self._win_height) // 2
        self.geometry(f"{self._win_width}x{self._win_height}+{x}+{y}")

    def _build_ui(self):
        """Build the form fields."""
        form = tk.Frame(self, bg=COLOR_BG)
        form.pack(padx=30, pady=20, fill=tk.BOTH, expand=True)

        self.fields = {}
        field_defs = [
            ("student_id", "学号 *", True),
            ("name", "姓名 *", True),
            ("major", "专业", False),
            ("class_name", "班级", False),
            ("contact", "联系方式", False),
        ]

        for i, (field_key, label_text, required) in enumerate(field_defs):
            tk.Label(
                form, text=label_text, font=("微软雅黑", 10),
                fg=COLOR_TEXT, bg=COLOR_BG,
            ).grid(row=i, column=0, sticky="e", padx=(0, 8), pady=4)

            entry = tk.Entry(
                form, font=("微软雅黑", 10), width=28,
                relief=tk.SOLID, borderwidth=1,
            )
            entry.grid(row=i, column=1, sticky="w", pady=4)

            # Disable student_id field when editing
            if self.is_edit and field_key == "student_id":
                entry.config(state=tk.DISABLED)

            self.fields[field_key] = (entry, required)

        # Buttons
        btn_frame = tk.Frame(self, bg=COLOR_BG)
        btn_frame.pack(pady=(0, 20))

        tk.Button(
            btn_frame, text="保存", font=("微软雅黑", 11, "bold"),
            bg=COLOR_PRIMARY, fg="white",
            activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
            relief=tk.FLAT, cursor="hand2", width=10,
            command=self._do_save,
        ).pack(side=tk.LEFT, padx=(0, 12))

        tk.Button(
            btn_frame, text="取消", font=("微软雅黑", 11),
            bg="#E0E0E0", fg=COLOR_TEXT, relief=tk.FLAT, cursor="hand2", width=10,
            command=self.destroy,
        ).pack(side=tk.LEFT)

    def _fill_initial(self):
        """Pre-populate form fields with initial values."""
        for key, value in self.initial.items():
            if key in self.fields:
                entry, _ = self.fields[key]
                if key == "student_id" and self.is_edit:
                    entry.config(state=tk.NORMAL)
                    entry.insert(0, str(value))
                    entry.config(state=tk.DISABLED)
                else:
                    entry.insert(0, str(value) if value else "")

    def _do_save(self):
        """Validate and return the form data."""
        data = {}
        errors = []

        for key, (entry, required) in self.fields.items():
            # For disabled fields in edit mode, read via get() (works on tkinter)
            if str(entry["state"]) == "disabled":
                value = self.initial.get(key, "")
            else:
                value = entry.get().strip()
            data[key] = value

            if required and not value:
                errors.append(f"{key} 不能为空")
                entry.config(highlightbackground=COLOR_ERROR,
                             highlightcolor=COLOR_ERROR, highlightthickness=1)

        # Additional validation
        if not validate_student_id(data.get("student_id", ""))[0]:
            errors.append("学号格式不正确 (6-20位字母数字)")
            self.fields["student_id"][0].config(
                highlightbackground=COLOR_ERROR,
                highlightcolor=COLOR_ERROR, highlightthickness=1)

        if data.get("contact") and not validate_contact(data["contact"])[0]:
            errors.append("联系方式格式不正确")

        if errors:
            return

        self.result = data
        self.destroy()
