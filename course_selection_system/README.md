# 学生选课及成绩管理系统

## 项目简介

本系统是一套面向高校教务管理的桌面端应用，基于 **PyQt5 + SQLAlchemy + MySQL** 构建，采用 **MVC三层架构** 设计。系统支持 **管理员、教师、学生** 三种角色，涵盖用户认证、课程管理、选课（含并发控制）、成绩管理、统计分析等核心教务功能。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 桌面GUI | PyQt5 5.15+ | 跨平台桌面界面框架 |
| ORM | SQLAlchemy 2.0+ | 数据库对象关系映射 |
| 数据库 | MySQL 5.7+ | 关系型数据库，utf8mb4字符集 |
| 密码加密 | bcrypt 4.0+ | 基于Blowfish的密码哈希 |
| Excel处理 | openpyxl 3.1+ | 批量导入成绩、导出报表 |
| 日志 | logging + TimedRotatingFileHandler | 每日滚动日志，保留30天 |

## 环境搭建

### 1. 前置依赖

- Python 3.10+
- MySQL 5.7+ 或 MariaDB 10.3+
- pip 包管理工具

### 2. 安装Python依赖

```bash
cd course_selection_system
pip install -r requirements.txt
```

### 3. MySQL数据库初始化

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS course_management_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE course_management_db;

-- 建表（详见 config/init_database.sql）
-- 初始化管理员账号（密码: admin123）
INSERT INTO user_account (user_id, password_hash, role, is_locked, login_fail_count)
VALUES ('admin', '<bcrypt_hash_of_admin123>', 'admin', 0, 0);
```

### 4. 配置文件

编辑 `config/config.ini`，填写您的数据库连接信息：

```ini
[database]
host = localhost
port = 3306
user = root
password = your_password
database = course_management_db
```

## PyCharm配置步骤

### 解释器配置
1. File → Settings → Project → Python Interpreter
2. 选择 Python 3.10+ 解释器
3. 安装 `requirements.txt` 中的依赖包

### 数据库插件配置
1. View → Tool Windows → Database
2. 添加 Data Source → MySQL
3. 填写 Host: localhost, Port: 3306, User: root, Database: course_management_db
4. 测试连接通过后即可浏览表结构和数据

### 运行配置
1. Run → Edit Configurations
2. 添加 Python 配置，Script path 选择 `main.py`
3. Working directory 设为项目根目录

## 运行方式

```bash
# 启动桌面应用
python main.py

# 运行单元测试
python -m unittest discover -s tests -p "test_*.py"

# 运行测试覆盖率
coverage run -m unittest discover -s tests -p "test_*.py"
coverage report -m
```

## 项目结构

```
course_selection_system/
├── main.py                    # 程序入口
├── config/                    # 配置模块
│   ├── config.ini             # 数据库/系统参数配置
│   └── settings.py            # 配置读取类
├── models/                    # 数据模型层 (M)
│   ├── base.py                # SQLAlchemy连接管理（单例+连接池）
│   ├── user_account.py        # 用户账号模型
│   ├── student.py             # 学生信息模型
│   ├── teacher.py             # 教师信息模型
│   ├── course.py              # 课程信息模型
│   ├── course_plan.py         # 开课计划模型
│   ├── enrollment.py          # 选课记录模型
│   ├── grade.py               # 成绩记录模型
│   └── operation_log.py       # 操作日志模型
├── controllers/               # 业务控制层 (C)
│   ├── auth_controller.py     # 登录认证/会话管理/密码修改
│   ├── enrollment_controller.py  # 选课核心逻辑（行级锁并发控制）
│   ├── grade_controller.py    # 成绩录入/批量导入/审核
│   └── stats_controller.py    # 统计分析/报表导出
├── views/                     # 界面视图层 (V)
│   ├── login_view.py          # 登录界面
│   └── admin/                 # 管理员界面
│       ├── admin_main_view.py     # 主窗口（导航+内容区）
│       └── student_mgmt_view.py   # 学生信息管理
├── utils/                     # 工具模块
│   ├── auth_util.py           # bcrypt密码加密验证
│   ├── log_util.py            # 日志工具
│   ├── validator.py           # 输入校验
│   ├── gpa_calculator.py      # 绩点计算
│   ├── db_util.py             # 数据库连接池管理
│   └── export_util.py         # Excel导出
├── tests/                     # 单元测试
│   ├── test_auth.py           # 认证模块测试
│   ├── test_enrollment.py     # 选课模块测试（含并发）
│   └── test_grade.py          # 成绩模块测试
├── requirements.txt           # Python依赖
└── README.md                  # 本文件
```

## 核心功能模块说明

| 模块 | 功能 | 关键特性 |
|------|------|---------|
| 登录认证 | 用户登录/登出/密码修改 | bcrypt密码加密、密码错误5次锁定、Session会话管理 |
| 选课管理 | 学生选课/退课 | 5项校验（时段/重复/冲突/容量/先修）、行级锁防超额 |
| 成绩管理 | 成绩录入/批量导入/修改/审核 | Excel批量导入、成绩审核流程（提交→审核→更正） |
| 统计分析 | 成绩排名/学业统计/分布分析 | SQL聚合函数、绩点累计计算、Excel报表导出 |

## 注意事项

### 并发安全

选课操作使用 **SELECT ... FOR UPDATE** 数据库行级锁：
- 在同一个事务中锁定 `course_plan` 行
- 比较 `enrolled` 与 `capacity` 后执行 `enrolled + 1`
- 事务提交后释放锁，防止超额选课

### 数据备份

- 建议定期备份 `course_management_db` 数据库
- 日志文件自动按日滚动，保留30天，位于 `logs/` 目录
- 备份文件存放于 `backup/` 目录

### 安全建议

- 生产环境请修改 `config.ini` 中的默认密码
- 建议将 `config.ini` 加入 `.gitignore` 避免敏感信息泄露
- bcrypt 加密轮数当前为12，生产环境可适当提高

### 扩展方向

系统架构预留了Web端扩展接口：
- Model 层已实现 `to_dict()` 方法，可直接用于JSON序列化
- 认证模块预留 JWT 接口
- 后续可将 View 层替换为 React/Vue 前端，Controller 层改造为 REST API
