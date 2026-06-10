# 选课系统 Course Selection System

> SCNU 软件工程小组项目

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
- Node.js 18+ (仅前端开发需要)
- pip
- SQL Server（配置见 [SQL_SERVER_SETUP_GUIDE.md](./SQL_SERVER_SETUP_GUIDE.md)）

---

## 快速开始

### 1. 克隆仓库

```powershell
git clone https://github.com/camdies/Software-Engineering.git
cd Software-Engineering\course_selection_system
```

### 2. 配置数据库

请先参考 [SQL_SERVER_SETUP_GUIDE.md](./SQL_SERVER_SETUP_GUIDE.md) 完成 SQL Server 配置。

### 3. 一键安装并启动

```powershell
# 安装 Python 依赖
pip install -r requirements.txt
pip install Flask flask-cors PyJWT marshmallow

# 启动 Web 服务
python run.py
```

浏览器访问 `http://localhost:5000`

### 4. 前端开发（可选）

```powershell
cd frontend
npm install
npm run dev       # 启动 Vite dev server (localhost:5173)
```

前端开发时 Vite 自动将 `/api` 请求代理到 Flask `localhost:5000`。

---

## 默认账号

| 角色 | 账号 | 密码 |
|------|------|------|
| 管理员 | admin | 123456 |
| 教师 | T001 | 123456 |
| 学生 | S001 | 123456 |

---

## 项目结构

```
course_selection_system/
├── backend/              # 后端
│   ├── api/              # Flask REST API (新增)
│   ├── controllers/      # 业务逻辑
│   ├── models/           # SQLAlchemy ORM
│   ├── config/           # 配置
│   └── utils/            # 工具
├── frontend/             # Vue.js 前端 (新增)
│   └── src/
│       ├── views/        # 页面组件
│       ├── router/       # Vue Router
│       ├── stores/       # Pinia 状态
│       └── components/   # 通用组件
├── tests/                # 测试用例
├── requirements.txt      # Python 依赖
├── run.py                # Web 启动入口
└── SQL_SERVER_SETUP_GUIDE.md  # 数据库配置指南
```

## 常见问题

**Q: 启动报端口占用？**

修改 `run.py` 中的 `port=5000` 为其他端口。

**Q: SQL Server 连接失败？**

请检查 `backend/config/config.ini` 中的数据库连接信息。

**Q: 前端页面空白？**

确认已执行 `cd frontend && npm run build` 构建前端。

---

## 许可证

[AGPL-3.0](../LICENSE)
