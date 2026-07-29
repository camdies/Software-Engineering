# CLAUDE.md — 高校教务管理系统

> SCNU 软件工程小组 v3.0 · Claude 协作开发指引

---

## 一、项目身份

- **项目名称**: 高校教务管理系统 (EduMgmt System v3.0)
- **团队**: SCNU 软件工程小组
- **代码仓库**: 本地 Git 管理，当前分支 `claude/gracious-brahmagupta-b9109a`
- **主分支**: `main`
- **Git 用户**: camdies
- **平台**: Windows 11 + PyCharm
- **详细架构**: 见 [ARCHITECTURE.md](ARCHITECTURE.md)（124文件、48 API端点、11张表）
- **API 文档**: 见 [API.md](API.md)
- **调试指南**: 见 [DEBUG.md](DEBUG.md)

---

## 二、技术栈速查

| 层级 | 技术 | 备注 |
|------|------|------|
| 前端 | Vue 3 (Composition API) + Element Plus + Vite | SPA，构建产物在 `frontend/dist/` |
| 后端 | Flask + JWT (HS256, 24h) | `run.py` 入口，工厂模式 |
| ORM | SQLAlchemy + PyMySQL | 双数据库支持 (MySQL / SQL Server) |
| 数据库 | MySQL 8.0+ (默认) | 便携版在 `mysql-portable/` |
| 测试 | pytest | `tests/` 目录 |
| 构建 | npm (Node 18+) | Vite 构建到 `frontend/dist/` |

---

## 三、常用命令（必须在项目根目录执行）

### 环境准备

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖 + 构建
cd frontend && npm install && npm run build && cd ..
```

### 启动应用

```bash
# 一键启动（包含 MySQL + Flask）
python run.py

# 或使用批处理（Windows）
start_all.bat          # 选项 [2] Auto Setup & Start（推荐首次）
```

### 前端开发模式（热更新）

```bash
# 终端 1 — 后端
python run.py

# 终端 2 — 前端热更新（访问 http://localhost:5173，API 自动代理到 :5000）
cd frontend && npm run dev
```

### 测试

```bash
# 运行全部测试
python -m pytest tests/ -v

# 运行单个测试模块
python -m pytest tests/test_enrollment.py -v
```

### 数据库操作

```bash
# 启动便携版 MySQL
cd mysql-portable && start_mysql.bat

# 导入 DDL + 测试数据（项目根目录）
# MySQL 初始化脚本: backend/config/init_database_mysql.sql
```

---

## 四、架构约定

### 4.1 后端分层（严格遵守）

```
Blueprint (路由，只做参数提取+调用Controller)
  → Controller (业务逻辑，不要处理request直接量)
    → Model (SQLAlchemy ORM，通过 DatabaseManager.get_session() 获取会话)
```

- **路由层**: `backend/api/blueprints/` — 9个蓝图，48个端点，只做参数提取和调用 controller
- **业务层**: `backend/controllers/` — 7个控制器，每个负责一个领域的业务逻辑
- **数据层**: `backend/models/` — 11个 ORM 模型 + `base.py` DatabaseManager 单例
- **工具层**: `backend/utils/` — 密码哈希、Excel导出、GPA计算、日志、校验

### 4.2 关键架构决策（不要违背）

1. **延迟数据库初始化**: `app_factory.py` 用 `@before_request` 懒初始化，不要在模块顶层访问 DB
2. **JWT 固定密钥**: `auth.py` 优先读 `config.ini` 中的 `jwt_secret`，否则 SHA256 生成
3. **Pinia 必须在 Router 之前**: `main.js` 中 `createPinia()` → `app.use(pinia)` → `app.use(router)`，顺序不能变
4. **选课并发**: 使用 `SELECT ... FOR UPDATE` 行级锁，不要用应用层锁
5. **状态列用 String(10)** 而非 SAEnum（兼容 SQL Server 无原生 ENUM）

### 4.3 API 规范

- **URL 前缀**: `/api/<角色或模块>/`
- **鉴权**: JWT Bearer token（`Authorization: Bearer <token>`）
- **响应格式**: `{ "success": bool, "data": any, "message": "..." }`
- **装饰器**: `@require_auth` + `@require_role('admin'|'teacher'|'student')`
- **详细文档**: 见 [API.md](API.md)

### 4.4 前端规范

- **组件**: Composition API (`<script setup>`)
- **状态管理**: Pinia (`stores/auth.js` + `stores/app.js`)
- **HTTP 客户端**: Axios 实例 (`utils/request.js`)，含 JWT 拦截器 + 401/403 自动处理
- **UI 框架**: Element Plus，全局样式覆盖在 `styles/global.scss`
- **页面组件**: 按角色分目录 `views/admin/`, `views/teacher/`, `views/student/`

---

## 五、代码风格约定

### 后端 (Python)

- 文件编码 UTF-8（项目有 GBK 历史问题，新增文件务必 UTF-8）
- 所有面向用户的错误消息用中文 `"操作成功"` / `"参数错误"`
- 控制器方法返回字典，由 Blueprint 通过 `success_response()` / `error_response()` 包装
- 敏感配置在 `backend/config/config.ini`（已 gitignore），模板在 `config.ini.example`
- 操作日志通过 `backend/utils/log_util.py` 写入

### 前端 (Vue/JS)

- 用户界面全中文
- 路由路径用英文（如 `/student/enroll`），页面标题用中文（如 "自主选课"）
- 新增页面需在 `router/index.js` 注册路由 + 角色权限
- 布局使用 `MainLayout.vue`，不要自建独立布局

### 提交规范

- 提交消息用中文，简洁描述变更内容
- 示例: `修复选课控制部分时段问题`、`修复前端教师停课按钮逻辑`
- 多个独立变更分多次提交，不要一个大提交包含不相关的修改

---

## 六、数据库说明

### 11张表

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

### 角色体系

| 角色 | 权限范围 |
|------|----------|
| `admin` | 人员管理、课程管理、审核中心、选课统计、选课控制、操作日志 |
| `teacher` | 授课计划、成绩录入/修改、统计分析 |
| `student` | 自主选课、课表查询、成绩查询、学业统计 |

---

## 七、安全约束（绝对不要做的）

1. 不要在前端硬编码 JWT secret 或数据库密码
2. 不要跳过 `@require_auth` 或 `@require_role` 装饰器
3. 不要使用字符串拼接构造 SQL（始终用 SQLAlchemy ORM）
4. 不要在前端直接将用户输入拼接到 HTML（Vue 默认转义，但 v-html 需审查）
5. 密码必须经过 bcrypt（12轮）哈希，后端工具 `auth_util.py`
6. 配置文件 `config.ini` 不要提交到 Git

---

## 八、常见开发场景

### 新增一个 API 端点

1. 在对应 Blueprint 文件添加路由函数 → 调用 Controller 方法
2. 在对应 Controller 添加业务方法 → 返回字典
3. 更新 [API.md](API.md) 文档
4. 如需鉴权变更，在 `auth.py` 确认角色

### 新增一个前端页面

1. 在 `views/<角色>/` 创建 `.vue` 文件
2. 在 `router/index.js` 注册路由 + `meta.roles` 权限
3. 如需后端数据，先确认 API 端点是否已存在

### 新增一张数据库表

1. 在 `backend/models/` 创建 ORM 模型文件
2. 更新 `backend/config/init_database_mysql.sql`（DDL + 测试数据）
3. 同步更新 `backend/config/init_database.sql`（SQL Server 版）
4. 在 `ARCHITECTURE.md` 更新表数量和说明

### 修改选课逻辑

1. 核心逻辑在 `backend/controllers/enrollment_controller.py`（选课/退课、5项校验、行级锁）
2. 前端在 `views/student/StudentEnroll.vue`（最复杂的页面，~600行）
3. 测试在 `tests/test_enrollment.py`（含并发测试）

### 调试

- 后端日志在 `logs/` 目录，使用 TimedRotatingFileHandler
- PyCharm 调试配置: Script path=`run.py`, Working directory=`<项目根目录>`
- 前端: `npm run dev` 启动 Vite 热更新，API 代理到 `:5000`
- 详见 [DEBUG.md](DEBUG.md)

---

## 九、构建产物（不要手动编辑）

以下由工具自动生成，已加入 `.gitignore`，拉取后重新构建:

| 产物 | 生成方式 |
|------|----------|
| `frontend/dist/` | `cd frontend && npm run build` |
| `frontend/node_modules/` | `cd frontend && npm install` |
| `mysql-portable/data/` | `start_all.bat` 自动初始化 |
| `backend/config/config.ini` | 从 `.example` 复制 + 手动配置 |
| `logs/` | 运行时自动创建 |
| `__pycache__/`, `*.pyc` | Python 自动生成 |

---

## 十、默认测试账号

所有账号密码均为 **123456**。

| 角色 | 账号 |
|------|------|
| 管理员 | admin / admin2 |
| 教师 | T001 ~ T008（多学院） |
| 学生 | STU001 ~ STU025（多专业/年级） |

完整列表见 [README.md](README.md) 默认账号章节。
