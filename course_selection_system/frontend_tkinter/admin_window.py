"""
frontend_tkinter/admin_window.py - Admin Main Window.

Provides the main admin dashboard with a left sidebar navigation tree
and a right content area that switches between management pages.
"""

import tkinter as tk
from tkinter import ttk

from backend.controllers.auth_controller import AuthController

from frontend_tkinter.admin_students import AdminStudentsPage
from frontend_tkinter.admin_teachers import AdminTeachersPage
from frontend_tkinter.admin_courses import AdminCoursesPage
from frontend_tkinter.admin_grade_audit import AdminGradeAuditPage
from frontend_tkinter.admin_logs import AdminLogsPage

# Colour theme
COLOR_PRIMARY = "#2196F3"
COLOR_BG = "#FAFAFA"
COLOR_SIDEBAR = "#FFFFFF"
COLOR_BORDER = "#E0E0E0"
COLOR_TEXT = "#212121"
COLOR_STATUS_BG = "#E3F2FD"

NAV_ITEMS = {
    "人员管理": [
        ("学生管理", "students"),
        ("教师管理", "teachers"),
    ],
    "课程管理": [
        ("课程信息", "courses"),
    ],
    "选课管理": [
    ],
    "成绩管理": [
        ("成绩审核", "grade_audit"),
    ],
    "系统管理": [
        ("操作日志", "logs"),
    ],
}


class AdminWindow(tk.Toplevel):
    """Admin main window with sidebar navigation and content area."""

    def __init__(self, master, user_id, login_time, on_logout=None):
        """Initialise the admin window.

        Args:
            master: Parent tkinter widget.
            user_id (str): The authenticated admin user ID.
            login_time (str): Login timestamp string.
            on_logout (callable): Called when the user logs out.
        """
        super().__init__(master)

        self.title("管理员 - 学生选课及成绩管理系统")
        self.configure(bg=COLOR_BG)
        self.user_id = user_id
        self.login_time = login_time
        self.on_logout_callback = on_logout

        # Window geometry
        self._win_width = 1280
        self._win_height = 800
        self._center_window()
        self.minsize(1024, 600)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Track current page
        self.current_page = None
        self.page_frames = {}

        self._build_ui()

        # Default selection: 学生管理
        self._select_nav("students")

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _center_window(self):
        """Centre the window on the screen."""
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - self._win_width) // 2
        y = (screen_h - self._win_height) // 2
        self.geometry(f"{self._win_width}x{self._win_height}+{x}+{y}")

    def _build_ui(self):
        """Construct the main admin layout."""
        # Outer PanedWindow to allow resizable sidebar
        self.paned = tk.PanedWindow(
            self, orient=tk.HORIZONTAL, bg=COLOR_BORDER, sashwidth=2,
        )
        self.paned.pack(fill=tk.BOTH, expand=True)

        # ---- Sidebar ----
        self.sidebar = tk.Frame(self.paned, bg=COLOR_SIDEBAR, width=220)
        self.paned.add(self.sidebar, minsize=180)

        self._build_sidebar()

        # ---- Content area ----
        self.content_area = tk.Frame(self.paned, bg=COLOR_BG)
        self.paned.add(self.content_area)

        # ---- Status bar ----
        self.status_bar = tk.Frame(self, bg=COLOR_STATUS_BG, height=28)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_bar.pack_propagate(False)

        status_text = f"当前用户: {self.user_id}  |  登录时间: {self.login_time}"
        tk.Label(
            self.status_bar, text=status_text, font=("微软雅黑", 9),
            fg=COLOR_TEXT, bg=COLOR_STATUS_BG,
        ).pack(side=tk.LEFT, padx=12, pady=4)

        # Logout button on status bar
        tk.Button(
            self.status_bar, text="退出登录", font=("微软雅黑", 9),
            bg=COLOR_STATUS_BG, fg=COLOR_PRIMARY, relief=tk.FLAT,
            cursor="hand2", command=self._on_close,
        ).pack(side=tk.RIGHT, padx=12, pady=2)

    def _build_sidebar(self):
        """Build the sidebar navigation tree."""
        # Header
        header = tk.Frame(self.sidebar, bg=COLOR_PRIMARY, height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header, text="管理菜单", font=("微软雅黑", 13, "bold"),
            fg="white", bg=COLOR_PRIMARY,
        ).pack(expand=True)

        # Navigation Treeview
        tree_frame = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.configure("Nav.Treeview", font=("微软雅黑", 10), rowheight=30)
        style.configure("Nav.Treeview.Heading", font=("微软雅黑", 10))

        self.nav_tree = ttk.Treeview(
            tree_frame, show="tree", selectmode="browse",
            style="Nav.Treeview",
        )
        self.nav_tree.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Insert navigation items
        for section, items in NAV_ITEMS.items():
            section_id = self.nav_tree.insert("", tk.END, text=section, open=True)
            for label, nav_key in items:
                self.nav_tree.insert(section_id, tk.END, text=label, tags=(nav_key,))

        # Handle selection
        self.nav_tree.bind("<<TreeviewSelect>>", self._on_nav_select)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _on_nav_select(self, event):
        """Handle sidebar navigation selection."""
        selection = self.nav_tree.selection()
        if not selection:
            return
        item = selection[0]
        tags = self.nav_tree.item(item, "tags")
        if tags:
            nav_key = tags[0]
            self._select_nav(nav_key)

    def _select_nav(self, nav_key):
        """Switch the content area to the given page.

        Args:
            nav_key (str): Key identifying the page.
        """
        # Destroy current page
        if self.current_page is not None:
            self.current_page.pack_forget()

        # Create page if not yet created
        if nav_key not in self.page_frames:
            self.page_frames[nav_key] = self._create_page(nav_key)

        page = self.page_frames.get(nav_key)
        if page is not None:
            page.pack(fill=tk.BOTH, expand=True)
            self.current_page = page
        else:
            self.current_page = None

    def _create_page(self, nav_key):
        """Create the appropriate page frame based on navigation key.

        Args:
            nav_key (str): Page identifier.

        Returns:
            tk.Frame or None: The created page frame.
        """
        page = tk.Frame(self.content_area, bg=COLOR_BG)

        if nav_key == "students":
            AdminStudentsPage(page, self.user_id).pack(fill=tk.BOTH, expand=True)
        elif nav_key == "teachers":
            AdminTeachersPage(page, self.user_id).pack(fill=tk.BOTH, expand=True)
        elif nav_key == "courses":
            AdminCoursesPage(page, self.user_id).pack(fill=tk.BOTH, expand=True)
        elif nav_key == "grade_audit":
            AdminGradeAuditPage(page, self.user_id).pack(fill=tk.BOTH, expand=True)
        elif nav_key == "logs":
            AdminLogsPage(page, self.user_id).pack(fill=tk.BOTH, expand=True)
        else:
            # Placeholder for pages not yet implemented
            tk.Label(
                page, text=f"功能开发中: {nav_key}",
                font=("微软雅黑", 14), fg=COLOR_TEXT, bg=COLOR_BG,
            ).pack(expand=True)
        return page

    # ------------------------------------------------------------------
    # Window lifecycle
    # ------------------------------------------------------------------

    def _on_close(self):
        """Handle window close: logout and destroy."""
        AuthController().logout(self.user_id)
        self.destroy()
        if self.on_logout_callback:
            self.on_logout_callback()
