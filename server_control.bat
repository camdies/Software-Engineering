@echo off
setlocal enabledelayedexpansion
title EduMgmt Server Control Panel
echo ============================================================
echo   EduMgmt System v3.0 - Server Control Panel
echo ============================================================
echo.

set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

:: Get local IP
for /f "tokens=*" %%a in ('powershell -NoProfile -Command ^
    "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike '*Loopback*' -and $_.PrefixOrigin -ne 'WellKnown'}).IPAddress | Select-Object -First 1" 2^>nul') do (
    if not "%%a"=="" set "LOCAL_IP=%%a"
)
if "%LOCAL_IP%"=="" (
    for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "127.0.0.1"') do (
        for /f "tokens=*" %%b in ("%%a") do (
            set "LOCAL_IP=%%b"
            goto :menu
        )
    )
)
:menu
echo   Local IP: %LOCAL_IP%
echo   Project:  %PROJECT_DIR%
echo.
echo --------------------------------------------------
echo   Server Control
echo   [1] Start server (localhost only)
echo   [2] Start server (LAN public)
echo   [3] Stop server
echo   [4] View server status
echo   [5] Rebuild frontend and start
echo.
echo   Global Internet Access (no third-party tools)
echo   [8] Setup campus/public network access guide
echo   [9] Start server for external access
echo.
echo   Collaboration Tools
echo   [6] Partner connection info
echo   [7] Package and distribute for partner
echo   [0] Exit
echo --------------------------------------------------
echo.

set /p CHOICE="Select [0-9]: "

if "%CHOICE%"=="1" goto :start_local
if "%CHOICE%"=="2" goto :start_public
if "%CHOICE%"=="3" goto :stop
if "%CHOICE%"=="4" goto :status
if "%CHOICE%"=="5" goto :rebuild
if "%CHOICE%"=="6" goto :partner_info
if "%CHOICE%"=="7" goto :distribute
if "%CHOICE%"=="8" goto :ext_access_guide
if "%CHOICE%"=="9" goto :start_external
if "%CHOICE%"=="0" goto :end
echo Invalid option, try again
pause
cls
goto :menu

:: =================================================================
:start_local
:: =================================================================
echo.
echo   Starting server (localhost only)...
echo   URL: http://localhost:5000
echo.
start http://localhost:5000
python run.py
goto :end

:: =================================================================
:start_public
:: =================================================================
echo.
echo   Starting server (LAN public)...
echo   Local:  http://localhost:5000
echo   Remote: http://%LOCAL_IP%:5000
echo   Ensure firewall port 5000 is open!
echo.
start http://localhost:5000
python run.py --public
goto :end

:: =================================================================
:stop
:: =================================================================
echo.
echo   Stopping all server processes...
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO TABLE /NH 2^>nul') do (
    echo   Stopping python.exe PID=%%a
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq ngrok.exe" /FO TABLE /NH 2^>nul') do (
    echo   Stopping ngrok.exe PID=%%a
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq frpc.exe" /FO TABLE /NH 2^>nul') do (
    echo   Stopping frpc.exe PID=%%a
    taskkill /F /PID %%a >nul 2>&1
)
echo   Done.
pause
goto :end

:: =================================================================
:status
:: =================================================================
echo.
echo   ---- Server Status ----
set "PY_COUNT=0"
for /f "tokens=1" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO TABLE /NH 2^>nul') do set /a PY_COUNT+=1
if %PY_COUNT% gtr 0 (
    echo   Flask Server   : RUNNING
    echo   Local URL      : http://localhost:5000
    echo   LAN URL        : http://%LOCAL_IP%:5000
) else (
    echo   Flask Server   : STOPPED
)
echo.

:: Check public/WAN IP
echo   ---- Network Info ----
echo   Local (LAN) IP : %LOCAL_IP%
for /f "tokens=*" %%p in ('curl -s ifconfig.me 2^>nul') do (
    if not "%%p"=="" echo   Public (WAN) IP : %%p
)
echo.

echo   ---- Firewall ----
netsh advfirewall firewall show rule name="EduMgmt Flask 5000" 2>nul | findstr /i "Enabled" >nul
if %errorlevel% equ 0 (echo   Port 5000 : OPEN) else (echo   Port 5000 : CLOSED - firewall rule needed)
echo.

echo   ---- Database ----
sc query MSSQL$SQLEXPRESS 2>nul | findstr "RUNNING" >nul
if %errorlevel% equ 0 (
    echo   SQL Server (SQLEXPRESS) : RUNNING
) else (
    sc query MSSQLSERVER 2>nul | findstr "RUNNING" >nul
    if %errorlevel% equ 0 (echo   SQL Server (MSSQLSERVER): RUNNING) else (echo   SQL Server: NOT DETECTED)
)
pause
goto :end

:: =================================================================
:rebuild
:: =================================================================
echo.
echo   Building frontend...
cd frontend
call npm run build
cd ..
echo   Done. Starting server (public)...
start http://localhost:5000
python run.py --public
goto :end

:: =================================================================
:partner_info
:: =================================================================
echo.
echo   +--------------------------------------------------+
echo   ^|         Partner Connection Info                  ^|
echo   +--------------------------------------------------+
echo   ^|  Browser access:                                ^|
echo   ^|    http://%LOCAL_IP%:5000                       ^|
echo   ^|                                                ^|
echo   ^|  Frontend dev proxy (VITE_API_TARGET):           ^|
echo   ^|    http://%LOCAL_IP%:5000                       ^|
echo   ^|                                                ^|
echo   ^|  Database (SSMS):                               ^|
echo   ^|    %LOCAL_IP%\SQLEXPRESS  (or MSSQLSERVER)     ^|
echo   ^|    user: sa / db: CourseManagementDB            ^|
echo   ^|                                                ^|
echo   ^|  Accounts:                                      ^|
echo   ^|    admin  / 123456                              ^|
echo   ^|    T001   / 123456                              ^|
echo   ^|    STU001 / 123456                              ^|
echo   +--------------------------------------------------+
echo.

:: Check public IP
for /f "tokens=*" %%p in ('curl -s --connect-timeout 5 ifconfig.me 2^>nul') do (
    if not "%%p"=="" (
        echo   Public (WAN) IP detected: %%p
        echo   If port forwarding is set: http://%%p:5000
    )
)
echo.
echo   For external access without VPN/proxy tools:
echo   See option [8] External Access Setup Guide
echo.
pause
goto :end

:: =================================================================
:distribute
:: =================================================================
echo.
echo   Packaging project (excludes node_modules, .git, __pycache__)...
set "PACKAGE_NAME=edu-mgmt-dist.zip"
set "PACKAGE_DIR=%PROJECT_DIR%..\edu-mgmt-dist"

if exist "%PACKAGE_DIR%" rmdir /s /q "%PACKAGE_DIR%"
mkdir "%PACKAGE_DIR%"

robocopy "%PROJECT_DIR%" "%PACKAGE_DIR%" /E /NFL /NDL /NJH /NJS /XD node_modules __pycache__ .git .claude .vscode .idea /XF *.pyc *.bak .env >nul
if %errorlevel% geq 8 echo   Warning: some copy errors, continuing...

if exist "%PACKAGE_DIR%\backend\config\config.ini" del "%PACKAGE_DIR%\backend\config\config.ini"
if exist "%PACKAGE_DIR%\backend\config\config.ini.example" (
    copy "%PACKAGE_DIR%\backend\config\config.ini.example" "%PACKAGE_DIR%\backend\config\config.ini" >nul
)

powershell -Command "Compress-Archive -Path '%PACKAGE_DIR%\*' -DestinationPath '%PROJECT_DIR%..\%PACKAGE_NAME%' -Force"
rmdir /s /q "%PACKAGE_DIR%"

echo.
echo   Package: %PROJECT_DIR%..\%PACKAGE_NAME%
echo.
echo   Partner steps:
echo   1. Extract zip
echo   2. Run: partner_connect.bat
echo   3. Enter the server IP or public URL
echo   4. Choose LAN or internet mode
echo.
pause
goto :end

:: =================================================================
:ext_access_guide
:: =================================================================
echo.
echo   +==========================================================+
echo   ^|  校园网/公网访问设置指南（无需第三方工具）              ^|
echo   +==========================================================+
echo.
echo   在中国校园网环境下，可以通过以下方式实现外网访问：
echo.
echo   ---- 方案一：校园网内直接访问（最简单）----
echo.
echo   如果你的开发伙伴和你同一个校园网（同一网段），
echo   直接用 [2] 局域网模式即可，不需要额外配置。
echo   URL: http://%LOCAL_IP%:5000
echo.
echo   ---- 方案二：路由器端口映射（有公网 IP）----
echo.
echo   前提：你的校园网/家庭宽带分配了公网 IPv4 地址
echo   （移动/联通/电信宽带有概率获得公网 IP，校园网通常没有）
echo.
echo   步骤：
echo   1. 先查询你的公网 IP:
for /f "tokens=*" %%p in ('curl -s --connect-timeout 5 ifconfig.me 2^>nul') do (
    if not "%%p"=="" echo      当前公网 IP: %%p
)
echo   2. 登录路由器管理页面（通常是 http://192.168.1.1）
echo      品牌       默认地址         默认账号/密码
echo      TP-Link    192.168.1.1      admin/admin
echo      Xiaomi     192.168.31.1     见路由器底部
echo      Huawei     192.168.3.1      admin/admin
echo      ASUS       192.168.50.1     admin/admin
echo   3. 找到"端口转发"/"虚拟服务器"/"Port Forwarding"
echo   4. 添加规则:
echo      服务端口: 5000
echo      内部 IP:  %LOCAL_IP%
echo      内部端口: 5000
echo      协议: TCP
echo   5. 保存并应用
echo   6. 外网访问地址: http://你的公网IP:5000
echo.
echo   ---- 方案三：IPv6 直连（推荐，校园网通常支持）----
echo.
echo   中国高校校园网普遍已部署 IPv6，每台设备都会分配
echo   独立的公网 IPv6 地址，无需端口映射即可直连！
echo.
echo   1. 查询本机 IPv6 地址:
echo      ipconfig ^| findstr "IPv6"
echo   2. 开放的 IPv6 地址通常是临时地址（Temporary）或
echo      公共地址（Public），不是以 fe80 开头的本地地址
echo   3. 在 Windows 防火墙中放行 IPv6 的 5000 端口:
echo      netsh advfirewall firewall add rule name="EduMgmt IPv6" dir=in action=allow protocol=TCP localport=5000
echo   4. 伙伴访问地址: http://[你的IPv6地址]:5000
echo      注意: 必须用方括号包裹 IPv6 地址!
echo      例如: http://[2001:da8:xxxx:xxxx::1]:5000
echo   5. 注意: IPv6 隐私扩展会导致地址定期变化
echo.
echo   ---- 方案四：使用 frp 内网穿透（自建）----
echo.
echo   如果你有一台有公网 IP 的云服务器（阿里云/腾讯云
echo   学生价约 10 元/月），可以自建 frp 替代 ngrok。
echo.
echo   服务端（云服务器）配置 frps.ini:
echo     [common]
echo     bind_port = 7000
echo     vhost_http_port = 8080
echo.
echo   客户端（你的电脑）配置 frpc.ini:
echo     [common]
echo     server_addr = 你的服务器IP
echo     server_port = 7000
echo     [web]
echo     type = http
echo     local_port = 5000
echo     custom_domains = 你的域名或IP
echo.
echo   下载 frp: https://github.com/fatedier/frp/releases
echo.
echo   ---- 方案五：ZeroTier / Tailscale 虚拟组网 ----
echo.
echo   创建虚拟局域网，你和伙伴安装客户端后，
echo   就可以像在同一局域网一样互相访问。
echo   ZeroTier 免费支持 25 个设备。
echo   网址: https://www.zerotier.com/
echo.
echo   ---- 方案六：Cloudflare Tunnel（免费）----
echo.
echo   Cloudflare Tunnel 类似于 ngrok 但完全免费，无限流量。
echo   需要一个域名（可以注册免费域名如 .tk/.ml）。
echo   网址: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
echo.
echo   +==========================================================+
echo   ^|  推荐优先级：同一局域网 ^> IPv6 直连 ^> 端口映射        ^|
echo   ^|              ^> ZeroTier ^> frp ^> Cloudflare Tunnel    ^|
echo   +==========================================================+
echo.
pause
goto :end

:: =================================================================
:start_external
:: =================================================================
echo.
echo   +--------------------------------------------------+
echo   ^|  Start server for external access                ^|
echo   +--------------------------------------------------+
echo.
echo   This starts Flask on 0.0.0.0:5000 so it accepts
echo   connections from any network interface (LAN, IPv6,
echo   port-forwarded WAN, VPN, etc.)
echo.
echo   Before starting, ensure:
echo   1. Firewall allows port 5000 (inbound)
echo   2. If using router port forwarding, it is configured
echo   3. If using IPv6, your partner has your IPv6 address
echo.
echo   Current network info:
echo     LAN IPv4 : %LOCAL_IP%
for /f "tokens=*" %%p in ('curl -s --connect-timeout 3 ifconfig.me 2^>nul') do (
    if not "%%p"=="" echo     Public IP: %%p
)
for /f "tokens=1,2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv6" ^| findstr /v "fe80" ^| findstr /v "::1"') do (
    for /f "tokens=*" %%c in ("%%b") do echo     IPv6     : %%a:%%c
)
echo.

:: Open firewall if needed
netsh advfirewall firewall show rule name="EduMgmt Flask 5000" 2>nul | findstr /i "Enabled" >nul
if %errorlevel% neq 0 (
    echo   Firewall rule missing. Adding now...
    netsh advfirewall firewall add rule name="EduMgmt Flask 5000" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1
    echo   Done.
)
echo.
echo   Starting Flask with external access...
echo   Press Ctrl+C to stop, or use option [3] in another window.
echo.

start http://localhost:5000
python run.py --public
goto :end

:end
endlocal
