---
description: 高校教务管理系统技术栈速查表（前端、后端、ORM、数据库、Excel/PDF、测试、构建分发）
alwaysApply: true
version: 1.0.0
---

# 技术栈速查

| 层级 | 技术 | 备注 |
|------|------|------|
| 前端 | Vue 3 (Composition API) + Element Plus + ECharts + Vite | SPA，构建产物在 `frontend/dist/` |
| 后端 | Flask + JWT (HS256, 24h) | `run.py` 入口，工厂模式 |
| ORM | SQLAlchemy + PyMySQL | 双数据库支持 (MySQL / SQL Server) |
| 数据库 | MySQL 8.0+ (默认) | 便携版在 `mysql-portable/`，嵌入式 Python 在 `python-embed/` |
| Excel | openpyxl（生成）+ pandas（统计） | 成绩批量导入、统计导出、课表导出 |
| PDF | reportlab | 仅课表 PDF 导出（学生端） |
| 测试 | pytest | `tests/` 目录 |
| 构建 | npm (Node 18+) | Vite 构建到 `frontend/dist/` |
| 分发 | NSIS 安装包 | `develop tool/setup.nsi` → `EduMgmt-Setup-3.0.0.exe` |

## 角色体系

| 角色 | 权限范围 |
|------|----------|
| `admin` | 人员管理、课程管理、审核中心、选课统计、选课控制、操作日志 |
| `teacher` | 授课计划、成绩录入/修改、统计分析 |
| `student` | 自主选课、课表查询、成绩查询、学业统计 |
