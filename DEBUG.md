# Debug 调试文档

> 高校教务管理系统 v3.0 — 问题排查与调试指南

---

## 目录

- [PyCharm 调试配置](#pycharm-调试配置)
- [常见问题排查](#常见问题排查)
- [日志系统](#日志系统)
- [前端调试](#前端调试)
- [数据库调试](#数据库调试)
- [调试技巧汇总](#调试技巧汇总)

---

## PyCharm 调试配置

### 1. 配置 Run/Debug Configuration

1. **Run → Edit Configurations → + → Python**
2. 按以下参数填写：

| 字段 | 值 |
|------|-----|
| Name | `EduMgmt Flask Debug` |
| Script path | `<项目根目录>/run.py` |
| Working directory | `<项目根目录>` |
| Environment variables | `FLASK_ENV=development` |
| Python interpreter | Python 3.11+ |

3. 勾选 **Run with Python console**（方便调试时在控制台交互）

### 2. Flask Debug 模式

`run.py` 默认以 debug 模式启动：

```python
app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
```

| 参数 | 作用 |
|------|------|
| `debug=True` | 代码修改后自动重载；异常页面显示完整 traceback |
| `threaded=True` | 多线程处理并发请求 |
| `host='0.0.0.0'` | 监听所有网络接口（允许局域网访问） |

调试模式下 Flask 会自动重载，修改 Python 代码后无需手动重启。

### 3. 断点调试

1. 在代码行号左侧点击添加断点（红点）
2. 右键配置 → **Debug 'EduMgmt Flask Debug'**（或 Shift+F9）
3. 程序运行到断点自动暂停，可执行：
   - **F7** — Step Into（进入函数内部）
   - **F8** — Step Over（执行当前行，不进入函数）
   - **F9** — Resume（继续运行到下一个断点）
   - **Alt+F8** — Evaluate Expression（计算表达式）

### 4. 关键断点位置

| 文件 | 行号 | 用途 |
|------|------|------|
| 控制器 `__init__` | 各 `*_controller.py` 首行 | 追踪请求入口 |
| `enrollment_controller.py` | `enroll_course()` | 选课逻辑入口 |
| `enrollment_controller.py` | `_check_enrollment_period()` | 选课时段校验 |
| `auth_controller.py` | `login()` | 登录认证 |
| `grade_controller.py` | `apply_grade_modify()` | 成绩修改申请 |
| `admin_controller.py` | CRUD 方法 | 管理员操作 |

---

## 常见问题排查

### 问题 1: MySQL 连接失败

**现象**:
```
sqlalchemy.exc.OperationalError: (2003, "Can't connect to MySQL server on 'localhost'")
```

**排查步骤**:
1. 检查 MySQL 是否启动：任务管理器 → 查找 `mysqld.exe` 进程
2. 检查端口占用：`netstat -ano | findstr 3306`
3. 检查 `backend/config/config.ini` 中密码是否正确
4. 检查 `mysql-portable/my.ini.auto` 是否存在且路径正确

**解决**:
- 如果 MySQL 未启动：运行 `start_all.bat` 选 [1]
- 如果端口被占用：`netstat -ano | findstr 3306` 找到 PID → 任务管理器结束进程
- 如果密码错误：确认 `config.ini` 中 `password = Cairenbin2005`

### 问题 2: 中文乱码

**现象**: 页面显示 `???` 或 `æ±‰å­—`

**排查**: 逐层检查编码设置

| 层级 | 检查项 | 正确值 |
|------|--------|--------|
| MySQL 数据库 | `SHOW CREATE DATABASE course_management_db` | `utf8mb4` |
| MySQL 表 | `SHOW CREATE TABLE user_account` | `utf8mb4_unicode_ci` |
| MySQL 连接 | `show variables like 'character%'` | `utf8mb4` |
| Flask | 请求/响应头 `Content-Type` | `application/json; charset=utf-8` |
| HTML | `<meta charset="utf-8">` | 在 `frontend/dist/index.html` 中 |
| Python 文件 | 文件编码声明 | `# -*- coding: utf-8 -*-` |

**解决**:
```sql
-- 如果数据库字符集不对
ALTER DATABASE course_management_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 问题 3: 端口 5000 被占用

**现象**:
```
OSError: [Errno 10048] Only one usage of each socket address is normally permitted
```

**解决**:
```bash
# Windows PowerShell
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# 或修改 run.py 中的端口号
app.run(debug=True, host='0.0.0.0', port=5001)
```

### 问题 4: CORS 跨域错误

**现象**: 浏览器控制台显示 `Access-Control-Allow-Origin` 相关错误

**原因**: Flask-CORS 未正确配置

**解决**: 检查 `run.py` 中是否有：
```python
from flask_cors import CORS
CORS(app, supports_credentials=True)
```

开发模式下 Vite dev server (:5173) 通过 Vite proxy 转发 `/api` 到 Flask (:5000)，不涉及 CORS。此问题只在使用生产模式但前端未构建到 `dist/` 时出现。

### 问题 5: 前端修改不生效

**原因**: Flask 在生产模式下直接提供 `frontend/dist/` 的静态文件，修改源码后需重新构建。

**解决**:
```bash
# 方法 1: 使用 start_all.bat 选项 [3]
# 方法 2: 手动构建
cd frontend
npm run build
```

**开发时推荐**: 使用 Vite 开发服务器（热更新）：
```bash
# 终端 1
python run.py

# 终端 2
cd frontend
npm run dev
# 浏览器访问 http://localhost:5173
```

### 问题 6: 选课按钮不可见/灰色

**检查清单**:
1. 当前学期选课是否开放：管理员 → 选课时段控制 → 检查 `enrollment_open=1` 且当前时间在 `enroll_start` ~ `enroll_end` 范围内
2. 学生是否已选满：检查该课程 `course_plan.enrolled < capacity`
3. 时间是否冲突：检查已选课程 schedule
4. 先修课是否通过：检查每门 prerequisite 对应的 grade.score >= 60

**API 直接测试**:
```bash
curl -X POST http://localhost:5000/api/enroll -H "Content-Type: application/json" -H "Authorization: Bearer <token>" -d '{"plan_id": 1}'
```

返回的 `message` 字段会说明具体失败原因。

### 问题 7: pip install 失败（bcrypt / mysqlclient）

**bcrypt 安装失败**（Windows）:
```bash
# 使用预编译 wheel
pip install --only-binary=:all: bcrypt
```

**PyMySQL 安装失败**:
```bash
pip install --upgrade pip setuptools wheel
pip install PyMySQL
```

---

## 日志系统

### 日志位置

所有日志文件位于项目根目录的 `logs/` 文件夹：

```
logs/
├── auth.log          # 认证模块日志
├── enrollment.log    # 选课模块日志
├── grade.log         # 成绩模块日志
├── admin.log         # 管理员操作日志
├── stats.log         # 统计分析日志
├── course.log        # 课程管理日志
└── general.log       # 通用日志
```

### 日志格式

```
[2026-06-18 09:30:15][INFO][auth_controller][login:45] 用户 admin 登录成功
[2026-06-18 09:30:20][ERROR][enrollment_controller][enroll_course:120] 选课失败: 课程容量已满 (plan_id=5)
```

格式说明: `[时间戳][级别][模块][函数:行号] 消息`

### 日志级别

| 级别 | 含义 | 何时使用 |
|------|------|----------|
| DEBUG | 调试信息 | 变量值、SQL 语句、中间状态 |
| INFO | 一般信息 | 正常操作记录（登录、选课成功） |
| WARNING | 警告 | 可恢复的异常（密码错误、容量满） |
| ERROR | 错误 | 需要关注的异常（数据库连接失败） |

### 修改日志级别

编辑 `backend/config/config.ini`:
```ini
[system]
log_level = DEBUG    # 可选: DEBUG | INFO | WARNING | ERROR
```

设为 `DEBUG` 后可以看到 SQLAlchemy 生成的 SQL 语句和更详细的调用栈。

### 日志轮转

- 单个日志文件最大 10MB
- 超过后自动轮转，保留最近 30 个备份
- 备份文件命名: `auth.log.1`, `auth.log.2`, ...

### 在 PyCharm 中查看日志

1. 直接打开 `logs/` 目录下的文件
2. 使用 PyCharm 的 **Run** 窗口 — 运行时日志会直接输出到控制台（debug 模式下）
3. 可配合 PyCharm **Grep Console** 插件，按颜色高亮不同级别的日志

---

## 前端调试

### Vite 开发服务器

开发时推荐使用 Vite dev server，修改 Vue 代码后**自动热更新**，无需手动构建：

```bash
cd frontend
npm run dev
```

访问 `http://localhost:5173`，API 请求自动代理到 Flask `:5000`。

### 浏览器 DevTools

**F12 → Network 标签**:
- 查看所有 API 请求的 URL、状态码、响应内容
- 勾选 **Preserve log** 保留页面跳转前的请求
- 右键请求 → **Copy as cURL** 复现请求

**F12 → Console 标签**:
- 查看前端错误和 `console.log` 输出
- 红色错误点击可跳转到源码位置

**F12 → Application 标签**:
- Storage → Local Storage → 查看 `token`（JWT 令牌）
- 手动清除 token 模拟未登录状态

### Vue DevTools

安装 Chrome/Firefox 扩展 **Vue.js devtools** 后：

- **Components** 标签: 查看组件树、props、data、computed
- **Pinia** 标签: 查看所有 store 状态、getter 值
- **Timeline** 标签: 追踪组件渲染和事件触发

### 常见前端调试场景

**"页面白屏"**:
1. Console 查看是否有 JS 报错
2. Network 检查 `index.html` 和 JS bundle 是否成功加载
3. 检查 `localStorage` 是否有 token（已登录但 token 过期会路由到 login）

**"数据显示为空"**:
1. Network 检查对应 API 是否返回 200
2. 如果是 401: token 过期，重新登录
3. 如果是 200 但数据为空: 检查 API 响应中的 `data` 字段

**"按钮点击无反应"**:
1. Console 检查是否报错
2. 检查按钮是否有 `disabled` 属性
3. 在 Vue DevTools 中检查组件状态

---

## 数据库调试

### PyCharm Database 工具窗口

1. **View → Tool Windows → Database**
2. 点击 **+** → Data Source → **MySQL**
3. Host: `localhost`, Port: `3306`
4. User: `root`, Password: `Cairenbin2005`
5. Database: `course_management_db`
6. 点击 **Test Connection** → OK

连接后可直接：
- 浏览表数据（双击表名）
- 执行 SQL 查询（右键 → Jump to Query Console）
- 查看表结构（Ctrl+B 或 Cmd+B）

### 命令行 MySQL

```bash
cd mysql-portable\bin
mysql.exe -u root -pCairenbin2005 --protocol=TCP course_management_db
```

常用查询：
```sql
-- 查看所有表
SHOW TABLES;

-- 查看表结构
DESC enrollment;

-- 查看当前选课统计
SELECT cp.course_id, cp.capacity, cp.enrolled, COUNT(e.enroll_id) AS actual
FROM course_plan cp
LEFT JOIN enrollment e ON cp.plan_id = e.plan_id AND e.status = '已选'
GROUP BY cp.plan_id;

-- 检查选课时段配置
SELECT * FROM semester_config WHERE is_current = 1;

-- 查看最近操作日志
SELECT * FROM operation_log ORDER BY log_time DESC LIMIT 20;

-- 查看密码重置待审核
SELECT * FROM password_reset_request WHERE status = '待审核' ORDER BY request_time DESC;
```

### 数据库重置

如果测试数据损坏需要重新初始化：

```bash
# 方法 1: 用 start_all.bat 自动初始化
# 先删除 mysql-portable/data/ 目录，再运行 start_all.bat 选 [1]

# 方法 2: 手动执行 SQL 脚本
cd mysql-portable\bin
mysql.exe -u root -pCairenbin2005 --protocol=TCP < ..\..\backend\config\init_database_mysql.sql
```

**注意**: 这会删除所有现有数据。

### SQLAlchemy SQL 调试

要查看 SQLAlchemy 实际执行的 SQL，在代码中添加：

```python
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

或设置 `config.ini` 中 `log_level = DEBUG`，日志文件会记录完整的 SQL 语句。

---

## 调试技巧汇总

### API 快速测试

使用 `curl` 直接测试 API（绕过前端）：

```bash
# 1. 登录获取 token
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"admin","password":"123456"}'

# 响应中包含 token，复制后用于后续请求

# 2. 带 token 调用 API
curl http://localhost:5000/api/enrollment/my-enrollments \
  -H "Authorization: Bearer <上面获取的token>"

# 3. 选课
curl -X POST http://localhost:5000/api/enrollment/enroll \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"plan_id": 1}'
```

### 验证 Token 内容

访问 https://jwt.io 粘贴 token 查看其中的 `user_id`、`role` 和过期时间。

### 检查前端构建产物

```bash
# 确认 dist 包含最新构建的组件
dir frontend\dist\assets\ | findstr "AdminEnrollment"
# 应包含 AdminEnrollmentControl-*.js 和 AdminEnrollmentControl-*.css
```

### 清除浏览器缓存

如果前端修改后仍需强制刷新：
- **Chrome/Edge**: Ctrl+Shift+R 或 F12 → Network → 勾选 Disable cache
- 或 F12 → Application → Clear storage → Clear site data

### 环境完整性检查清单

调试前先过一遍：

- [ ] Python 3.11+: `python --version`
- [ ] Node.js 18+: `node --version`
- [ ] pip 依赖: `pip show Flask SQLAlchemy PyMySQL bcrypt`
- [ ] npm 依赖: `dir frontend\node_modules\`
- [ ] 前端已构建: `frontend\dist\index.html` 存在
- [ ] config.ini: `driver = mysql`, `password = Cairenbin2005`
- [ ] MySQL 进程: 任务管理器中有 `mysqld.exe`
- [ ] 端口 3306: `netstat -ano | findstr 3306` 有 LISTENING
- [ ] 端口 5000: 空闲（`netstat -ano | findstr 5000` 无 LISTENING 或为旧 Flask 进程）
- [ ] `mysql-portable\data\` 目录存在且非空
- [ ] `mysql-portable\my.ini.auto` 文件存在

以上全部通过后再启动 Flask，90% 的启动问题都在这 11 项中。
