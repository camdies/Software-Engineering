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


class LoginWindow:
    """Login window for user authentication.

    Embeds directly in the root window (not a Toplevel) to avoid
    visibility issues on Windows when root is withdrawn.
    """

    def __init__(self, master, on_success=None):
        self.master = master
        self.on_success_callback = on_success
        self.auth_controller = AuthController()
        self.error_label = None

        master.title("学生选课及成绩管理系统 - 登录")
        master.configure(bg=COLOR_BG)
        master.resizable(False, False)

        self._win_width = 420
        self._win_height = 380
        self._center_window()

        self._build_ui()

        master.bind("<Return>", lambda _e: self._do_login())
        master.protocol("WM_DELETE_WINDOW", self._on_close)

    def destroy(self):
        """Clean up — called by app before recreating the login view."""
        self.master.unbind("<Return>")

    def _center_window(self):
        screen_w = self.master.winfo_screenwidth()
        screen_h = self.master.winfo_screenheight()
        x = (screen_w - self._win_width) // 2
        y = (screen_h - self._win_height) // 2
        self.master.geometry(f"{self._win_width}x{self._win_height}+{x}+{y}")

    def _build_ui(self):
        master = self.master

        header = tk.Label(
            master, text="学生选课及成绩管理系统",
            font=("微软雅黑", 16, "bold"),
            fg=COLOR_PRIMARY, bg=COLOR_BG,
        )
        header.pack(pady=(30, 5))

        sub_header = tk.Label(
            master, text="请登录您的账号",
            font=("微软雅黑", 10),
            fg=COLOR_SUBTEXT, bg=COLOR_BG,
        )
        sub_header.pack(pady=(0, 25))

        form = tk.Frame(master, bg=COLOR_BG)
        form.pack(padx=50, fill=tk.X)

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

        tk.Label(
            form, text="密码", font=("微软雅黑", 11),
            fg=COLOR_TEXT, bg=COLOR_BG,
        ).grid(row=2, column=0, sticky="w", pady=(0, 2))

        self.entry_password = tk.Entry(
            form, font=("微软雅黑", 11), width=30,
            show="*", relief=tk.SOLID, borderwidth=1,
        )
        self.entry_password.grid(row=3, column=0, ipady=4, pady=(0, 12))

        self.error_label = tk.Label(
            form, text="", font=("微软雅黑", 9),
            fg=COLOR_ERROR, bg=COLOR_BG, wraplength=300,
        )
        self.error_label.grid(row=4, column=0, pady=(0, 10))

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

    def _do_login(self):
        user_id = self.entry_user_id.get().strip()
        password = self.entry_password.get()

        if not user_id:
            self._show_error("请输入用户ID")
            return
        if not password:
            self._show_error("请输入密码")
            return

        self.btn_login.config(state=tk.DISABLED, text="登录中...")
        self.master.update()

        result = self.auth_controller.login(user_id, password)

        self.btn_login.config(state=tk.NORMAL, text="登录")

        if result.get("success"):
            self._clear_error()
            if self.on_success_callback:
                self.on_success_callback(result["user_id"], result["role"])
        else:
            msg = result.get("message", "登录失败")
            if "锁定" in msg or "locked" in msg.lower():
                messagebox.showwarning("账号已锁定", msg)
            else:
                self._show_error(msg)

    def _show_error(self, message):
        if self.error_label:
            self.error_label.config(text=message)

    def _clear_error(self):
        if self.error_label:
            self.error_label.config(text="")

    def _on_close(self):
        self.master.destroy()
