"""
frontend_tkinter/student_stats.py - Academic Statistics Page.

Displays the student's academic summary (total credits, GPA,
failed courses) via StatsController.get_academic_stats().
"""

import tkinter as tk
from tkinter import ttk, messagebox

from backend.controllers.stats_controller import StatsController

# Colour theme
COLOR_PRIMARY = "#2196F3"
COLOR_PRIMARY_HOVER = "#1976D2"
COLOR_BG = "#FAFAFA"
COLOR_TEXT = "#212121"
COLOR_DANGER = "#F44336"


class StudentStatsPage(tk.Frame):
    """Academic statistics page for students."""

    def __init__(self, master, student_id):
        """Initialise the stats page.

        Args:
            master: Parent widget.
            student_id (str): The student's user ID.
        """
        super().__init__(master, bg=COLOR_BG)
        self.student_id = student_id
        self.sc = StatsController()

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        title_frame = tk.Frame(self, bg=COLOR_BG)
        title_frame.pack(fill=tk.X, padx=16, pady=(12, 8))
        tk.Label(
            title_frame, text="学业统计", font=("微软雅黑", 14, "bold"),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).pack(side=tk.LEFT)

        # Summary cards
        summary_frame = tk.Frame(self, bg=COLOR_BG)
        summary_frame.pack(fill=tk.X, padx=16, pady=(0, 12))

        # Credit card
        credit_card = tk.Frame(summary_frame, bg="white", relief=tk.SOLID,
                               borderwidth=1, padx=30, pady=20)
        credit_card.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(
            credit_card, text="已修学分", font=("微软雅黑", 10),
            fg=COLOR_TEXT, bg="white",
        ).pack()
        self.lbl_credits = tk.Label(
            credit_card, text="--", font=("微软雅黑", 28, "bold"),
            fg=COLOR_PRIMARY, bg="white",
        )
        self.lbl_credits.pack(pady=(4, 0))

        # GPA card
        gpa_card = tk.Frame(summary_frame, bg="white", relief=tk.SOLID,
                            borderwidth=1, padx=30, pady=20)
        gpa_card.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(
            gpa_card, text="累计 GPA", font=("微软雅黑", 10),
            fg=COLOR_TEXT, bg="white",
        ).pack()
        self.lbl_gpa = tk.Label(
            gpa_card, text="--", font=("微软雅黑", 28, "bold"),
            fg=COLOR_PRIMARY, bg="white",
        )
        self.lbl_gpa.pack(pady=(4, 0))

        # Failed courses section
        failed_title = tk.Frame(self, bg=COLOR_BG)
        failed_title.pack(fill=tk.X, padx=16, pady=(0, 4))
        tk.Label(
            failed_title, text="未通过课程", font=("微软雅黑", 11, "bold"),
            fg=COLOR_DANGER, bg=COLOR_BG,
        ).pack(side=tk.LEFT)

        tree_frame = tk.Frame(self, bg=COLOR_BG)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        columns = ("course_name", "score", "semester")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="browse",
        )

        col_headers = {"course_name": "课程名称", "score": "成绩", "semester": "学期"}
        col_widths = {"course_name": 300, "score": 120, "semester": 180}

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

    def _load_data(self):
        """Load academic statistics for the student."""
        stats = self.sc.get_academic_stats(self.student_id)

        self.lbl_credits.config(text=str(stats.get("total_credits", "0.0")))
        self.lbl_gpa.config(text=str(stats.get("cumulative_gpa", "0.00")))

        for item in self.tree.get_children():
            self.tree.delete(item)

        failed = stats.get("failed_courses", [])
        if failed:
            for row in failed:
                self.tree.insert("", tk.END, values=(
                    row.get("course_name", ""),
                    row.get("score", ""),
                    row.get("semester", ""),
                ))
        else:
            # Show a placeholder indicating all courses passed
            self.tree.insert("", tk.END, values=(
                "暂无未通过课程", "", "",
            ))
