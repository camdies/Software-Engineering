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
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    for /f "tokens=*" %%b in ("%%a") do (
        set "LOCAL_IP=%%b"
        goto :menu
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
echo   External Access (Internet)
echo   [8] Install ngrok
echo   [9] Start server with ngrok tunnel
echo.
echo   Collaboration Tools
echo   [6] Partner connection info
echo   [7] Package and distribute
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
echo   Make sure firewall port 5000 is open!
echo.
start http://localhost:5000
python run.py --public
goto :end

:: =================================================================
:stop
:: =================================================================
echo.
echo   Searching for Python and ngrok processes...
for /f "tokens=2" %%a in ('tasklist ^| findstr /i "python.exe"') do (
    echo   Killing python.exe PID=%%a
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=2" %%a in ('tasklist ^| findstr /i "ngrok.exe"') do (
    echo   Killing ngrok.exe PID=%%a
    taskkill /F /PID %%a >nul 2>&1
)
echo   All server processes terminated.
pause
goto :end

:: =================================================================
:status
:: =================================================================
echo.
echo   --- Server Status ---
tasklist 2>nul | findstr /i "python.exe" >nul
if %errorlevel% equ 0 (
    echo   Flask Server: RUNNING
    tasklist | findstr /i "python.exe"
    echo.
    echo   Local:  http://localhost:5000
    echo   Remote: http://%LOCAL_IP%:5000
) else (
    echo   Flask Server: STOPPED
)

tasklist 2>nul | findstr /i "ngrok.exe" >nul
if %errorlevel% equ 0 (
    echo   ngrok Tunnel: RUNNING
    tasklist | findstr /i "ngrok.exe"
    echo   Check ngrok URL: http://127.0.0.1:4040
) else (
    echo   ngrok Tunnel: STOPPED
)

echo.
echo   --- Firewall Rules ---
netsh advfirewall firewall show rule name="EduMgmt Flask 5000" 2>nul | findstr /i "Enabled"
netsh advfirewall firewall show rule name="SQL Server 1433" 2>nul | findstr /i "Enabled"

echo.
echo   --- Database ---
sc query MSSQL$SQLEXPRESS 2>nul | findstr "STATE"
sc query MSSQLSERVER 2>nul | findstr "STATE"

echo.
echo   --- Network ---
echo   Local IP: %LOCAL_IP%
ping -n 1 %LOCAL_IP% 2>nul | findstr "TTL"

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
echo   Frontend build complete!
echo   Starting server...
start http://localhost:5000
python run.py --public
goto :end

:: =================================================================
:partner_info
:: =================================================================
echo.
echo   +--------------------------------------------------+
echo   |         Partner Connection Info                  |
echo   +--------------------------------------------------+
echo   |                                                  |
echo   |  Web browser (zero setup):                       |
echo   |    http://%LOCAL_IP%:5000                       |
echo   |                                                  |
echo   |  Frontend dev proxy (VITE_API_TARGET):           |
echo   |    http://%LOCAL_IP%:5000                       |
echo   |                                                  |
echo   |  Database (SSMS):                                |
echo   |    Server: %LOCAL_IP%\SQLEXPRESS                |
echo   |    User: sa                                      |
echo   |    DB: CourseManagementDB                        |
echo   |                                                  |
echo   |  Default accounts:                               |
echo   |    admin  / 123456                               |
echo   |    T001   / 123456  (teacher)                    |
echo   |    STU001 / 123456  (student)                    |
echo   |                                                  |
echo   |  Docs: SETUP_PARTNER.md                          |
echo   +--------------------------------------------------+
echo.

:: Check if ngrok is installed and show external URL
where ngrok >nul 2>&1
if %errorlevel% equ 0 (
    echo   ngrok status: INSTALLED
    echo   To get public URL, start with option [9]
    echo   Then visit http://127.0.0.1:4040 to see the ngrok URL
) else (
    echo   ngrok status: NOT INSTALLED
    echo   For internet access, use option [8] to install
)

echo.
pause
goto :end

:: =================================================================
:distribute
:: =================================================================
echo.
echo   Packaging project (excluding node_modules, .git, __pycache__)...
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
echo   Package ready: %PROJECT_DIR%..\%PACKAGE_NAME%
echo.
echo   Send this zip to your partner. They should:
echo   1. Extract the zip
echo   2. Run: partner_connect.bat
echo   3. Enter this IP: %LOCAL_IP%
echo   4. npm run dev -- and open http://localhost:5173
echo.
pause
goto :end

:: =================================================================
:install_ngrok
:: =================================================================
echo.
echo   Installing ngrok for external internet access...
echo.
echo   ngrok creates a public tunnel from the internet to your local
echo   port 5000. Users anywhere can access your server.
echo.
echo   ---
echo   1. Go to https://ngrok.com/download
echo   2. Download ngrok for Windows (zip)
echo   3. Extract ngrok.exe to: %USERPROFILE%\ngrok\
echo   4. Sign up at https://dashboard.ngrok.com/signup (free)
echo   5. Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
echo   6. Run: %USERPROFILE%\ngrok\ngrok.exe config add-authtoken YOUR_TOKEN
echo   ---
echo.
echo   Already done? Let me check...

where ngrok >nul 2>&1
if %errorlevel% equ 0 (
    echo   ngrok is already installed: OK
    ngrok version 2>&1 | findstr /i "ngrok"
    echo   You can use option [9] to start the tunnel.
) else (
    if exist "%USERPROFILE%\ngrok\ngrok.exe" (
        echo   Found ngrok at %USERPROFILE%\ngrok\ngrok.exe but not in PATH.
        echo   Adding to PATH...
        set "PATH=!PATH!;%USERPROFILE%\ngrok"
        setx PATH "!PATH!" >nul 2>&1
        echo   Done. Please restart this script for PATH to take effect.
    ) else (
        echo   ngrok not found. Would you like me to download it?
        set /p DL_NGROK="Download ngrok now with winget? (Y/N): "
        if /i "!DL_NGROK!"=="Y" (
            winget install ngrok 2>&1
            if %errorlevel% neq 0 (
                echo   winget failed. Please install manually from https://ngrok.com/download
            )
        ) else (
            echo   Skipping download. Please install manually.
        )
    )
)
echo.
pause
goto :end

:: =================================================================
:start_ngrok
:: =================================================================
where ngrok >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%USERPROFILE%\ngrok\ngrok.exe" (
        set "PATH=!PATH!;%USERPROFILE%\ngrok"
    ) else (
        echo   ngrok is not installed! Use option [8] first.
        pause
        goto :end
    )
)

echo.
echo   +--------------------------------------------------+
echo   |  Starting ngrok tunnel + Flask server             |
echo   +--------------------------------------------------+
echo.
echo   Flask starting on port 5000...
echo   ngrok starting on port 5000...

:: Start Flask in background
start "EduMgmt Flask" python run.py --public

:: Wait for Flask to start
echo   Waiting for Flask to boot...
ping -n 4 127.0.0.1 >nul

:: Start ngrok
echo   Launching ngrok...
start "EduMgmt ngrok" ngrok http 5000

:: Wait and show the public URL
ping -n 4 127.0.0.1 >nul

echo.
echo   ==================================================
echo     IMPORTANT: Open http://127.0.0.1:4040 in browser
echo     to see the public ngrok URL.
echo.
echo     That is the URL your partner can use from
echo     anywhere on the internet!
echo   ==================================================
echo.
echo   Share this URL with your partner.
echo   The URL looks like: https://xxxx-xx-xx-xxx-xx.ngrok-free.app
echo.
echo   Press any key to open ngrok status page...
pause >nul
start http://127.0.0.1:4040

goto :end

:end
endlocal
