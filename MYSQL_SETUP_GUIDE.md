# MySQL 8.0 下载 → 安装 → 嵌入项目全流程指引

> 本指引将 MySQL 数据库嵌入到项目目录中，实现免安装版（Portable）部署，
> 即项目目录自包含数据库，拷贝到任何电脑上都能直接运行。

---

## 方案选择

| 方案 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| **A: 标准安装** | 个人开发机 | 简单快速，开机自启 | 需要管理员权限，绑定系统 |
| **B: 嵌入式部署** | 团队协作 / 分发 | 项目自包含，拷贝即用 | 需手动启停，稍复杂 |

**推荐方案 B**：把 MySQL 装在项目目录下，伙伴拿到项目后无需额外配置数据库。

---

## 方案 A：标准安装 MySQL（最快上手）

### 1. 下载 MySQL 8.0

打开 https://dev.mysql.com/downloads/installer/ ，下载 `mysql-installer-community-8.0.xx.msi`（约 350MB）。

### 2. 安装

1. 运行 `.msi` 安装程序
2. 选择 **Server only**（只需要数据库服务）
3. 一路 Next，在 **Accounts and Roles** 页面设置 **root 密码**（记下来！）
4. 确保 **MySQL80** 服务设为自动启动
5. 完成安装

### 3. 验证

打开命令提示符：

```powershell
mysql -u root -p
```

输入密码后进入 MySQL 命令行即表示成功。

### 4. 初始化项目数据库

```powershell
cd "D:\C++\VisualStudio study\Software Engineering"
mysql -u root -p < backend\config\init_database_mysql.sql
```

输入 root 密码，脚本会自动创建 `course_management_db` 数据库和全部 11 张表，并插入测试数据。

### 5. 配置项目连接

编辑 `backend\config\config.ini`，确保 `[database]` 段如下：

```ini
[database]
driver = mysql
host = localhost
port = 3306
user = root
password = 你设置的root密码
database = course_management_db
pool_size = 10
```

---

## 方案 B：MySQL 嵌入项目目录（推荐，免安装分发）

### 1. 下载 MySQL 8.0 ZIP Archive（免安装版）

官方下载页：https://dev.mysql.com/downloads/mysql/

选择 **Windows (x86, 64-bit), ZIP Archive**（约 200MB），下载到项目根目录。

或者直接命令行（PowerShell）：

```powershell
cd "D:\C++\VisualStudio study\Software Engineering"

# 下载 MySQL 8.0.36 ZIP 免安装版
Invoke-WebRequest -Uri "https://dev.mysql.com/get/Downloads/MySQL-8.0/mysql-8.0.36-winx64.zip" -OutFile "mysql.zip"

# 解压
Expand-Archive mysql.zip -DestinationPath .
Rename-Item mysql-8.0.36-winx64 mysql-portable
Remove-Item mysql.zip
```

最终目录结构：
```
Software Engineering/
├── mysql-portable/          ← MySQL 免安装版
│   ├── bin/
│   │   ├── mysqld.exe
│   │   └── mysql.exe
│   ├── data/                ← 数据库数据文件（初始化后生成）
│   └── my.ini               ← 配置文件
├── backend/
├── frontend/
├── run.py
└── ...
```

### 2. 创建 MySQL 配置文件

在 `mysql-portable/` 目录下创建 `my.ini`：

```ini
[mysqld]
# 基于项目目录的相对路径
basedir=D:/C++/VisualStudio study/Software Engineering/mysql-portable
datadir=D:/C++/VisualStudio study/Software Engineering/mysql-portable/data

# 端口（与 config.ini 一致）
port=3306

# 字符集
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci

# 默认存储引擎
default-storage-engine=INNODB

# 连接数
max_connections=50

# 允许从 localhost 之外的地址连接（如果需要局域网访问）
# bind-address=0.0.0.0

# 认证插件（兼容旧客户端）
default_authentication_plugin=mysql_native_password

[client]
port=3306
default-character-set=utf8mb4

[mysql]
default-character-set=utf8mb4
```

> **重要**：`basedir` 和 `datadir` 请根据你的实际项目路径修改！

### 3. 初始化 MySQL 数据目录

以**管理员身份**打开 PowerShell：

```powershell
cd "D:\C++\VisualStudio study\Software Engineering\mysql-portable"

# 初始化数据目录（生成 root 随机密码）
.\bin\mysqld.exe --defaults-file="%CD%\my.ini" --initialize-insecure --console
```

> `--initialize-insecure` 表示 root 无初始密码。查看控制台输出确认初始化成功。

### 4. 启动 MySQL

```powershell
cd "D:\C++\VisualStudio study\Software Engineering\mysql-portable"

# 前台启动（调试用，Ctrl+C 停止）
.\bin\mysqld.exe --defaults-file="%CD%\my.ini" --console

# 后台启动（安装为 Windows 服务）
.\bin\mysqld.exe --install MySQL-EduMgmt --defaults-file="%CD%\my.ini"
net start MySQL-EduMgmt
```

### 5. 设置 root 密码

首次启动后，打开**另一个**命令提示符：

```powershell
cd "D:\C++\VisualStudio study\Software Engineering\mysql-portable\bin"

# 无密码登录（--initialize-insecure 模式）
.\mysql.exe -u root

# 在 MySQL 命令行中设置密码
ALTER USER 'root'@'localhost' IDENTIFIED BY 'Cairenbin2005';
FLUSH PRIVILEGES;
EXIT;
```

### 6. 初始化项目数据库

```powershell
cd "D:\C++\VisualStudio study\Software Engineering"

# 用项目提供的 DDL 脚本初始化
.\mysql-portable\bin\mysql.exe -u root -pCairenbin2005 < backend\config\init_database_mysql.sql
```

验证：
```powershell
.\mysql-portable\bin\mysql.exe -u root -pCairenbin2005 -e "USE course_management_db; SHOW TABLES;"
```

应输出 11 张表。

### 7. 配置项目连接

编辑 `backend\config\config.ini`：

```ini
[database]
driver = mysql
host = localhost
port = 3306
user = root
password = Cairenbin2005
database = course_management_db
pool_size = 10
```

### 8. 启动项目

```powershell
# 确保 MySQL 已启动
net start MySQL-EduMgmt

# 启动 Flask
python run.py
```

---

## 可选：配置为 Windows 服务（开机自启）

把嵌入式 MySQL 注册为 Windows 服务：

```powershell
cd "D:\C++\VisualStudio study\Software Engineering\mysql-portable"

# 安装服务
.\bin\mysqld.exe --install MySQL-EduMgmt --defaults-file="%CD%\my.ini"

# 启动服务
net start MySQL-EduMgmt

# 设为自动启动
sc config MySQL-EduMgmt start=auto
```

如果不想要服务了，卸载：
```powershell
net stop MySQL-EduMgmt
.\bin\mysqld.exe --remove MySQL-EduMgmt
```

---

## 日常操作

### 启停 MySQL

```powershell
# 启动
net start MySQL-EduMgmt

# 停止
net stop MySQL-EduMgmt
```

如果不安装服务，前台启动：
```powershell
cd "D:\C++\VisualStudio study\Software Engineering\mysql-portable"
.\bin\mysqld.exe --defaults-file="%CD%\my.ini" --console
```

### 数据备份

```powershell
# 导出
.\mysql-portable\bin\mysqldump.exe -u root -pCairenbin2005 course_management_db > backup_%date:~0,10%.sql

# 导入恢复
.\mysql-portable\bin\mysql.exe -u root -pCairenbin2005 course_management_db < backup_xxx.sql
```

### 完全重置数据库

```powershell
.\mysql-portable\bin\mysql.exe -u root -pCairenbin2005 -e "DROP DATABASE IF EXISTS course_management_db;"
.\mysql-portable\bin\mysql.exe -u root -pCairenbin2005 < backend\config\init_database_mysql.sql
```

---

## 伙伴分发清单

当你把整个项目目录拷贝给伙伴时，伙伴只需要：

1. **安装 Python 3.11+** 和 **Node.js 18+**（如果要用前端热重载）
2. **修改 `mysql-portable\my.ini`** 中的 `basedir` 和 `datadir` 为自己的路径
3. **安装 MySQL 服务**（见上方 "配置为 Windows 服务"）
4. **启动 MySQL + Flask** 即可

```powershell
# 伙伴拿到项目后执行
cd "D:\...\Software Engineering\mysql-portable"
.\bin\mysqld.exe --install MySQL-EduMgmt --defaults-file="%CD%\my.ini"
net start MySQL-EduMgmt

cd ..
pip install -r requirements.txt
pip install Flask flask-cors PyJWT marshmallow
python run.py
```

---

## 常见问题

| 问题 | 解决 |
|------|------|
| `mysqld.exe` 启动闪退 | 检查 `my.ini` 路径是否正确，`basedir` 和 `datadir` 必须用正斜杠 `/` |
| `Access denied for user 'root'` | 用 `--initialize-insecure` 重新初始化，或重置密码 |
| 端口 3306 被占用 | 修改 `my.ini` 和 `config.ini` 中的端口号 |
| `Can't connect to MySQL server` | 确认 MySQL 服务已启动：`net start MySQL-EduMgmt` |
| 中文乱码 | 确认 `my.ini` 中 `character-set-server=utf8mb4` |
| 伙伴机无法连接 MySQL | 修改 `my.ini` 添加 `bind-address=0.0.0.0`，并开放防火墙 3306 端口 |

---

## 驱动备选（如果需要用 SQL Server）

项目仍保留 SQL Server 支持，如需切换：

1. 安装 ODBC Driver 18 for SQL Server
2. 修改 `config.ini` 中 `driver = mssql`
3. 执行 `backend\config\init_database.sql`（SQL Server 版 DDL）
4. 安装 pyodbc：`pip install pyodbc`
