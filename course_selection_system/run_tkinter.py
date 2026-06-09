"""
run_tkinter.py — 启动Tkinter前端版本

使用Python标准库tkinter构建的桌面应用。
运行方式: python run_tkinter.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from frontend_tkinter.app import main

if __name__ == "__main__":
    main()
