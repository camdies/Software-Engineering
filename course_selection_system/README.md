# 高校教务管理系统

> SCNU 软件工程小组项目 v2.0

## 功能特性

- **学生端**: 自主选课（卡片式浏览+详情对话框）、个人周课表、成绩查询、学业统计
- **教师端**: 授课计划申请（管理员审核制）、成绩录入、成绩修改申请、统计分析
- **管理员端**: 人员管理、课程管理、审核中心（密码重置+成绩修改+授课计划三合一）、选课统计、操作日志
- 找回密码（用户申请→管理员审核）
- Excel / PDF 导出

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue.js 3 + Element Plus + Vite |
| 后端 API | Flask + JWT |
| 数据访问 | SQLAlchemy / pyodbc / pymssql |
| 数据库 | SQL Server / MySQL |

---

## 环境要求

- Python 3.11+
- Node.js 18+ (前端开发需要)
- SQL Server（配置见 [SQL_SERVER_SETUP_GUIDE.md](./SQL_SERVER_SETUP_GUIDE.md)）

---

## 快速开始

### 1. 配置数据库

参考 [SQL_SERVER_SETUP_GUIDE.md](./SQL_SERVER_SETUP_GUIDE.md) 安装并配置 SQL Server，
然后在 SSMS 中执行 `backend/config/init_database.sql`。

### 2. 修改数据库连接

编辑 `backend/config/config.ini`，设置数据库连接信息。

### 3. 安装依赖并启动

```powershell
# Python 依赖
pip install -r requirements.txt
pip install Flask flask-cors PyJWT marshmallow

# 构建前端（首次或前端有修改时需要）
cd frontend
npm install
npm run build
cd ..

# 启动
python run.py
```

浏览器访问 `http://localhost:5000`

### 4. 前端开发模式（可选）

```powershell
cd frontend
npm run dev       # http://localhost:5173，自动代理 API 到 :5000
```

---

## 默认账号

| 角色 | 账号 | 密码 |
|------|------|------|
| 管理员 | admin | 123456 |
| 教师 | T001 | 123456 |
| 学生 | STU001 | 123456 |

---

## 上课时间（11节）

| 节次 | 时间 |
|------|------|
| 第1节 | 08:30-09:10 |
| 第2节 | 09:20-10:00 |
| 第3节 | 10:20-11:00 |
| 第4节 | 11:10-11:50 |
| 第5节 | 14:30-15:10 |
| 第6节 | 15:20-16:00 |
| 第7节 | 16:10-16:50 |
| 第8节 | 17:00-17:40 |
| 第9节 | 19:00-19:40 |
| 第10节 | 19:50-20:30 |
| 第11节 | 20:40-21:20 |

---

## 项目结构

```
course_selection_system/
├── backend/
│   ├── api/              # Flask REST API (Blueprints)
│   ├── controllers/      # 业务逻辑
│   ├── models/           # SQLAlchemy ORM (9个模型)
│   ├── config/           # 配置 + DDL 脚本
│   └── utils/            # 工具
├── frontend/
│   └── src/
│       ├── views/        # 17个页面组件
│       │   ├── admin/    # 管理员（5个）
│       │   ├── teacher/  # 教师（4个）
│       │   └── student/  # 学生（5个）
│       ├── router/       # Vue Router
│       ├── stores/       # Pinia
│       └── components/   # 通用组件
├── tests/
├── run.py
└── SQL_SERVER_SETUP_GUIDE.md
```

---

## 许可证

[AGPL-3.0](../LICENSE)
