# 高校教务管理系统 - 开发伙伴协作指南

> 把你的电脑作为共享开发服务器，伙伴可通过局域网、IPv6 直连、端口映射等方式访问。
> 提供一键启停、状态查看、分发打包、伙伴自动配置等全套工具。

---

## 一、主机端操作（你的电脑）— server_control.bat

**无需手动敲命令**，双击项目根目录下的 `server_control.bat` 即可。

### 菜单说明

| 选项 | 功能 |
|------|------|
| `[1]` 启动服务器 (仅本机) | `python run.py` → `http://localhost:5000` |
| `[2]` 启动服务器 (局域网公开) | `python run.py --public` → 局域网/校园网伙伴可访问 |
| `[3]` 停止服务器 | 自动关闭所有 python.exe、ngrok.exe、frpc.exe 进程 |
| `[4]` 查看服务器状态 | 运行状态、公网IP、防火墙、数据库、LAN/IPv6 |
| `[5]` 重建前端并启动 | `npm run build` 后启动公开模式 |
| `[6]` 伙伴连接信息 | 显示伙伴需要的完整连接参数（含公网IP和IPv6） |
| `[7]` 打包分发给伙伴 | 自动打包项目（排除 node_modules、.git 等），生成 zip |
| `[8]` 公网访问设置指南 | 六种方案详解（校园网直连/IPv6/端口映射/frp/ZeroTier/Cloudflare） |
| `[9]` 启动外网可访问服务器 | 自动配置防火墙 + 启动 Flask 公开模式 |
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
2. 同一局域网/校园网用 [2]；需要公网访问用 [9]
3. 服务器启动后保持终端窗口运行
4. 伙伴通过你提供的地址访问
5. 停止时关闭终端窗口，或重新打开 server_control.bat 选 [3]
```

---

### 外网访问方案（选项 8 — 详细指南）

按推荐优先级排列：

#### 方案一：同一校园网/局域网（最简单）

如果你和伙伴在同一个校园网网段内，直接用 `[2]` 局域网模式即可。
URL: `http://你的IP:5000`

#### 方案二：IPv6 直连（强烈推荐，国内校园网首选）

中国高校校园网普遍已部署 IPv6，每台设备都会分配独立的**公网 IPv6 地址**，无需端口映射，无需任何第三方工具！

1. 在 CMD 中运行 `ipconfig`，找到不以 `fe80` 开头、不以 `::1` 开头的 IPv6 地址
2. 在防火墙中放行 IPv6 的 5000 端口
3. 伙伴访问: `http://[你的IPv6地址]:5000`（必须用方括号包裹）
4. 服务端用 `[9]` 启动，伙伴端 `partner_connect.bat` 选 `[2] IPv6 模式`

**注意：** Windows 默认开启 IPv6 隐私扩展，地址会定期变化。如需固定地址，可在网卡设置中关闭"随机化标识符"。

#### 方案三：路由器端口映射（家庭宽带有公网 IPv4）

前提是你的宽带分配了公网 IPv4 地址（移动/联通/电信部分用户有）。

1. 查询公网 IP：打开 `ip.sb` 或 `ifconfig.me`
2. 登录路由器管理页面（通常是 `http://192.168.1.1`）
3. 找到"端口转发"/"虚拟服务器"功能
4. 添加规则：外部端口 5000 → 内部 IP `你的局域网IP` → 内部端口 5000 → TCP
5. 保存后，外网访问: `http://你的公网IP:5000`

常见路由器默认登录：

| 品牌 | 默认地址 | 默认账号/密码 |
|------|---------|--------------|
| TP-Link | 192.168.1.1 | admin/admin |
| 小米 | 192.168.31.1 | 见路由器底部 |
| 华为 | 192.168.3.1 | admin/admin |
| 华硕 | 192.168.50.1 | admin/admin |

#### 方案四：frp 自建内网穿透（有云服务器）

如果你有一台有公网 IP 的云服务器（阿里云/腾讯云学生价约 10 元/月），可以自建 frp。

服务端（云服务器）创建 `frps.ini`：
```ini
[common]
bind_port = 7000
vhost_http_port = 8080
```

客户端（你的电脑）创建 `frpc.ini`：
```ini
[common]
server_addr = 你的云服务器IP
server_port = 7000
[web]
type = http
local_port = 5000
custom_domains = 你的域名或服务器IP
```

下载地址: https://github.com/fatedier/frp/releases

#### 方案五：ZeroTier 虚拟组网

创建虚拟局域网，你和伙伴安装客户端后即可像在同一局域网互相访问。
ZeroTier 免费支持 25 个设备，无需公网 IP。
网址: https://www.zerotier.com/

#### 方案六：Cloudflare Tunnel（免费，需域名）

完全免费，无限流量。需要一个域名（可注册免费域名）。
网址: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/

**推荐优先级：同一局域网 > IPv6 直连 > 端口映射 > ZeroTier > frp > Cloudflare Tunnel**

---

### 伙伴连接流程

1. 主机启动服务器（`[2]` 或 `[9]`）
2. 主机按 `[6]` 查看完整连接信息（含 LAN IP、公网 IP、IPv6 地址）
3. 主机将地址分享给伙伴
4. 伙伴在浏览器打开或通过 `partner_connect.bat` 配置前端开发环境

---

## 二、伙伴端操作（开发伙伴的电脑）— partner_connect.bat

### 方式 A：纯浏览器使用（零安装）

直接在浏览器打开主机给的地址。默认账号 `admin / 123456`。

### 方式 B：前端开发模式（推荐，可修改前端代码）

1. 从 GitHub 拉取代码，或接收主机打包的 `edu-mgmt-dist.zip`
2. 解压后双击项目根目录下的 **`partner_connect.bat`**
3. 选择连接方式：
   - `[1]` 局域网/同一校园网
   - `[2]` **IPv6 直连（校园网推荐）**
   - `[3]` 公网 IP / 域名
4. 输入主机提供的地址
5. 脚本自动配置 `VITE_API_TARGET` 并检测连通性
6. 可选一键启动 `npm run dev`
7. 打开 `http://localhost:5173`，所有 API 请求自动代理到主机

**partner_connect.bat 功能：**
- 自动创建 `frontend/.env.local`，写入 `VITE_API_TARGET` 指向主机
- IPv6 地址自动添加方括号和端口号
- 局域网模式自动 ping 测试连通性
- 显示完整连接信息摘要
- 一键启动前端开发服务器

### 方式 C：完全独立部署

按照 `SQL_SERVER_SETUP_GUIDE.md` 在伙伴电脑上安装 SQL Server 并初始化数据库，完全独立运行。

---

## 三、工具文件清单

| 文件 | 用途 | 使用者 |
|------|------|--------|
| `server_control.bat` | 服务器控制面板（启停/状态/分发/公网指南） | 主机（你） |
| `partner_connect.bat` | 伙伴连接配置工具（LAN/IPv6/公网三种模式） | 开发伙伴 |
| `run.py --public` | Flask 对外监听模式（绑定 0.0.0.0） | 主机 |
| `frontend/.env.local` | Vite 代理目标（partner_connect.bat 自动生成） | 伙伴 |
| `SETUP_PARTNER.md` | 本文档 | 双方 |

---

## 四、常见问题排查

| 问题 | 排查方法 |
|------|---------|
| 伙伴连不上 | 主机 `server_control.bat` → `[4]` 查看状态 |
| 伙伴 ping 不通主机 | 两台电脑是否在同一局域网/同一网段？是否开了防火墙？ |
| 能 ping 通但网页打不开 | 主机防火墙是否放行 5000 端口？Flask 是否以 `--public` 启动？ |
| 页面打开但 API 请求失败 | 主机检查 `config.ini` 数据库密码，打开浏览器控制台看具体报错 |
| 操作过程中频繁掉线到登录页 | 在 `config.ini` 的 `[web]` 段配置固定 `jwt_secret` |
| IPv6 地址连不上 | 确认用的是公网 IPv6（不是 fe80 开头的本地地址），双方防火墙都放行 5000 |
| IPv6 地址过几天就变了 | Windows 隐私扩展会自动更换，可在网卡属性中关闭 |
| 端口映射后外网仍无法访问 | 检查是否运营商做了 NAT（大内网），部分地区宽带无公网 IPv4 |
| 校园网没有公网 IPv4 | 正常现象，尝试 IPv6 直连（方案二）或 ZeroTier（方案五） |
