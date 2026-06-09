"""
run_pyside6.py — 启动PySide6前端版本

使用PySide6专业GUI框架构建的桌面应用（代码控制界面，不使用.ui文件）。
运行方式: python run_pyside6.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from frontend_pyside6.app import main

if __name__ == "__main__":
    main()
