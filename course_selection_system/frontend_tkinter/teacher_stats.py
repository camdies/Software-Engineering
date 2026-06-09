"""
frontend_tkinter/teacher_stats.py - Statistics View for Teachers.

Provides course plan selection and displays class statistics
(avg, max, min, pass_rate, rank list) via StatsController.
Supports exporting stats to Excel.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from backend.controllers.teacher_controller import TeacherController
from backend.controllers.stats_controller import StatsController

# Colour theme
COLOR_PRIMARY = "#2196F3"
COLOR_PRIMARY_HOVER = "#1976D2"
COLOR_BG = "#FAFAFA"
COLOR_TEXT = "#212121"
COLOR_SUCCESS = "#4CAF50"


class TeacherStatsPage(tk.Frame):
    """Statistics view for teachers."""

    def __init__(self, master, teacher_id):
        """Initialise the stats page.

        Args:
            master: Parent widget.
            teacher_id (str): The teacher's user ID.
        """
        super().__init__(master, bg=COLOR_BG)
        self.teacher_id = teacher_id
        self.tc = TeacherController()
        self.sc = StatsController()
        self.plans_data = []
        self.current_stats = None

        self._build_ui()
        self._load_plans()

    def _build_ui(self):
        title_frame = tk.Frame(self, bg=COLOR_BG)
        title_frame.pack(fill=tk.X, padx=16, pady=(12, 8))
        tk.Label(
            title_frame, text="统计分析", font=("微软雅黑", 14, "bold"),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).pack(side=tk.LEFT)

        # Selector
        selector = tk.Frame(self, bg=COLOR_BG, height=40)
        selector.pack(fill=tk.X, padx=16, pady=(0, 8))
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
            selector, text="导出Excel", font=("微软雅黑", 10),
            bg=COLOR_SUCCESS, fg="white",
            activebackground="#43A047", activeforeground="white",
            relief=tk.FLAT, cursor="hand2",
            command=self._do_export,
        ).pack(side=tk.LEFT)

        # Statistics summary
        summary_frame = tk.LabelFrame(
            self, text="成绩概览", font=("微软雅黑", 10, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT,
        )
        summary_frame.pack(fill=tk.X, padx=16, pady=(0, 8))

        summary_grid = tk.Frame(summary_frame, bg=COLOR_BG)
        summary_grid.pack(padx=20, pady=12, fill=tk.X)

        self.stat_labels = {}
        stats_defs = [
            ("平均分", "lbl_avg"),
            ("最高分", "lbl_max"),
            ("最低分", "lbl_min"),
            ("及格率", "lbl_pass_rate"),
        ]
        for i, (label_text, key) in enumerate(stats_defs):
            tk.Label(
                summary_grid, text=label_text + ":", font=("微软雅黑", 11, "bold"),
                fg=COLOR_TEXT, bg=COLOR_BG,
            ).grid(row=0, column=i * 2, sticky="e", padx=(0, 4))

            lbl = tk.Label(
                summary_grid, text="--", font=("微软雅黑", 14, "bold"),
                fg=COLOR_PRIMARY, bg=COLOR_BG,
            )
            lbl.grid(row=0, column=i * 2 + 1, sticky="w", padx=(0, 20))
            self.stat_labels[key] = lbl

        # Rank list
        rank_title = tk.Frame(self, bg=COLOR_BG)
        rank_title.pack(fill=tk.X, padx=16, pady=(0, 4))
        tk.Label(
            rank_title, text="成绩排名", font=("微软雅黑", 11, "bold"),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).pack(side=tk.LEFT)

        tree_frame = tk.Frame(self, bg=COLOR_BG)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 8))

        columns = ("rank", "student_id", "name", "score")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="browse",
        )
        col_headers = {"rank": "排名", "student_id": "学号",
                       "name": "姓名", "score": "成绩"}
        col_widths = {"rank": 80, "student_id": 160, "name": 200, "score": 120}

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

    def _load_plans(self):
        """Load teaching plans."""
        self.plans_data = self.tc.get_teaching_plans(self.teacher_id)
        plan_list = []
        for p in self.plans_data:
            plan_list.append(
                f"[{p.get('course_id','')}] {p.get('semester','')} "
                f"(plan_id={p.get('plan_id')})"
            )
        self.combo_plan["values"] = plan_list
        if plan_list:
            self.combo_plan.current(0)
            self._on_plan_select(None)

    def _on_plan_select(self, event):
        """Load statistics for the selected plan."""
        idx = self.combo_plan.current()
        if idx < 0 or idx >= len(self.plans_data):
            return

        plan_id = self.plans_data[idx].get("plan_id")
        stats = self.sc.get_class_stats(self.teacher_id, plan_id)
        self.current_stats = stats

        # Update summary labels
        self.stat_labels["lbl_avg"].config(text=str(stats.get("avg_score", "0.0")))
        self.stat_labels["lbl_max"].config(text=str(stats.get("max_score", "0")))
        self.stat_labels["lbl_min"].config(text=str(stats.get("min_score", "0")))
        self.stat_labels["lbl_pass_rate"].config(
            text=f"{stats.get('pass_rate', 0.0):.1%}")

        # Update rank list
        for item in self.tree.get_children():
            self.tree.delete(item)

        rank_list = stats.get("rank_list", [])
        for row in rank_list:
            self.tree.insert("", tk.END, values=(
                row.get("rank", ""),
                row.get("student_id", ""),
                row.get("name", ""),
                row.get("score", ""),
            ))

    def _do_export(self):
        """Export current statistics to an Excel file."""
        if self.current_stats is None:
            messagebox.showwarning("提示", "请先选择课程查看统计数据")
            return

        file_path = filedialog.asksaveasfilename(
            title="导出统计数据",
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx"), ("所有文件", "*.*")],
        )
        if not file_path:
            return

        success = self.sc.export_stats_to_excel(self.current_stats, file_path)
        if success:
            messagebox.showinfo("成功", f"统计数据已导出到:\n{file_path}")
        else:
            messagebox.showerror("错误", "导出失败，请重试")
