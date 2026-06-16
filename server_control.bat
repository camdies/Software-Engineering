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

"mysql-portable\bin\mysqladmin.exe" -u root -pCairenbin2005 --protocol=TCP ping 2>nul | findstr "alive" >nul
if %errorlevel% equ 0 (
    echo MySQL already running.
    pause
    goto :menu
)

pushd mysql-portable
set "MYSQL_DIR=%CD%"
set "AUTO_INI=%MYSQL_DIR%\my.ini.auto"

:: First-time init if data/ missing
if not exist "data\" (
    echo Data directory not found. Running first-time init...
    echo.
    mkdir data
    .\bin\mysqld.exe --defaults-file="%AUTO_INI%" --initialize-insecure --console
    if %errorlevel% neq 0 (
        echo [ERROR] MySQL init failed.
        pause
        popd
        goto :menu
    )
    echo Init OK. Importing database...
    start "EduMgmt MySQL Init" /MIN .\bin\mysqld.exe --defaults-file="%AUTO_INI%" --console
    set "AT=0"
    :wait_init_fg
    timeout /t 1 /nobreak >nul
    set /a AT+=1
    if !AT! geq 30 (
        echo [ERROR] MySQL failed to start.
        taskkill /FI "WINDOWTITLE eq EduMgmt MySQL Init" /F 2>nul
        pause
        popd
        goto :menu
    )
    .\bin\mysql.exe -u root --protocol=TCP -e "SELECT 1;" 2>nul | findstr "1" >nul
    if %errorlevel% neq 0 goto :wait_init_fg
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

:: Generate my.ini.auto
> "%AUTO_INI%" (
    for /f "usebackq delims=" %%l in ("my.ini") do (
        set "line=%%l"
        set "line=!line:CURRENT_DIR=%MYSQL_DIR%!"
        echo !line!
    )
)
start "EduMgmt MySQL" /MIN .\bin\mysqld.exe --defaults-file="%AUTO_INI%" --console
popd

echo Waiting for MySQL...
set "ATTEMPTS=0"
:wait_mysql_fg
timeout /t 1 /nobreak >nul
set /a ATTEMPTS+=1
"mysql-portable\bin\mysql.exe" -u root -pCairenbin2005 --protocol=TCP -e "SELECT 1;" 2>nul | findstr "1" >nul
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
call :ensure_mysql
call :ensure_config

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
call :ensure_mysql
call :ensure_config

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
"mysql-portable\bin\mysqladmin.exe" -u root -pCairenbin2005 --protocol=TCP ping 2>nul | findstr "alive" >nul && echo MySQL foreground   : RUNNING
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
:ensure_mysql
"mysql-portable\bin\mysqladmin.exe" -u root -pCairenbin2005 --protocol=TCP ping 2>nul | findstr "alive" >nul
if %errorlevel% equ 0 exit /b

sc query MySQL-EduMgmt 2>nul | findstr RUNNING >nul
if %errorlevel% equ 0 exit /b

echo [INFO] MySQL is not running. Starting MySQL foreground...
pushd mysql-portable
set "MYSQL_DIR=%CD%"
set "AUTO_INI=%MYSQL_DIR%\my.ini.auto"

:: Auto-init if data/ missing
if not exist "data\" (
    mkdir data
    .\bin\mysqld.exe --defaults-file="%AUTO_INI%" --initialize-insecure --console
    if %errorlevel% neq 0 (
        echo [ERROR] MySQL init failed.
        popd
        exit /b 1
    )
    start "EduMgmt MySQL Init" /MIN .\bin\mysqld.exe --defaults-file="%AUTO_INI%" --console
    set "AT=0"
    :em_wait_init
    timeout /t 1 /nobreak >nul
    set /a AT+=1
    if !AT! geq 30 ( popd & echo [ERROR] MySQL failed to start. & exit /b 1 )
    .\bin\mysql.exe -u root --protocol=TCP -e "SELECT 1;" 2>nul | findstr "1" >nul || goto :em_wait_init
    .\bin\mysql.exe -u root --protocol=TCP -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'Cairenbin2005'; FLUSH PRIVILEGES;" 2>nul
    chcp 65001 >nul
    pushd ..
    type backend\config\init_database_mysql.sql | .\mysql-portable\bin\mysql.exe -u root -pCairenbin2005 --default-character-set=utf8mb4 2>nul
    popd
    chcp 936 >nul
    .\bin\mysqladmin.exe -u root -pCairenbin2005 --protocol=TCP shutdown 2>nul
    timeout /t 2 /nobreak >nul
)

> "%AUTO_INI%" (
    for /f "usebackq delims=" %%l in ("my.ini") do (
        set "line=%%l"
        set "line=!line:CURRENT_DIR=%MYSQL_DIR%!"
        echo !line!
    )
)
start "EduMgmt MySQL" /MIN .\bin\mysqld.exe --defaults-file="%AUTO_INI%" --console
popd

set "ATTEMPTS=0"
:em_wait
timeout /t 1 /nobreak >nul
set /a ATTEMPTS+=1
"mysql-portable\bin\mysql.exe" -u root -pCairenbin2005 --protocol=TCP -e "SELECT 1;" 2>nul | findstr "1" >nul
if %errorlevel% equ 0 exit /b
if %ATTEMPTS% geq 20 exit /b
goto :em_wait

:: =================================================================
:ensure_config
if not exist "backend\config\config.ini" (
    copy "backend\config\config.ini.example" "backend\config\config.ini" >nul
)
powershell -Command ^
  "$c = Get-Content 'backend\config\config.ini' -Raw; ^
   $c = $c -replace 'driver\s*=\s*mssql','driver = mysql'; ^
   $c = $c -replace 'port\s*=\s*1433','port = 3306'; ^
   $c = $c -replace 'password\s*=\s*.*','password = Cairenbin2005'; ^
   Set-Content 'backend\config\config.ini' -Value $c -NoNewline" 2>nul
exit /b

:: =================================================================
:distribute
cls
echo ============================================================
echo   Package for Partner Distribution
echo ============================================================
echo.
echo This creates a self-contained zip that partners unzip
echo and run with double-click on start_all.bat.
echo.
echo What is included:
echo   - Full project source (backend + frontend)
echo   - mysql-portable (portable MySQL, no data/)
echo   - start_all.bat (one-click launch, auto-init DB)
echo.

set /p CONFIRM="Continue? (Y/N): "
if /i not "%CONFIRM%"=="Y" goto :menu

echo.
echo [1/3] Purging machine-specific data...
if exist "mysql-portable\data\" (
    pushd mysql-portable
    .\bin\mysqladmin.exe -u root -pCairenbin2005 --protocol=TCP ping 2>nul | findstr "alive" >nul
    if %errorlevel% equ 0 (
        .\bin\mysql.exe -u root -pCairenbin2005 --protocol=TCP -e "RESET MASTER;" 2>nul
        .\bin\mysql.exe -u root -pCairenbin2005 --protocol=TCP -e "FLUSH LOGS;" 2>nul
        echo Binary logs purged.
    )
    popd
)
echo Done.

echo.
echo [2/3] Copying project files...
set "PKG=%CD%\..\edu-mgmt-dist"
if exist "%PKG%" rmdir /s /q "%PKG%"
robocopy "%CD%" "%PKG%" /E /NFL /NDL /NJH /NJS /XD node_modules __pycache__ .git .claude .vscode .idea /XF *.pyc *.bak .env >nul
rmdir /s /q "%PKG%\mysql-portable\data" 2>nul
del "%PKG%\mysql-portable\my.ini.auto" 2>nul
if exist "%PKG%\backend\config\config.ini" del "%PKG%\backend\config\config.ini"
if exist "%PKG%\backend\config\config.ini.example" copy "%PKG%\backend\config\config.ini.example" "%PKG%\backend\config\config.ini" >nul
echo Copy complete.

echo.
echo [3/3] Creating zip...
powershell -Command "Compress-Archive -Path '%PKG%\*' -DestinationPath '%CD%\..\edu-mgmt-dist.zip' -Force" 2>nul
rmdir /s /q "%PKG%"
echo.
echo   Done: ..\edu-mgmt-dist.zip
echo.
echo   Partner instructions:
echo     1. Unzip to any directory
echo     2. Install Python 3.11+ (one-time)
echo     3. Double-click start_all.bat
echo     4. Open http://localhost:5000
echo.
pause
goto :menu

:: =================================================================
:end
endlocal
