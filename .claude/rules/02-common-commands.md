---
description: 高校教务管理系统常用命令（启动、前端开发、测试、数据库操作）
alwaysApply: false
version: 1.0.0
---

# 常用命令

所有命令必须在项目根目录执行。

## 启动应用

```bash
# 一键启动（包含 MySQL + Flask）
python run.py

# 或使用批处理（Windows）
start_all.bat          # 选项 [2] Auto Setup & Start（推荐首次）
```

## 前端开发模式（热更新）

```bash
# 终端 1 — 后端
python run.py

# 终端 2 — 前端热更新（访问 http://localhost:5173，API 自动代理到 :5000）
cd frontend && npm run dev
```

## 测试

```bash
# 运行全部测试
python -m pytest tests/ -v

# 运行单个测试模块
python -m pytest tests/test_enrollment.py -v
```

## 数据库操作

```bash
# 启动便携版 MySQL
cd mysql-portable && start_mysql.bat

# 导入 DDL + 测试数据（项目根目录）
# MySQL 初始化脚本: backend/config/init_database_mysql.sql
```
