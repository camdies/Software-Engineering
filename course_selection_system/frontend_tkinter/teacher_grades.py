"""
frontend_tkinter/teacher_grades.py - Grade Entry and Teaching Info Page.

Provides:
- TeacherTeachingPage: displays the teacher's teaching plans and enrolled students.
- TeacherGradesPage: allows entering grades for enrolled students per course plan.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from backend.controllers.teacher_controller import TeacherController
from backend.controllers.grade_controller import GradeController

# Colour theme
COLOR_PRIMARY = "#2196F3"
COLOR_PRIMARY_HOVER = "#1976D2"
COLOR_BG = "#FAFAFA"
COLOR_TEXT = "#212121"
COLOR_SUCCESS = "#4CAF50"


class TeacherTeachingPage(tk.Frame):
    """Teaching plans overview page.

    Shows the teacher's current teaching plans and enrolled students.
    """

    def __init__(self, master, teacher_id):
        super().__init__(master, bg=COLOR_BG)
        self.teacher_id = teacher_id
        self.controller = TeacherController()

        self._build_ui()
        self._load_plans()

    def _build_ui(self):
        title_frame = tk.Frame(self, bg=COLOR_BG)
        title_frame.pack(fill=tk.X, padx=16, pady=(12, 8))
        tk.Label(
            title_frame, text="任课信息", font=("微软雅黑", 14, "bold"),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).pack(side=tk.LEFT)

        # Plan selector
        selector = tk.Frame(self, bg=COLOR_BG, height=40)
        selector.pack(fill=tk.X, padx=16, pady=(0, 6))
        selector.pack_propagate(False)

        tk.Label(
            selector, text="选择课程:", font=("微软雅黑", 10), bg=COLOR_BG,
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.combo_plan = ttk.Combobox(
            selector, font=("微软雅黑", 10), width=50, state="readonly",
        )
        self.combo_plan.pack(side=tk.LEFT, padx=(0, 12))
        self.combo_plan.bind("<<ComboboxSelected>>", self._on_plan_select)

        tk.Button(
            selector, text="刷新", font=("微软雅黑", 10),
            bg=COLOR_PRIMARY, fg="white",
            activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
            relief=tk.FLAT, cursor="hand2",
            command=self._load_plans,
        ).pack(side=tk.LEFT)

        # Treeview for enrolled students
        tree_frame = tk.Frame(self, bg=COLOR_BG)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        columns = ("student_id", "name", "enroll_id")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="browse",
        )
        col_headers = {"student_id": "学号", "name": "姓名", "enroll_id": "选课ID"}
        col_widths = {"student_id": 160, "name": 160, "enroll_id": 100}

        for col in columns:
            self.tree.heading(col, text=col_headers.get(col, col))
            self.tree.column(col, width=col_widths.get(col, 120), anchor=tk.CENTER,
                             minwidth=60)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        style = ttk.Style()
        style.configure("Treeview", font=("微软雅黑", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))

        self.plans_data = []

    def _load_plans(self):
        """Load teaching plans from the controller."""
        self.plans_data = self.controller.get_teaching_plans(self.teacher_id)
        plan_list = []
        for p in self.plans_data:
            label = (
                f"[{p.get('course_id','')}] {p.get('semester','')} "
                f"({p.get('time_slot','')} @ {p.get('location','')}) "
                f"容量: {p.get('enrolled',0)}/{p.get('capacity',0)}"
            )
            plan_list.append(label)
        self.combo_plan["values"] = plan_list
        if plan_list:
            self.combo_plan.current(0)
            self._on_plan_select(None)

    def _on_plan_select(self, event):
        """Load enrolled students for the selected plan."""
        idx = self.combo_plan.current()
        if idx < 0 or idx >= len(self.plans_data):
            return

        plan = self.plans_data[idx]
        plan_id = plan.get("plan_id")

        for item in self.tree.get_children():
            self.tree.delete(item)

        students = self.controller.get_enrolled_students(plan_id)
        for s in students:
            self.tree.insert("", tk.END, values=(
                s.get("student_id", ""),
                s.get("name", ""),
                s.get("enroll_id", ""),
            ))


class TeacherGradesPage(tk.Frame):
    """Grade entry page for teachers.

    Allows selecting a course plan, viewing enrolled students, and
    entering/saving grades via GradeController.record_grade().
    Supports batch import from Excel files.
    """

    def __init__(self, master, teacher_id):
        super().__init__(master, bg=COLOR_BG)
        self.teacher_id = teacher_id
        self.tc = TeacherController()
        self.gc = GradeController()
        self.plans_data = []
        self.grade_entries = {}

        self._build_ui()
        self._load_plans()

    def _build_ui(self):
        title_frame = tk.Frame(self, bg=COLOR_BG)
        title_frame.pack(fill=tk.X, padx=16, pady=(12, 8))
        tk.Label(
            title_frame, text="成绩录入", font=("微软雅黑", 14, "bold"),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).pack(side=tk.LEFT)

        # Plan selector
        selector = tk.Frame(self, bg=COLOR_BG, height=40)
        selector.pack(fill=tk.X, padx=16, pady=(0, 6))
        selector.pack_propagate(False)

        tk.Label(
            selector, text="选择课程:", font=("微软雅黑", 10), bg=COLOR_BG,
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.combo_plan = ttk.Combobox(
            selector, font=("微软雅黑", 10), width=50, state="readonly",
        )
        self.combo_plan.pack(side=tk.LEFT, padx=(0, 12))
        self.combo_plan.bind("<<ComboboxSelected>>", self._on_plan_select)

        tk.Button(
            selector, text="刷新", font=("微软雅黑", 10),
            bg=COLOR_PRIMARY, fg="white",
            activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
            relief=tk.FLAT, cursor="hand2",
            command=self._load_plans,
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            selector, text="保存成绩", font=("微软雅黑", 10),
            bg=COLOR_SUCCESS, fg="white",
            activebackground="#43A047", activeforeground="white",
            relief=tk.FLAT, cursor="hand2",
            command=self._do_save_all,
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            selector, text="批量导入", font=("微软雅黑", 10),
            bg=COLOR_PRIMARY, fg="white",
            activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
            relief=tk.FLAT, cursor="hand2",
            command=self._do_batch_import,
        ).pack(side=tk.LEFT)

        # Scrollable canvas for the editable grid
        canvas_frame = tk.Frame(self, bg=COLOR_BG)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        self.canvas = tk.Canvas(canvas_frame, bg=COLOR_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL,
                                  command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLOR_BG)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw",
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind canvas width to resize inner frame
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        """Resize the inner frame to match canvas width."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _load_plans(self):
        self.plans_data = self.tc.get_teaching_plans(self.teacher_id)
        plan_list = []
        for p in self.plans_data:
            label = (
                f"[{p.get('course_id','')}] {p.get('semester','')} "
                f"- 已选: {p.get('enrolled',0)}/{p.get('capacity',0)}"
            )
            plan_list.append(label)
        self.combo_plan["values"] = plan_list
        if plan_list:
            self.combo_plan.current(0)
            self._on_plan_select(None)

    def _on_plan_select(self, event):
        """Build the editable grid for the selected plan."""
        idx = self.combo_plan.current()
        if idx < 0 or idx >= len(self.plans_data):
            return

        plan = self.plans_data[idx]
        plan_id = plan.get("plan_id")

        # Clear existing
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.grade_entries.clear()

        students = self.tc.get_enrolled_students(plan_id)

        # Header row
        headers = ["学号", "姓名", "成绩"]
        widths = [18, 18, 14]
        for j, (h, w) in enumerate(zip(headers, widths)):
            tk.Label(
                self.scrollable_frame, text=h, font=("微软雅黑", 10, "bold"),
                bg=COLOR_PRIMARY, fg="white", relief=tk.SOLID, borderwidth=1,
                width=w, anchor=tk.CENTER,
            ).grid(row=0, column=j, sticky="nsew", padx=0, pady=0)

        # Student rows
        if not students:
            tk.Label(
                self.scrollable_frame, text="暂无选课学生", font=("微软雅黑", 10),
                bg=COLOR_BG, fg=COLOR_TEXT,
            ).grid(row=1, column=0, columnspan=3, pady=20)
            return

        for i, s in enumerate(students):
            row_idx = i + 1
            bg_color = "#FFFFFF" if i % 2 == 0 else "#F5F5F5"

            sid = s.get("student_id", "")
            sname = s.get("name", "")

            tk.Label(
                self.scrollable_frame, text=sid, font=("微软雅黑", 10),
                bg=bg_color, relief=tk.SOLID, borderwidth=1,
                width=18, anchor=tk.CENTER,
            ).grid(row=row_idx, column=0, sticky="nsew", padx=0, pady=0)

            tk.Label(
                self.scrollable_frame, text=sname, font=("微软雅黑", 10),
                bg=bg_color, relief=tk.SOLID, borderwidth=1,
                width=18, anchor=tk.CENTER,
            ).grid(row=row_idx, column=1, sticky="nsew", padx=0, pady=0)

            entry = tk.Entry(
                self.scrollable_frame, font=("微软雅黑", 10),
                relief=tk.SOLID, borderwidth=1, width=14,
            )
            entry.grid(row=row_idx, column=2, sticky="nsew", padx=0, pady=0)
            self.grade_entries[sid] = entry

    def _do_save_all(self):
        """Save all entered grades."""
        idx = self.combo_plan.current()
        if idx < 0 or idx >= len(self.plans_data):
            messagebox.showwarning("提示", "请先选择课程")
            return

        plan_id = self.plans_data[idx].get("plan_id")
        success_count = 0
        fail_count = 0

        for sid, entry in self.grade_entries.items():
            value = entry.get().strip()
            if not value:
                continue
            try:
                score = int(value)
            except ValueError:
                fail_count += 1
                continue

            result = self.gc.record_grade(
                self.teacher_id, sid, plan_id, score,
            )
            if result.get("success"):
                success_count += 1
            else:
                fail_count += 1

        messagebox.showinfo(
            "录入结果",
            f"成绩保存完成\n\n成功: {success_count} 条\n失败: {fail_count} 条",
        )
        if success_count > 0:
            self._on_plan_select(None)

    def _do_batch_import(self):
        """Batch import grades from an Excel file."""
        idx = self.combo_plan.current()
        if idx < 0 or idx >= len(self.plans_data):
            messagebox.showwarning("提示", "请先选择课程")
            return

        plan_id = self.plans_data[idx].get("plan_id")

        file_path = filedialog.askopenfilename(
            title="选择成绩导入文件",
            filetypes=[("Excel 文件", "*.xlsx"), ("所有文件", "*.*")],
        )
        if not file_path:
            return

        result = self.gc.batch_record_grade(self.teacher_id, plan_id, file_path)
        success = result.get("success_count", 0)
        fail = result.get("fail_count", 0)
        fail_list = result.get("fail_list", [])

        fail_detail = ""
        if fail_list:
            fail_detail = "\n\n失败详情:\n"
            for item in fail_list[:10]:
                fail_detail += (
                    f"  第{item.get('row','?')}行, 学号:{item.get('student_id','')}, "
                    f"原因:{item.get('reason','')}\n"
                )
            if len(fail_list) > 10:
                fail_detail += f"  ... 共 {len(fail_list)} 条失败\n"

        messagebox.showinfo(
            "批量导入结果",
            f"导入完成\n\n成功: {success} 条\n失败: {fail} 条{fail_detail}",
        )
        self._on_plan_select(None)
