@echo off
setlocal enabledelayedexpansion
title EduMgmt System v3.0
cd /d "%~dp0"

echo.
echo  ============================================
echo    EduMgmt System v3.0 - Web ^|^| 教务管理系统
echo  ============================================
echo.
echo  [1] Quick Start ^(skip checks, start now^)
echo  [2] Auto Setup ^& Start ^(check deps, rebuild, start^)
echo  [3] Rebuild Frontend Only ^(npm build, then start^)
echo  [4] Exit
echo.
set /p "CHOICE=  Enter choice [1-4]: "

if "%CHOICE%"=="4" exit /b 0
if "%CHOICE%"=="3" goto :rebuild_frontend
if "%CHOICE%"=="2" goto :auto_setup
if "%CHOICE%"=="1" goto :quick_start

echo  Invalid choice.
pause
exit /b 1

:: ====================================================================
::  OPTION 2 — Auto Setup: check everything, install what's missing
:: ====================================================================
:auto_setup
echo.
echo  [Auto Setup] Checking prerequisites...

:: --- Check Python ---
call :check_python || exit /b 1
for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo    Python: %%v

:: --- Check Node.js ---
call :check_node || exit /b 1
for /f "tokens=2" %%v in ('node --version 2^>^&1') do echo    Node.js: %%v
for /f "tokens=2" %%v in ('npm --version 2^>^&1') do echo    npm: %%v

:: --- Check / install Python deps ---
echo.
echo  [Python] Checking dependencies...
pip show Flask >nul 2>&1 && pip show SQLAlchemy >nul 2>&1 && pip show PyMySQL >nul 2>&1
if %errorlevel% neq 0 (
    echo    Installing Python dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo    [ERROR] pip install failed.
        pause
        exit /b 1
    )
)
echo    Python deps OK.

:: --- Check / install Node deps ---
echo.
echo  [Frontend] Checking Node dependencies...
if not exist "frontend\node_modules\" (
    echo    Installing npm packages...
    pushd frontend
    call npm install
    if %errorlevel% neq 0 (
        echo    [ERROR] npm install failed.
        popd
        pause
        exit /b 1
    )
    popd
    echo    npm packages installed.
)

:: --- Check / rebuild frontend ---
echo.
echo  [Frontend] Building dist...
pushd frontend
call npm run build
if %errorlevel% neq 0 (
    echo    [ERROR] npm build failed.
    popd
    pause
    exit /b 1
)
popd
echo    Frontend dist ready.

goto :start_services

:: ====================================================================
::  OPTION 3 — Rebuild Frontend Only
:: ====================================================================
:rebuild_frontend
echo.
echo  [Frontend] Rebuilding...

call :check_node || exit /b 1

if not exist "frontend\node_modules\" (
    echo    Installing npm packages...
    pushd frontend
    call npm install
    popd
)
echo    Building...
pushd frontend
call npm run build
if %errorlevel% neq 0 (
    echo    [ERROR] npm build failed.
    popd
    pause
    exit /b 1
)
popd
echo    Frontend dist updated.

goto :start_services

:: ====================================================================
::  OPTION 1 — Quick Start (original behavior)
:: ====================================================================
:quick_start
echo.
echo  [Quick Start] Skipping dependency checks...

call :check_python || exit /b 1
for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo    Python: %%v

:: Check mysql-portable
if not exist "mysql-portable\my.ini" (
    echo    [ERROR] mysql-portable\my.ini not found.
    pause
    exit /b 1
)

:: Quick Python deps check
pip show Flask >nul 2>&1 && pip show SQLAlchemy >nul 2>&1 && pip show PyMySQL >nul 2>&1
if %errorlevel% neq 0 (
    echo    Installing Python dependencies...
    pip install -r requirements.txt
)

:: Quick frontend check — warn if dist missing
if not exist "frontend\dist\index.html" (
    echo.
    echo    [WARNING] frontend\dist\ not found. Flask will serve API only.
    echo    Run option [2] or [3] to rebuild the frontend.
    echo.
)

goto :start_services

:: ====================================================================
::  START SERVICES — shared across all options
:: ====================================================================
:start_services

:: --- Fix config.ini ---
if not exist "backend\config\config.ini" (
    echo  Creating config.ini from template...
    copy "backend\config\config.ini.example" "backend\config\config.ini" >nul
)
echo  Fixing config.ini for MySQL...
powershell -Command "$c=Get-Content 'backend\config\config.ini' -Raw; $c=$c -replace 'driver\s*=\s*mssql','driver = mysql'; $c=$c -replace 'password\s*=\s*.*','password = Cairenbin2005'; $c=$c -replace 'port\s*=\s*1433','port = 3306'; Set-Content 'backend\config\config.ini' -Value $c -NoNewline" 2>nul

:: --- Generate my.ini.auto + first-time MySQL init ---
pushd mysql-portable
set "MD=%CD%"
set "AINI=%MD%\my.ini.auto"

> "%AINI%" (
    for /f "usebackq delims=" %%l in ("my.ini") do (
        set "line=%%l"
        set "line=!line:CURRENT_DIR=%MD%!"
        set "line=!line:CURRENT_DIR\data=%MD%\data!"
        echo !line!
    )
)

if exist "data\" goto :skip_init

echo.
echo  [First-time setup: initializing MySQL...]
echo  This runs once. Please wait about 10 seconds.
echo.

mkdir data
.\bin\mysqld.exe --defaults-file="%AINI%" --initialize-insecure --console
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] MySQL init failed.
    pause
    popd
    exit /b 1
)
echo  MySQL data directory created.

start "EduMgmt MySQL Init" /MIN .\bin\mysqld.exe --defaults-file="%AINI%" --console

set "ATTEMPTS=0"
:wait_init
timeout /t 1 /nobreak >nul
set /a ATTEMPTS+=1
.\bin\mysql.exe -u root --protocol=TCP -e "SELECT 1;" 2>nul | findstr "1" >nul
if %errorlevel% equ 0 goto :mysql_init_ready
if !ATTEMPTS! geq 30 (
    echo  [ERROR] MySQL failed to start.
    taskkill /FI "WINDOWTITLE eq EduMgmt MySQL Init" /F 2>nul
    pause
    popd
    exit /b 1
)
goto :wait_init

:mysql_init_ready
echo  MySQL started. Importing database...

.\bin\mysql.exe -u root --protocol=TCP -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'Cairenbin2005'; FLUSH PRIVILEGES;" 2>nul

chcp 65001 >nul
pushd ..
type backend\config\init_database_mysql.sql | .\mysql-portable\bin\mysql.exe -u root -pCairenbin2005 --default-character-set=utf8mb4 2>nul
popd
chcp 936 >nul

echo  Database imported.

.\bin\mysqladmin.exe -u root -pCairenbin2005 --protocol=TCP shutdown 2>nul
timeout /t 2 /nobreak >nul
taskkill /FI "WINDOWTITLE eq EduMgmt MySQL Init" /F 2>nul

echo  First-time setup complete.
echo.

:skip_init
popd

:: --- Start MySQL ---
echo  Starting MySQL...
pushd mysql-portable
start "EduMgmt MySQL" /MIN .\bin\mysqld.exe --defaults-file="%AINI%" --console
popd

echo  Waiting for MySQL to become ready...
set "ATTEMPTS=0"
:wait_mysql
timeout /t 1 /nobreak >nul
set /a ATTEMPTS+=1
"mysql-portable\bin\mysql.exe" -u root -pCairenbin2005 --protocol=TCP -e "SELECT 1;" 2>nul | findstr "1" >nul
if %errorlevel% equ 0 goto :mysql_ready
if %ATTEMPTS% geq 20 goto :mysql_ready
goto :wait_mysql

:mysql_ready
echo  MySQL is ready.

:: --- Start Flask ---
echo  Starting Flask server...
start "EduMgmt Flask" python run.py

:: --- Done ---
echo.
echo  ============================================
echo    Setup complete!
echo.
echo    Open http://localhost:5000 in browser
echo.
echo    Accounts:
echo      admin  / 123456
echo      T001   / 123456  (teacher)
echo      STU001 / 123456  (student)
echo.
echo    Close this window to stop all services.
echo  ============================================
echo.
pause >nul
endlocal
exit /b 0

:: ====================================================================
::  SUBROUTINES
:: ====================================================================

:check_python
python --version >nul 2>&1
if %errorlevel% equ 0 exit /b 0
echo.
echo  [ERROR] Python not found in PATH.
echo  Download: https://www.python.org/downloads/
echo  ^(Check "Add Python to PATH" during install^)
echo.
pause
exit /b 1

:check_node
node --version >nul 2>&1
if %errorlevel% equ 0 exit /b 0
echo.
echo  [ERROR] Node.js not found in PATH.
echo  Download: https://nodejs.org/ ^(LTS version recommended^)
echo  ^(npm is included with Node.js^)
echo.
pause
exit /b 1
