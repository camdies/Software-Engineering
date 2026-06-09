"""
frontend_tkinter/admin_grade_audit.py - Grade Audit Page.

Displays grades with "待审核" status and allows the admin to approve
or reject grade modification requests via GradeController.audit_grade().
"""

import re
import tkinter as tk
from tkinter import ttk, messagebox

from backend.controllers.grade_controller import GradeController
from backend.models.base import DatabaseManager
from backend.models.grade import Grade

# Colour theme
COLOR_PRIMARY = "#2196F3"
COLOR_PRIMARY_HOVER = "#1976D2"
COLOR_BG = "#FAFAFA"
COLOR_TEXT = "#212121"
COLOR_SUCCESS = "#4CAF50"
COLOR_DANGER = "#F44336"


class AdminGradeAuditPage(tk.Frame):
    """Grade audit page for reviewing modification requests."""

    def __init__(self, master, admin_id):
        """Initialise the grade audit page.

        Args:
            master: Parent widget.
            admin_id (str): The admin user ID.
        """
        super().__init__(master, bg=COLOR_BG)
        self.admin_id = admin_id
        self.controller = GradeController()

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        title_frame = tk.Frame(self, bg=COLOR_BG)
        title_frame.pack(fill=tk.X, padx=16, pady=(12, 8))
        tk.Label(
            title_frame, text="成绩审核", font=("微软雅黑", 14, "bold"),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).pack(side=tk.LEFT)

        # Action buttons
        toolbar = tk.Frame(self, bg=COLOR_BG, height=36)
        toolbar.pack(fill=tk.X, padx=16, pady=(0, 6))
        toolbar.pack_propagate(False)

        tk.Button(
            toolbar, text="通过", font=("微软雅黑", 10),
            bg=COLOR_SUCCESS, fg="white",
            activebackground="#43A047", activeforeground="white",
            relief=tk.FLAT, cursor="hand2", width=10,
            command=self._do_approve,
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            toolbar, text="驳回", font=("微软雅黑", 10),
            bg=COLOR_DANGER, fg="white",
            activebackground="#E53935", activeforeground="white",
            relief=tk.FLAT, cursor="hand2", width=10,
            command=self._do_reject,
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

        columns = ("grade_id", "student_id", "course", "old_score", "new_score", "reason")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="browse",
        )

        col_headers = {
            "grade_id": "ID", "student_id": "学号", "course": "课程",
            "old_score": "原成绩", "new_score": "新成绩", "reason": "原因",
        }
        col_widths = {"grade_id": 60, "student_id": 120, "course": 180,
                      "old_score": 80, "new_score": 80, "reason": 280}

        for col in columns:
            self.tree.heading(col, text=col_headers.get(col, col))
            self.tree.column(col, width=col_widths.get(col, 100), anchor=tk.CENTER,
                             minwidth=60)
        # Reason column left-aligned for readability
        self.tree.column("reason", anchor=tk.W)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        style = ttk.Style()
        style.configure("Treeview", font=("微软雅黑", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))

    def _load_data(self):
        """Load all grades with '待审核' status."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            db = DatabaseManager.get_instance()
            with db.get_session() as session:
                grades = session.query(Grade).filter_by(status="待审核").all()
                for g in grades:
                    # Extract new score from modify_reason
                    new_score = ""
                    if g.modify_reason:
                        m = re.search(r'修改为(\d+)', g.modify_reason)
                        new_score = m.group(1) if m else ""
                    # Extract reason text (after the colon)
                    reason_text = g.modify_reason or ""
                    # Try to get course name
                    course_name = ""
                    try:
                        from backend.models.course_plan import CoursePlan
                        from backend.models.course import Course
                        cp = session.query(CoursePlan).filter_by(
                            plan_id=g.plan_id).first()
                        if cp:
                            c = session.query(Course).filter_by(
                                course_id=cp.course_id).first()
                            if c:
                                course_name = c.course_name
                    except Exception:
                        course_name = str(g.plan_id)

                    self.tree.insert("", tk.END, values=(
                        g.grade_id,
                        g.student_id,
                        course_name,
                        g.score or "",
                        new_score,
                        reason_text,
                    ))
        except Exception as exc:
            messagebox.showerror("加载失败", f"无法加载审核数据: {exc}")

    def _get_selected_grade_id(self):
        """Get the grade_id of the selected row."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个待审核的成绩记录")
            return None
        return int(self.tree.item(selection[0], "values")[0])

    def _do_approve(self):
        grade_id = self._get_selected_grade_id()
        if grade_id is None:
            return
        result = self.controller.audit_grade(self.admin_id, grade_id, "approve")
        if result.get("success"):
            messagebox.showinfo("成功", "成绩审核已通过")
            self._load_data()
        else:
            messagebox.showerror("错误", result.get("message", "审核失败"))

    def _do_reject(self):
        grade_id = self._get_selected_grade_id()
        if grade_id is None:
            return
        result = self.controller.audit_grade(self.admin_id, grade_id, "reject")
        if result.get("success"):
            messagebox.showinfo("成功", "成绩审核已驳回")
            self._load_data()
        else:
            messagebox.showerror("错误", result.get("message", "审核操作失败"))
