@echo off
setlocal enabledelayedexpansion
title EduMgmt System v3.0
cd /d "%~dp0"

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

if exist "%ROOT%\python-embed\python.exe" (
    set "PYTHON=%ROOT%\python-embed\python.exe"
    echo Using embedded Python
) else (
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        echo Python not found. Reinstall with Full Install.
        pause
        exit /b 1
    )
    set "PYTHON=python"
    echo Using system Python
)

if not exist "%ROOT%\frontend\dist\index.html" (
    echo Frontend files missing. Please reinstall.
    pause
    exit /b 1
)

if not exist "%ROOT%\backend\config\config.ini" (
    copy /Y "%ROOT%\backend\config\config.ini.example" "%ROOT%\backend\config\config.ini" >nul
)

echo ============================================================
echo   EduMgmt System v3.0
echo ============================================================

"!PYTHON!" "%ROOT%\start_mysql.py" "%ROOT%"
if !errorlevel! neq 0 (
    echo MySQL startup failed.
    pause
    exit /b 1
)

echo Checking database schema...
"!PYTHON!" "%ROOT%\run.py" --upgrade-db-only
if !errorlevel! neq 0 (
    echo Database schema upgrade failed. See logs for details.
    pause
    exit /b 1
)

echo.
echo Starting backend - http://localhost:5000
echo Press Ctrl+C to stop all services.
echo.

"!PYTHON!" "%ROOT%\run.py"

echo.
echo Shutting down MySQL...
taskkill /F /IM mysqld.exe 2>nul
echo All services stopped.
endlocal
