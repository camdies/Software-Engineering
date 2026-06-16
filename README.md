# 高校教务管理系统

> SCNU 软件工程小组项目 v3.0

## 功能特性

### 学生端
- **自主选课**: 搜索栏目 + 可折叠类型筛选（院系/学分/时间/考核/类型），课程以缩小页签形式展示
- **课程名点击**: 弹窗展示课程详细信息
- **页签展开**: 点按页签展开课程详情，选课按钮在详情最右侧
- **选课反馈**: 选课成功后页签标签自动变绿，详情界面选课按钮同步变为退课按钮
- **退课确认**: 退课需要二次确认弹窗
- **右侧侧边栏**: 已选课程信息标签，默认缩小时态，点按后展开
  - 顶部占用表（横坐标：课节1-11，纵坐标：周一至周日）色块展示
  - 绿色：空闲周数 = 总周数 | 黄色：空闲周数 >= 总周数/2 | 红色：空闲周数 < 总周数/2
  - 占用表下方列举已选课程列表
- **个人课表查询**: 按上课时段对一周课程进行详细展示（支持多节次占用），支持导出 Excel、PDF
- **成绩查询**: 已修课程成绩及绩点一览
- **学业统计**: 总学分、累计GPA、未通过课程

### 教师端
- **授课计划申请**: 教师自行提出授课计划，选择上课起止周数（默认学期20周），管理员审核
- **成绩录入**: 单条录入 + Excel 批量导入
- **成绩修改**: 提交修改申请，管理员审核
- **统计分析**: 班级成绩统计、分数段分布、Excel 导出

### 管理员端
- **人员管理**: 新增教师/学生时系统默认注册账号（学号/工号=账号），密码默认 123456 或管理员自定义
- **课程管理**: 课程信息 CRUD（含课程类型、面向专业等字段）
- **审核中心**: 密码重置审核、成绩修改审核、课程审核（授课计划）三合一页签
- **选课统计**: 按学期查看各课程选课情况
- **选课控制**: 设置选课开放/关闭时间段
- **操作日志**: 全量审计日志查询

### 找回密码
- 登录界面"忘记密码"功能，用户提交重置申请，管理员审核通过后密码重置为默认 123456

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue.js 3 + Element Plus + Vite |
| 后端 API | Flask + JWT |
| 数据访问 | SQLAlchemy + PyMySQL |
| 数据库 | MySQL 8.0+ (默认) / SQL Server (可选) |

---

## 环境要求

- Python 3.11+
- Node.js 18+ (前端开发需要)
- MySQL 8.0+（配置见 [MYSQL_SETUP_GUIDE.md](./MYSQL_SETUP_GUIDE.md)）

---

## 快速开始

### 方式一：一键启动（推荐，无需安装 MySQL）

```powershell
# 1. 安装 Python 3.11+（https://www.python.org/downloads/，勾选 Add Python to PATH）
# 2. 双击 start_all.bat
# 3. 浏览器打开 http://localhost:5000
```

`start_all.bat` 自动完成：生成 `my.ini` 路径 → 启动 MySQL 前台 → 安装 Python 依赖 → 启动 Flask。

### 方式二：分步手动启动

#### 1. 安装并配置 MySQL

参考 **[MYSQL_SETUP_GUIDE.md](./MYSQL_SETUP_GUIDE.md)** — 完整指引：下载 → 初始化 → 嵌入项目目录。

#### 2. 初始化数据库

```powershell
# 注意：PowerShell 管道必须设置 UTF-8 编码，否则中文数据损坏
$OutputEncoding = [System.Text.UTF8Encoding]::new()
Get-Content backend\config\init_database_mysql.sql -Encoding UTF8 | mysql -u root -p --default-character-set=utf8mb4
```

#### 3. 修改数据库连接

将 `backend/config/config.ini.example` 复制为 `backend/config/config.ini`，编辑其中的数据库连接信息：
```ini
[database]
driver = mysql
host = localhost
port = 3306
user = root
password = YOUR_MYSQL_PASSWORD
database = course_management_db
```

#### 4. 安装依赖并启动

```powershell
# Python 依赖
pip install -r requirements.txt
pip install Flask flask-cors PyJWT

# 构建前端（首次或前端有修改时需要）
cd frontend
npm install
npm run build
cd ..

# 启动
python run.py
```

浏览器访问 `http://localhost:5000`

### 5. 前端开发模式（可选）

```powershell
cd frontend
npm run dev       # http://localhost:5173，自动代理 API 到 :5000
```

---

## 默认账号

| 角色 | 账号 | 密码 |
|------|------|------|
| 管理员 | admin | 123456 |
| 教师 | T001 / T002 / T003 | 123456 |
| 学生 | STU001 ~ STU005 | 123456 |

---

## 上课时间表（每天11节）

| 节次 | 名称 | 时间 | 时段 |
|------|------|------|------|
| 第1节 | 第一节 | 08:30-09:10 | 上午 |
| 第2节 | 第二节 | 09:20-10:00 | 上午 |
| 第3节 | 第三节 | 10:20-11:00 | 上午 |
| 第4节 | 第四节 | 11:10-11:50 | 上午 |
| 第5节 | 第五节 | 14:30-15:10 | 下午 |
| 第6节 | 第六节 | 15:20-16:00 | 下午 |
| 第7节 | 第七节 | 16:10-16:50 | 下午 |
| 第8节 | 第八节 | 17:00-17:40 | 下午 |
| 第9节 | 第九节 | 19:00-19:40 | 晚上 |
| 第10节 | 第十节 | 19:50-20:30 | 晚上 |
| 第11节 | 第十一节 | 20:40-21:20 | 晚上 |

---

## 数据库设计

### 表结构（11张表）

| 表名 | 用途 |
|------|------|
| `class_period` | 上课节次时间表（11节课固定数据） |
| `semester_config` | 学期配置表（总周数、起止日期、选课开关） |
| `user_account` | 用户账号表（密码、角色、锁定状态） |
| `student` | 学生信息表 |
| `teacher` | 教师信息表 |
| `course` | 课程信息表（含课程类型、面向专业） |
| `course_plan` | 开课计划表（教师申请→管理员审核） |
| `enrollment` | 选课记录表 |
| `grade` | 成绩记录表（含 new_score 字段） |
| `operation_log` | 操作日志表 |
| `password_reset_request` | 密码重置申请表 |

### 关键设计
- **授课计划审核制**: 教师提交 `course_plan`（状态=待审核），管理员审核通过后方可被学生选课
- **学期默认20周**: `semester_config.total_weeks = 20`，教师提交 `course_plan` 时自由选择 `start_week` / `end_week`
- **上课节次**: `class_period` 表定义每天11节课的固定时间
- **学生/教师自动注册**: 管理员创建学生/教师时自动创建 `user_account`，默认密码 123456
- **选课并发安全**: `SELECT ... FOR UPDATE` 行级锁防止超额
- **找回密码**: 用户提交 `password_reset_request`，管理员审核通过后重置

---

## 项目结构

```
高校教务管理系统/
├── backend/
│   ├── api/              # Flask REST API (Blueprints, 9个)
│   │   └── blueprints/   # 按功能模块拆分
│   ├── controllers/      # 业务逻辑 (7个控制器)
│   ├── models/           # SQLAlchemy ORM (11个模型)
│   ├── config/           # 配置文件 + DDL 初始化脚本
│   └── utils/            # 工具 (密码、校验、导出、GPA、日志)
├── frontend/
│   └── src/
│       ├── views/        # 页面组件
│       │   ├── admin/    # 管理员（5个）
│       │   ├── teacher/  # 教师（4个）
│       │   └── student/  # 学生（4个）
│       ├── router/       # Vue Router
│       ├── stores/       # Pinia
│       ├── layouts/      # 布局组件
│       └── components/   # 通用组件
├── mysql-portable/       # MySQL 8.0 便携版（start_all.bat 自动启动）
├── tests/
├── run.py
├── start_all.bat         # 一键启动（MySQL + Flask）
├── server_control.bat    # 服务管理控制面板
├── README.md
├── API.md
├── ARCHITECTURE.md
└── MYSQL_SETUP_GUIDE.md
```

---

## 许可证

[AGPL-3.0](LICENSE)
