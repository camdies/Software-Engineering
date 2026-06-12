@echo off
setlocal enabledelayedexpansion
title EduMgmt Server Control Panel

set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

:: Get local IP
for /f "tokens=*" %%a in ('powershell -NoProfile -Command ^
    "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike '*Loopback*' -and $_.PrefixOrigin -ne 'WellKnown'}).IPAddress | Select-Object -First 1" 2^>nul') do (
    if not "%%a"=="" set "LOCAL_IP=%%a"
)
if "%LOCAL_IP%"=="" (
    for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "127.0.0.1"') do (
        for /f "tokens=*" %%b in ("%%a") do set "LOCAL_IP=%%b"
    )
)

:: Get IPv6 address (skip loopback and link-local)
set "IPV6="
for /f "tokens=*" %%a in ('powershell -NoProfile -Command ^
    "(Get-NetIPAddress -AddressFamily IPv6 | Where-Object {$_.InterfaceAlias -notlike '*Loopback*' -and $_.IPAddress -notlike 'fe80*' -and $_.IPAddress -notlike '::1'}).IPAddress | Select-Object -First 1" 2^>nul') do (
    if not "%%a"=="" set "IPV6=%%a"
)

:menu
cls
echo ============================================================
echo   EduMgmt System v3.0 - Server Control Panel
echo ============================================================
echo.
echo   Local IP:  %LOCAL_IP%
if not "%IPV6%"=="" echo   IPv6:      %IPV6%
echo   Project:   %PROJECT_DIR%
echo.
echo   ---- Server Control ----
echo   [1] Start server (localhost only)
echo   [2] Start server (LAN + IPv6 public)
echo   [3] Stop server
echo   [4] View server status
echo   [5] Rebuild frontend and start
echo.
echo   ---- External Access ----
echo   [A] IPv6 direct access guide and test
echo   [B] All external access options (port forward, frp, ZeroTier...)
echo.
echo   ---- Partner Tools ----
echo   [6] Partner connection info
echo   [7] Package and distribute for partner
echo.
echo   [R] Return to this menu
echo   [0] Exit
echo --------------------------------------------------
echo.

set /p CHOICE="Select: "

if "%CHOICE%"=="1" goto :start_local
if "%CHOICE%"=="2" goto :start_public
if "%CHOICE%"=="3" goto :stop
if "%CHOICE%"=="4" goto :status
if "%CHOICE%"=="5" goto :rebuild
if "%CHOICE%"=="6" goto :partner_info
if "%CHOICE%"=="7" goto :distribute
if /i "%CHOICE%"=="A" goto :ipv6_guide
if /i "%CHOICE%"=="B" goto :ext_access_guide
if /i "%CHOICE%"=="R" goto :menu
if "%CHOICE%"=="0" goto :end
echo Invalid option, try again...
pause
goto :menu

:: =================================================================
:start_local
:: =================================================================
start "EduMgmt Flask [localhost]" python run.py
echo.
echo   Server starting at http://localhost:5000
echo   This window will stay open. Press R then Enter to return to menu.
echo.
set /p X=""
goto :menu

:: =================================================================
:start_public
:: =================================================================
echo.
echo   Starting server in PUBLIC mode (LAN + IPv6)...
echo.
echo     Local: http://localhost:5000
echo     LAN:   http://%LOCAL_IP%:5000
if not "%IPV6%"=="" echo     IPv6:   http://[%IPV6%]:5000
echo.
echo   Make sure firewall port 5000 is OPEN!
echo.

:: Auto-open firewall if needed (best-effort)
netsh advfirewall firewall show rule name="EduMgmt Flask 5000" 2>nul | findstr /i "Enabled" >nul
if %errorlevel% neq 0 (
    echo   Adding firewall rule for port 5000...
    netsh advfirewall firewall add rule name="EduMgmt Flask 5000" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1
)

start "EduMgmt Flask [public]" python run.py --public

echo   Server is running in a separate window.
echo   Press R then Enter to return to this menu.
echo.
set /p X=""
goto :menu

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
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq frpc.exe" /FO TABLE /NH 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo   Done.
echo   Press R then Enter to return to menu.
set /p X=""
goto :menu

:: =================================================================
:status
:: =================================================================
cls
echo.
echo   ============================================================
echo     SERVER STATUS
echo   ============================================================
echo.

set "PY_COUNT=0"
for /f "tokens=1" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO TABLE /NH 2^>nul') do set /a PY_COUNT+=1
if %PY_COUNT% gtr 0 (
    echo   Flask Server   : RUNNING
    echo     Local: http://localhost:5000
    echo     LAN:   http://%LOCAL_IP%:5000
    if not "%IPV6%"=="" echo     IPv6:   http://[%IPV6%]:5000
) else (
    echo   Flask Server   : STOPPED
)

echo.
echo   ---- Firewall ----
netsh advfirewall firewall show rule name="EduMgmt Flask 5000" 2>nul | findstr /i "Enabled" >nul
if %errorlevel% equ 0 (echo   Port 5000 TCP: OPEN) else (echo   Port 5000 TCP: NO RULE (use [2] to auto-add))

echo.
echo   ---- Database ----
sc query MSSQL$SQLEXPRESS 2>nul | findstr "RUNNING" >nul && echo   SQL Server (SQLEXPRESS): RUNNING
sc query MSSQLSERVER 2>nul | findstr "RUNNING" >nul && echo   SQL Server (MSSQLSERVER): RUNNING
sc query MSSQL$SQLEXPRESS 2>nul | findstr "STOPPED" >nul && echo   SQL Server: STOPPED
sc query MSSQLSERVER 2>nul | findstr "STOPPED" >nul && echo   SQL Server: STOPPED

echo.
echo   ---- Network ----
echo     LAN IPv4 : %LOCAL_IP%
if not "%IPV6%"=="" echo     IPv6     : %IPV6%
for /f "tokens=*" %%p in ('curl -s --connect-timeout 3 ifconfig.me 2^>nul') do (
    if not "%%p"=="" echo     Public IP: %%p
)

echo.
echo   Press R then Enter to return to menu.
set /p X=""
goto :menu

:: =================================================================
:rebuild
:: =================================================================
echo.
echo   Building frontend...
cd frontend
call npm run build
cd ..
echo   Done. Starting server (public)...
start "EduMgmt Flask [public]" python run.py --public
echo   Press R then Enter to return to menu.
set /p X=""
goto :menu

:: =================================================================
:partner_info
:: =================================================================
cls
echo.
echo   +==================================================+
echo   ^|       PARTNER CONNECTION INFO                    ^|
echo   +==================================================+
echo   ^|                                                  ^|
echo   ^|  LAN (same network):                             ^|
echo   ^|    http://%LOCAL_IP%:5000                       ^|
if not "%IPV6%"=="" (
echo   ^|                                                  ^|
echo   ^|  IPv6 (campus network / internet):              ^|
echo   ^|    http://[%IPV6%]:5000                         ^|
)
echo   ^|                                                  ^|
echo   ^|  Accounts:                                       ^|
echo   ^|    admin  / 123456                               ^|
echo   ^|    T001   / 123456  (teacher)                    ^|
echo   ^|    STU001 / 123456  (student)                    ^|
echo   ^|                                                  ^|
echo   ^|  Partner tools:                                  ^|
echo   ^|    partner_connect.bat - auto proxy setup        ^|
echo   ^|    SETUP_PARTNER.md  - full guide               ^|
echo   +==================================================+

:: Public WAN IP
for /f "tokens=*" %%p in ('curl -s --connect-timeout 3 ifconfig.me 2^>nul') do (
    if not "%%p"=="" (
        echo.
        echo   Public WAN IP detected: %%p
        echo   If port forwarding is set up: http://%%p:5000
    )
)

echo.
echo   Press R then Enter to return to menu.
set /p X=""
goto :menu

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

powershell -Command "Compress-Archive -Path '%PACKAGE_DIR%\*' -DestinationPath '%PROJECT_DIR%..\%PACKAGE_NAME%' -Force" 2>nul
rmdir /s /q "%PACKAGE_DIR%"

echo.
echo   Package: %PROJECT_DIR%..\%PACKAGE_NAME%
echo.
echo   Partner steps:
echo   1. Extract zip
echo   2. Run: partner_connect.bat
echo   3. Choose [2] IPv6 or [1] LAN
echo.
echo   Press R then Enter to return to menu.
set /p X=""
goto :menu

:: =================================================================
:ipv6_guide
:: =================================================================
cls
echo.
echo   +==========================================================+
echo   ^|   IPv6 DIRECT ACCESS - Setup and Test                   ^|
echo   +==========================================================+
echo.
echo   China campus networks almost always have IPv6.
echo   Every device gets its own PUBLIC IPv6 address,
echo   so NO port mapping or third-party tools needed!
echo.
echo   ---- Step 1: Check your IPv6 ----
echo.

if "%IPV6%"=="" (
    echo   [WARNING] No public IPv6 detected!
    echo.
    echo   Possible reasons:
    echo   - Your network does not have IPv6 (rare in Chinese campuses)
    echo   - IPv6 is disabled in Windows network adapter
    echo.
    echo   To enable IPv6:
    echo   1. Control Panel - Network and Sharing Center
    echo   2. Click your network connection
    echo   3. Properties - check "Internet Protocol Version 6 (TCP/IPv6)"
    echo   4. OK, wait a few seconds, then re-run this tool
) else (
    echo   Your IPv6: %IPV6%
    echo.
    echo   TEST IT: Open this in your browser:
    echo     http://[%IPV6%]:5000
    echo.

    :: Quick self-test
    if %PY_COUNT% gtr 0 (
        curl -s -o nul --connect-timeout 3 "http://[%IPV6%]:5000" 2>nul && (
            echo   [OK] IPv6 self-test PASSED - server reachable
        ) || (
            echo   [INFO] Self-test inconclusive (server may need --public mode)
        )
    )
)

echo.
echo   ---- Step 2: Partner tests your IPv6 ----
echo.
echo   Partner should:
if not "%IPV6%"=="" echo   1. Open: http://[%IPV6%]:5000
echo   2. Or run partner_connect.bat and choose [2] IPv6
echo   3. Enter the IPv6 address (WITHOUT brackets, script adds them)
echo.
echo   ---- Step 3: If partner cannot connect ----
echo.
echo   1. Windows Firewall must allow port 5000 on IPv6:
echo      netsh advfirewall firewall add rule name="EduMgmt IPv6" dir=in action=allow protocol=TCP localport=5000
echo.
echo   2. Partner's network must also have IPv6. Test:
echo      On partner's PC, open https://test-ipv6.com
echo      If it shows "IPv6 not supported", partner needs to enable IPv6
echo.
echo   3. Some campus firewalls may block incoming IPv6 connections.
echo      If so, try option [B] for alternatives.
echo.
echo   ---- IPv6 privacy note ----
echo   Windows may change your IPv6 address periodically
echo   (privacy extensions). If the address keeps changing:
echo   Run in admin PowerShell:
echo     Set-NetIPv6Protocol -RandomizeIdentifiers Disabled
echo.
echo   +==========================================================+

echo.
echo   Press R then Enter to return to menu.
set /p X=""
goto :menu

:: =================================================================
:ext_access_guide
:: =================================================================
cls
echo.
echo   +==========================================================+
echo   ^|   ALL EXTERNAL ACCESS OPTIONS                           ^|
echo   +==========================================================+
echo.
echo   RECOMMENDED ORDER for Chinese campus networks:
echo.
echo   1. IPv6 direct [option A]
echo      Zero config, already built-in, best for campus
echo.
echo   2. Same campus network LAN
echo      If both on the same campus subnet, just use [2]
echo      URL: http://%LOCAL_IP%:5000
echo.
echo   3. Router port forwarding (for home broadband)
echo      Login to router admin (192.168.1.1 etc.)
echo      Port Forward: external 5000 -^> %LOCAL_IP%:5000 TCP
echo      Then use: http://YOUR_PUBLIC_IP:5000
echo.
echo   4. ZeroTier virtual LAN (free, 25 devices)
echo      https://www.zerotier.com/
echo      Both install client, join same network, get virtual IP
echo.
echo   5. frp self-hosted tunnel (need cloud server ~10 CNY/month)
echo      https://github.com/fatedier/frp/releases
echo      Server: Alibaba Cloud / Tencent Cloud student pricing
echo.
echo   6. Cloudflare Tunnel (free, needs a domain name)
echo      https://developers.cloudflare.com/cloudflare-one/
echo.
echo   7. ngrok (free tier, limited bandwidth, URL changes)
echo      https://ngrok.com/download
echo.
echo   +==========================================================+

echo.
echo   Press R then Enter to return to menu.
set /p X=""
goto :menu

:: =================================================================
:start_external
:: =================================================================
echo.
echo   Starting server for EXTERNAL ACCESS...
echo.
echo   The server will listen on ALL network interfaces.

:: Firewall
netsh advfirewall firewall show rule name="EduMgmt Flask 5000" 2>nul | findstr /i "Enabled" >nul
if %errorlevel% neq 0 (
    echo   Adding Windows Firewall rule for port 5000...
    netsh advfirewall firewall add rule name="EduMgmt Flask 5000" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1
)

echo.
echo   When ready, your partner can connect via:
echo     LAN:  http://%LOCAL_IP%:5000
if not "%IPV6%"=="" echo     IPv6:  http://[%IPV6%]:5000
echo.
echo   Server starting in a NEW WINDOW...
echo   Close that window or use [3] to stop.
echo   This menu will stay open.

start "EduMgmt Flask [external]" python run.py --public

echo.
echo   Press R then Enter to return to menu.
set /p X=""
goto :menu

:end
endlocal
