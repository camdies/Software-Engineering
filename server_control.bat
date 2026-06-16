@echo off
chcp 65001 >nul
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
echo   [D] Start MySQL (service, admin)
echo   [F] Start MySQL (foreground, no admin)
echo   [E] Stop MySQL
echo.
echo   [6] Partner info
echo   [7] Package for partner (inc. mysql-portable)
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
if /i "%CHOICE%"=="F" goto :mysql_foreground
if /i "%CHOICE%"=="E" goto :mysql_stop
if "%CHOICE%"=="0"  goto :end
echo Unknown option.
pause
goto :menu

:: =================================================================
:mysql_foreground
cls
echo === MySQL Start (Foreground, No Admin) ===
echo.
if not exist "mysql-portable\bin\mysqld.exe" (
    echo mysql-portable\ not found.
    pause
    goto :menu
)

"mysql-portable\bin\mysqladmin.exe" -u root --protocol=TCP ping 2>nul | findstr "alive" >nul
if %errorlevel% equ 0 (
    echo MySQL already running.
    pause
    goto :menu
)

pushd mysql-portable
set "MYSQL_DIR=%CD%"
set "AUTO_INI=%MYSQL_DIR%\my.ini.auto"
> "%AUTO_INI%" (
    for /f "usebackq delims=" %%l in ("my.ini") do (
        set "line=%%l"
        set "line=!line:CURRENT_DIR=%MYSQL_DIR%!"
        echo !line!
    )
)
echo Starting MySQL in foreground window...
:: Write temp launcher bat to avoid nested-quote hell
> "%MYSQL_DIR%\_run_mysql.bat" (
    echo @echo off
    echo chcp 65001 ^>nul
    echo cd /d "%MYSQL_DIR%"
    echo start "EduMgmt MySQL" /MIN "%MYSQL_DIR%\bin\mysqld.exe" --defaults-file="%AUTO_INI%" --console
)
call "%MYSQL_DIR%\_run_mysql.bat"
del "%MYSQL_DIR%\_run_mysql.bat" 2>nul
popd

echo Waiting for MySQL...
set "ATTEMPTS=0"
:wait_mysql_fg
timeout /t 1 /nobreak >nul
set /a ATTEMPTS+=1
"mysql-portable\bin\mysqladmin.exe" -u root --protocol=TCP ping 2>nul | findstr "alive" >nul
if %errorlevel% equ 0 goto :mysql_fg_ready
if %ATTEMPTS% geq 20 goto :mysql_fg_timeout
goto :wait_mysql_fg

:mysql_fg_ready
echo MySQL is ready (foreground mode).
pause
goto :menu

:mysql_fg_timeout
echo MySQL did not start within 20s. Check the MySQL window.
pause
goto :menu

:: =================================================================
:mysql_start
cls
echo === MySQL Start (Service, Admin Required) ===
echo.

echo Checking service status...
sc query MySQL-EduMgmt 2>nul | findstr RUNNING >nul
if %errorlevel% equ 0 (
    echo MySQL-EduMgmt already running.
    pause
    goto :menu
)

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

if not exist "mysql-portable\bin\mysqld.exe" (
    echo mysql-portable\ not found. See MYSQL_SETUP_GUIDE.md.
    pause
    goto :menu
)

echo Installing MySQL-EduMgmt service from mysql-portable...
pushd mysql-portable
set "MYSQL_DIR=%CD%"
set "AUTO_INI=%MYSQL_DIR%\my.ini.auto"
> "%AUTO_INI%" (
    for /f "usebackq delims=" %%l in ("my.ini") do (
        set "line=%%l"
        set "line=!line:CURRENT_DIR=%MYSQL_DIR%!"
        echo !line!
    )
)
.\bin\mysqld.exe --install MySQL-EduMgmt --defaults-file="%AUTO_INI%" 2>nul
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
taskkill /FI "WINDOWTITLE eq EduMgmt MySQL" /F 2>nul
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
    "mysql-portable\bin\mysqladmin.exe" -u root --protocol=TCP ping 2>nul | findstr "alive" >nul
    if %errorlevel% neq 0 (
        echo [WARNING] MySQL is not running.
        echo Start it first: [D] or [F] from main menu.
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
    "mysql-portable\bin\mysqladmin.exe" -u root --protocol=TCP ping 2>nul | findstr "alive" >nul
    if %errorlevel% neq 0 (
        echo [WARNING] MySQL is not running.
        echo Start it first: [D] or [F] from main menu.
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
echo Stopping all EduMgmt processes...
taskkill /FI "WINDOWTITLE eq EduMgmt Flask" /F 2>nul
taskkill /FI "WINDOWTITLE eq EduMgmt MySQL" /F 2>nul
echo Done.
pause
goto :menu

:: =================================================================
:status
cls
echo === Status ===
echo.
tasklist 2>nul | findstr "EduMgmt" >nul && echo EduMgmt processes : RUNNING || echo EduMgmt processes : STOPPED
sc query MySQL-EduMgmt 2>nul | findstr RUNNING >nul && echo MySQL-EduMgmt     : RUNNING
sc query MySQL80       2>nul | findstr RUNNING >nul && echo MySQL80            : RUNNING
sc query MariaDB       2>nul | findstr RUNNING >nul && echo MariaDB            : RUNNING
"mysql-portable\bin\mysqladmin.exe" -u root --protocol=TCP ping 2>nul | findstr "alive" >nul && echo MySQL foreground   : RUNNING
echo.
netsh advfirewall firewall show rule name="EduMgmt Flask 5000" 2>nul | findstr Enabled >nul && echo Firewall          : Port 5000 OPEN || echo Firewall          : Port 5000 NO RULE
echo LAN IPv4         : %LOCAL_IP%
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
echo ============================================================
echo   Package for Partner Distribution
echo ============================================================
echo.
echo This creates a self-contained zip that partners can unzip
echo and run with double-click on start_all.bat.
echo.
echo What is included:
echo   - Full project source (backend + frontend)
echo   - mysql-portable with pre-loaded database
echo   - start_all.bat (one-click launch)
echo.

set /p CONFIRM="Continue? (Y/N): "
if /i not "%CONFIRM%"=="Y" goto :menu

echo.
echo [1/3] Purging machine-specific data from mysql-portable...
if exist "mysql-portable\data\auto.cnf" del "mysql-portable\data\auto.cnf"
for %%f in ("mysql-portable\data\*.err") do if exist "%%f" del "%%f"
if exist "mysql-portable\my.ini.auto" del "mysql-portable\my.ini.auto"
pushd mysql-portable
if exist "data\" (
    .\bin\mysqladmin.exe -u root --protocol=TCP ping 2>nul | findstr "alive" >nul
    if %errorlevel% equ 0 (
        .\bin\mysql.exe -u root --protocol=TCP -e "RESET MASTER;" 2>nul
        .\bin\mysql.exe -u root --protocol=TCP -e "FLUSH LOGS;" 2>nul
        echo Binary logs purged.
    ) else (
        echo MySQL not running, skipping binary log purge.
    )
)
popd

echo.
echo [2/3] Copying project files...
set "PKG=%CD%\..\edu-mgmt-dist"
if exist "%PKG%" rmdir /s /q "%PKG%"
robocopy "%CD%" "%PKG%" /E /NFL /NDL /NJH /NJS /XD node_modules __pycache__ .git .claude .vscode .idea /XF *.pyc *.bak .env >nul
if exist "%PKG%\backend\config\config.ini" del "%PKG%\backend\config\config.ini"
if exist "%PKG%\backend\config\config.ini.example" copy "%PKG%\backend\config\config.ini.example" "%PKG%\backend\config\config.ini" >nul
echo Copy complete.

echo.
echo [3/3] Creating zip archive...
powershell -Command "Compress-Archive -Path '%PKG%\*' -DestinationPath '%CD%\..\edu-mgmt-dist.zip' -Force" 2>nul
rmdir /s /q "%PKG%"
echo.
echo ============================================================
echo   Done: ..\edu-mgmt-dist.zip
echo.
echo   Partner instructions:
echo     1. Unzip to any directory
echo     2. Install Python 3.11+ (one-time)
echo     3. Double-click start_all.bat
echo     4. Open http://localhost:5000
echo ============================================================
pause
goto :menu

:: =================================================================
:end
endlocal
