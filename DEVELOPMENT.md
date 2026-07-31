# 技术栈与开发介绍

> 面向新加入团队的开发者，帮助你快速理解技术选型、开发流程和代码规范。

---

## 一、项目概览

高校教务管理系统是一个**单体 Web 应用**，采用前后端分离式开发、部署时合为一体的架构。目标用户是大学教务管理人员、教师和学生。

| 维度 | 说明 |
|------|------|
| 应用类型 | Web SPA（Single Page Application） |
| 部署方式 | Flask 服务静态文件 + REST API，单进程运行 |
| 用户角色 | 管理员（admin）、教师（teacher）、学生（student） |
| 代码规模 | ~124 个源文件，48 个 API 端点，11 张数据库表 |
| 开发方式 | PyCharm 为主 IDE，Windows 11 开发环境 |

---

## 二、技术栈详解

### 2.1 后端 — Python Flask

| 组件 | 版本 | 用途 |
|------|------|------|
| **Flask** | ≥3.0 | Web 框架，提供路由、请求上下文、静态文件服务 |
| **flask-cors** | ≥4.0 | 跨域支持（前端开发模式时 Vite :5173 → Flask :5000） |
| **PyJWT** | ≥2.8 | JSON Web Token 签发与验证，HS256 算法，24 小时过期 |
| **bcrypt** | ≥4.0 | 密码哈希，12 轮加盐 |

**为什么选 Flask 而不是 Django？**

Flask 轻量灵活，适合 3 人小组快速迭代。Django 的 ORM、Admin、模板引擎在这个项目中用不上，反而增加学习成本。项目规模（48 端点、11 表）也在 Flask 的舒适区内。

### 2.2 数据访问 — SQLAlchemy ORM

| 组件 | 版本 | 用途 |
|------|------|------|
| **SQLAlchemy** | ≥2.0 | Python ORM，支持 MySQL 和 SQL Server 双数据库 |
| **PyMySQL** | ≥1.1 | MySQL 的纯 Python 驱动（无需安装 MySQL 客户端库） |

**为什么用 ORM 而不是原生 SQL？**
- 编译时防 SQL 注入（参数化查询自动处理）
- 数据库切换（MySQL ↔ SQL Server）只需改一行配置
- 表结构通过 Python 类表达，和 DDL 脚本互为文档

**双数据库支持的设计动机：** 学校机房普遍安装 SQL Server，但开发阶段用便携版 MySQL 更轻量。通过 `config.ini` 的 `driver` 字段一键切换。

### 2.3 前端 — Vue 3 生态

| 组件 | 版本 | 用途 |
|------|------|------|
| **Vue 3** | ≥3.4 | Composition API（`<script setup>`），响应式 UI 框架 |
| **Vite** | ≥5.4 | 开发服务器（HMR 热更新）+ 生产构建 |
| **Element Plus** | ≥2.7 | UI 组件库（表格、表单、弹窗、标签页等） |
| **Pinia** | ≥2.1 | 状态管理（auth token、用户角色、侧边栏状态） |
| **Vue Router** | ≥4.3 | 前端路由 + 导航守卫（角色权限校验） |
| **Axios** | ≥1.7 | HTTP 客户端，JWT 拦截器自动附加 token |
| **ECharts** | ≥6.1 | 数据可视化（教师端统计图表） |

**为什么 Vue 3 而不是 React？** 团队更熟悉 Vue 生态；Vue 的模板语法和 SFC（单文件组件）对后端开发者更友好；Element Plus 是 Vue 3 生态中最成熟的中后台 UI 库。

### 2.4 工具链

| 组件 | 版本 | 用途 |
|------|------|------|
| **openpyxl** | ≥3.1 | 读写 Excel（成绩批量导入、课表导出） |
| **reportlab** | ≥4.0 | 课表 PDF 导出 |
| **pandas** | ≥2.0 | 成绩统计分析 |
| **pytest** | — | 测试框架 |
| **sass** | ≥1.77 | SCSS 预处理器 |

### 2.5 数据库

| 数据库 | 版本 | 使用场景 |
|--------|------|----------|
| **MySQL** | 8.0+ | **默认**。开发/测试用便携版（`mysql-portable/`），生产用服务器版 |
| **SQL Server** | 2019+ | 可选。通过 ODBC Driver 18 连接，适配学校机房环境 |

---

## 三、项目结构

```
项目根目录/
├── backend/
│   ├── api/                     # Flask API 层
│   │   ├── app_factory.py       # App 工厂：CORS、蓝图注册、静态文件、懒初始化 DB
│   │   ├── auth.py              # JWT 签发/验证 + @require_auth + @require_role 装饰器
│   │   ├── response.py          # success_response() / error_response() 统一包装
│   │   └── blueprints/          # 9 个蓝图，48 个端点（只做参数提取）
│   │       ├── auth_bp.py       # /api/auth       — 登录/登出/密码修改
│   │       ├── admin_bp.py      # /api/admin      — 管理员 CRUD
│   │       ├── audit_bp.py      # /api/audit      — 审核中心
│   │       ├── student_bp.py    # /api/student    — 学生查询
│   │       ├── teacher_bp.py    # /api/teacher    — 教师查询
│   │       ├── enrollment_bp.py # /api/enrollment — 选课/退课
│   │       ├── grade_bp.py      # /api/grade      — 成绩管理
│   │       ├── stats_bp.py      # /api/stats      — 统计分析
│   │       └── password_reset_bp.py  # /api/auth  — 忘记密码
│   ├── controllers/             # 业务逻辑层（7 个控制器）
│   ├── models/                  # SQLAlchemy ORM 模型（11 张表 + base.py）
│   ├── config/                  # 配置 + DDL 初始化脚本
│   │   ├── config.ini.example   # 配置模板（真实 config.ini 已 gitignore）
│   │   ├── settings.py          # ConfigParser 单例
│   │   ├── init_database_mysql.sql    # MySQL 完整 DDL + 测试数据
│   │   └── init_database.sql          # SQL Server 版 DDL
│   └── utils/                   # 工具模块
│       ├── auth_util.py         # bcrypt（12 轮）
│       ├── export_util.py       # Excel 导出
│       ├── gpa_calculator.py    # GPA 计算
│       ├── log_util.py          # 操作日志（TimedRotatingFileHandler）
│       └── validator.py         # 输入校验
├── frontend/
│   └── src/
│       ├── views/               # 页面组件（按角色分三个子目录）
│       ├── router/index.js      # 路由 + beforeEach 导航守卫
│       ├── stores/              # Pinia（auth.js + app.js）
│       ├── utils/request.js     # Axios 实例（JWT 拦截器）
│       ├── layouts/MainLayout.vue
│       └── styles/global.scss
├── tests/                       # pytest 测试用例
├── mysql-portable/              # MySQL 8.0 便携版（免安装，开箱即用）
├── run.py                       # Flask 启动入口
├── start_all.bat                # Windows 一键启动
├── server_control.bat           # 服务管理控制面板
└── CLAUDE.md                    # Claude Code 协作指引
```

---

## 四、分层架构

```
┌────────────────────────────────────────────────┐
│  前端 (Vue 3 + Element Plus)                    │
│  views/ → stores/ → utils/request.js            │
│  Axios 拦截器自动附带 JWT → /api/*               │
└──────────────────┬─────────────────────────────┘
                   │ HTTP JSON
┌──────────────────▼─────────────────────────────┐
│  Blueprint 路由层 (9 个)                         │
│  职责：提取请求参数 → 调用 Controller → 包装响应   │
│  不写业务逻辑，不直接操作 Model                     │
└──────────────────┬─────────────────────────────┘
                   │ 函数调用
┌──────────────────▼─────────────────────────────┐
│  Controller 业务层 (7 个)                        │
│  职责：业务规则校验 → ORM 查询/写入 → 事务管理      │
│  通过 DatabaseManager.get_session() 获取会话       │
│  不得访问 request 对象                            │
└──────────────────┬─────────────────────────────┘
                   │ ORM
┌──────────────────▼─────────────────────────────┐
│  Model 数据层 (11 张表 + base.py)                 │
│  DatabaseManager 单例管理 Engine 和 Session       │
│  支持 MySQL / SQL Server 双驱动                   │
└──────────────────┬─────────────────────────────┘
                   │
┌──────────────────▼─────────────────────────────┐
│  MySQL 8.0 / SQL Server                         │
└────────────────────────────────────────────────┘
```

### 为什么要这样分层？

- **Blueprint 不写业务逻辑**：路由只是薄薄一层，方便统一处理鉴权和响应格式
- **Controller 不碰 request**：业务方法可以独立测试，切换 Web 框架时只需改 Blueprint
- **Model 通过 base.py 管理连接**：懒初始化避免启动时数据库不可达导致崩溃

---

## 五、开发环境搭建

### 5.1 基础要求

| 工具 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | 后端运行和测试 |
| Node.js | 18+ | 前端构建（生产模式可以不用，直接用预构建的 `dist/`） |
| Git | 最新版 | 代码版本管理 |
| PyCharm | 最新版 | 推荐 IDE（也支持 VS Code） |

### 5.2 首次搭建步骤

```bash
# 1. 克隆仓库
git clone <仓库地址>
cd 高校教务管理系统

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 配置数据库连接
cp backend/config/config.ini.example backend/config/config.ini
# 编辑 config.ini，填入你的数据库密码

# 4. 构建前端（需要 Node.js）
cd frontend
npm install
npm run build    # 产物输出到 frontend/dist/
cd ..

# 5. 初始化数据库
# 方式 A：用便携版 MySQL（推荐）
#   双击 start_all.bat → [2] Auto Setup & Start
# 方式 B：连接已有 MySQL，手动导入
#   mysql -u root -p < backend/config/init_database_mysql.sql

# 6. 启动
python run.py
# 打开 http://localhost:5000
```

已有数据库会在启动时自动执行幂等的增量结构检查。也可以在启动前手动运行：

```powershell
python run.py --upgrade-db-only
```

该命令只补充当前版本所需的列和约束，不会重建数据表；若发现多条
`semester_config.is_current=1`，会拒绝自动选择并要求先修正数据。

### 5.3 前端热更新开发模式

修改前端代码时，每次 `npm run build` 太慢。用 Vite 开发服务器实现秒级热更新：

```bash
# 终端 1：后端
python run.py

# 终端 2：前端
cd frontend
npm run dev
# 访问 http://localhost:5173（API 请求自动代理到 :5000）
```

`vite.config.js` 中配置了代理规则：`/api` 和 `/uploads` 开头的请求自动转发到 Flask 后端。

---

## 六、核心业务设计

### 6.1 课程-计划-选课三级模型

```
course（课程定义）
  │  例：CS101 — 数据结构 — 4学分 — 计算机学院
  │
  ▼
course_plan（开课计划，教师申请→管理员审核）
  │  例：CS101 — 2024秋 — 王老师 — 第1-16周 — 每周一第3-4节 — 容量40人
  │
  ▼
enrollment（选课记录）
  │  例：张三 → CS101-2024秋-01班
  │
  ▼
grade（成绩）
  │  例：张三 → CS101 — 85分 — 绩点3.5
```

**设计要点：**
- 同一门课可以有多条 `course_plan`（不同学期、不同班级）
- `course_plan.status` 为"已通过"后，学生才可见
- 选课/退课固定按 `Student → CoursePlan → Enrollment` 锁序；MySQL 使用
  `SELECT ... FOR UPDATE`，SQL Server 使用 `UPDLOCK, ROWLOCK, HOLDLOCK`。
  `(student_id, plan_id)` 唯一约束是最终并发兜底。

### 6.2 选课流程（最复杂的业务）

```
学生浏览课程 → 筛选/搜索 → 点击选课
  → 校验 1: 是否在本学期选课时段内
  → 校验 2: 课程容量是否未满（FOR UPDATE 锁定）
  → 校验 3: 是否已选过此课（防重）
  → 校验 4: 课表时间是否冲突
  → 校验 5: 学分是否超上限
  → 创建 enrollment 记录
  → 写操作日志
```

当多个学生同时抢最后一席时，行级锁确保只有一人成功，其余收到"课程已满"。

### 6.3 审核流程

系统有三条审核流（统一在 `AdminAudit.vue` 三个页签中处理）：

| 审核类型 | 提交者 | 数据表 | 状态流转 |
|----------|--------|--------|----------|
| 课程审核 | 教师 | `course_plan` | 待审核 → 已通过 / 已拒绝 |
| 成绩修改 | 教师 | `grade` | new_score 非空 → 管理员审核 → score = new_score / new_score 清空 |
| 密码重置 | 任意用户 | `password_reset_request` | 待审核 → 已通过 / 已拒绝 |

### 6.4 角色权限矩阵

| API 前缀 | admin | teacher | student | 公开 |
|----------|:-----:|:-------:|:-------:|:----:|
| `/api/auth` | ✓ | ✓ | ✓ | login/forgot-password |
| `/api/admin` | ✓ | | | |
| `/api/audit` | ✓ | | | |
| `/api/student` | | | ✓ | |
| `/api/teacher` | | ✓ | | |
| `/api/enrollment` | | | ✓ | |
| `/api/grade` | ✓ | ✓ | | |
| `/api/stats` | ✓ | ✓ | | |

---

## 七、代码规范

### 7.1 Python

```python
# 文件编码：UTF-8（不要用 GBK）
# 错误消息：中文

# ✅ 控制器方法返回字典，由 Blueprint 用 success_response() 包装
def get_students(self, page, per_page, keyword):
    students, total = self._query_students(page, per_page, keyword)
    return {
        "students": students,
        "total": total,
        "page": page,
    }

# ❌ Controller 不要直接访问 request
def get_students(self, request):    # 错误
    page = request.args.get("page")

# ❌ 不要字符串拼接 SQL
query = f"SELECT * FROM student WHERE name = '{name}'"  # SQL 注入风险
```

### 7.2 Vue / JavaScript

```javascript
// ✅ Composition API + <script setup>
// ✅ 路由路径英文，页面标题中文
// ✅ 所有页面使用 MainLayout

// ❌ 不要自建独立布局
// ❌ 不要在前端硬编码 JWT secret 或数据库密码
// ❌ 不要在 props 里传递敏感数据
```

### 7.3 Git 提交

```
提交消息格式：中文，简洁描述变更
✅ 修复选课控制部分时段问题
✅ 修复前端教师停课按钮逻辑
✅ 新增学生成绩统计图表
❌ fix bug
❌ update code
```

---

## 八、数据库设计要点

| 设计决策 | 原因 |
|----------|------|
| 状态列用 `String(10)` 而非 ENUM | SQL Server 无原生 ENUM，用字符串兼容双数据库 |
| 密码 bcrypt 12 轮 | 业界标准，破解成本高 |
| `semester_config.enrollment_open` 开关 | 管理员可随时关闭选课（系统维护/学期结束） |
| `operation_log` 记录所有操作 | 审计溯源，满足教务管理合规要求 |
| `course_plan.start_week/end_week` | 部分课程如实习课只上前半学期，不是所有课都占满 20 周 |
| `grade.new_score` 字段 | 成绩修改不走直接覆盖，而是提交 new_score 等待审核 |

---

## 九、测试

```bash
# 运行全部测试
python -m pytest tests/ -v

# 运行单个模块
python -m pytest tests/test_enrollment.py -v

# 选课测试含并发用例（验证行级锁）
python -m pytest tests/test_enrollment.py -v -k "concurrent"
```

| 测试文件 | 覆盖内容 |
|----------|----------|
| `test_auth.py` | 登录/登出/token 刷新/密码修改 |
| `test_enrollment.py` | 选课 5 项校验 + 并发选课容量控制 |
| `test_grade.py` | 成绩录入/批量导入/修改申请/审核 |

---

## 十、构建与部署

### 开发阶段

```
python run.py              # 后端 :5000
cd frontend && npm run dev # 前端 :5173（热更新）
```

### 生产部署（腾讯云轻量服务器）

参考 `CLOUD_MIGRATION.md`，核心步骤：

1. 服务器安装 Python 3.11+ + MySQL 8.0
2. `git clone` 代码 → `pip install` → `npm run build`
3. Nginx 反向代理 `:5000`，配置静态文件缓存
4. `config.ini` 填入生产数据库连接信息
5. `run_prod.py` 以 production 模式启动

### 打包分发

双击 `server_control.bat` → `[7] Package for partner`，生成自包含 zip（含便携 MySQL + 预构建前端 + 嵌入式 Python），伙伴解压即用。

---

## 十一、常见开发任务速查

| 任务 | 改哪里 | 参考 |
|------|--------|------|
| 加一个新页面 | `views/<角色>/` + `router/index.js` | 第四章结构 |
| 加一个 API | `blueprints/` + `controllers/` | 分层架构图 |
| 加一张表 | `models/` + 两个 `init_database_*.sql` | 第八章设计要点 |
| 改选课逻辑 | `controllers/enrollment_controller.py` | 第六章 6.2 |
| 改登录 | `controllers/auth_controller.py` + `stores/auth.js` | API.md 第 3.1 节 |
| 改权限 | `api/auth.py` 装饰器 | 第六章 6.4 角色矩阵 |
| 调试 | 看 `logs/` 或 `npm run dev` 浏览器控制台 | DEBUG.md |

---

## 十二、相关文档索引

| 文档 | 内容 |
|------|------|
| [README.md](README.md) | 用户视角：功能介绍、快速开始、默认账号 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 代码视角：124 文件清单、数据流图、架构决策 |
| [API.md](API.md) | 接口视角：48 个端点完整文档 |
| [DEBUG.md](DEBUG.md) | 调试视角：PyCharm 配置、常见问题、日志 |
| [CLAUDE.md](CLAUDE.md) | AI 协作：Claude Code 工作指引 |
| [SETUP_PARTNER.md](SETUP_PARTNER.md) | 协作视角：项目分发、局域网/外网连接 |
| [CLOUD_MIGRATION.md](CLOUD_MIGRATION.md) | 运维视角：服务器部署 |
