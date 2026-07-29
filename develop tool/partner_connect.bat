@echo off
setlocal enabledelayedexpansion
title EduMgmt - Partner Connect Setup

:top
cls
echo.
echo   +--------------------------------------------------+
echo   ^|  EduMgmt System - Partner Connection Setup       ^|
echo   +--------------------------------------------------+
echo.
echo   This tool configures VITE_API_TARGET so your
echo   local Vite dev server connects to the host.
echo.
echo   ---- CONNECTION TYPE ----
echo   [1] LAN / same campus network (IPv4: 192.168.x.x)
echo   [2] IPv6 direct (campus network, most common in China)
echo   [3] WAN / public hostname (port forward, frp, ngrok...)
echo.
echo   For Chinese campus networks: try IPv6 first.
echo   Ask the host to run server_control.bat [A] for their IPv6.
echo.
echo   [0] Exit
echo   +--------------------------------------------------+
echo.

set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

set /p CONN_TYPE="Select [0-3]: "

if "%CONN_TYPE%"=="0" goto :end
if "%CONN_TYPE%"=="1" goto :lan
if "%CONN_TYPE%"=="2" goto :ipv6
if "%CONN_TYPE%"=="3" goto :remote
echo Invalid, try again...
pause
goto :top

:: =================================================================
:lan
:: =================================================================
echo.
echo   [LAN MODE]
echo   Ask host for their IP (run server_control.bat, see the top line).
echo   Usually: 192.168.x.x  or  10.x.x.x
echo.
set /p HOST_ADDR="Host LAN IP: "
if "%HOST_ADDR%"=="" set "HOST_ADDR=localhost"
:: Ensure port
echo %HOST_ADDR% | findstr ":" >nul
if %errorlevel% neq 0 set "HOST_ADDR=%HOST_ADDR%:5000"
set "API_TARGET=http://%HOST_ADDR%"
goto :config

:: =================================================================
:ipv6
:: =================================================================
echo.
echo   [IPv6 MODE]  (recommended for Chinese campus networks)
echo.
echo   Host should run:  ipconfig ^| findstr "IPv6"
echo   Copy the address that does NOT start with fe80 or ::1
echo   Example: 2001:da8:1234:5678:1234:5678:abcd:ef01
echo.
echo   IMPORTANT: copy carefully, the address is long!
echo.
set /p HOST_ADDR="Host IPv6 address: "
if "%HOST_ADDR%"=="" echo No address, aborting. && pause && goto :top
:: Clean brackets if user typed them
set "HOST_ADDR=%HOST_ADDR:[=%"
set "HOST_ADDR=%HOST_ADDR:]=%"
:: Build URL: http://[ipv6]:5000
set "API_TARGET=http://[%HOST_ADDR%]:5000"
goto :config

:: =================================================================
:remote
:: =================================================================
echo.
echo   [WAN MODE]
echo   Enter the full hostname or IP:port, e.g.:
echo     12.34.56.78:5000
echo     myserver.example.com:5000
echo     https://xxxx.ngrok-free.app
echo.
set /p HOST_ADDR="Host address: "
if "%HOST_ADDR%"=="" echo No address, aborting. && pause && goto :top
:: Strip protocol
set "HOST_ADDR=%HOST_ADDR:https://=%"
set "HOST_ADDR=%HOST_ADDR:http://=%"
if "%HOST_ADDR:~-1%"=="/" set "HOST_ADDR=%HOST_ADDR:~0,-1%"
:: Determine http vs https
echo %HOST_ADDR% | findstr /i "ngrok" >nul
if %errorlevel% equ 0 (
    set "API_TARGET=https://%HOST_ADDR%"
) else (
    echo %HOST_ADDR% | findstr ":" >nul
    if %errorlevel% neq 0 set "HOST_ADDR=%HOST_ADDR%:5000"
    set "API_TARGET=http://%HOST_ADDR%"
)
goto :config

:: =================================================================
:config
:: =================================================================
echo.
echo   ---- Configuring ----
echo   Writing VITE_API_TARGET=!API_TARGET!
echo VITE_API_TARGET=!API_TARGET! > frontend\.env.local
echo   ^> frontend\.env.local created

:: =================================================================
:: Connectivity test
:: =================================================================
echo.
echo   ---- Testing connectivity ----
if "%CONN_TYPE%"=="1" (
    for /f "tokens=1 delims=:" %%a in ("%HOST_ADDR%") do ping -n 1 -w 2000 %%a >nul 2>&1
    if %errorlevel% equ 0 (echo   ping OK) else (echo   [WARN] ping failed - check network)
)
if "%CONN_TYPE%"=="2" (
    echo   Testing IPv6 TCP connection...
    curl -s -o nul --connect-timeout 5 "!API_TARGET!" 2>nul && echo   HTTP OK || echo   [WARN] cannot reach !API_TARGET! (ensure host server is running with [2])
)
if "%CONN_TYPE%"=="3" (
    echo   Testing HTTP...
    curl -s -o nul -w "HTTP %%{http_code}" --connect-timeout 5 "!API_TARGET!/api/auth/login" 2>nul
    echo.
)

:: =================================================================
:: Summary
:: =================================================================
echo.
echo   +--------------------------------------------------+
echo   ^|  SETUP COMPLETE                                  ^|
echo   +--------------------------------------------------+
echo   ^|                                                  ^|
echo   ^|  Browser (zero install):                         ^|
echo   ^|    !API_TARGET!                                 ^|
echo   ^|                                                  ^|
echo   ^|  Frontend dev (hot reload):                      ^|
echo   ^|    cd frontend ^&^& npm run dev                      ^|
echo   ^|    then open http://localhost:5173               ^|
echo   ^|                                                  ^|
echo   ^|  Accounts:                                       ^|
echo   ^|    admin  / 123456                               ^|
echo   ^|    T001   / 123456                               ^|
echo   ^|    STU001 / 123456                               ^|
echo   +--------------------------------------------------+
echo.

set /p START_NOW="Launch 'npm run dev' now? (Y/N): "
if /i "!START_NOW!"=="Y" (
    echo Starting npm run dev...
    start "EduMgmt Vite" cmd /c "cd frontend && npm run dev"
    echo Vite dev server starting in separate window.
)

echo.
echo   Press R to reconfigure, any other key to exit.
set /p AGAIN=""
if /i "!AGAIN!"=="R" goto :top

:end
endlocal
