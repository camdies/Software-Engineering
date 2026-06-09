"""Admin enrollment time period control page."""

import os
import configparser
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QGroupBox, QFormLayout,
                                QMessageBox, QDateTimeEdit)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont

from backend.config.settings import Settings

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "backend", "config", "config.ini")

STYLE = """
#primaryBtn { background-color: #2196f3; color: white; border: none; border-radius: 4px; padding: 8px 20px; font-size: 13px; }
#primaryBtn:hover { background-color: #1976d2; }
#secondaryBtn { background-color: #e0e0e0; color: #424242; border: none; border-radius: 4px; padding: 8px 20px; font-size: 13px; }
#secondaryBtn:hover { background-color: #bdbdbd; }
QGroupBox { font-size: 14px; font-weight: bold; color: #1565c0; border: 2px solid #e3f2fd; border-radius: 8px; margin-top: 12px; padding-top: 18px; }
QGroupBox::title { subcontrol-origin: margin; left: 16px; padding: 0 8px; }
QLabel { font-size: 13px; }
"""


class EnrollmentControlPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = Settings.get_instance()
        self._config_path = os.path.normpath(CONFIG_PATH)
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("选课时段控制")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #1565c0;")
        layout.addWidget(title)

        # Enrollment open/close toggle
        toggle_group = QGroupBox("选课开关")
        toggle_layout = QHBoxLayout()
        self._status_label = QLabel("当前状态: 未知")
        self._status_label.setFont(QFont("Microsoft YaHei", 12))
        toggle_layout.addWidget(self._status_label)
        toggle_layout.addStretch()

        self._toggle_btn = QPushButton()
        self._toggle_btn.setObjectName("primaryBtn")
        self._toggle_btn.clicked.connect(self._toggle_enrollment)
        toggle_layout.addWidget(self._toggle_btn)
        toggle_group.setLayout(toggle_layout)
        layout.addWidget(toggle_group)

        # Time settings
        time_group = QGroupBox("选课时间段设置")
        time_layout = QFormLayout()
        time_layout.setSpacing(12)

        self._open_time = QDateTimeEdit()
        self._open_time.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self._open_time.setCalendarPopup(True)
        time_layout.addRow("开放时间:", self._open_time)

        self._close_time = QDateTimeEdit()
        self._close_time.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self._close_time.setCalendarPopup(True)
        time_layout.addRow("关闭时间:", self._close_time)

        save_btn = QPushButton("保存时间设置")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save_time_settings)
        time_layout.addRow(save_btn)

        time_group.setLayout(time_layout)
        layout.addWidget(time_group)

        layout.addStretch()

    def _load_settings(self):
        try:
            is_open = self._settings.enrollment_is_open
            label_text = f"当前状态: {'选课已开放' if is_open else '选课已关闭'}"
            self._status_label.setText(label_text)
            self._status_label.setStyleSheet(
                f"color: {'#4caf50' if is_open else '#f44336'}; font-weight: bold;")
            self._toggle_btn.setText("关闭选课" if is_open else "开启选课")
            toggle_style = (
                f"QPushButton {{ background-color: {'#f44336' if is_open else '#4caf50'}; "
                f"color: white; border: none; border-radius: 4px; padding: 8px 20px; font-size: 13px; }}"
                f"QPushButton:hover {{ background-color: {'#d32f2f' if is_open else '#388e3c'}; }}")
            self._toggle_btn.setStyleSheet(toggle_style)

            if self._settings.enrollment_open_time:
                self._open_time.setDateTime(
                    QDateTime.fromString(self._settings.enrollment_open_time, "yyyy-MM-dd HH:mm:ss"))
            else:
                self._open_time.setDateTime(QDateTime.currentDateTime())
            if self._settings.enrollment_close_time:
                self._close_time.setDateTime(
                    QDateTime.fromString(self._settings.enrollment_close_time, "yyyy-MM-dd HH:mm:ss"))
            else:
                future = QDateTime.currentDateTime().addMonths(1)
                self._close_time.setDateTime(future)
        except Exception as e:
            self._status_label.setText(f"当前状态: 读取失败 ({e})")

    def _save_config(self, section, key, value):
        cfg = configparser.ConfigParser()
        cfg.read(self._config_path, encoding="utf-8")
        if section not in cfg:
            cfg.add_section(section)
        cfg.set(section, key, str(value))
        with open(self._config_path, "w", encoding="utf-8") as f:
            cfg.write(f)
        # Force-reload settings
        Settings._config = None
        self._settings = Settings.get_instance()

    def _toggle_enrollment(self):
        try:
            is_open = self._settings.enrollment_is_open
            new_state = not is_open
            self._save_config("enrollment", "is_open", str(new_state).lower())
            self._load_settings()
            QMessageBox.information(self, "成功",
                f"选课已{'开启' if new_state else '关闭'}")
        except Exception as e:
            QMessageBox.warning(self, "失败", f"操作失败: {e}")

    def _save_time_settings(self):
        try:
            open_str = self._open_time.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            close_str = self._close_time.dateTime().toString("yyyy-MM-dd HH:mm:ss")

            if self._open_time.dateTime() >= self._close_time.dateTime():
                QMessageBox.warning(self, "提示", "关闭时间必须晚于开放时间")
                return

            # Save both in one write to avoid intermediate state
            cfg = configparser.ConfigParser()
            cfg.read(self._config_path, encoding="utf-8")
            cfg.set("enrollment", "open_time", open_str)
            cfg.set("enrollment", "close_time", close_str)
            with open(self._config_path, "w", encoding="utf-8") as f:
                cfg.write(f)
            Settings._config = None
            self._settings = Settings.get_instance()
            self._load_settings()

            QMessageBox.information(self, "成功", "选课时间段设置已保存")
        except Exception as e:
            QMessageBox.warning(self, "失败", f"保存失败: {e}")
