"""
run_pyside6.py — 启动PySide6前端版本

使用PySide6专业GUI框架构建的桌面应用（代码控制界面，不使用.ui文件）。
运行方式: python run_pyside6.py
"""

import sys
import os
import ctypes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Pre-load Qt6Core.dll from the bundled PySide6 directory before any import.
# System PATH entries (Anaconda, standalone Qt) may point to incompatible Qt
# DLLs — Windows resolves by PATH order, so the wrong ones load and crash.
# LoadLibraryExW with LOAD_WITH_ALTERED_SEARCH_PATH forces all Qt DLL
# dependencies to resolve from the PySide6 directory exclusively.
_pyside6_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    ".venv", "Lib", "site-packages", "PySide6",
)
_qt_core = os.path.join(_pyside6_dir, "Qt6Core.dll")
if os.path.isfile(_qt_core):
    ctypes.windll.kernel32.LoadLibraryExW(_qt_core, None, 0x00000008)

from frontend_pyside6.app import main

if __name__ == "__main__":
    main()
