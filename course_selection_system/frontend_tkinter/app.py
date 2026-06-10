"""
frontend_tkinter/app.py - Main Application Entry Point.

Initialises the database connection, launches the login window,
and routes authenticated users to their role-specific main window.
"""

import tkinter as tk
from tkinter import messagebox
from datetime import datetime

from backend.models.base import DatabaseManager
from frontend_tkinter.login_window import LoginWindow
from frontend_tkinter.admin_window import AdminWindow
from frontend_tkinter.teacher_window import TeacherWindow
from frontend_tkinter.student_window import StudentWindow


class Application:
    """Main application controller.

    Uses the root window directly — no withdraw() — to avoid
    Toplevel visibility issues on Windows tkinter 8.6.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.current_window = None
        self.user_id = None
        self.role = None
        self.login_time = None

    def run(self):
        """Initialise the database and show the login window."""
        try:
            db_mgr = DatabaseManager.get_instance()
            db_mgr.create_all_tables()
        except Exception as exc:
            messagebox.showerror(
                "数据库连接失败",
                f"无法连接数据库，请检查配置。\n\n错误信息: {exc}",
            )
            self.root.destroy()
            return

        self.show_login()
        self.root.mainloop()

    def _clear_root(self):
        """Destroy all child widgets of root, resetting it for the next view."""
        for w in self.root.winfo_children():
            w.destroy()

    def show_login(self):
        """Display the login form directly in the root window."""
        self._clear_root()
        if self.current_window is not None:
            self.current_window.destroy()
            self.current_window = None

        login_win = LoginWindow(self.root, on_success=self.on_login_success)
        self.current_window = login_win

    def on_login_success(self, user_id, role):
        """Callback when login succeeds. Open the appropriate role window.

        Args:
            user_id (str): The authenticated user ID.
            role (str): The user's role (admin/teacher/student).
        """
        self.user_id = user_id
        self.role = role
        self.login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self._clear_root()
        self.root.title("学生选课及成绩管理系统")  # Reset title

        # Open the role-specific window (each is a Toplevel)
        if role == "admin":
            win = AdminWindow(
                self.root, user_id=self.user_id, login_time=self.login_time,
                on_logout=self.on_logout,
            )
        elif role == "teacher":
            win = TeacherWindow(
                self.root, user_id=self.user_id, login_time=self.login_time,
                on_logout=self.on_logout,
            )
        elif role == "student":
            win = StudentWindow(
                self.root, user_id=self.user_id, login_time=self.login_time,
                on_logout=self.on_logout,
            )
        else:
            messagebox.showerror("错误", f"未知的角色类型: {role}")
            self.show_login()
            return

        # Hide root AFTER Toplevel is created so WM tracks it properly
        self.root.withdraw()
        self.current_window = win

    def on_logout(self):
        """Callback when the user logs out from a role window.

        Logs out via AuthController and returns to the login screen.
        """
        from backend.controllers.auth_controller import AuthController

        if self.user_id:
            AuthController().logout(self.user_id)

        self.user_id = None
        self.role = None
        self.login_time = None

        if self.current_window is not None:
            self.current_window.destroy()
            self.current_window = None

        self.root.deiconify()
        self.show_login()


def main():
    """Entry point for the tkinter frontend."""
    app = Application()
    app.run()
