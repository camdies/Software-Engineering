"""
frontend_tkinter/student_enroll.py - Course Selection Page.

Displays available courses and allows the student to enroll
via EnrollmentController.select_course().
"""

import tkinter as tk
from tkinter import ttk, messagebox

from backend.controllers.student_controller import StudentController
from backend.controllers.enrollment_controller import EnrollmentController

# Colour theme
COLOR_PRIMARY = "#2196F3"
COLOR_PRIMARY_HOVER = "#1976D2"
COLOR_BG = "#FAFAFA"
COLOR_TEXT = "#212121"
COLOR_SUCCESS = "#4CAF50"


class StudentEnrollPage(tk.Frame):
    """Course selection page for students."""

    def __init__(self, master, student_id):
        """Initialise the enroll page.

        Args:
            master: Parent widget.
            student_id (str): The student's user ID.
        """
        super().__init__(master, bg=COLOR_BG)
        self.student_id = student_id
        self.sc = StudentController()
        self.ec = EnrollmentController()

        self._build_ui()
        self._load_courses()

    def _build_ui(self):
        title_frame = tk.Frame(self, bg=COLOR_BG)
        title_frame.pack(fill=tk.X, padx=16, pady=(12, 8))
        tk.Label(
            title_frame, text="选课中心", font=("微软雅黑", 14, "bold"),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).pack(side=tk.LEFT)

        # Toolbar
        toolbar = tk.Frame(self, bg=COLOR_BG, height=36)
        toolbar.pack(fill=tk.X, padx=16, pady=(0, 6))
        toolbar.pack_propagate(False)

        tk.Button(
            toolbar, text="选课", font=("微软雅黑", 10, "bold"),
            bg=COLOR_SUCCESS, fg="white",
            activebackground="#43A047", activeforeground="white",
            relief=tk.FLAT, cursor="hand2", width=10,
            command=self._do_enroll,
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            toolbar, text="刷新", font=("微软雅黑", 10),
            bg=COLOR_PRIMARY, fg="white",
            activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
            relief=tk.FLAT, cursor="hand2", width=8,
            command=self._load_courses,
        ).pack(side=tk.LEFT)

        # Treeview
        tree_frame = tk.Frame(self, bg=COLOR_BG)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        columns = ("course_id", "course_name", "credit", "teacher_id",
                   "time_slot", "location", "availability")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="browse",
        )

        col_headers = {
            "course_id": "课程代码", "course_name": "课程名称",
            "credit": "学分", "teacher_id": "教师",
            "time_slot": "时间", "location": "地点",
            "availability": "余量/容量",
        }
        col_widths = {"course_id": 120, "course_name": 180, "credit": 60,
                      "teacher_id": 100, "time_slot": 140, "location": 120,
                      "availability": 100}

        for col in columns:
            self.tree.heading(col, text=col_headers.get(col, col))
            self.tree.column(col, width=col_widths.get(col, 100), anchor=tk.CENTER,
                             minwidth=60)
        self.tree.column("course_name", anchor=tk.W)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        style = ttk.Style()
        style.configure("Treeview", font=("微软雅黑", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))

        self.courses_data = []

    def _load_courses(self):
        """Load available courses from the controller."""
        self.courses_data = self.sc.get_available_courses()

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in self.courses_data:
            available = row.get("available", 0)
            capacity = row.get("capacity", 0)
            avail_text = f"{available}/{capacity}"
            self.tree.insert("", tk.END, values=(
                row.get("course_id", ""),
                row.get("course_name", ""),
                row.get("credit", ""),
                row.get("teacher_id", ""),
                row.get("time_slot", ""),
                row.get("location", ""),
                avail_text,
            ))

    def _do_enroll(self):
        """Enroll in the selected course."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要选修的课程")
            return

        idx = self.tree.index(selection[0])
        if idx < 0 or idx >= len(self.courses_data):
            return

        course = self.courses_data[idx]
        plan_id = course.get("plan_id")
        course_name = course.get("course_name", str(plan_id))

        if not messagebox.askyesno("确认选课", f"确定要选修课程「{course_name}」吗？"):
            return

        result = self.ec.select_course(self.student_id, plan_id)
        if result.get("success"):
            messagebox.showinfo("选课成功", result.get("message", "选课成功！"))
            self._load_courses()
        else:
            messagebox.showerror("选课失败", result.get("message", "选课失败"))
