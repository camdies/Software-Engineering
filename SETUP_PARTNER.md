# 开发伙伴协作指南

> 把你的项目分发给伙伴，伙伴解压后双击 `start_all.bat` 即可本地运行。
> 也支持浏览器直连、前端开发代理等模式。

## 一、方式 A：完整项目分发（推荐，伙伴零配置）

伙伴收到 `edu-mgmt-dist.zip` 后，**只需两步**：

1. **安装 Python 3.11+**（一次性）  
   https://www.python.org/downloads/  
   安装时勾选 **"Add Python to PATH"**

2. **双击 `start_all.bat`**  
   浏览器打开 `http://localhost:5000`

`start_all.bat` 自动完成：
- 动态生成正确的 MySQL `my.ini` 路径
- 前台模式启动 MySQL（不需要管理员权限）
- 安装 Python 依赖（首次）
- 启动 Flask 服务器

### 分发打包（主机操作）

双击 `server_control.bat` → `[7] Package for partner`

打包内容：
- 完整项目源码（backend + frontend + 文档）
- **mysql-portable 便携数据库**（含预置数据，开箱即用）
- `start_all.bat` 一键启动脚本

排除内容：`node_modules`、`.git`、`config.ini`（密码安全）

---

## 二、方式 B：浏览器直连（伙伴零安装）

主机运行服务器后，伙伴直接用浏览器打开地址即可。默认账号 `admin / 123456`。

1. 主机双击 `server_control.bat`，选择：
   - `[2]` 局域网模式（同一校园网）
   - `[F]` 先启动 MySQL 前台，再 `[2]` 启动服务器
2. 主机选 `[6]` 查看连接信息
3. 将 LAN 地址分享给伙伴
4. 伙伴在浏览器打开该地址

---

## 三、方式 C：前端开发代理

伙伴修改前端代码，API 请求代理到主机的后端服务器。

1. 从 GitHub 拉取代码，或接收主机打包的 `edu-mgmt-dist.zip`
2. 安装 Node.js 18+（一次性）
3. 解压后双击 `partner_connect.bat`
4. 选择连接方式（LAN / IPv6 / 公网）
5. 输入主机提供的地址
6. 脚本自动配置 `VITE_API_TARGET` 并启动 `npm run dev`
7. 打开 `http://localhost:5173`

---

## 四、server_control.bat 控制面板

双击 `server_control.bat` 打开控制面板：

| 选项 | 功能 |
|------|------|
| `[1]` 启动服务器 (仅本机) | `python run.py` → `http://localhost:5000` |
| `[2]` 启动服务器 (局域网) | `python run.py --public` → 局域网伙伴可访问 |
| `[3]` 停止服务器 | 关闭 Flask 和 MySQL 前台进程 |
| `[4]` 查看状态 | Flask/MySQL 运行状态、防火墙、IP |
| `[5]` 重建前端并启动 | `npm run build` 后启动服务器 |
| `[D]` 启动 MySQL (服务模式) | 注册为 Windows 服务（需管理员） |
| `[F]` 启动 MySQL (前台模式) | 无需管理员权限，前台窗口运行 |
| `[E]` 停止 MySQL | 停止所有 MySQL 相关进程/服务 |
| `[6]` 伙伴连接信息 | 显示 LAN 地址和默认账号 |
| `[7]` 打包分发给伙伴 | 生成自包含 zip（含 mysql-portable） |
| `[0]` 退出 | 关闭控制面板 |

---

## 五、外网访问方案

### 方案一：同一校园网 / 局域网（最简单）

你和伙伴在同一网段，主机用 `[2]` 局域网模式启动即可。  
URL: `http://你的IP:5000`

### 方案二：IPv6 直连（国内校园网推荐）

中国高校校园网普遍已部署 IPv6，每台设备有独立公网 IPv6 地址。

1. CMD 运行 `ipconfig`，找不以 `fe80`/`::1` 开头的 IPv6 地址
2. 防火墙放行 IPv6 5000 端口
3. 伙伴访问: `http://[你的IPv6地址]:5000`

### 方案三：路由器端口映射（家庭宽带有公网 IPv4）

1. 查询公网 IP：打开 `ip.sb`
2. 路由器管理页添加端口转发：外部 5000 → 你的局域网 IP:5000
3. 外网访问: `http://你的公网IP:5000`

### 方案四：ZeroTier 虚拟组网

你和伙伴安装 ZeroTier 客户端后即可互相访问，免费支持 25 个设备。  
https://www.zerotier.com/

### 方案五：Cloudflare Tunnel（免费，需域名）

https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/

**推荐优先级：完整分发 > 局域网 > IPv6 直连 > 端口映射 > ZeroTier > Cloudflare Tunnel**

---

## 六、工具文件清单

| 文件 | 用途 | 使用者 |
|------|------|--------|
| `start_all.bat` | 一键启动（MySQL + Flask + 依赖） | 伙伴 |
| `server_control.bat` | 服务器控制面板 | 主机 |
| `partner_connect.bat` | 前端开发代理配置 | 开发伙伴 |
| `mysql-portable/start_mysql.bat` | MySQL 独立启动脚本 | 双方 |
| `run.py --public` | Flask 对外监听 | 主机 |
| `frontend/.env.local` | Vite 代理目标（partner_connect.bat 自动生成） | 伙伴 |

---

## 七、常见问题

| 问题 | 解决 |
|------|------|
| `start_all.bat` 报 "Python not found" | 安装 Python 3.11+，勾选 "Add Python to PATH" |
| MySQL 启动失败 / 端口冲突 | 关闭其他 MySQL 进程：`server_control.bat` → `[E]` |
| 伙伴连不上主机 | 主机 `server_control.bat` → `[4]` 查看状态 |
| 页面打开但 API 请求失败 | 检查 `config.ini` 数据库密码；浏览器控制台看具体报错 |
| 登录后频繁掉线 | 在 `config.ini` 的 `[web]` 段配置固定 `jwt_secret` |
| IPv6 地址连不上 | 确认用公网 IPv6（非 fe80），双方防火墙放行 5000 |
| 网页中文显示 ??? | 参考 MYSQL_SETUP_GUIDE.md：确保导入时用了正确的管道编码 |
