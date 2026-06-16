@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "MYSQL_DIR=%CD%"
set "AUTO_INI=%MYSQL_DIR%\my.ini.auto"

:: Auto-generate my.ini.auto with current directory paths
> "%AUTO_INI%" (
    for /f "usebackq delims=" %%l in ("%MYSQL_DIR%\my.ini") do (
        set "line=%%l"
        set "line=!line:CURRENT_DIR=%MYSQL_DIR%!"
        set "line=!line:CURRENT_DIR\data=%MYSQL_DIR%\data!"
        echo !line!
    )
)

echo MySQL base dir: %MYSQL_DIR%
echo.

:: Parse argument: --foreground (default) or --install (admin required)
if /i "%1"=="--install" goto :install
if /i "%1"=="-i" goto :install

:: Default: foreground mode (no admin required)
echo Starting MySQL in foreground mode (no admin needed)...
echo Press Ctrl+C to stop.
echo.

.\bin\mysqld.exe --defaults-file="%AUTO_INI%" --console
goto :end

:install
echo Installing MySQL-EduMgmt as Windows service...
echo (Administrator privileges required)
echo.

.\bin\mysqld.exe --install MySQL-EduMgmt --defaults-file="%AUTO_INI%" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo Install failed. Try:
    echo   1. Right-click start_mysql.bat ^> Run as Administrator
    echo   2. Or just run without --install for foreground mode
    echo.
    pause
    exit /b 1
)
echo Service installed. Starting...
net start MySQL-EduMgmt
if %errorlevel% neq 0 (
    echo.
    echo Service installed but failed to start.
    echo Check: port 3306 already in use? my.ini paths correct?
    echo.
)
echo Done.

:end
endlocal
