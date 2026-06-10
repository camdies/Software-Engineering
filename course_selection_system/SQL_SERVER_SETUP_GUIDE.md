# Microsoft SQL Server 2025 + SSMS 2022 安装与配置指南

> **适用**: 学生选课及成绩管理系统（course_selection_system）
> **数据库**: Microsoft SQL Server 2025 Developer Edition
> **管理工具**: SQL Server Management Studio (SSMS) 2022

---

## 目录

1. [系统要求](#1-系统要求)
2. [安装 SQL Server 2025](#2-安装-sql-server-2025)
3. [安装 SSMS 2022](#3-安装-ssms-2022)
4. [安装 ODBC Driver 18](#4-安装-odbc-driver-18)
5. [配置 SQL Server](#5-配置-sql-server)
6. [初始化数据库](#6-初始化数据库)
7. [配置项目连接](#7-配置项目连接)
8. [常见问题排查](#8-常见问题排查)
9. [在 SSMS 中管理数据库](#9-在-ssms-中管理数据库)

---

## 1. 系统要求

| 组件 | 最低要求 |
|------|----------|
| 操作系统 | Windows 10/11 (x64) 或 Windows Server 2019/2022 |
| 内存 | 4 GB RAM（推荐 8 GB+） |
| 磁盘空间 | 6 GB 可用空间 |
| .NET Framework | 4.7.2 或更高（SQL Server 安装程序会自动安装） |
| 网络 | TCP/IP 协议已启用 |

---

## 2. 安装 SQL Server 2025

### 2.1 下载

从 Microsoft 官方下载 SQL Server 2025 **Developer Edition**（免费，功能完整）：

- 官方下载页: https://www.microsoft.com/sql-server/sql-server-downloads
- 直接选择 **Developer** 版本

### 2.2 安装步骤

```
1. 运行 SQL2025-SSEI-Dev.exe
2. 选择安装类型 → "自定义"
3. 指定安装目录（默认 C:\Program Files\Microsoft SQL Server）
4. 等待安装程序下载组件
5. 在"SQL Server 安装中心"中选择 "全新 SQL Server 独立安装"
```

**关键配置界面：**

#### 功能选择
勾选以下功能：
- ☑ **数据库引擎服务**（必须）
- ☑ **SQL Server 复制**（可选）
- ☑ **全文和语义提取**（可选）

#### 实例配置
- 选择 **默认实例**（实例名: MSSQLSERVER）
- 或命名实例（如 SQLEXPRESS）
- ⚠️ 记住实例名，后续连接时需要

#### 服务器配置
- SQL Server 代理: **自动**
- SQL Server 数据库引擎: **自动**

#### 数据库引擎配置 — 身份验证模式
选择 **混合模式（SQL Server 身份验证和 Windows 身份验证）**：

```
├── Windows 身份验证模式
└── 混合模式 ← 推荐选择此项
    ├── sa 登录密码: ______________ (设置一个强密码，记住它)
    └── 确认密码:   ______________
```

#### 指定 SQL Server 管理员
点击 **"添加当前用户"** 将你的 Windows 账户设为管理员。

### 2.3 验证安装

打开 **SQL Server 配置管理器**：

```
Win + R → 输入 SQLServerManager16.msc → 回车
```

确认以下服务状态为 **"正在运行"**：
- SQL Server (MSSQLSERVER)
- SQL Server 浏览器

---

## 3. 安装 SSMS 2022

### 3.1 下载

SSMS 是独立的免费工具：

- 下载页: https://aka.ms/ssmsfullsetup
- 当前推荐版本: **SSMS 20.x**（兼容 SQL Server 2025）

### 3.2 安装

```
1. 运行 SSMS-Setup-CHS.exe
2. 接受许可条款
3. 安装路径默认即可
4. 等待安装完成（约 5-10 分钟）
5. 重启计算机（推荐）
```

### 3.3 首次连接

```
1. 打开 SSMS
2. 服务器类型: 数据库引擎
3. 服务器名称: localhost（或 .\SQLEXPRESS）
4. 身份验证: SQL Server 身份验证
5. 登录名: sa
6. 密码: （你在安装时设置的密码）
7. ☑ 记住密码
8. 点击 "连接"
```

---

## 4. 安装 ODBC Driver 18

Python 通过 `pyodbc` 连接 SQL Server 需要 ODBC Driver。

### 4.1 下载安装

```
下载链接: https://aka.ms/downloadmsodbcsql
选择: ODBC Driver 18 for SQL Server (x64)
```

运行安装程序，全部默认即可。

### 4.2 验证安装

打开 PowerShell 或 CMD：

```powershell
# 查看已安装的 ODBC 驱动
Get-OdbcDriver | Where-Object {$_.Name -like "*SQL Server*"}
```

应看到类似输出：
```
Name: ODBC Driver 18 for SQL Server
Platform: 64-bit
```

---

## 5. 配置 SQL Server

### 5.1 启用 TCP/IP 协议

```
1. 打开 "SQL Server 配置管理器"
2. SQL Server 网络配置 → MSSQLSERVER 的协议
3. 右键 TCP/IP → 启用
4. 右键 TCP/IP → 属性 → IP 地址 选项卡
5. 滚动到底部 "IPAll":
   - TCP 端口: 1433
6. 确定 → 重启 SQL Server 服务
```

### 5.2 配置 Windows 防火墙

```powershell
# 以管理员身份运行 PowerShell
New-NetFirewallRule -DisplayName "SQL Server 1433" `
    -Direction Inbound -Protocol TCP -LocalPort 1433 -Action Allow
```

### 5.3 在 SSMS 中创建登录用户（可选，不使用 sa）

```sql
-- 创建专用登录用户
USE master;
GO

CREATE LOGIN CourseAppUser
    WITH PASSWORD = 'YourStrongPassword123!',
    DEFAULT_DATABASE = CourseManagementDB;
GO

-- 授予数据库权限（初始化后执行）
USE CourseManagementDB;
GO

CREATE USER CourseAppUser FOR LOGIN CourseAppUser;
GO

ALTER ROLE db_datareader ADD MEMBER CourseAppUser;
ALTER ROLE db_datawriter ADD MEMBER CourseAppUser;
ALTER ROLE db_ddladmin   ADD MEMBER CourseAppUser;
GO
```

---

## 6. 初始化数据库

### 6.1 方式一：在 SSMS 中执行 SQL 脚本（推荐）

```
1. 打开 SSMS，连接到服务器
2. Ctrl+O → 打开 backend/config/init_database.sql
3. 检查脚本顶部的数据库名称是否为 CourseManagementDB
4. F5（或点击 "执行"）运行整个脚本
5. 消息窗口应显示: "数据库 CourseManagementDB 初始化完成"
```

### 6.2 方式二：使用 sqlcmd 命令行

```powershell
# 使用 sqlcmd 工具执行
sqlcmd -S localhost -U sa -P "your_password" `
    -i "backend\config\init_database.sql"
```

### 6.3 验证初始化结果

在 SSMS 中执行：

```sql
USE CourseManagementDB;
GO

-- 查看所有表
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME;

-- 查看测试用户
SELECT user_id, role FROM dbo.user_account;

-- 查看测试课程
SELECT course_id, course_name, credit FROM dbo.course;
```

应该看到 8 张表和 6 个测试用户。

---

## 7. 配置项目连接

编辑 `backend/config/config.ini`：

```ini
[database]
driver = mssql
host = localhost
; 默认实例端口 1433，命名实例可能是动态端口
; 命名实例可填写为 localhost\SQLEXPRESS 并注释掉 port
port = 1433
user = sa
password = your_sa_password
database = CourseManagementDB
pool_size = 10
```

### 连接字符串格式说明

| 场景 | config.ini 配置 |
|------|-----------------|
| 默认实例 + sa | `host=localhost` `port=1433` `user=sa` |
| 命名实例 | `host=localhost\SQLEXPRESS` `port=1433` 或注释掉 port |
| 专用用户 | `user=CourseAppUser` `password=YourStrongPassword123!` |
| Windows 认证 | `user=` 留空，需配置 Trusted_Connection（需修改 settings.py） |

---

## 8. 常见问题排查

### Q: 连接失败："无法打开到 SQL Server 的连接"

```
检查清单:
☐ TCP/IP 协议是否已启用？（SQL Server 配置管理器）
☐ SQL Server 服务是否正在运行？（services.msc）
☐ 防火墙是否放行 1433 端口？
☐ 端口号是否正确？（命名实例可能是动态端口）
☐ 是否允许多种身份验证模式？
```

### Q: "Login failed for user 'sa'"

```
1. 使用 Windows 认证登录 SSMS
2. 右键服务器 → 属性 → 安全性
3. 确认选中 "SQL Server 和 Windows 身份验证模式"
4. 展开 安全性 → 登录名 → 右键 sa → 属性
5. 修改密码，取消选中 "强制密码策略"（仅开发环境）
6. 状态 页面 → 确认 "授予" 和 "启用"
```

### Q: ODBC Driver 17/18 not found

```
pip install pyodbc
# 如果报 "Driver not found"，检查:
# 1. ODBC Driver 是否已安装（控制面板 → ODBC 数据源）
# 2. 系统是 64 位还是 32 位（需匹配 Python 位数）
# 3. 可用 pymssql 替代: pip install pymssql
#    并在 settings.py 中将 driver=ODBC+Driver+18+for+SQL+Server
#    替换为 pymssql 连接字符串
```

### Q: Python 端 "TCP Provider: No connection could be made"

```
1. ping localhost — 确保 TCP/IP 正常
2. telnet localhost 1433 — 测试端口可达
3. 检查 SQL Server 配置管理器 → TCP/IP 属性 → IP 地址
   → IP1/IP2 的 "已启用"=是, TCP 端口=1433
```

### Q: 切换回 MySQL

```ini
# config.ini
[database]
driver = mysql
host = localhost
port = 3306
user = root
password = your_mysql_password
database = course_management_db
pool_size = 10
```

然后使用 `backend/config/init_database_mysql.sql`（原 MySQL DDL 脚本）。

---

## 9. 在 SSMS 中管理数据库

### 常用操作

| 操作 | 方法 |
|------|------|
| 查看表数据 | 右键表 → "选择前 1000 行" |
| 编辑表结构 | 右键表 → "设计" |
| 新建查询 | Ctrl+N |
| 执行查询 | F5 |
| 备份数据库 | 右键数据库 → 任务 → 备份 |
| 分离/附加 | 右键数据库 → 任务 → 分离/附加 |
| 查看日志 | 对象资源管理器 → 管理 → SQL Server 日志 |

### 推荐 SSMS 设置

```
工具 → 选项:
├── 文本编辑器 → 所有语言 → 行号 ☑
├── 查询结果 → SQL Server → 以网格显示结果
│   └── 在结果集中包括列标题 ☑
└── 环境 → 启动时 → 打开对象资源管理器
```

---

## 附录: 快速命令参考

```powershell
# 启动/停止 SQL Server 服务
net start MSSQLSERVER
net stop MSSQLSERVER

# 或使用 PowerShell
Start-Service MSSQLSERVER
Stop-Service MSSQLSERVER
Restart-Service MSSQLSERVER

# 查看 SQL Server 错误日志
# 位置: C:\Program Files\Microsoft SQL Server\MSSQL16.MSSQLSERVER\MSSQL\Log\ERRORLOG
```

```sql
-- SSMS 常用诊断查询

-- 查看当前连接
SELECT session_id, login_name, host_name, program_name
FROM sys.dm_exec_sessions WHERE is_user_process = 1;

-- 查看数据库大小
EXEC sp_spaceused;

-- 查看所有用户表
SELECT name, create_date FROM sys.tables ORDER BY name;

-- 查看索引
SELECT t.name AS TableName, i.name AS IndexName
FROM sys.indexes i JOIN sys.tables t ON i.object_id = t.object_id
WHERE i.type > 0 ORDER BY t.name;
```
