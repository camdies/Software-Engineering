# 高校教务管理系统 v3.0 — 项目代码架构表

> 总文件数: **124** (不含 .venv, node_modules, __pycache__, .git)  
> 后端: Python Flask + SQLAlchemy (38 .py)  
> 前端: Vue 3 + Element Plus + Vite (17 .vue + 5 .js)  
> 数据库: MySQL 8.0+ (默认) / SQL Server (可选) (2 .sql)

---

## 一、目录总览

```
项目根目录/
├── backend/              ← Python Flask REST API
│   ├── api/              # Flask 应用工厂、认证、响应格式、蓝图路由
│   │   └── blueprints/   # 9 个蓝图 (46 个 API 端点)
│   ├── controllers/      # 7 个业务逻辑控制器
│   ├── models/           # 11 个 SQLAlchemy ORM 模型
│   ├── config/           # 配置文件 + DDL 初始化脚本
│   └── utils/            # 6 个工具模块
├── frontend/             ← Vue.js 3 SPA
│   ├── src/
│   │   ├── views/        # 14 个页面组件
│   │   │   ├── admin/    # 管理员端 (7个)
│   │   │   ├── teacher/  # 教师端 (4个)
│   │   │   └── student/  # 学生端 (3个)
│   │   ├── router/       # Vue Router 配置
│   │   ├── stores/       # Pinia 状态管理
│   │   ├── layouts/      # 布局组件
│   │   ├── components/   # 通用组件
│   │   ├── utils/        # Axios 实例 + 常量
│   │   └── styles/       # 全局 SCSS
│   └── dist/             # 构建产物
├── tests/                # 测试用例
├── logs/                 # 日志文件
├── *.bat                 # Windows 批处理工具 (start_all/server_control/partner_connect)
├── *.md                  # 文档 (7个)
├── mysql-portable/       # MySQL 8.0 便携版 (含 start_mysql.bat)
└── run.py                # 入口文件
```

---

## 二、后端架构 (backend/)

### 2.1 API 层 (`backend/api/`)

| 文件 | 大小 | 职责 |
|------|------|------|
| `app_factory.py` | 4.1 KB | Flask 应用工厂: CORS、蓝图注册、静态文件服务、延迟数据库初始化 |
| `auth.py` | 4.4 KB | JWT 创建/解码、`@require_auth` / `@require_role` 装饰器 |
| `response.py` | 2.3 KB | `success_response()` / `error_response()` / `wrap_controller_result()` |

### 2.2 蓝图路由 (`backend/api/blueprints/`) — 46 个端点

| 文件 | 大小 | URL 前缀 | 端点数 | 角色 |
|------|------|----------|--------|------|
| `admin_bp.py` | 12.9 KB | `/api/admin` | 17 | 管理员 |
| `audit_bp.py` | 6.5 KB | `/api/audit` | 5 | 管理员 |
| `auth_bp.py` | 2.7 KB | `/api/auth` | 4 | 公开/任意 |
| `password_reset_bp.py` | 1.0 KB | `/api/auth` | 1 | 公开 |
| `student_bp.py` | 2.0 KB | `/api/student` | 4 | 学生 |
| `teacher_bp.py` | 6.2 KB | `/api/teacher` | 6 | 教师 |
| `enrollment_bp.py` | 1.5 KB | `/api/enrollment` | 2 | 学生 |
| `grade_bp.py` | 3.5 KB | `/api/grade` | 4 | 教师/管理员 |
| `stats_bp.py` | 2.9 KB | `/api/stats` | 3 | 教师/管理员 |

### 2.3 控制器 (`backend/controllers/`) — 业务逻辑

| 文件 | 大小 | 类 | 职责 |
|------|------|---|------|
| `admin_controller.py` | 20.1 KB | `AdminController` | 学生/教师/课程 CRUD、日志查询 |
| `auth_controller.py` | 13.8 KB | `AuthController` | 登录/登出/密码修改/密码重置/忘记密码 |
| `enrollment_controller.py` | 18.4 KB | `EnrollmentController` | 选课/退课 (5项校验 + 行级锁) |
| `grade_controller.py` | 17.3 KB | `GradeController` | 成绩录入/批量导入/修改申请/审核 |
| `stats_controller.py` | 13.0 KB | `StatsController` | 班级统计/学业统计/成绩分布/课表导出 |
| `student_controller.py` | 7.4 KB | `StudentController` | 可选课程/已选课程/成绩查询 |
| `teacher_controller.py` | 2.9 KB | `TeacherController` | 授课计划/选课学生查询 |

### 2.4 模型 (`backend/models/`) — 11 个 ORM 表

| 文件 | 大小 | 表名 | 说明 |
|------|------|------|------|
| `class_period.py` | 1.4 KB | `class_period` | 上课节次时间表 (11节课固定数据) |
| `semester_config.py` | 2.4 KB | `semester_config` | 学期配置表 (默认20周/选课开关) |
| `user_account.py` | 2.5 KB | `user_account` | 用户账号 (密码/角色/锁定状态) |
| `student.py` | 2.3 KB | `student` | 学生信息 |
| `teacher.py` | 2.1 KB | `teacher` | 教师信息 |
| `course.py` | 3.0 KB | `course` | 课程信息 (含课程类型/面向专业) |
| `course_plan.py` | 5.3 KB | `course_plan` | 开课计划 (教师申请→管理员审核) |
| `enrollment.py` | 2.8 KB | `enrollment` | 选课记录 |
| `grade.py` | 3.4 KB | `grade` | 成绩记录 (含 new_score) |
| `operation_log.py` | 2.5 KB | `operation_log` | 操作日志 |
| `password_reset_request.py` | 2.6 KB | `password_reset_request` | 密码重置申请 |
| `base.py` | 5.8 KB | — | DatabaseManager 单例 + Engine/Session 管理 |

### 2.5 工具 (`backend/utils/`)

| 文件 | 大小 | 职责 |
|------|------|------|
| `auth_util.py` | 1.8 KB | bcrypt 密码哈希/验证 (12轮) |
| `export_util.py` | 4.0 KB | openpyxl Excel 导出 (带样式) |
| `gpa_calculator.py` | 2.2 KB | 百分制→绩点映射 / 累计GPA计算 |
| `log_util.py` | 2.8 KB | TimedRotatingFileHandler 日志 |
| `validator.py` | 3.9 KB | 输入校验 (学号/成绩/密码/联系方式/学分) |

### 2.6 配置 (`backend/config/`)

| 文件 | 大小 | 说明 |
|------|------|------|
| `init_database_mysql.sql` | ~22 KB | 完整 MySQL DDL + 测试数据 (11表, 含 new_password 列) |
| `init_database.sql` | 24.8 KB | SQL Server 版 DDL (同结构，不同语法) |
| `config.ini.example` | ~1 KB | 数据库/系统/Web/选课 配置模板（含 [web] 段 jwt_secret） |
| `settings.py` | ~5 KB | ConfigParser 配置读取单例 |

---

## 三、前端架构 (frontend/)

### 3.1 入口与配置

| 文件 | 大小 | 职责 |
|------|------|------|
| `index.html` | 0.7 KB | HTML 入口 (含 Loading 占位) |
| `vite.config.js` | 1.4 KB | Vite 构建配置 (API 代理/__API_BASE__ 注入) |
| `package.json` | 0.5 KB | npm 依赖声明 |
| `src/main.js` | 1.3 KB | Vue 应用初始化 (Pinia → Router → ElementPlus) |
| `src/App.vue` | 0.1 KB | 根组件 (纯 `<router-view />`) |

### 3.2 路由 (`src/router/`)

| 文件 | 大小 | 路由数 | 说明 |
|------|------|--------|------|
| `index.js` | 4.2 KB | 17 | 含 beforeEach 导航守卫 (JWT + 角色校验) |

复映射:

| 路径 | 组件 | 角色 |
|------|------|------|
| `/login` | LoginView | public |
| `/admin/students` | AdminStudents | admin |
| `/admin/teachers` | AdminTeachers | admin |
| `/admin/courses` | AdminCourses | admin |
| `/admin/course-plans` | AdminCoursePlans | admin |
| `/admin/audit` | AdminAudit | admin |
| `/admin/enrollment-stats` | AdminEnrollmentStats | admin |
| `/admin/logs` | AdminLogs | admin |
| `/teacher/plans` | TeacherPlans | teacher |
| `/teacher/grades` | TeacherGrades | teacher |
| `/teacher/grade-modify` | TeacherGradeModify | teacher |
| `/teacher/stats` | TeacherStats | teacher |
| `/student/enroll` | StudentEnroll | student |
| `/student/my-courses` | StudentSchedule | student |
| `/student/grades` | StudentGrades | student |
| `/student/stats` | StudentStats | student |

### 3.3 视图组件 (`src/views/`)

**管理员端 (7个)**

| 文件 | 大小 | 功能 |
|------|------|------|
| `AdminStudents.vue` | 5.1 KB | 学生 CRUD + 分页搜索 + 自动注册账号 |
| `AdminTeachers.vue` | 4.6 KB | 教师 CRUD + 分页搜索 + 自动注册账号 |
| `AdminCourses.vue` | 4.5 KB | 课程 CRUD + 完整信息录入 |
| `AdminCoursePlans.vue` | 1.9 KB | 开课计划查看 |
| `AdminAudit.vue` | 7.2 KB | 三合一审核中心 (密码重置/成绩/课程) |
| `AdminEnrollmentStats.vue` | 1.8 KB | 选课统计 (容量/已选进度条) |
| `AdminLogs.vue` | 2.3 KB | 操作日志分页查询 |

**教师端 (4个)**

| 文件 | 大小 | 功能 |
|------|------|------|
| `TeacherPlans.vue` | 9.1 KB | 授课计划申请/编辑/停课 + 课程搜索 |
| `TeacherGrades.vue` | 3.6 KB | 成绩录入 + Excel 批量导入 |
| `TeacherGradeModify.vue` | 2.9 KB | 成绩修改申请 |
| `TeacherStats.vue` | 3.9 KB | 班级统计/分数段分布/排名 |

**学生端 (3个)**

| 文件 | 大小 | 功能 |
|------|------|------|
| `StudentEnroll.vue` | 20.6 KB | 选课主页: 搜索栏 + 折叠筛选 + 页签式卡片 + 弹窗详情 + 右侧占用表侧边栏 |
| `StudentSchedule.vue` | 9.2 KB | 个人课表: 11节×7天周表 + 彩色课程块 + Excel/PDF导出 |
| `StudentGrades.vue` | 1.5 KB | 成绩查询 (颜色标记分数段) |
| `StudentStats.vue` | 1.3 KB | 学业统计 (学分/GPA/未通过课程) |

**登录 (1个)**

| 文件 | 大小 | 功能 |
|------|------|------|
| `LoginView.vue` | 4.7 KB | 登录表单 + 忘记密码弹窗 |

### 3.4 状态管理与工具

| 文件 | 大小 | 职责 |
|------|------|------|
| `stores/auth.js` | 1.6 KB | Pinia 认证 store (token/role/userId + login/logout) |
| `stores/app.js` | 0.4 KB | Pinia 应用 store (侧边栏/面包屑) |
| `utils/request.js` | 2.1 KB | Axios 实例 (baseURL + JWT拦截器 + 401/403处理) |
| `utils/constants.js` | 0.2 KB | 角色标签常量 |
| `styles/global.scss` | 1.3 KB | Element Plus 覆盖 + 通用布局类 |

### 3.5 布局与通用组件

| 文件 | 大小 | 职责 |
|------|------|------|
| `layouts/MainLayout.vue` | 6.5 KB | 主布局: 侧边栏(角色菜单) + 顶栏(面包屑/角色标签/登出) + `<router-view>` |
| `components/ChangePasswordDialog.vue` | 2.5 KB | 修改密码弹窗 (旧密码+新密码+确认) |

---

## 四、工具脚本

| 文件 | 大小 | 说明 |
|------|------|------|
| `server_control.bat` | ~15 KB | 服务器控制面板: 启停/状态/分发/MySQL前台/后台 |
| `start_all.bat` | ~3 KB | 一键启动（MySQL + Flask + 依赖安装） |
| `partner_connect.bat` | 5.9 KB | 伙伴前端开发代理配置: LAN/IPv6/WAN 三模式 |
| `ipv6_diagnostic.bat` | 6.8 KB | IPv6 连通性诊断: 5项检测 + 防火墙修复 |
| `mysql-portable/start_mysql.bat` | ~1 KB | MySQL 独立启动（自动路径替换） |

---

## 五、文档

| 文件 | 大小 | 说明 |
|------|------|------|
| `README.md` | 6.4 KB | 项目说明、技术栈、快速开始、默认账号、上课时间表 |
| `API.md` | 15.8 KB | 完整 API 文档 (46端点, 请求/响应示例, 错误码) |
| `CLOUD_MIGRATION.md` | 9.5 KB | 腾讯云轻量服务器迁移教程 (Nginx + Flask + MySQL) |
| `SETUP_PARTNER.md` | ~5 KB | 开发伙伴协作指南（完整分发/浏览器直连/前端代理三模式） |
| `SQL_SERVER_SETUP_GUIDE.md` | ~12 KB | SQL Server + SSMS + ODBC 安装与配置完整指南 |
| `MYSQL_SETUP_GUIDE.md` | ~3 KB | 数据库修复/重建/迁移指引 |

---

## 六、测试

| 文件 | 大小 | 说明 |
|------|------|------|
| `tests/run_all.py` | 0.5 KB | 测试发现/运行器 |
| `tests/test_auth.py` | 3.9 KB | 认证模块测试 |
| `tests/test_enrollment.py` | 8.4 KB | 选课逻辑测试 (并发+5项校验) |
| `tests/test_grade.py` | 4.2 KB | 成绩管理测试 |

---

## 七、数据流图

```
用户浏览器 (Vue SPA)
    │
    │ HTTP /api/*
    ▼
Flask (app_factory.py)
    │
    ├─ @require_auth → JWT 解码 → g.current_user
    ├─ @require_role → 角色校验
    │
    ▼
Blueprint 路由 (9个)
    │
    ├─ 参数提取 (request.args / request.get_json())
    ├─ 参数校验 (必填/格式)
    │
    ▼
Controller 业务方法
    │
    ├─ DatabaseManager.get_session() → SQLAlchemy Session
    ├─ 查询/写入/事务管理
    ├─ 操作日志 (_write_log)
    │
    ▼
JSON Response → Axios 拦截器 → Pinia → Vue 组件渲染
```

---

## 八、关键架构决策

1. **双数据库支持**: `settings.py` 根据 `config.ini [database].driver` 切换 mssql/mysql 连接字符串
2. **SAEnum → String 迁移**: 所有模型的状态列改用 `String(10)` 而非 `SAEnum`, 避免 MSSQL 无原生 ENUM 导致的 LookupError
3. **延迟数据库初始化**: `app_factory.py` 使用 `@before_request` 懒初始化 DB, 避免启动时 DB 不可达导致 Flask 无法启动
4. **JWT 固定密钥**: `auth.py` 优先读 `config.ini` 中的 `jwt_secret`, 否则基于主机名 SHA256 生成 (保证重启后 token 不失效)
5. **Pinia 必须在 Router 之前安装**: `main.js` 先 `createPinia()` → `app.use(pinia)` → `app.use(router)` (否则登录页卡死)
6. **选课并发安全**: `enrollment_controller.py` 使用 `SELECT ... FOR UPDATE` 行级锁配合事务保证容量不超额
7. **前端 API 地址可配置**: `vite.config.js` 通过 `define.__API_BASE__` 注入构建时常量 (支持 `VITE_API_TARGET` 指向远程后端)
