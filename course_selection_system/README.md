# 学生选课及成绩管理系统

## 项目简介

本系统是一套面向高校教务管理的桌面端应用，基于 **Python 3.10+** 开发，采用 **前后端分离** 的 **MVC 三层架构** 设计。

### 核心特性

| 特性 | 说明 |
|------|------|
| **双前端版本** | Tkinter 版（零外部依赖）和 PySide6 版（专业UI），后端代码100%共享 |
| **三种角色** | 管理员（系统管理）、教师（成绩录入与统计）、学生（选课与查分） |
| **并发安全** | 选课使用 `SELECT ... FOR UPDATE` 行级锁，防止超额选课 |
| **成绩审核流** | 教师提交修改申请 → 管理员审核通过/驳回 → 成绩更正 |
| **审计追溯** | 所有关键操作（登录/选课/成绩/系统）写入 operation_log 表 |
| **绩点计算** | 8级绩点映射（90-100→4.0, 85-89→3.7, ..., 0-59→0.0）|
| **Excel 导入导出** | 批量导入成绩（openpyxl）、导出统计报表（带样式） |
| **日志管理** | 按日期滚动的分级日志（DEBUG/INFO/WARNING/ERROR），保留30天 |

### 技术栈

| 层级 | Tkinter版 | PySide6版 |
|------|-----------|-----------|
| GUI框架 | Python标准库 tkinter | PySide6 6.6+ |
| 后端 | backend/ (共享) | backend/ (共享) |
| ORM | SQLAlchemy 2.0+ | SQLAlchemy 2.0+ |
| 数据库 | MySQL 5.7+ / MariaDB 10.3+ | 同左 |
| 密码加密 | bcrypt 4.0+ (12 rounds) | 同左 |
| Excel处理 | openpyxl 3.1+ | 同左 |

---

## 快速开始

### 1. 环境要求

- **Python**: 3.10 或更高版本
- **MySQL**: 5.7+ 或 MariaDB 10.3+
- **pip**: 最新版本

### 2. 克隆项目并安装依赖

```bash
cd course_selection_system
pip install -r requirements.txt
```

### 3. MySQL 数据库初始化

```bash
# 方式一: 命令行导入
mysql -u root -p < backend/config/init_database.sql

# 方式二: 在MySQL客户端中执行
# source backend/config/init_database.sql;
```

初始化脚本会自动创建 `course_management_db` 数据库，包含：
- 8 张数据表（user_account / student / teacher / course / course_plan / enrollment / grade / operation_log）
- 全部外键约束、索引
- 测试数据（1个管理员 + 2个教师 + 3个学生 + 5门课程 + 5条开课计划 + 8条选课记录）

### 4. 修改配置文件

编辑 `backend/config/config.ini`：

```ini
[database]
host = localhost
port = 3306
user = root
password = your_mysql_password
database = course_management_db

[enrollment]
# 是否需要打开选课开关（测试选课功能时设为 true）
is_open = true
```

### 5. 启动应用

```bash
# Tkinter 版本（Python自带，无需额外安装GUI库）
python run_tkinter.py

# PySide6 版本（需要 pip install PySide6）
python run_pyside6.py
```

### 6. 测试账号

| 角色 | 账号 | 密码 | 说明 |
|------|------|------|------|
| 管理员 | admin | 123456 | 全部管理功能 |
| 教师 | T001 | 123456 | 成绩录入、统计分析 |
| 教师 | T002 | 123456 | 同上 |
| 学生 | STU001 | 123456 | 选课、查成绩 |
| 学生 | STU002 | 123456 | 同上 |
| 学生 | STU003 | 123456 | 同上 |

---

## 项目结构

```
course_selection_system/
│
├── run_tkinter.py              # 启动 Tkinter 前端版本
├── run_pyside6.py              # 启动 PySide6 前端版本
├── requirements.txt            # Python依赖清单
├── README.md                   # 本文档
│
├── backend/                    # ★ 后端逻辑层（两个前端100%共享）
│   ├── config/
│   │   ├── config.ini          # 数据库、系统参数配置
│   │   ├── settings.py         # 配置读取单例
│   │   └── init_database.sql   # 数据库DDL + 测试数据
│   ├── models/                 # ORM 数据模型（M层）
│   │   ├── base.py             # SQLAlchemy Engine + Session管理
│   │   ├── user_account.py     # 用户账号
│   │   ├── student.py          # 学生信息
│   │   ├── teacher.py          # 教师信息
│   │   ├── course.py           # 课程信息
│   │   ├── course_plan.py      # 开课计划
│   │   ├── enrollment.py       # 选课记录
│   │   ├── grade.py            # 成绩记录
│   │   └── operation_log.py    # 操作日志
│   ├── controllers/            # 业务逻辑（C层）
│   │   ├── auth_controller.py          # 登录认证/密码管理
│   │   ├── admin_controller.py         # 管理员CRUD
│   │   ├── teacher_controller.py       # 教师业务
│   │   ├── student_controller.py       # 学生业务
│   │   ├── enrollment_controller.py    # ★ 选课核心（行级锁）
│   │   ├── grade_controller.py         # 成绩管理/审核
│   │   └── stats_controller.py         # 统计分析
│   └── utils/                  # 工具函数
│       ├── auth_util.py        # bcrypt 密码加密
│       ├── log_util.py         # 日志配置
│       ├── validator.py        # 输入校验
│       ├── gpa_calculator.py   # 绩点计算
│       ├── export_util.py      # Excel导出
│
├── frontend_tkinter/           # ★ Tkinter 前端（Python标准库）
│   ├── app.py                  # 应用入口
│   ├── login_window.py         # 登录窗口
│   ├── admin_window.py         # 管理员主窗口（导航+内容区）
│   ├── admin_students.py       # 学生信息管理
│   ├── admin_teachers.py       # 教师信息管理
│   ├── admin_courses.py        # 课程管理
│   ├── admin_grade_audit.py    # 成绩审核
│   ├── admin_logs.py           # 操作日志查看
│   ├── teacher_window.py       # 教师主窗口
│   ├── teacher_grades.py       # 成绩录入
│   ├── teacher_grade_modify.py # 成绩修改申请
│   ├── teacher_stats.py        # 统计分析
│   ├── student_window.py       # 学生主窗口
│   ├── student_enroll.py       # 选课中心
│   ├── student_my_courses.py   # 已选课程
│   ├── student_grades.py       # 成绩查询
│   └── student_stats.py        # 学业统计
│
├── frontend_pyside6/           # ★ PySide6 前端（专业Qt界面）
│   ├── app.py                  # 应用入口
│   ├── login_window.py         # 登录窗口
│   ├── main_window.py          # 统一主窗口（按角色配置导航）
│   ├── admin_students.py       # 学生信息管理
│   ├── admin_teachers.py       # 教师信息管理
│   ├── admin_courses.py        # 课程管理
│   ├── admin_course_plans.py   # 开课计划管理
│   ├── admin_enrollment_control.py  # 选课时段控制
│   ├── admin_enrollment_stats.py    # 选课统计
│   ├── admin_grade_audit.py    # 成绩审核
│   ├── admin_logs.py           # 操作日志
│   ├── teacher_courses.py      # 任课信息
│   ├── teacher_grades.py       # 成绩录入
│   ├── teacher_grade_modify.py # 成绩修改
│   ├── teacher_stats.py        # 统计分析
│   ├── student_enroll.py       # 选课中心
│   ├── student_my_courses.py   # 已选课程
│   ├── student_grades.py       # 成绩查询
│   └── student_stats.py        # 学业统计
│
└── tests/                      # 单元测试
    ├── test_auth.py            # 认证模块测试
    ├── test_enrollment.py      # 选课模块测试（含并发）
    ├── test_grade.py           # 成绩模块测试（含绩点）
    └── run_all.py              # 测试运行入口
```

---

## 功能模块详解

### 1. 登录认证 (`auth_controller.py`)

```
登录流程:
  用户输入 → 查询 user_account → 检查锁定状态
  → bcrypt 密码验证 → 更新 last_login
  → 写入操作日志 → 返回角色信息

安全机制:
  - 密码错误5次 → is_locked=1（需管理员解锁）
  - 密码存储: bcrypt 12轮加盐哈希
  - 会话超时: config.ini 中 session_timeout 控制
```

### 2. 选课管理 (`enrollment_controller.py`) ★ 核心

```
选课 5 项校验（按顺序，任一失败立即返回）:

  校验1 — 选课时段: 当前时间 ∈ [open_time, close_time]
  校验2 — 重复选课: enrollment 表不存在 (student_id, plan_id) 且 status='已选'
  校验3 — 时间冲突: 解析 time_slot 字段比对
  校验4 — 容量校验: SELECT ... FOR UPDATE 行级锁 → enrolled < capacity
  校验5 — 先修课: grade 表中每门 prerequisite 的 score >= 60

全部通过后在同一事务中:
  INSERT enrollment + UPDATE course_plan.enrolled + 写日志
```

**并发安全原理**: 当两个学生同时选最后一门课时，后执行的 `SELECT ... FOR UPDATE` 会被阻塞，等第一个事务提交后才看到已满的 `enrolled` 值，从而返回"容量已满"。

### 3. 成绩管理 (`grade_controller.py`)

```
成绩录入:
  score ∈ [0,100] → 查询 enrollment 确认已选
  → 调用 gpa_calculator 计算绩点 → INSERT grade

批量导入 (Excel):
  openpyxl 逐行解析 → 逐行校验 → 批量 INSERT
  → 返回 {success_count, fail_count, fail_list}

成绩修改审核流程:
  教师: apply_grade_modify → status='待审核'
  管理员: audit_grade('approve') → score更新 + status='已更正'
  管理员: audit_grade('reject') → status恢复'正常'
```

### 4. 统计分析 (`stats_controller.py`)

| 功能 | 说明 |
|------|------|
| 班级统计 | AVG/MAX/MIN/及格率 + 排名列表 |
| 学业统计 | 已修学分、累计GPA、未通过课程 |
| 成绩分布 | 优秀(90-100)/良好(75-89)/中等(60-74)/不及格(0-59) |
| Excel导出 | 表头加粗蓝色背景、交替行色、汇总行 |

### 5. 绩点计算 (`gpa_calculator.py`)

| 分数段 | 绩点 |
|--------|------|
| 90–100 | 4.0 |
| 85–89 | 3.7 |
| 80–84 | 3.3 |
| 75–79 | 3.0 |
| 70–74 | 2.7 |
| 65–69 | 2.3 |
| 60–64 | 2.0 |
| 0–59 | 0.0 |

累计平均绩点 = Σ(绩点 × 学分) / Σ(学分)

---

## PyCharm 配置

### 配置 Python 解释器
1. File → Settings → Project → Python Interpreter
2. 选择 Python 3.10+ 解释器
3. 安装依赖: 点击 `+` 搜索并安装 `PyMySQL`, `SQLAlchemy`, `bcrypt`, `openpyxl`, `PySide6`

### 配置运行
1. Run → Edit Configurations → 添加 Python 配置
2. **Tkinter 版本**: Script path = `run_tkinter.py`
3. **PySide6 版本**: Script path = `run_pyside6.py`
4. Working directory = 项目根目录

### 配置 MySQL 数据源
1. View → Tool Windows → Database
2. `+` → Data Source → MySQL
3. Host: localhost, Port: 3306, User: root
4. Database: course_management_db
5. 测试连接 → OK

---

## 运行测试

```bash
# 运行全部测试（17个用例）
python tests/run_all.py

# 运行单个测试模块
python -m unittest tests.test_auth
python -m unittest tests.test_enrollment
python -m unittest tests.test_grade

# 测试覆盖率
pip install coverage
coverage run tests/run_all.py
coverage report -m
```

---

## 两个前端版本对比

| 维度 | Tkinter 版 | PySide6 版 |
|------|-----------|------------|
| 依赖 | Python标准库（零额外安装） | 需 `pip install PySide6` |
| 视觉效果 | 基础控件，可定制性有限 | 专业Qt样式，QSS美化 |
| 跨平台 | ✅ Windows/macOS/Linux | ✅ Windows/macOS/Linux |
| 开发复杂度 | 简单直接 | 更丰富的Widget和Signal/Slot |
| 适合场景 | 快速部署、内网环境 | 正式交付、专业展示 |
| 后端代码 | 100%共享 `backend/` | 100%共享 `backend/` |

**两个版本的后端逻辑完全相同**，只在 `frontend_tkinter/` 和 `frontend_pyside6/` 目录中实现不同的UI层，均通过导入 `backend/` 包调用相同的控制器。

---

## 扩展方向

系统架构已预留 Web 端扩展接口：
- Model 层全部实现 `to_dict()` 方法，可直接 JSON 序列化
- Controller 层返回统一 `dict` 格式
- 后续可将 View 层替换为 React/Vue 前端，Controller 层改造为 REST API（FastAPI/Flask）
- 认证模块预留 JWT 接口

---

## 注意事项

- 生产部署前修改 `backend/config/config.ini` 中的数据库密码
- 建议将 `config.ini` 加入 `.gitignore` 避免敏感信息泄露
- 日志文件位于 `logs/` 目录，自动每日滚动，保留30天
- bcrypt 加密轮数当前为 12，可在 `auth_util.py` 中调整
