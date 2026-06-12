# 开发伙伴协作指南 — 主机端 + 伙伴端双人配置

> 把你的电脑作为服务器，让开发伙伴在局域网内直接访问你的项目。
> 提供一键启停、状态查看、分发打包、伙伴自动配置等全套工具。

---

## 一、主机端操作（在你的电脑上）— 使用 server_control.bat

**你不需要手动敲命令**，双击项目根目录下的 `server_control.bat` 即可。

### 菜单说明

| 选项 | 功能 |
|------|------|
| `[1]` 启动服务器 (仅本机) | `python run.py` → `http://localhost:5000` |
| `[2]` 启动服务器 (公开) | `python run.py --public` → 局域网伙伴可访问 |
| `[3]` 停止服务器 | 自动查找并关闭 python.exe 进程 |
| `[4]` 查看服务器状态 | 显示运行状态、防火墙规则、数据库、本机 IP |
| `[5]` 重建前端+启动 | `npm run build` 后启动公开模式 |
| `[6]` 伙伴连接信息查看 | 显示伙伴需要的完整连接参数 |
| `[7]` 打包分发给伙伴 | 自动打包项目（排除无关文件） |
| `[0]` 退出 | 关闭控制面板 |

### 首次运行前需要做的事（仅一次）

**1. 开放防火墙**

以**管理员身份**运行一次 PowerShell：

```powershell
New-NetFirewallRule -DisplayName "EduMgmt Flask 5000" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

**2. 设置 JWT 固定密钥**（避免重启后全部用户掉线）

编辑 `backend\config\config.ini`，在 `[web]` 段填一个固定值：

```ini
[web]
jwt_secret = my-very-secret-key-change-this
```

### 日常使用流程

```
1. 双击 server_control.bat
2. 输入 2（启动公开模式）
3. 服务器启动，终端保持运行
4. 伙伴即可通过 http://你的IP:5000 访问
5. 要停止时，关闭终端窗口，或重新打开 server_control.bat 选 [3]
```

---

## 二、伙伴端操作（开发伙伴的电脑上）— 使用 partner_connect.bat

### 方式 A：浏览器直接使用（零安装）

主机启动后，伙伴浏览器打开 `http://主机IP:5000` 即可。默认账号 `admin / 123456`。

### 方式 B：前端开发模式（推荐，可改代码）

1. 从 GitHub 拉取项目，或从主机接收分发包 `edu-mgmt-dist.zip`
2. 解压后，双击项目根目录下的 **`partner_connect.bat`**
3. 输入主机的局域网 IP 地址
4. 脚本自动配置 `VITE_API_TARGET`，可选立即启动 `npm run dev`
5. 浏览器打开 `http://localhost:5173`，所有 API 代理到主机

**partner_connect.bat 做了什么：**
- 设置 `frontend/.env.local` 中的 `VITE_API_TARGET` 指向主机
- 自动 ping 测试主机连通性
- 显示连接信息摘要
- 可选一键启动前端开发服务器

### 方式 C：独立运行全部

按 `SQL_SERVER_SETUP_GUIDE.md` 在伙伴电脑安装 SQL Server 并初始化数据库，完全独立运行。

---

## 三、工具文件说明

| 文件 | 用途 | 谁用 |
|------|------|------|
| `server_control.bat` | 服务器控制面板（启停/状态/分发） | 主机（你） |
| `partner_connect.bat` | 伙伴连接配置工具（自动代理设置） | 开发伙伴 |
| `run.py --public` | Flask 公开模式入口 | 主机 |
| `frontend/.env.local` | Vite 代理目标（partner_connect.bat 自动生成） | 伙伴 |
| `SETUP_PARTNER.md` | 本文档 | 双方 |

---

## 四、快速排查

| 问题 | 检查 |
|------|------|
| 伙伴连不上 | 主机 `server_control.bat` → `[4]` 查看状态 |
| 伙伴 ping 不通 | 两台电脑是否在同一局域网/同一网段 |
| 伙伴能 ping 但网页打不开 | 主机防火墙是否放行 5000 端口 |
| 页面打开但 API 报错 | 主机检查 `config.ini` 数据库密码是否正确 |
| 登录后频繁掉线 | 在 `config.ini` 中配置固定 `jwt_secret` |
| 外网访问（不在同一局域网） | 主机安装 [ngrok](https://ngrok.com/): `ngrok http 5000` |
