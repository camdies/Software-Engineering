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
echo   [1] Start server (localhost only)
echo   [2] Start server (LAN public --public)
echo   [3] Stop server
echo   [4] View server status
echo   [5] Rebuild frontend and start
echo   [6] Partner connection info
echo   [7] Package and distribute
echo   [0] Exit
echo --------------------------------------------------
echo.

set /p CHOICE="Select [0-7]: "

if "%CHOICE%"=="1" goto :start_local
if "%CHOICE%"=="2" goto :start_public
if "%CHOICE%"=="3" goto :stop
if "%CHOICE%"=="4" goto :status
if "%CHOICE%"=="5" goto :rebuild
if "%CHOICE%"=="6" goto :partner_info
if "%CHOICE%"=="7" goto :distribute
if "%CHOICE%"=="0" goto :end
echo Invalid option, try again
pause
cls
goto :menu

:start_local
echo.
echo   Starting server (localhost only)...
echo   URL: http://localhost:5000
echo.
start http://localhost:5000
python run.py
goto :end

:start_public
echo.
echo   Starting server (LAN public)...
echo   Local:  http://localhost:5000
echo   Remote: http://%LOCAL_IP%:5000
echo   Make sure firewall port 5000 is open!
echo.
start http://localhost:5000
python run.py --public
goto :end

:stop
echo.
echo   Searching for Python processes...
for /f "tokens=2" %%a in ('tasklist ^| findstr /i "python.exe"') do (
    echo   Killing python.exe PID=%%a
    taskkill /F /PID %%a >nul 2>&1
)
echo   Server process terminated.
pause
goto :end

:status
echo.
echo   --- Server Status ---
tasklist 2>nul | findstr /i "python.exe" >nul
if %errorlevel% equ 0 (
    echo   Server: RUNNING
    tasklist | findstr /i "python.exe"
    echo.
    echo   Local:  http://localhost:5000
    echo   Remote: http://%LOCAL_IP%:5000
) else (
    echo   Server: STOPPED
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

:rebuild
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

:partner_info
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
pause
goto :end

:distribute
echo.
echo   Packaging project (excluding node_modules, .git, __pycache__)...
set "PACKAGE_NAME=edu-mgmt-dist.zip"
set "PACKAGE_DIR=%PROJECT_DIR%..\edu-mgmt-dist"

if exist "%PACKAGE_DIR%" rmdir /s /q "%PACKAGE_DIR%"
mkdir "%PACKAGE_DIR%"

robocopy "%PROJECT_DIR%" "%PACKAGE_DIR%" /E /NFL /NDL /NJH /NJS /XD node_modules __pycache__ .git .claude .vscode .idea /XF *.pyc *.bak .env >nul
if %errorlevel% geq 8 (
    echo   Warning: some copy errors, continuing...
)

:: Replace config.ini with clean template
if exist "%PACKAGE_DIR%\backend\config\config.ini" del "%PACKAGE_DIR%\backend\config\config.ini"
if exist "%PACKAGE_DIR%\backend\config\config.ini.example" (
    copy "%PACKAGE_DIR%\backend\config\config.ini.example" "%PACKAGE_DIR%\backend\config\config.ini" >nul
)

:: Zip
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

:end
endlocal
