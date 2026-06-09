"""
frontend_tkinter/student_window.py - Student Main Window.

Provides sidebar navigation and content switching for student operations:
- 选课中心: Course enrollment
- 已选课程: My enrolled courses
- 成绩查询: Grade query
- 学业统计: Academic statistics
"""

import tkinter as tk
from tkinter import ttk

from backend.controllers.auth_controller import AuthController

from frontend_tkinter.student_enroll import StudentEnrollPage
from frontend_tkinter.student_my_courses import StudentMyCoursesPage
from frontend_tkinter.student_grades import StudentGradesPage
from frontend_tkinter.student_stats import StudentStatsPage

# Colour theme
COLOR_PRIMARY = "#2196F3"
COLOR_BG = "#FAFAFA"
COLOR_SIDEBAR = "#FFFFFF"
COLOR_BORDER = "#E0E0E0"
COLOR_TEXT = "#212121"
COLOR_STATUS_BG = "#E3F2FD"

NAV_ITEMS = [
    ("选课中心", "enroll"),
    ("已选课程", "my_courses"),
    ("成绩查询", "grades"),
    ("学业统计", "stats"),
]


class StudentWindow(tk.Toplevel):
    """Student main window with sidebar navigation and content area."""

    def __init__(self, master, user_id, login_time, on_logout=None):
        """Initialise the student window.

        Args:
            master: Parent tkinter widget.
            user_id (str): The authenticated student user ID.
            login_time (str): Login timestamp string.
            on_logout (callable): Called when the user logs out.
        """
        super().__init__(master)

        self.title("学生 - 学生选课及成绩管理系统")
        self.configure(bg=COLOR_BG)
        self.user_id = user_id
        self.login_time = login_time
        self.on_logout_callback = on_logout

        self._win_width = 1200
        self._win_height = 750
        self._center_window()
        self.minsize(960, 550)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.current_page = None
        self.page_frames = {}

        self._build_ui()
        self._select_nav("enroll")

    def _center_window(self):
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - self._win_width) // 2
        y = (screen_h - self._win_height) // 2
        self.geometry(f"{self._win_width}x{self._win_height}+{x}+{y}")

    def _build_ui(self):
        self.paned = tk.PanedWindow(
            self, orient=tk.HORIZONTAL, bg=COLOR_BORDER, sashwidth=2,
        )
        self.paned.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        self.sidebar = tk.Frame(self.paned, bg=COLOR_SIDEBAR, width=200)
        self.paned.add(self.sidebar, minsize=160)

        header = tk.Frame(self.sidebar, bg=COLOR_PRIMARY, height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, text="学生菜单", font=("微软雅黑", 13, "bold"),
            fg="white", bg=COLOR_PRIMARY,
        ).pack(expand=True)

        # Navigation buttons
        nav_frame = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR)
        nav_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.nav_buttons = {}
        for label, nav_key in NAV_ITEMS:
            btn = tk.Button(
                nav_frame, text=label, font=("微软雅黑", 11),
                bg=COLOR_SIDEBAR, fg=COLOR_TEXT,
                activebackground=COLOR_PRIMARY, activeforeground="white",
                relief=tk.FLAT, cursor="hand2", anchor="w",
                command=lambda k=nav_key: self._select_nav(k),
            )
            btn.pack(fill=tk.X, pady=1)
            self.nav_buttons[nav_key] = btn

        # Content area
        self.content_area = tk.Frame(self.paned, bg=COLOR_BG)
        self.paned.add(self.content_area)

        # Status bar
        self.status_bar = tk.Frame(self, bg=COLOR_STATUS_BG, height=28)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar.pack_propagate(False)

        status_text = f"当前用户: {self.user_id}  |  登录时间: {self.login_time}"
        tk.Label(
            self.status_bar, text=status_text, font=("微软雅黑", 9),
            fg=COLOR_TEXT, bg=COLOR_STATUS_BG,
        ).pack(side=tk.LEFT, padx=12, pady=4)

        tk.Button(
            self.status_bar, text="退出登录", font=("微软雅黑", 9),
            bg=COLOR_STATUS_BG, fg=COLOR_PRIMARY, relief=tk.FLAT,
            cursor="hand2", command=self._on_close,
        ).pack(side=tk.RIGHT, padx=12, pady=2)

    def _select_nav(self, nav_key):
        """Switch to the given navigation page.

        Args:
            nav_key (str): Page identifier.
        """
        for key, btn in self.nav_buttons.items():
            if key == nav_key:
                btn.config(bg=COLOR_PRIMARY, fg="white")
            else:
                btn.config(bg=COLOR_SIDEBAR, fg=COLOR_TEXT)

        if self.current_page is not None:
            self.current_page.pack_forget()

        if nav_key not in self.page_frames:
            self.page_frames[nav_key] = self._create_page(nav_key)

        page = self.page_frames.get(nav_key)
        if page is not None:
            page.pack(fill=tk.BOTH, expand=True)
            self.current_page = page

    def _create_page(self, nav_key):
        """Create the page frame for the given nav key.

        Args:
            nav_key (str): Page identifier.

        Returns:
            tk.Frame or None
        """
        page = tk.Frame(self.content_area, bg=COLOR_BG)

        if nav_key == "enroll":
            StudentEnrollPage(page, self.user_id).pack(fill=tk.BOTH, expand=True)
        elif nav_key == "my_courses":
            StudentMyCoursesPage(page, self.user_id).pack(fill=tk.BOTH, expand=True)
        elif nav_key == "grades":
            StudentGradesPage(page, self.user_id).pack(fill=tk.BOTH, expand=True)
        elif nav_key == "stats":
            StudentStatsPage(page, self.user_id).pack(fill=tk.BOTH, expand=True)
        else:
            tk.Label(
                page, text=f"功能开发中: {nav_key}", font=("微软雅黑", 14),
                fg=COLOR_TEXT, bg=COLOR_BG,
            ).pack(expand=True)
        return page

    def _on_close(self):
        """Handle window close: logout and destroy."""
        AuthController().logout(self.user_id)
        self.destroy()
        if self.on_logout_callback:
            self.on_logout_callback()
