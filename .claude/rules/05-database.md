---
description: 数据库表结构说明和新增表流程——修改 ORM 模型或数据库脚本时遵守
alwaysApply: false
globs:
  - "backend/models/**/*.py"
  - "backend/config/*.sql"
version: 1.0.0
---

# 数据库说明

## 11张表

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `class_period` | 上课节次（11节固定数据） | period_number, start_time, end_time |
| `semester_config` | 学期配置 | total_weeks, start_date, end_date, enrollment_open |
| `user_account` | 用户账号 | user_id, password_hash, role, is_locked |
| `student` | 学生信息 | student_id, name, department, grade |
| `teacher` | 教师信息 | teacher_id, name, department, title |
| `course` | 课程信息 | course_code, name, credit, type, department |
| `course_plan` | 开课计划（审核制） | plan_id, status(待审核/已通过/已拒绝), start_week, end_week |
| `enrollment` | 选课记录 | student_id, plan_id, enrolled_at |
| `grade` | 成绩记录 | student_id, plan_id, score, new_score(修改申请) |
| `operation_log` | 操作审计日志 | user_id, action, target, timestamp |
| `password_reset_request` | 密码重置申请 | user_id, reason, status |

## 新增数据库表流程

1. 在 `backend/models/` 创建 ORM 模型文件
2. 更新 `backend/config/init_database_mysql.sql`（DDL + 测试数据）
3. 同步更新 `backend/config/init_database.sql`（SQL Server 版）
4. 在 `ARCHITECTURE.md` 更新表数量和说明
