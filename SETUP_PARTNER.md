# 高校教务管理系统 - 开发伙伴协作指南

> 把你的电脑作为共享开发服务器，伙伴可通过局域网或 ngrok 外网穿透访问。
> 提供一键启停、状态查看、分发打包、伙伴自动配置等全套工具。

---

## 一、主机端操作（你的电脑）— server_control.bat

**无需手动敲命令**，双击项目根目录下的 `server_control.bat` 即可。

### 菜单说明

| 选项 | 功能 |
|------|------|
| `[1]` 启动服务器 (仅本机) | `python run.py` → `http://localhost:5000` |
| `[2]` 启动服务器 (局域网公开) | `python run.py --public` → 局域网伙伴可访问 |
| `[3]` 停止服务器 | 自动关闭所有 python.exe 和 ngrok.exe 进程 |
| `[4]` 查看服务器状态 | 运行状态、防火墙规则、数据库状态、本机 IP |
| `[5]` 重建前端并启动 | `npm run build` 后启动公开模式 |
| `[6]` 伙伴连接信息 | 显示伙伴需要的完整连接参数 |
| `[7]` 打包分发给伙伴 | 自动打包项目（排除 node_modules、.git 等），生成 zip |
| `[8]` 安装 ngrok | 安装/配置 ngrok 外网穿透工具 |
| `[9]` 启动 ngrok 隧道 | Flask + ngrok 同时启动，互联网任意位置可访问 |
| `[0]` 退出 | 关闭控制面板 |

### 首次运行前的准备工作（仅需一次）

**1. 开放 Windows 防火墙**

以**管理员身份**运行 PowerShell：

```powershell
New-NetFirewallRule -DisplayName "EduMgmt Flask 5000" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

**2. 设置 JWT 固定密钥**（避免服务器重启后所有用户自动退出登录）

编辑 `backend\config\config.ini`，在 `[web]` 段填写一个固定值：

```ini
[web]
jwt_secret = my-secret-key-change-this-to-something-unique
jwt_expiration_hours = 24
```

如果不设置此项，每次重启 Flask 后 JWT 密钥随机变化，所有已登录用户会掉线回到登录页。

---

### 日常使用流程

```
1. 双击 server_control.bat
2. 局域网用 [2]，外网用 [9](ngrok)
3. 服务器启动后保持终端窗口运行
4. 伙伴通过 http://你的IP:5000 或 ngrok 公网地址访问
5. 停止时关闭终端窗口，或重新打开 server_control.bat 选 [3]
```

---

### 外网访问指南（选项 9 — ngrok 隧道）

当开发伙伴和你**不在同一个局域网**时，使用 ngrok 建立公网隧道：

1. 在 server_control.bat 中按 `[8]` 安装 ngrok
2. 浏览器打开 https://dashboard.ngrok.com/signup 注册免费账号
3. 登录后到 https://dashboard.ngrok.com/get-started/your-authtoken 复制你的 authtoken
4. 在命令行中运行：`ngrok config add-authtoken 你的token`
5. 配置完成后按 `[9]` 启动 — Flask 和 ngrok 同时运行
6. 浏览器打开 http://127.0.0.1:4040 查看 ngrok 分配的公网地址
7. 把该地址（形如 `https://xxxx.ngrok-free.app`）发给伙伴即可

**ngrok 免费版限制：**
- 同时只能开 1 条隧道
- 每月流量约 1 GB
- 每次重启 ngrok 地址会变化（付费版可固定域名）
- 闲置约 2 小时后会话可能断开

---

### 伙伴连接流程

1. 主机启动服务器（`[2]` 或 `[9]`）
2. 主机按 `[6]` 查看连接信息
3. **局域网**：主机分享 `http://192.168.x.x:5000` 地址
4. **外网**：主机分享 ngrok 公网地址（从 http://127.0.0.1:4040 查看）
5. 伙伴在浏览器打开或通过 `partner_connect.bat` 配置前端开发环境

---

## 二、伙伴端操作（开发伙伴的电脑）— partner_connect.bat

### 方式 A：纯浏览器使用（零安装）

直接在浏览器打开主机给的地址。默认账号 `admin / 123456`。

### 方式 B：前端开发模式（推荐，可修改前端代码）

1. 从 GitHub 拉取代码，或接收主机打包的 `edu-mgmt-dist.zip`
2. 解压后双击项目根目录下的 **`partner_connect.bat`**
3. 选择 `[1]` 局域网 或 `[2]` 外网
4. 输入主机的局域网 IP 或 ngrok 公网地址
5. 脚本自动配置 `VITE_API_TARGET` 并检测连通性
6. 可选一键启动 `npm run dev`
7. 打开 `http://localhost:5173`，所有 API 请求自动代理到主机

**partner_connect.bat 功能：**
- 自动创建 `frontend/.env.local`，写入 `VITE_API_TARGET` 指向主机
- ngrok 地址自动识别为 https
- 局域网模式自动 ping 测试连通性
- 外网模式用 curl 测试 API 可达性
- 显示完整连接信息摘要
- 一键启动前端开发服务器

### 方式 C：完全独立部署

按照 `SQL_SERVER_SETUP_GUIDE.md` 在伙伴电脑上安装 SQL Server 并初始化数据库，完全独立运行。

---

## 三、工具文件清单

| 文件 | 用途 | 使用者 |
|------|------|--------|
| `server_control.bat` | 服务器控制面板（启停/状态/分发/ngrok） | 主机（你） |
| `partner_connect.bat` | 伙伴连接配置工具（自动代理设置+连通性测试） | 开发伙伴 |
| `run.py --public` | Flask 对外监听模式（绑定 0.0.0.0） | 主机 |
| `frontend/.env.local` | Vite 代理目标（partner_connect.bat 自动生成） | 伙伴 |
| `SETUP_PARTNER.md` | 本文档 | 双方 |

---

## 四、常见问题排查

| 问题 | 排查方法 |
|------|---------|
| 伙伴连不上 | 主机 `server_control.bat` → `[4]` 查看服务器状态 |
| 伙伴 ping 不通主机 | 两台电脑是否在同一局域网/同一网段？ |
| 能 ping 通但网页打不开 | 主机防火墙是否放行 5000 端口？ |
| 页面打开但 API 请求失败 | 主机检查 `config.ini` 数据库密码是否正确 |
| 操作过程中频繁掉线到登录页 | 在 `config.ini` 的 `[web]` 段配置固定 `jwt_secret` |
| 需要外网访问（不在同一网络） | 主机用 `[8]` 安装 ngrok，`[9]` 启动隧道 |
| ngrok 报 "authentication failed" | 先运行 `ngrok config add-authtoken 你的token` |
| ngrok 报 "address already in use" | 已有 ngrok 实例在运行，用 `[3]` 关闭后重试 |
| 公网地址每次启动都变化 | ngrok 免费版限制，付费版支持固定域名 |
| 公网访问 ngrok 页面显示 "visit this site" | 需要在请求头添加 `ngrok-skip-browser-warning`，或用付费版 |
