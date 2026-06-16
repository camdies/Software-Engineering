@echo off
setlocal enabledelayedexpansion
title EduMgmt Server Control Panel
cd /d "%~dp0"

set "LOCAL_IP="
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "127.0.0.1" 2^>nul') do (
    for /f "tokens=*" %%b in ("%%a") do if "%LOCAL_IP%"=="" set "LOCAL_IP=%%b"
)
if "%LOCAL_IP%"=="" set "LOCAL_IP=unknown"

:menu
cls
echo ============================================================
echo   EduMgmt System v3.0 - Server Control Panel
echo ============================================================
echo.
echo   LAN IP : %LOCAL_IP%
echo   Project: %CD%
echo.
echo   [1] Start server (localhost)
echo   [2] Start server (LAN public)
echo   [3] Stop server
echo   [4] View status
echo   [5] Rebuild frontend and start
echo.
echo   [D] Start MySQL
echo   [E] Stop MySQL
echo.
echo   [6] Partner info
echo   [7] Package for partner
echo.
echo   [0] Exit
echo --------------------------------------------------
echo.

set "CHOICE="
set /p CHOICE="Select: "

if "%CHOICE%"=="1"  goto :start_local
if "%CHOICE%"=="2"  goto :start_public
if "%CHOICE%"=="3"  goto :stop_all
if "%CHOICE%"=="4"  goto :status
if "%CHOICE%"=="5"  goto :rebuild
if "%CHOICE%"=="6"  goto :partner_info
if "%CHOICE%"=="7"  goto :distribute
if /i "%CHOICE%"=="D" goto :mysql_start
if /i "%CHOICE%"=="E" goto :mysql_stop
if "%CHOICE%"=="0"  goto :end
echo Unknown option.
pause
goto :menu

:: =================================================================
:mysql_start
cls
echo === MySQL Start ===
echo.

echo [1/2] Checking service status...
sc query MySQL-EduMgmt 2>nul | findstr RUNNING >nul
if %errorlevel% equ 0 (
    echo MySQL-EduMgmt already running.
    pause
    goto :menu
)

:: Try net start existing services
net start MySQL-EduMgmt 2>nul
if %errorlevel% equ 0 (
    echo MySQL-EduMgmt started.
    pause
    goto :menu
)

net start MySQL80 2>nul
if %errorlevel% equ 0 (
    echo MySQL80 started.
    pause
    goto :menu
)

:: Try installing from mysql-portable
if not exist "mysql-portable\bin\mysqld.exe" (
    echo mysql-portable\ not found. See MYSQL_SETUP_GUIDE.md.
    pause
    goto :menu
)

echo [2/2] Installing MySQL-EduMgmt service from mysql-portable...
pushd mysql-portable
set "MYSQL_DIR=%CD%"
.\bin\mysqld.exe --install MySQL-EduMgmt --defaults-file="%MYSQL_DIR%\my.ini" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo Install failed. You need Administrator privileges.
    echo Right-click server_control.bat ^> Run as Administrator.
    popd
    pause
    goto :menu
)
net start MySQL-EduMgmt 2>nul
if %errorlevel% equ 0 (
    echo MySQL-EduMgmt installed and started.
) else (
    echo Service installed but failed to start. Check my.ini paths.
)
popd
pause
goto :menu

:: =================================================================
:mysql_stop
cls
echo Stopping MySQL...
net stop MySQL-EduMgmt 2>nul
net stop MySQL80 2>nul
net stop MariaDB 2>nul
echo Done.
pause
goto :menu

:: =================================================================
:start_local
cls
echo === Start Server (localhost) ===
echo.
sc query MySQL-EduMgmt 2>nul | findstr RUNNING >nul
if %errorlevel% neq 0 (
    sc query MySQL80 2>nul | findstr RUNNING >nul
    if %errorlevel% neq 0 (
        echo [WARNING] MySQL is not running.
        echo Server will fail to connect to database!
        echo.
    )
)
echo Starting Flask at http://localhost:5000 ...
start "EduMgmt Flask" python run.py
echo Done.
pause
goto :menu

:: =================================================================
:start_public
cls
echo === Start Server (LAN Public) ===
echo.
sc query MySQL-EduMgmt 2>nul | findstr RUNNING >nul
if %errorlevel% neq 0 (
    sc query MySQL80 2>nul | findstr RUNNING >nul
    if %errorlevel% neq 0 (
        echo [WARNING] MySQL is not running.
        echo Server will fail to connect to database!
        echo.
    )
)
echo Opening firewall port 5000...
netsh advfirewall firewall add rule name="EduMgmt Flask 5000" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1
echo.
echo   Local : http://localhost:5000
echo   LAN   : http://%LOCAL_IP%:5000
echo.
start "EduMgmt Flask" python run.py --public
echo Done.
pause
goto :menu

:: =================================================================
:stop_all
echo Stopping Flask...
taskkill /FI "IMAGENAME eq python.exe" /F 2>nul
echo Done.
pause
goto :menu

:: =================================================================
:status
cls
echo === Status ===
echo.
tasklist 2>nul | findstr python.exe >nul && echo Flask : RUNNING || echo Flask : STOPPED
sc query MySQL-EduMgmt 2>nul | findstr RUNNING >nul && echo MySQL-EduMgmt : RUNNING
sc query MySQL80       2>nul | findstr RUNNING >nul && echo MySQL80 : RUNNING
sc query MariaDB       2>nul | findstr RUNNING >nul && echo MariaDB : RUNNING
echo.
netsh advfirewall firewall show rule name="EduMgmt Flask 5000" 2>nul | findstr Enabled >nul && echo Firewall : Port 5000 OPEN || echo Firewall : Port 5000 NO RULE
echo LAN IPv4 : %LOCAL_IP%
echo.
pause
goto :menu

:: =================================================================
:rebuild
cls
echo Building frontend...
cd frontend
call npm run build
cd ..
echo Starting server (public)...
start "EduMgmt Flask" python run.py --public
echo Done.
pause
goto :menu

:: =================================================================
:partner_info
cls
echo.
echo   LAN:  http://%LOCAL_IP%:5000
echo.
echo   Accounts:
echo     admin  / 123456
echo     T001   / 123456 (teacher)
echo     STU001 / 123456 (student)
echo.
pause
goto :menu

:: =================================================================
:distribute
cls
echo Packaging project (excluding node_modules, .git, mysql-portable)...
set "PKG=%CD%\..\edu-mgmt-dist"
if exist "%PKG%" rmdir /s /q "%PKG%"
robocopy "%CD%" "%PKG%" /E /NFL /NDL /NJH /NJS /XD node_modules __pycache__ .git .claude .vscode .idea mysql-portable /XF *.pyc *.bak .env >nul
if exist "%PKG%\backend\config\config.ini" del "%PKG%\backend\config\config.ini"
if exist "%PKG%\backend\config\config.ini.example" copy "%PKG%\backend\config\config.ini.example" "%PKG%\backend\config\config.ini" >nul
powershell -Command "Compress-Archive -Path '%PKG%\*' -DestinationPath '%CD%\..\edu-mgmt-dist.zip' -Force" 2>nul
rmdir /s /q "%PKG%"
echo Done: ..\edu-mgmt-dist.zip
pause
goto :menu

:: =================================================================
:end
endlocal
