"""
frontend_tkinter/student_my_courses.py - My Courses Page.

Displays the student's currently enrolled courses and allows
dropping a course via EnrollmentController.drop_course().
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
COLOR_DANGER = "#F44336"


class StudentMyCoursesPage(tk.Frame):
    """My Courses page showing enrolled courses."""

    def __init__(self, master, student_id):
        """Initialise the my-courses page.

        Args:
            master: Parent widget.
            student_id (str): The student's user ID.
        """
        super().__init__(master, bg=COLOR_BG)
        self.student_id = student_id
        self.sc = StudentController()
        self.ec = EnrollmentController()

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        title_frame = tk.Frame(self, bg=COLOR_BG)
        title_frame.pack(fill=tk.X, padx=16, pady=(12, 8))
        tk.Label(
            title_frame, text="已选课程", font=("微软雅黑", 14, "bold"),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).pack(side=tk.LEFT)

        # Toolbar
        toolbar = tk.Frame(self, bg=COLOR_BG, height=36)
        toolbar.pack(fill=tk.X, padx=16, pady=(0, 6))
        toolbar.pack_propagate(False)

        tk.Button(
            toolbar, text="退课", font=("微软雅黑", 10, "bold"),
            bg=COLOR_DANGER, fg="white",
            activebackground="#E53935", activeforeground="white",
            relief=tk.FLAT, cursor="hand2", width=10,
            command=self._do_drop,
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            toolbar, text="刷新", font=("微软雅黑", 10),
            bg=COLOR_PRIMARY, fg="white",
            activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
            relief=tk.FLAT, cursor="hand2", width=8,
            command=self._load_data,
        ).pack(side=tk.LEFT)

        # Treeview
        tree_frame = tk.Frame(self, bg=COLOR_BG)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        columns = ("course_id", "course_name", "credit", "time_slot", "enroll_time")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="browse",
        )

        col_headers = {
            "course_id": "课程代码", "course_name": "课程名称",
            "credit": "学分", "time_slot": "上课时间", "enroll_time": "选课时间",
        }
        col_widths = {"course_id": 140, "course_name": 220, "credit": 80,
                      "time_slot": 180, "enroll_time": 180}

        for col in columns:
            self.tree.heading(col, text=col_headers.get(col, col))
            self.tree.column(col, width=col_widths.get(col, 120), anchor=tk.CENTER,
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

        self.my_courses_data = []

    def _load_data(self):
        """Load the student's enrolled courses."""
        self.my_courses_data = self.sc.get_my_courses(self.student_id)

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in self.my_courses_data:
            self.tree.insert("", tk.END, values=(
                row.get("course_id", ""),
                row.get("course_name", ""),
                row.get("credit", ""),
                row.get("time_slot", ""),
                row.get("enroll_time", ""),
            ))

    def _do_drop(self):
        """Drop the selected course."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要退选的课程")
            return

        idx = self.tree.index(selection[0])
        if idx < 0 or idx >= len(self.my_courses_data):
            return

        course = self.my_courses_data[idx]
        plan_id = course.get("plan_id")
        course_name = course.get("course_name", str(plan_id))

        if not messagebox.askyesno("确认退课", f"确定要退选课程「{course_name}」吗？"):
            return

        result = self.ec.drop_course(self.student_id, plan_id)
        if result.get("success"):
            messagebox.showinfo("退课成功", result.get("message", "退课成功！"))
            self._load_data()
        else:
            messagebox.showerror("退课失败", result.get("message", "退课失败"))
