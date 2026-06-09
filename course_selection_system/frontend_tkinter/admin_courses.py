"""
frontend_tkinter/admin_courses.py - Course Management Page.

Provides search, pagination, and CRUD operations for course records
via the AdminController backend.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from backend.controllers.admin_controller import AdminController
from backend.utils.validator import validate_credit

# Colour theme
COLOR_PRIMARY = "#2196F3"
COLOR_PRIMARY_HOVER = "#1976D2"
COLOR_BG = "#FAFAFA"
COLOR_TEXT = "#212121"
COLOR_ERROR = "#F44336"


class AdminCoursesPage(tk.Frame):
    """Course management page embedded in the admin content area."""

    def __init__(self, master, admin_id):
        """Initialise the course management page.

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
        self.all_courses = []

        self._build_ui()
        self._load_data()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        title_frame = tk.Frame(self, bg=COLOR_BG)
        title_frame.pack(fill=tk.X, padx=16, pady=(12, 8))
        tk.Label(
            title_frame, text="课程管理", font=("微软雅黑", 14, "bold"),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).pack(side=tk.LEFT)

        self._build_search_bar()
        self._build_toolbar()
        self._build_treeview()
        self._build_pagination()

    def _build_search_bar(self):
        search_frame = tk.Frame(self, bg=COLOR_BG, height=44)
        search_frame.pack(fill=tk.X, padx=16, pady=(0, 8))
        search_frame.pack_propagate(False)

        tk.Label(
            search_frame, text="课程代码:", font=("微软雅黑", 10), bg=COLOR_BG,
        ).pack(side=tk.LEFT, padx=(0, 4))
        self.entry_search_id = tk.Entry(
            search_frame, font=("微软雅黑", 10), width=14,
            relief=tk.SOLID, borderwidth=1,
        )
        self.entry_search_id.pack(side=tk.LEFT, padx=(0, 12))

        tk.Label(
            search_frame, text="课程名称:", font=("微软雅黑", 10), bg=COLOR_BG,
        ).pack(side=tk.LEFT, padx=(0, 4))
        self.entry_search_name = tk.Entry(
            search_frame, font=("微软雅黑", 10), width=14,
            relief=tk.SOLID, borderwidth=1,
        )
        self.entry_search_name.pack(side=tk.LEFT, padx=(0, 16))

        tk.Button(
            search_frame, text="搜索", font=("微软雅黑", 10),
            bg=COLOR_PRIMARY, fg="white",
            activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
            relief=tk.FLAT, cursor="hand2",
            command=self._do_search,
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(
            search_frame, text="重置", font=("微软雅黑", 10),
            bg="#E0E0E0", fg=COLOR_TEXT, relief=tk.FLAT, cursor="hand2",
            command=self._do_reset,
        ).pack(side=tk.LEFT)

    def _build_toolbar(self):
        toolbar = tk.Frame(self, bg=COLOR_BG, height=36)
        toolbar.pack(fill=tk.X, padx=16, pady=(0, 6))
        toolbar.pack_propagate(False)

        for text, cmd in [
            ("新增", self._do_add),
            ("编辑", self._do_edit),
            ("删除", self._do_delete),
            ("导出", self._do_export),
        ]:
            tk.Button(
                toolbar, text=text, font=("微软雅黑", 10),
                bg=COLOR_PRIMARY, fg="white",
                activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
                relief=tk.FLAT, cursor="hand2", width=8,
                command=cmd,
            ).pack(side=tk.LEFT, padx=(0, 8))

    def _build_treeview(self):
        tree_frame = tk.Frame(self, bg=COLOR_BG)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 6))

        columns = ("course_id", "course_name", "credit", "hours", "exam_type")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="browse",
        )

        col_headers = {
            "course_id": "课程代码", "course_name": "课程名称",
            "credit": "学分", "hours": "学时", "exam_type": "考核方式",
        }
        col_widths = {"course_id": 140, "course_name": 200, "credit": 80,
                      "hours": 80, "exam_type": 100}

        for col in columns:
            self.tree.heading(col, text=col_headers.get(col, col))
            self.tree.column(col, width=col_widths.get(col, 100), anchor=tk.CENTER,
                             minwidth=60)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        style = ttk.Style()
        style.configure("Treeview", font=("微软雅黑", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))

    def _build_pagination(self):
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
            pager, values=["10", "20", "50"], font=("微软雅黑", 10),
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

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_data(self):
        params = {
            "course_id": self.entry_search_id.get().strip() or None,
            "course_name": self.entry_search_name.get().strip() or None,
        }
        result = self.controller.get_courses(
            page=self.current_page, page_size=self.page_size, **params,
        )
        self.total_records = result.get("total", 0)
        data = result.get("data", [])

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in data:
            self.tree.insert("", tk.END, values=(
                row.get("course_id", ""),
                row.get("course_name", ""),
                row.get("credit", ""),
                row.get("hours", ""),
                row.get("exam_type", ""),
            ))

        total_pages = max(1, (self.total_records + self.page_size - 1) // self.page_size)
        self.lbl_page.config(text=f"第 {self.current_page}/{total_pages} 页")
        self.lbl_total.config(text=f"共 {self.total_records} 条")

    # ------------------------------------------------------------------
    # Search / Pagination
    # ------------------------------------------------------------------

    def _do_search(self):
        self.current_page = 1
        self._load_data()

    def _do_reset(self):
        self.entry_search_id.delete(0, tk.END)
        self.entry_search_name.delete(0, tk.END)
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
            self.page_size = 20
        self.current_page = 1
        self._load_data()

    # ------------------------------------------------------------------
    # CRUD Operations
    # ------------------------------------------------------------------

    def _get_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个课程")
            return None
        values = self.tree.item(selection[0], "values")
        return {
            "course_id": values[0],
            "course_name": values[1],
            "credit": values[2],
            "hours": values[3],
            "exam_type": values[4],
        }

    def _do_add(self):
        dialog = CourseFormDialog(self, title="新增课程")
        self.wait_window(dialog)
        if dialog.result:
            try:
                from backend.models.base import DatabaseManager
                from backend.models.course import Course
                from backend.utils.auth_util import hash_password

                data = dialog.result
                db = DatabaseManager.get_instance()
                with db.get_session() as session:
                    existing = session.query(Course).filter_by(
                        course_id=data["course_id"]).first()
                    if existing:
                        messagebox.showerror("错误", "该课程代码已存在")
                        return
                    session.add(Course(
                        course_id=data["course_id"],
                        course_name=data["course_name"],
                        credit=data.get("credit") or None,
                        hours=int(data["hours"]) if data.get("hours") else None,
                        exam_type=data.get("exam_type") or None,
                    ))
                messagebox.showinfo("成功", "课程创建成功")
                self._load_data()
            except Exception as exc:
                messagebox.showerror("错误", f"创建失败: {exc}")

    def _do_edit(self):
        course = self._get_selected()
        if course is None:
            return
        dialog = CourseFormDialog(self, title="编辑课程", initial=course)
        self.wait_window(dialog)
        if dialog.result:
            try:
                from backend.models.base import DatabaseManager
                from backend.models.course import Course

                data = dialog.result
                cid = data.pop("course_id")
                db = DatabaseManager.get_instance()
                with db.get_session() as session:
                    c = session.query(Course).filter_by(course_id=cid).first()
                    if c is None:
                        messagebox.showerror("错误", "课程不存在")
                        return
                    for k, v in data.items():
                        if hasattr(c, k):
                            setattr(c, k, v)
                messagebox.showinfo("成功", "课程信息更新成功")
                self._load_data()
            except Exception as exc:
                messagebox.showerror("错误", f"更新失败: {exc}")

    def _do_delete(self):
        course = self._get_selected()
        if course is None:
            return
        cid = course["course_id"]
        if not messagebox.askyesno("确认删除",
                                   f"确定要删除课程 {cid} ({course['course_name']}) 吗？"):
            return
        try:
            from backend.models.base import DatabaseManager
            from backend.models.course import Course
            db = DatabaseManager.get_instance()
            with db.get_session() as session:
                c = session.query(Course).filter_by(course_id=cid).first()
                if c is None:
                    messagebox.showerror("错误", "课程不存在")
                    return
                session.delete(c)
            messagebox.showinfo("成功", "课程删除成功")
            self._load_data()
        except Exception as exc:
            messagebox.showerror("错误", f"删除失败: {exc}")

    def _do_export(self):
        file_path = filedialog.asksaveasfilename(
            title="导出课程数据",
            defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
        )
        if not file_path:
            return
        try:
            import csv
            result = self.controller.get_courses(page=1, page_size=9999)
            data = result.get("data", [])
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["课程代码", "课程名称", "学分", "学时", "考核方式"])
                for row in data:
                    writer.writerow([
                        row.get("course_id", ""),
                        row.get("course_name", ""),
                        row.get("credit", ""),
                        row.get("hours", ""),
                        row.get("exam_type", ""),
                    ])
            messagebox.showinfo("成功", f"已导出 {len(data)} 条记录")
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))


class CourseFormDialog(tk.Toplevel):
    """Dialog for adding or editing a course."""

    def __init__(self, master, title="课程信息", initial=None):
        super().__init__(master)
        self.title(title)
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.result = None
        self.initial = initial or {}
        self.is_edit = initial is not None

        self._win_width = 440
        self._win_height = 340
        self._center_window()

        self._build_ui()
        self._fill_initial()

    def _center_window(self):
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - self._win_width) // 2
        y = (screen_h - self._win_height) // 2
        self.geometry(f"{self._win_width}x{self._win_height}+{x}+{y}")

    def _build_ui(self):
        form = tk.Frame(self, bg=COLOR_BG)
        form.pack(padx=30, pady=20, fill=tk.BOTH, expand=True)

        self.fields = {}
        field_defs = [
            ("course_id", "课程代码 *", True),
            ("course_name", "课程名称 *", True),
            ("credit", "学分", False),
            ("hours", "学时", False),
            ("exam_type", "考核方式", False),
        ]

        for i, (field_key, label_text, required) in enumerate(field_defs):
            tk.Label(
                form, text=label_text, font=("微软雅黑", 10),
                fg=COLOR_TEXT, bg=COLOR_BG,
            ).grid(row=i, column=0, sticky="e", padx=(0, 8), pady=4)

            if field_key == "exam_type":
                entry = ttk.Combobox(
                    form, values=["考试", "考查"],
                    font=("微软雅黑", 10), width=26, state="normal",
                )
            else:
                entry = tk.Entry(
                    form, font=("微软雅黑", 10), width=28,
                    relief=tk.SOLID, borderwidth=1,
                )
            entry.grid(row=i, column=1, sticky="w", pady=4)

            if self.is_edit and field_key == "course_id":
                entry.config(state=tk.DISABLED)

            self.fields[field_key] = (entry, required)

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
        for key, value in self.initial.items():
            if key in self.fields:
                entry, _ = self.fields[key]
                if key == "course_id" and self.is_edit:
                    entry.config(state=tk.NORMAL)
                    entry.insert(0, str(value))
                    entry.config(state=tk.DISABLED)
                elif isinstance(entry, ttk.Combobox):
                    entry.set(str(value) if value else "")
                else:
                    entry.insert(0, str(value) if value else "")

    def _do_save(self):
        data = {}
        errors = []

        for key, (entry, required) in self.fields.items():
            if str(entry["state"]) == "disabled":
                value = self.initial.get(key, "")
            elif isinstance(entry, ttk.Combobox):
                value = entry.get().strip()
            else:
                value = entry.get().strip()
            data[key] = value

            if required and not value:
                errors.append(f"{key} 不能为空")
                if not isinstance(entry, ttk.Combobox):
                    entry.config(highlightbackground=COLOR_ERROR,
                                 highlightcolor=COLOR_ERROR, highlightthickness=1)

        if data.get("credit") and not validate_credit(data["credit"])[0]:
            errors.append("学分必须在0.5-20之间，以0.5为步进")

        if errors:
            return

        self.result = data
        self.destroy()
