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
echo   [3] Stop server (kill all python + ngrok)
echo   [4] View server status
echo   [5] Rebuild frontend and start
echo.
echo   External Access (Internet)
echo   [8] Install / setup ngrok
echo   [9] Start server + ngrok tunnel
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
if "%CHOICE%"=="8" goto :install_ngrok
if "%CHOICE%"=="9" goto :start_ngrok
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

set "NGROK_COUNT=0"
for /f "tokens=1" %%a in ('tasklist /FI "IMAGENAME eq ngrok.exe" /FO TABLE /NH 2^>nul') do set /a NGROK_COUNT+=1
if %NGROK_COUNT% gtr 0 (
    echo   ngrok Tunnel   : RUNNING
    echo   ngrok status   : http://127.0.0.1:4040
) else (
    echo   ngrok Tunnel   : STOPPED
)
echo.

echo   ---- Firewall ----
netsh advfirewall firewall show rule name="EduMgmt Flask 5000" 2>nul | findstr /i "Enabled" >nul
if %errorlevel% equ 0 (echo   Port 5000 : OPEN) else (echo   Port 5000 : CLOSED - run: netsh advfirewall ... allow 5000)
echo.

echo   ---- Database ----
sc query MSSQL$SQLEXPRESS 2>nul | findstr "RUNNING" >nul
if %errorlevel% equ 0 (
    echo   SQL Server (SQLEXPRESS) : RUNNING
) else (
    sc query MSSQLSERVER 2>nul | findstr "RUNNING" >nul
    if %errorlevel% equ 0 (echo   SQL Server (MSSQLSERVER): RUNNING) else (echo   SQL Server: NOT DETECTED)
)
echo.
echo   Network: %LOCAL_IP%
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
echo   Done.
echo   Starting server (public)...
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

where ngrok >nul 2>&1
if %errorlevel% equ 0 (
    echo   ngrok: INSTALLED - use [9] for internet access
    for /f "tokens=*" %%u in ('curl -s http://127.0.0.1:4040/api/tunnels 2^>nul ^| findstr /i "public_url"') do (
        echo   Current tunnel: %%u
    )
) else (
    echo   ngrok: NOT INSTALLED - use [8] to install for internet access
)
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
echo   3. Enter: %LOCAL_IP%
echo   4. Choose LAN or internet mode
echo.
pause
goto :end

:: =================================================================
:install_ngrok
:: =================================================================
echo.
echo   ngrok Setup for Internet Access
echo   ================================
echo.
echo   ngrok creates a public URL so partners anywhere on the
echo   internet can access your local server.
echo.

where ngrok >nul 2>&1
if %errorlevel% equ 0 (
    echo   ngrok already installed:
    ngrok version 2>&1 | findstr /i "ngrok"
    echo.
    echo   To verify auth: ngrok http 5000
    echo   If you get "authentication failed", run:
    echo     ngrok config add-authtoken YOUR_TOKEN
    echo   Get your token at: https://dashboard.ngrok.com/get-started/your-authtoken
    pause
    goto :end
)

if exist "%USERPROFILE%\ngrok\ngrok.exe" (
    echo   Found ngrok at %USERPROFILE%\ngrok\ngrok.exe
    echo   Adding to current session PATH...
    set "PATH=!PATH!;%USERPROFILE%\ngrok"
    echo   Done.
    pause
    goto :end
)

echo   Option 1: Install with winget
echo   Option 2: Manual install
echo.
set /p NG_INSTALL="Choose [1-2]: "
if "%NG_INSTALL%"=="1" (
    winget install ngrok 2>&1
    if %errorlevel% equ 0 (
        echo   ngrok installed via winget.
        echo   Now run: ngrok config add-authtoken YOUR_TOKEN
    ) else (
        echo   winget failed. Try option 2.
    )
    pause
    goto :end
)

echo.
echo   Manual install steps:
echo   1. Open https://ngrok.com/download
echo   2. Download "ngrok for Windows" (zip)
echo   3. Extract ngrok.exe to: %USERPROFILE%\ngrok\
echo   4. Open https://dashboard.ngrok.com/signup (free)
echo   5. Copy your authtoken from dashboard
echo   6. Run in terminal:
echo      %USERPROFILE%\ngrok\ngrok.exe config add-authtoken YOUR_TOKEN
echo   7. Then option [9] will work
echo.
pause
goto :end

:: =================================================================
:start_ngrok
:: =================================================================
:: Resolve ngrok location
set "NGROK_EXE=ngrok"
where ngrok >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%USERPROFILE%\ngrok\ngrok.exe" (
        set "NGROK_EXE=%USERPROFILE%\ngrok\ngrok.exe"
    ) else if exist "C:\ngrok\ngrok.exe" (
        set "NGROK_EXE=C:\ngrok\ngrok.exe"
    ) else (
        echo   ngrok not found!
        echo   Option [8] first to install, or put ngrok.exe in
        echo   %%USERPROFILE%%\ngrok\ or somewhere in PATH.
        pause
        goto :end
    )
)

echo.
echo   +--------------------------------------------------+
echo   ^|  Starting Flask + ngrok tunnel                   ^|
echo   +--------------------------------------------------+
echo.
echo   Flask : http://localhost:5000
echo   LAN   : http://%LOCAL_IP%:5000
echo   ngrok : starting tunnel...

:: Kill any existing ngrok first
taskkill /F /IM ngrok.exe >nul 2>&1

:: Open Flask in its own minimized window, hidden
start "EduMgmt-Flask" /MIN python run.py --public

:: Wait for Flask to be ready
echo   Waiting for Flask to start...
set /a WAIT=0
:wait_flask
ping -n 2 127.0.0.1 >nul
set /a WAIT+=1
curl -s -o nul http://127.0.0.1:5000 2>nul
if %errorlevel% neq 0 (
    if %WAIT% lss 15 goto :wait_flask
)
if %WAIT% lss 15 (
    echo   Flask ready (after %WAIT% seconds).
) else (
    echo   Flask may not be ready, but starting ngrok anyway...
)

:: Start ngrok in a new visible window so user can see the URL
echo   Starting ngrok...
start "EduMgmt-ngrok" "%NGROK_EXE%" http 5000

:: Wait for ngrok to establish
echo   Waiting for ngrok tunnel to establish...
set /a WAIT=0
set "NGROK_URL="
:wait_ngrok
ping -n 2 127.0.0.1 >nul
set /a WAIT+=1
:: Try to get public URL from ngrok's local API
for /f "delims=" %%u in ('curl -s http://127.0.0.1:4040/api/tunnels 2^>nul ^| findstr /r "public_url"') do set "NGROK_URL=%%u"
if "%NGROK_URL%"=="" (
    if %WAIT% lss 10 goto :wait_ngrok
)

echo.
echo   +==================================================+
echo   ^|  ngrok TUNNEL ACTIVE                            ^|
echo   +==================================================+
echo.

if not "%NGROK_URL%"=="" (
    echo   Public URL: %NGROK_URL%
) else (
    echo   Open http://127.0.0.1:4040 to see the public URL
    start http://127.0.0.1:4040
)

echo.
echo   Share this URL with your partner.
echo   They can access from anywhere on the internet!
echo.
echo   +==================================================+
echo.
echo   Press Ctrl+C in the ngrok window to stop the tunnel.
echo   Or run this script and choose [3] to stop everything.
echo.
echo   This window will stay open. Press any key to open
echo   the ngrok status page and check the public URL...
pause >nul
start http://127.0.0.1:4040
goto :end

:end
endlocal
