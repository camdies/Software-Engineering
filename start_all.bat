@echo off
setlocal enabledelayedexpansion
title EduMgmt System - Quick Start
cd /d "%~dp0"

echo.
echo  [ EduMgmt System v3.0 - Quick Start ]
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found in PATH.
    echo  Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo  Python: %%v

:: Check mysql-portable
if not exist "mysql-portable\my.ini" (
    echo  [ERROR] mysql-portable\my.ini not found.
    pause
    exit /b 1
)

:: Check / Fix config.ini -- always force driver=mysql + correct password
if not exist "backend\config\config.ini" (
    echo  Creating config.ini from template...
    copy "backend\config\config.ini.example" "backend\config\config.ini" >nul
)
echo  Fixing config.ini for MySQL...
powershell -Command ^
  "$c = Get-Content 'backend\config\config.ini' -Raw; ^
   $c = $c -replace 'driver\s*=\s*mssql','driver = mysql'; ^
   $c = $c -replace 'driver\s*=\s*mysql','driver = mysql'; ^
   $c = $c -replace 'password\s*=\s*.*','password = Cairenbin2005'; ^
   $c = $c -replace 'port\s*=\s*1433','port = 3306'; ^
   Set-Content 'backend\config\config.ini' -Value $c -NoNewline" 2>nul

:: Generate my.ini.auto with correct paths
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

:: First-time init if data/ missing
if not exist "data\" (
    echo.
    echo  [ First-time setup: initializing MySQL... ]
    echo  This runs once. Please wait about 10 seconds.
    echo.

    mkdir data
    .\bin\mysqld.exe --defaults-file="%AUTO_INI%" --initialize-insecure --console
    if %errorlevel% neq 0 (
        echo.
        echo  [ERROR] MySQL init failed.
        pause
        popd
        exit /b 1
    )
    echo  MySQL data directory created.

    start "EduMgmt MySQL Init" /MIN .\bin\mysqld.exe --defaults-file="%AUTO_INI%" --console

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
)

popd

:: Start MySQL
echo  Starting MySQL...
pushd mysql-portable
start "EduMgmt MySQL" /MIN .\bin\mysqld.exe --defaults-file="%AUTO_INI%" --console
popd

echo  Waiting for MySQL to become ready...
set "ATTEMPTS=0"
:wait_mysql
timeout /t 1 /nobreak >nul
set /a ATTEMPTS+=1
"mysql-portable\bin\mysql.exe" -u root -pCairenbin2005 --protocol=TCP -e "SELECT 1;" 2>nul | findstr "1" >nul
if %errorlevel% equ 0 goto :mysql_ready
if %ATTEMPTS% geq 20 (
    echo  [WARNING] MySQL did not start within 20 seconds.
)
goto :wait_mysql

:mysql_ready
echo  MySQL is ready.

:: Install Python deps
echo  Checking Python dependencies...
pip show Flask >nul 2>&1 && pip show SQLAlchemy >nul 2>&1 && pip show PyMySQL >nul 2>&1
if %errorlevel% neq 0 (
    echo  Installing Python dependencies...
    pip install -r requirements.txt
    pip install Flask flask-cors PyJWT
)

:: Start Flask
echo  Starting Flask server...
start "EduMgmt Flask" python run.py

:: Done
echo.
echo  [ Setup complete! ]
echo.
echo   Open http://localhost:5000 in your browser
echo.
echo   Accounts:
echo     admin  / 123456
echo     T001   / 123456 (teacher)
echo     STU001 / 123456 (student)
echo.
echo   Close this window to stop.
echo.
pause >nul
endlocal
