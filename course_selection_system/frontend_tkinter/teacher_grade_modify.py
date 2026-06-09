"""
frontend_tkinter/teacher_grade_modify.py - Grade Modification Request Page.

Allows teachers to search for a student's grade and submit
a modification request via GradeController.apply_grade_modify().
"""

import tkinter as tk
from tkinter import ttk, messagebox

from backend.controllers.grade_controller import GradeController
from backend.controllers.teacher_controller import TeacherController
from backend.models.base import DatabaseManager
from backend.models.grade import Grade
from backend.models.course_plan import CoursePlan
from backend.models.course import Course
from backend.models.student import Student

# Colour theme
COLOR_PRIMARY = "#2196F3"
COLOR_PRIMARY_HOVER = "#1976D2"
COLOR_BG = "#FAFAFA"
COLOR_TEXT = "#212121"
COLOR_ERROR = "#F44336"


class TeacherGradeModifyPage(tk.Frame):
    """Grade modification request page for teachers."""

    def __init__(self, master, teacher_id):
        """Initialise the grade modify page.

        Args:
            master: Parent widget.
            teacher_id (str): The teacher's user ID.
        """
        super().__init__(master, bg=COLOR_BG)
        self.teacher_id = teacher_id
        self.gc = GradeController()
        self.tc = TeacherController()
        self.current_grade_id = None

        self._build_ui()
        self._load_plan_list()

    def _build_ui(self):
        title_frame = tk.Frame(self, bg=COLOR_BG)
        title_frame.pack(fill=tk.X, padx=16, pady=(12, 8))
        tk.Label(
            title_frame, text="成绩修改申请", font=("微软雅黑", 14, "bold"),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).pack(side=tk.LEFT)

        # Search bar
        search_frame = tk.Frame(self, bg=COLOR_BG)
        search_frame.pack(fill=tk.X, padx=16, pady=(0, 12))

        tk.Label(
            search_frame, text="选择课程:", font=("微软雅黑", 10), bg=COLOR_BG,
        ).grid(row=0, column=0, sticky="e", padx=(0, 6), pady=4)

        self.combo_plan = ttk.Combobox(
            search_frame, font=("微软雅黑", 10), width=40, state="readonly",
        )
        self.combo_plan.grid(row=0, column=1, sticky="w", pady=4)

        tk.Label(
            search_frame, text="学号:", font=("微软雅黑", 10), bg=COLOR_BG,
        ).grid(row=1, column=0, sticky="e", padx=(0, 6), pady=4)

        self.entry_student_id = tk.Entry(
            search_frame, font=("微软雅黑", 10), width=20,
            relief=tk.SOLID, borderwidth=1,
        )
        self.entry_student_id.grid(row=1, column=1, sticky="w", pady=4)

        tk.Button(
            search_frame, text="查询成绩", font=("微软雅黑", 10),
            bg=COLOR_PRIMARY, fg="white",
            activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
            relief=tk.FLAT, cursor="hand2",
            command=self._do_search,
        ).grid(row=1, column=2, padx=(12, 0), pady=4)

        # Current grade info display
        self.info_frame = tk.LabelFrame(
            self, text="当前成绩信息", font=("微软雅黑", 10, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT,
        )
        self.info_frame.pack(fill=tk.X, padx=16, pady=(0, 12))

        info_grid = tk.Frame(self.info_frame, bg=COLOR_BG)
        info_grid.pack(padx=16, pady=12, fill=tk.X)

        info_labels = [
            ("课程:", "lbl_course"),
            ("学生:", "lbl_student"),
            ("当前成绩:", "lbl_score"),
            ("绩点:", "lbl_gpa"),
            ("状态:", "lbl_status"),
        ]

        self.info_widgets = {}
        for i, (label_text, key) in enumerate(info_labels):
            tk.Label(
                info_grid, text=label_text, font=("微软雅黑", 10),
                fg=COLOR_TEXT, bg=COLOR_BG,
            ).grid(row=i // 3, column=(i % 3) * 2, sticky="e", padx=(0, 4), pady=3)

            lbl = tk.Label(
                info_grid, text="--", font=("微软雅黑", 10),
                fg=COLOR_TEXT, bg=COLOR_BG,
            )
            lbl.grid(row=i // 3, column=(i % 3) * 2 + 1, sticky="w", pady=3)
            self.info_widgets[key] = lbl

        # New score and reason
        modify_frame = tk.LabelFrame(
            self, text="修改申请", font=("微软雅黑", 10, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT,
        )
        modify_frame.pack(fill=tk.X, padx=16, pady=(0, 12))

        modify_form = tk.Frame(modify_frame, bg=COLOR_BG)
        modify_form.pack(padx=16, pady=12, fill=tk.X)

        tk.Label(
            modify_form, text="新成绩:", font=("微软雅黑", 10),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).grid(row=0, column=0, sticky="e", padx=(0, 6), pady=4)

        self.entry_new_score = tk.Entry(
            modify_form, font=("微软雅黑", 10), width=10,
            relief=tk.SOLID, borderwidth=1,
        )
        self.entry_new_score.grid(row=0, column=1, sticky="w", pady=4)

        tk.Label(
            modify_form, text="修改原因:", font=("微软雅黑", 10),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).grid(row=1, column=0, sticky="ne", padx=(0, 6), pady=4)

        self.txt_reason = tk.Text(
            modify_form, font=("微软雅黑", 10), width=50, height=4,
            relief=tk.SOLID, borderwidth=1,
        )
        self.txt_reason.grid(row=1, column=1, sticky="w", pady=4)

        tk.Button(
            modify_form, text="提交申请", font=("微软雅黑", 11, "bold"),
            bg=COLOR_PRIMARY, fg="white",
            activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
            relief=tk.FLAT, cursor="hand2", width=12,
            command=self._do_submit,
        ).grid(row=2, column=1, sticky="w", pady=(12, 0))

    def _load_plan_list(self):
        """Load the teacher's teaching plans into the combobox."""
        plans = self.tc.get_teaching_plans(self.teacher_id)
        self.plans_data = plans
        plan_list = []
        for p in plans:
            plan_list.append(
                f"[{p.get('course_id','')}] {p.get('semester','')} "
                f"(plan_id={p.get('plan_id')})"
            )
        self.combo_plan["values"] = plan_list
        if plan_list:
            self.combo_plan.current(0)

    def _do_search(self):
        """Search for the student's grade in the selected plan."""
        student_id = self.entry_student_id.get().strip()
        idx = self.combo_plan.current()

        if not student_id:
            messagebox.showwarning("提示", "请输入学号")
            return
        if idx < 0 or idx >= len(self.plans_data):
            messagebox.showwarning("提示", "请选择课程")
            return

        plan_id = self.plans_data[idx].get("plan_id")

        try:
            db = DatabaseManager.get_instance()
            with db.get_session() as session:
                grade = session.query(Grade).filter_by(
                    student_id=student_id, plan_id=plan_id).first()

                if grade is None:
                    self._clear_info()
                    messagebox.showinfo("无记录", "未找到该学生在此课程的成绩记录")
                    return

                self.current_grade_id = grade.grade_id

                # Get course name
                plan = session.query(CoursePlan).filter_by(plan_id=plan_id).first()
                course_name = ""
                if plan:
                    course = session.query(Course).filter_by(
                        course_id=plan.course_id).first()
                    course_name = course.course_name if course else str(plan_id)
                else:
                    course_name = str(plan_id)

                # Get student name
                student = session.query(Student).filter_by(
                    student_id=student_id).first()
                student_name = student.name if student else ""

                self.info_widgets["lbl_course"].config(text=course_name)
                self.info_widgets["lbl_student"].config(
                    text=f"{student_id} ({student_name})")
                self.info_widgets["lbl_score"].config(text=str(grade.score or ""))
                self.info_widgets["lbl_gpa"].config(text=str(grade.gpa_point or ""))
                self.info_widgets["lbl_status"].config(text=grade.status or "")

        except Exception as exc:
            messagebox.showerror("查询失败", f"查询成绩时发生错误: {exc}")

    def _clear_info(self):
        """Clear the info display."""
        for lbl in self.info_widgets.values():
            lbl.config(text="--")
        self.current_grade_id = None

    def _do_submit(self):
        """Submit the grade modification request."""
        if self.current_grade_id is None:
            messagebox.showwarning("提示", "请先查询要修改的成绩记录")
            return

        new_score_str = self.entry_new_score.get().strip()
        reason = self.txt_reason.get("1.0", tk.END).strip()

        if not new_score_str:
            messagebox.showwarning("提示", "请输入新成绩")
            return
        if not reason:
            messagebox.showwarning("提示", "请输入修改原因")
            return

        try:
            new_score = int(new_score_str)
        except ValueError:
            messagebox.showwarning("提示", "新成绩必须为有效整数")
            return

        result = self.gc.apply_grade_modify(
            self.teacher_id, self.current_grade_id, new_score, reason,
        )
        if result.get("success"):
            messagebox.showinfo("成功", result.get("message", "修改申请已提交"))
            self.entry_new_score.delete(0, tk.END)
            self.txt_reason.delete("1.0", tk.END)
            self._do_search()  # Refresh
        else:
            messagebox.showerror("错误", result.get("message", "申请提交失败"))
