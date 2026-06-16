@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title EduMgmt System - Quick Start
cd /d "%~dp0"

echo.
echo ============================================================
echo   EduMgmt System v3.0 - Quick Start
echo ============================================================
echo.

:: ───────── 1. Check Python ─────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Download: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo Python: %%v

:: ───────── 2. Check/Fix config.ini ─────────
if not exist "backend\config\config.ini" (
    echo Creating backend\config\config.ini from template...
    copy "backend\config\config.ini.example" "backend\config\config.ini" >nul
    echo Edit backend\config\config.ini to set your database password if needed.
)

:: ───────── 3. Generate my.ini.auto with correct paths ─────────
if not exist "mysql-portable\my.ini" (
    echo [ERROR] mysql-portable\my.ini not found.
    pause
    exit /b 1
)

pushd mysql-portable
set "MYSQL_DIR=%CD%"
set "AUTO_INI=%MYSQL_DIR%\my.ini.auto"
> "%AUTO_INI%" (
    for /f "usebackq delims=" %%l in ("my.ini") do (
        set "line=%%l"
        set "line=!line:CURRENT_DIR=%MYSQL_DIR%!"
        set "line=!line:CURRENT_DIR\data=%MYSQL_DIR%\data!"
        echo !line!
    )
)

:: ───────── 4. First-time init: create data directory if missing ─────────
if not exist "data\" (
    echo.
    echo ============================================================
    echo   First-time setup: initializing MySQL database...
    echo   This runs once. Please wait ~10 seconds.
    echo ============================================================
    echo.

    mkdir data

    :: Initialize fresh InnoDB data directory (no root password)
    .\bin\mysqld.exe --defaults-file="%AUTO_INI%" --initialize-insecure --console
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] MySQL initialization failed.
        pause
        popd
        exit /b 1
    )
    echo MySQL data directory created.

    :: Start MySQL temporarily (foreground, in background window)
    start "EduMgmt MySQL Init" /MIN .\bin\mysqld.exe --defaults-file="%AUTO_INI%" --console

    :: Wait for it to be ready
    set "ATTEMPTS=0"
    :wait_init
    timeout /t 1 /nobreak >nul
    set /a ATTEMPTS+=1
    .\bin\mysql.exe -u root --protocol=TCP -e "SELECT 1;" 2>nul | findstr "1" >nul
    if %errorlevel% equ 0 goto :mysql_init_ready
    if !ATTEMPTS! geq 30 (
        echo [ERROR] MySQL failed to start after init.
        taskkill /FI "WINDOWTITLE eq EduMgmt MySQL Init" /F 2>nul
        pause
        popd
        exit /b 1
    )
    goto :wait_init

    :mysql_init_ready
    echo MySQL started, importing database...

    :: Set root password to match config.ini
    .\bin\mysql.exe -u root --protocol=TCP -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'Cairenbin2005'; FLUSH PRIVILEGES;" 2>nul

    :: Import DDL with UTF-8
    pushd ..
    type backend\config\init_database_mysql.sql | .\mysql-portable\bin\mysql.exe -u root -pCairenbin2005 --default-character-set=utf8mb4 2>nul
    if %errorlevel% neq 0 (
        echo [WARNING] DDL import may have errors. Check MySQL window.
    ) else (
        echo Database imported successfully.
    )
    popd

    :: Enable binary logging (needed for RESET MASTER on distribute)
    .\bin\mysql.exe -u root -pCairenbin2005 --protocol=TCP -e "RESET MASTER;" 2>nul

    :: Stop the temp instance
    .\bin\mysqladmin.exe -u root -pCairenbin2005 --protocol=TCP shutdown 2>nul
    timeout /t 2 /nobreak >nul
    taskkill /FI "WINDOWTITLE eq EduMgmt MySQL Init" /F 2>nul

    echo.
    echo ============================================================
    echo   First-time setup complete!
    echo ============================================================
    echo.
)

popd

:: ───────── 5. Start MySQL (foreground, no admin) ─────────
echo Starting MySQL...
pushd mysql-portable
start "EduMgmt MySQL" /MIN .\bin\mysqld.exe --defaults-file="%AUTO_INI%" --console
popd

:: Wait for MySQL
echo Waiting for MySQL to become ready...
set "ATTEMPTS=0"
:wait_mysql
timeout /t 1 /nobreak >nul
set /a ATTEMPTS+=1
"mysql-portable\bin\mysql.exe" -u root -pCairenbin2005 --protocol=TCP -e "SELECT 1;" 2>nul | findstr "1" >nul
if %errorlevel% equ 0 goto :mysql_ready
if %ATTEMPTS% geq 20 (
    echo [WARNING] MySQL did not start within 20 seconds.
    echo Check the MySQL window for errors.
)
goto :wait_mysql

:mysql_ready
echo MySQL is ready.

:: ───────── 6. Install Python deps ─────────
echo Checking Python dependencies...
pip show Flask >nul 2>&1 && pip show SQLAlchemy >nul 2>&1 && pip show PyMySQL >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    pip install Flask flask-cors PyJWT
)

:: ───────── 7. Start Flask ─────────
echo Starting Flask server...
start "EduMgmt Flask" python run.py

:: ───────── Done ─────────
echo.
echo ============================================================
echo   Setup complete!
echo.
echo   Open http://localhost:5000 in your browser
echo.
echo   Accounts:
echo     admin  / 123456
echo     T001   / 123456 (teacher)
echo     STU001 / 123456 (student)
echo ============================================================
echo.
echo Close this window to stop the application.
echo Or run server_control.bat [3] to stop.
pause >nul
endlocal
