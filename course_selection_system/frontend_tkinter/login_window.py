"""
frontend_tkinter/login_window.py - Login Window.

Provides the authentication UI using AuthController.login().
On success, invokes a callback to transition to the role-specific window.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from backend.controllers.auth_controller import AuthController

# Colour theme constants
COLOR_PRIMARY = "#2196F3"
COLOR_PRIMARY_HOVER = "#1976D2"
COLOR_BG = "#FAFAFA"
COLOR_ERROR = "#F44336"
COLOR_TEXT = "#212121"
COLOR_SUBTEXT = "#757575"


class LoginWindow(tk.Toplevel):
    """Login window for user authentication.

    Centered 420x380 window with user_id/password fields,
    login/exit buttons, and error feedback.
    """

    def __init__(self, master, on_success=None):
        """Initialise the login window.

        Args:
            master: Parent tkinter widget (usually the root Tk).
            on_success (callable): Callback(user_id, role) on successful login.
        """
        super().__init__(master)

        self.title("学生选课及成绩管理系统 - 登录")
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self.on_success_callback = on_success
        self.auth_controller = AuthController()
        self.error_label = None

        # Window size and centering
        self._win_width = 420
        self._win_height = 380
        self._center_window()

        # Make modal to parent
        self.transient(master)
        self.grab_set()

        # Build UI
        self._build_ui()

        # Bind Enter key to login
        self.bind("<Return>", lambda _e: self._do_login())
        # Handle window close (Exit)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def _center_window(self):
        """Centre the window on the screen."""
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - self._win_width) // 2
        y = (screen_h - self._win_height) // 2
        self.geometry(f"{self._win_width}x{self._win_height}+{x}+{y}")

    def _build_ui(self):
        """Construct the login form."""
        # Header
        header = tk.Label(
            self, text="学生选课及成绩管理系统",
            font=("微软雅黑", 16, "bold"),
            fg=COLOR_PRIMARY, bg=COLOR_BG,
        )
        header.pack(pady=(30, 5))

        sub_header = tk.Label(
            self, text="请登录您的账号",
            font=("微软雅黑", 10),
            fg=COLOR_SUBTEXT, bg=COLOR_BG,
        )
        sub_header.pack(pady=(0, 25))

        # Form frame
        form = tk.Frame(self, bg=COLOR_BG)
        form.pack(padx=50, fill=tk.X)

        # User ID
        tk.Label(
            form, text="用户ID", font=("微软雅黑", 11),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).grid(row=0, column=0, sticky="w", pady=(0, 2))

        self.entry_user_id = tk.Entry(
            form, font=("微软雅黑", 11), width=30,
            relief=tk.SOLID, borderwidth=1,
        )
        self.entry_user_id.grid(row=1, column=0, ipady=4, pady=(0, 12))
        self.entry_user_id.focus_set()

        # Password
        tk.Label(
            form, text="密码", font=("微软雅黑", 11),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).grid(row=2, column=0, sticky="w", pady=(0, 2))

        self.entry_password = tk.Entry(
            form, font=("微软雅黑", 11), width=30,
            show="*", relief=tk.SOLID, borderwidth=1,
        )
        self.entry_password.grid(row=3, column=0, ipady=4, pady=(0, 12))

        # Error message label (hidden by default)
        self.error_label = tk.Label(
            form, text="", font=("微软雅黑", 9),
            fg=COLOR_ERROR, bg=COLOR_BG, wraplength=300,
        )
        self.error_label.grid(row=4, column=0, pady=(0, 10))

        # Buttons frame
        btn_frame = tk.Frame(form, bg=COLOR_BG)
        btn_frame.grid(row=5, column=0, pady=(5, 0))

        self.btn_login = tk.Button(
            btn_frame, text="登录", font=("微软雅黑", 11, "bold"),
            bg=COLOR_PRIMARY, fg="white",
            activebackground=COLOR_PRIMARY_HOVER, activeforeground="white",
            relief=tk.FLAT, cursor="hand2",
            width=12, height=1,
            command=self._do_login,
        )
        self.btn_login.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_exit = tk.Button(
            btn_frame, text="退出", font=("微软雅黑", 11),
            bg="#E0E0E0", fg=COLOR_TEXT,
            activebackground="#BDBDBD", activeforeground=COLOR_TEXT,
            relief=tk.FLAT, cursor="hand2",
            width=12, height=1,
            command=self._on_close,
        )
        self.btn_exit.pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _do_login(self):
        """Validate input and attempt login via AuthController."""
        user_id = self.entry_user_id.get().strip()
        password = self.entry_password.get()

        if not user_id:
            self._show_error("请输入用户ID")
            return
        if not password:
            self._show_error("请输入密码")
            return

        # Disable the login button to prevent double-submit
        self.btn_login.config(state=tk.DISABLED, text="登录中...")
        self.update()

        result = self.auth_controller.login(user_id, password)

        self.btn_login.config(state=tk.NORMAL, text="登录")

        if result.get("success"):
            self._clear_error()
            self.grab_release()
            if self.on_success_callback:
                self.on_success_callback(result["user_id"], result["role"])
        else:
            msg = result.get("message", "登录失败")
            if "锁定" in msg or "locked" in msg.lower():
                messagebox.showwarning("账号已锁定", msg)
            else:
                self._show_error(msg)

    def _show_error(self, message):
        """Display an error message in red below the form fields."""
        if self.error_label:
            self.error_label.config(text=message)

    def _clear_error(self):
        """Clear the error message label."""
        if self.error_label:
            self.error_label.config(text="")

    def _on_close(self):
        """Handle window close / Exit button."""
        self.grab_release()
        self.destroy()
        # If no callback has fired, the app should quit
        if self.on_success_callback is None:
            self.master.destroy()
