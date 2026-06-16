@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "MYSQL_DIR=%CD%"
set "AUTO_INI=%MYSQL_DIR%\my.ini.auto"

> "%AUTO_INI%" (
    for /f "usebackq delims=" %%l in ("%MYSQL_DIR%\my.ini") do (
        set "line=%%l"
        set "line=!line:CURRENT_DIR=%MYSQL_DIR%!"
        set "line=!line:CURRENT_DIR\data=%MYSQL_DIR%\data!"
        echo !line!
    )
)

:: Auto-init if data/ missing
if not exist "data\" (
    echo Data directory not found. Running first-time init...
    mkdir data
    .\bin\mysqld.exe --defaults-file="%AUTO_INI%" --initialize-insecure --console
    if %errorlevel% neq 0 (
        echo [ERROR] MySQL init failed.
        pause
        exit /b 1
    )
    echo Init OK. Starting temp instance to import DB...
    start "EduMgmt MySQL Init" /MIN .\bin\mysqld.exe --defaults-file="%AUTO_INI%" --console
    set "AT=0"
    :wait_init_local
    timeout /t 1 /nobreak >nul
    set /a AT+=1
    if !AT! geq 30 (
        taskkill /FI "WINDOWTITLE eq EduMgmt MySQL Init" /F 2>nul
        echo [ERROR] MySQL failed to start.
        pause
        exit /b 1
    )
    .\bin\mysql.exe -u root --protocol=TCP -e "SELECT 1;" 2>nul | findstr "1" >nul || goto :wait_init_local
    .\bin\mysql.exe -u root --protocol=TCP -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'Cairenbin2005'; FLUSH PRIVILEGES;" 2>nul
    chcp 65001 >nul
    pushd ..
    type backend\config\init_database_mysql.sql | .\mysql-portable\bin\mysql.exe -u root -pCairenbin2005 --default-character-set=utf8mb4 2>nul
    popd
    chcp 936 >nul
    .\bin\mysqladmin.exe -u root -pCairenbin2005 --protocol=TCP shutdown 2>nul
    timeout /t 2 /nobreak >nul
    echo First-time setup complete.
    echo.
)

echo MySQL base dir: %MYSQL_DIR%
echo.

if /i "%1"=="--install" goto :install
if /i "%1"=="-i" goto :install

echo Starting MySQL in foreground mode (no admin needed)...
echo Press Ctrl+C to stop.
echo.
.\bin\mysqld.exe --defaults-file="%AUTO_INI%" --console
goto :end

:install
echo Installing MySQL-EduMgmt as Windows service (admin required)...
echo.
.\bin\mysqld.exe --install MySQL-EduMgmt --defaults-file="%AUTO_INI%" 2>nul
if %errorlevel% neq 0 (
    echo Install failed. Right-click ^> Run as Administrator.
    echo Or run without --install for foreground mode.
    pause
    exit /b 1
)
net start MySQL-EduMgmt
if %errorlevel% neq 0 (
    echo Service installed but failed to start.
    echo Check port 3306 already in use?
)
echo Done.

:end
endlocal
