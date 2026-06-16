# 教务管理系统 — 腾讯云轻量应用服务器迁移指南

> 将后端 + 数据库部署到腾讯云轻量服务器，前端可部署到任何静态托管或继续本地开发。

---

## 一、架构概览

```
┌─────────────────────┐     HTTPS/HTTP      ┌──────────────────────────┐
│   用户浏览器         │ ←─────────────────→ │  腾讯云轻量服务器         │
│   (Vue 前端 SPA)     │                     │                          │
│                      │                     │  Nginx (反向代理)         │
│   前端可部署到:       │                     │   ├─ /api/* → Flask:5000  │
│   - 同一服务器的      │                     │   ├─ /     → Vue dist    │
│     Nginx 静态文件    │                     │   └─ SSL (Let's Encrypt) │
│   - GitHub Pages      │                     │                          │
│   - 任何 CDN          │                     │  Flask (Waitress)        │
│                      │                     │   └─ :5000               │
│                      │                     │                          │
│                      │                     │  MySQL 8.0               │
│                      │                     │   └─ :3306               │
└─────────────────────┘                     └──────────────────────────┘
```

---

## 二、准备工作

### 2.1 购买腾讯云轻量应用服务器

1. 打开 https://cloud.tencent.com/product/lighthouse
2. 选择配置：
   - **系统镜像**: Windows Server 2022 数据中心版
   - **CPU**: 2核及以上
   - **内存**: 2GB 及以上（MySQL 建议 4GB）
   - **带宽**: 3Mbps 及以上
3. 购买后获取：**公网 IP**、**Administrator 密码**

### 2.2 本地准备

1. 确保本地项目最新版本：
```powershell
cd "D:\C++\VisualStudio study\Software Engineering"
git pull origin main
```

2. 打包项目后端（排除前端 node_modules 和数据库密码）：
```
双击 server_control.bat → [7] 打包分发给伙伴
```
或手动打包：
```powershell
powershell -Command "Compress-Archive -Path 'backend','requirements.txt','requirements_web.txt','run.py','run_prod.py','README.md','API.md' -DestinationPath 'edu-mgmt-backend.zip' -Force"
```

3. 准备好 `backend\config\init_database_mysql.sql` 脚本文件

---

## 三、服务器端操作（远程桌面连接）

### 3.1 登录服务器

1. Win + R → `mstsc` → 输入服务器公网 IP
2. 用户名: `Administrator`
3. 密码: 购买时设置的密码

### 3.2 安装 Python 3.11+

```powershell
# 下载 Python
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile "python-installer.exe"

# 安装（勾选 "Add Python to PATH"）
.\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
```

### 3.3 安装 MySQL 8.0

```powershell
# 下载 MySQL 8.0 Installer
Invoke-WebRequest -Uri "https://dev.mysql.com/get/Downloads/MySQLInstaller/mysql-installer-community-8.0.36.0.msi" -OutFile "mysql-installer.msi"

# 安装（静默模式）
msiexec /i mysql-installer.msi /quiet
```

安装完成后：
1. 运行 MySQL Installer → 选择 "Developer Default" 或 "Server only"
2. 设置 **root 密码**
3. 确保 MySQL 服务 (MySQL80) 已启动

### 3.4 初始化数据库

```powershell
cd C:\edu-mgmt
mysql -u root -p < backend\config\init_database_mysql.sql
```

验证：
```powershell
mysql -u root -p -e "USE course_management_db; SELECT * FROM user_account;"
```
应能看到 admin/T001/STU001 等账号。

### 3.5 配置项目连接

编辑 `C:\edu-mgmt\backend\config\config.ini.example`，重命名为 `config.ini`：

```ini
[database]
driver = mysql
host = localhost
port = 3306
user = root
password = YOUR_MYSQL_PASSWORD
database = course_management_db
pool_size = 10

[system]
log_level = INFO
log_dir = logs
default_total_weeks = 20
session_timeout = 3600
max_login_attempts = 5

[web]
jwt_secret = my-production-secret-key-change-this-to-random-string
jwt_expiration_hours = 24

[enrollment]
is_open = true
open_time = 2026-09-01 08:00:00
close_time = 2026-12-31 23:59:59
```

**关键**: 必须设置固定的 `jwt_secret`（随机字符串），否则服务器重启后所有用户掉线！

### 3.6 安装 Python 依赖

```powershell
cd C:\edu-mgmt
pip install -r requirements.txt
pip install -r requirements_web.txt
pip install waitress
```

### 3.7 启动后端（测试）

```powershell
cd C:\edu-mgmt
python run_prod.py
```

应该在服务器上看到：
```
  EduMgmt System v3.0 - Production Server
  Starting waitress on http://0.0.0.0:5000
```

在服务器浏览器打开 `http://localhost:5000`，确认 API 正常。

### 3.8 开放腾讯云防火墙

1. 登录腾讯云控制台 → 轻量应用服务器 → 你的实例
2. **防火墙** → 添加规则：
   - 端口: `5000`，协议: `TCP`，策略: 允许，备注: "Flask API"
   - 端口: `80`，协议: `TCP`，策略: 允许，备注: "Nginx HTTP"
   - 端口: `443`，协议: `TCP`，策略: 允许，备注: "Nginx HTTPS"

### 3.9 安装 Nginx 作为反向代理

```powershell
# 下载 Nginx for Windows
Invoke-WebRequest -Uri "https://nginx.org/download/nginx-1.26.0.zip" -OutFile "nginx.zip"
Expand-Archive nginx.zip -DestinationPath C:\
```

编辑 `C:\nginx-1.26.0\conf\nginx.conf`：

```nginx
worker_processes 1;

events {
    worker_connections 1024;
}

http {
    include mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;

    server {
        listen 80;
        server_name _;

        charset utf-8;
        client_max_body_size 50m;

        root C:/edu-mgmt/frontend/dist;
        index index.html;

        location /api/ {
            proxy_pass http://127.0.0.1:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_read_timeout 60s;
        }

        location / {
            try_files $uri $uri/ /index.html;
        }
    }
}
```

### 3.10 构建前端（指向服务器）

在**本地**构建前端，然后上传到服务器：

```powershell
# 本地执行
cd frontend
$env:VITE_API_TARGET="http://你的服务器公网IP:5000"
npm run build

# 将 dist 目录上传到服务器的 C:\edu-mgmt\frontend\dist\
```

### 3.11 设置 Nginx + Flask 开机自启

创建 `C:\edu-mgmt\start_services.bat`：

```batch
@echo off
start "Nginx" C:\nginx-1.26.0\nginx.exe
start "Flask" /MIN python C:\edu-mgmt\run_prod.py
```

Win + R → `taskschd.msc` → 创建基本任务：
- 触发器: **系统启动时**
- 操作: **启动程序** → `C:\edu-mgmt\start_services.bat`

---

## 四、前端部署选项

### 选项 A：前端部署在服务器上（简单）

前端和后端在同一台服务器，Nginx 同时处理。用户访问 `http://服务器IP` 即可。

### 选项 B：前端部署到 GitHub Pages（免费）

```powershell
$env:VITE_API_TARGET="http://你的服务器IP:5000"
npm run build
# 将 dist/ 推送到 gh-pages 分支
```

### 选项 C：本地开发 + 远程后端

```powershell
# 本地前端连接远程后端
$env:VITE_API_TARGET="http://你的服务器IP:5000"
npm run dev
```

---

## 五、验证部署

1. **API 测试**：浏览器打开 `http://服务器IP:5000/api/auth/login`（POST）
2. **前端测试**：浏览器打开 `http://服务器IP` → 登录 admin/123456
3. **功能测试**：选课、成绩录入、审核流程

---

## 六、安全加固建议

1. **修改默认密码**：admin / 123456 → 立即修改
2. **Windows 防火墙**：仅开放 80/443（3306 仅限本地连接）
3. **MySQL**：创建专用用户替代 root
4. **config.ini**：jwt_secret 使用 32 位以上随机字符串
5. **Nginx**：配置 HTTPS（Let's Encrypt + win-acme）
6. **定期备份**：`mysqldump -u root -p course_management_db > backup.sql`

---

## 七、常见问题

| 问题 | 解决 |
|------|------|
| 5000 端口访问不了 | 检查腾讯云防火墙 + Windows 防火墙 |
| Flask 启动报数据库连接错误 | 检查 config.ini 密码，确认 MySQL 服务正在运行 |
| 登录后立即掉线 | config.ini 中 jwt_secret 未设置或为空 |
| Nginx 404 错误 | 确认 nginx.conf 中 root 路径正确 |
| 跨域 CORS 错误 | app_factory.py 已配置 `origins: "*"`，无需额外设置 |
| MySQL 连接超时 | 检查 MySQL 服务是否启动: `sc query MySQL80` |
