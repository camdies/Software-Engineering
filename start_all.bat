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

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Download: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo Python: %%v

:: Check/Fix my.ini paths
if not exist "mysql-portable\my.ini" (
    echo [ERROR] mysql-portable\my.ini not found.
    pause
    exit /b 1
)

echo Generating mysql-portable\my.ini.auto with current paths...
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
popd

:: Start MySQL (foreground, no admin)
echo Starting MySQL in foreground mode...
start "EduMgmt MySQL" /MIN cmd /c "cd /d \"%MYSQL_DIR%\" && \"%MYSQL_DIR%\bin\mysqld.exe\" --defaults-file=\"%AUTO_INI%\" --console"

:: Wait for MySQL to be ready
echo Waiting for MySQL to become ready...
set "ATTEMPTS=0"
:wait_mysql
timeout /t 1 /nobreak >nul
set /a ATTEMPTS+=1
"%MYSQL_DIR%\bin\mysqladmin.exe" -u root --protocol=TCP ping 2>nul | findstr "alive" >nul
if %errorlevel% equ 0 goto :mysql_ready
if %ATTEMPTS% geq 20 (
    echo [WARNING] MySQL did not start within 20 seconds.
    echo Please check the MySQL window for errors.
)
goto :wait_mysql

:mysql_ready
echo MySQL is ready.

:: Check/Fix config.ini
if not exist "backend\config\config.ini" (
    echo Creating backend\config\config.ini from template...
    copy "backend\config\config.ini.example" "backend\config\config.ini" >nul
    echo Edit backend\config\config.ini to configure database password if needed.
)

:: Install Python deps (skip if already installed)
echo Checking Python dependencies...
pip show Flask >nul 2>&1 && pip show SQLAlchemy >nul 2>&1 && pip show PyMySQL >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    pip install Flask flask-cors PyJWT
)

:: Start Flask
echo Starting Flask server...
start "EduMgmt Flask" python run.py

:: Done
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
