"""
frontend_tkinter/student_grades.py - Grade Query Page.

Displays the student's grades across all courses
via StudentController.get_my_grades().
"""

import tkinter as tk
from tkinter import ttk

from backend.controllers.student_controller import StudentController

# Colour theme
COLOR_PRIMARY = "#2196F3"
COLOR_PRIMARY_HOVER = "#1976D2"
COLOR_BG = "#FAFAFA"
COLOR_TEXT = "#212121"


class StudentGradesPage(tk.Frame):
    """Grade query page for students."""

    def __init__(self, master, student_id):
        """Initialise the grades page.

        Args:
            master: Parent widget.
            student_id (str): The student's user ID.
        """
        super().__init__(master, bg=COLOR_BG)
        self.student_id = student_id
        self.sc = StudentController()

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        title_frame = tk.Frame(self, bg=COLOR_BG)
        title_frame.pack(fill=tk.X, padx=16, pady=(12, 8))
        tk.Label(
            title_frame, text="成绩查询", font=("微软雅黑", 14, "bold"),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).pack(side=tk.LEFT)

        # Toolbar
        toolbar = tk.Frame(self, bg=COLOR_BG, height=36)
        toolbar.pack(fill=tk.X, padx=16, pady=(0, 6))
        toolbar.pack_propagate(False)

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

        columns = ("course_name", "credit", "score", "gpa_point", "semester", "status")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="browse",
        )

        col_headers = {
            "course_name": "课程", "credit": "学分", "score": "成绩",
            "gpa_point": "绩点", "semester": "学期", "status": "状态",
        }
        col_widths = {"course_name": 220, "credit": 80, "score": 80,
                      "gpa_point": 80, "semester": 160, "status": 100}

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

    def _load_data(self):
        """Load the student's grades."""
        grades = self.sc.get_my_grades(self.student_id)

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in grades:
            self.tree.insert("", tk.END, values=(
                row.get("course_name", ""),
                row.get("credit", ""),
                row.get("score", ""),
                row.get("gpa_point", ""),
                row.get("semester", ""),
                row.get("status", ""),
            ))
