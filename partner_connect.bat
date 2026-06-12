@echo off
setlocal enabledelayedexpansion
title EduMgmt - Partner Connect Setup

echo.
echo   +--------------------------------------------------+
echo   |  EduMgmt System - Partner Connection Setup       |
echo   +--------------------------------------------------+
echo.
echo   This tool configures your frontend dev environment
echo   to connect to the host's backend API.
echo.
echo   Choose connection type:
echo   [1] LAN/local network (direct IP)
echo   [2] Internet/remote (ngrok URL or hostname)
echo.

set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

set /p CONN_TYPE="Select [1-2]: "

if "%CONN_TYPE%"=="1" goto :lan
if "%CONN_TYPE%"=="2" goto :remote
echo Invalid option, defaulting to LAN
goto :lan

:: =================================================================
:lan
:: =================================================================
echo.
echo [LAN MODE] Enter the host server's local IP address
echo.
echo   Ask your partner (the person running the server) for their IP.
echo   They can run server_control.bat and select [6] to see it.
echo.
set /p HOST_ADDR="Host IP (e.g. 192.168.1.100): "
if "%HOST_ADDR%"=="" (
    echo   No IP entered, using localhost
    set "HOST_ADDR=localhost"
)
goto :config

:: =================================================================
:remote
:: =================================================================
echo.
echo [INTERNET MODE] Enter the ngrok URL or hostname
echo.
echo   The host should run 'ngrok http 5000' and share the public URL.
echo   It looks like: https://xxxx-xx-xx-xxx-xx.ngrok-free.app
echo.
echo   You can also enter any hostname or IP:port like:
echo     myserver.example.com:5000
echo     12.34.56.78:5000
echo.
set /p HOST_ADDR="Host URL or hostname:port: "
if "%HOST_ADDR%"=="" (
    echo   No address entered, aborting.
    pause
    goto :end
)
:: Strip protocol prefix if present
set "HOST_ADDR=%HOST_ADDR:https://=%"
set "HOST_ADDR=%HOST_ADDR:http://=%"
:: Remove trailing slash
if "%HOST_ADDR:~-1%"=="/" set "HOST_ADDR=%HOST_ADDR:~0,-1%"

:: Determine protocol - ngrok URLs use https
echo %HOST_ADDR% | findstr /i "ngrok" >nul
if %errorlevel% equ 0 (
    set "PROTO=https"
) else (
    set "PROTO=http"
)
set "FULL_URL=!PROTO!://%HOST_ADDR%"
goto :config

:: =================================================================
:config
:: =================================================================
echo   Target: !PROTO!://%HOST_ADDR%

:: =================================================================
:: Configure Vite proxy
:: =================================================================
echo.
echo   Configuring frontend API proxy target...

:: Determine if it's just IP (no port specified) and append :5000
echo %HOST_ADDR% | findstr ":" >nul
if %errorlevel% neq 0 (
    :: No port specified, assume 5000
    set "HOST_ADDR=%HOST_ADDR%:5000"
)

:: For LAN: always http. For remote: may be https (ngrok)
if "%CONN_TYPE%"=="1" (
    set "API_TARGET=http://%HOST_ADDR%"
) else (
    if "!PROTO!"=="https" (
        set "API_TARGET=https://%HOST_ADDR%"
    ) else (
        set "API_TARGET=http://%HOST_ADDR%"
    )
)

echo VITE_API_TARGET=!API_TARGET! > frontend\.env.local
echo   Created: frontend\.env.local
echo   VITE_API_TARGET=!API_TARGET!

:: =================================================================
:: Verify connectivity (skip for LAN ping since ngrok URLs may not respond to ping)
:: =================================================================
echo.
echo   Checking host reachability...

if "%CONN_TYPE%"=="1" (
    :: Extract just the IP from IP:port for ping
    for /f "tokens=1 delims=:" %%a in ("%HOST_ADDR%") do set "PING_HOST=%%a"
    ping -n 1 -w 2000 !PING_HOST! >nul 2>&1
    if %errorlevel% equ 0 (
        echo   ping !PING_HOST! - OK
    ) else (
        echo   [WARNING] ping !PING_HOST! failed
        echo   Check that both computers are on the same network.
    )
) else (
    echo   Skipping ping check for remote URL
    echo   To verify: open !API_TARGET! in your browser
)

:: =================================================================
:: Test API
:: =================================================================
echo.
echo   Testing API connectivity...
curl -s -o nul -w "%%{http_code}" "!API_TARGET!/api/auth/login" --connect-timeout 5 2>nul | findstr "200 401 404" >nul
if %errorlevel% equ 0 (
    echo   API reachable at !API_TARGET! - OK
) else (
    echo   [WARNING] Could not reach API at !API_TARGET!
    echo   This is normal if the server is not running yet.
    echo   Make sure the host has started the server first.
)

:: =================================================================
:: Summary
:: =================================================================
echo.
echo   +--------------------------------------------------+
echo   |  Connection Summary                              |
echo   +--------------------------------------------------+
echo   |                                                  |
echo   |  Option A: Browser (no install needed)           |
echo   |    !API_TARGET!                                 |
echo   |                                                  |
echo   |  Option B: Frontend dev (hot reload)             |
echo   |    cd frontend                                   |
echo   |    npm run dev                                   |
echo   |    Open http://localhost:5173                    |
echo   |    All API calls proxy to host                   |
echo   |                                                  |
echo   |  Accounts:                                       |
echo   |    admin  / 123456                               |
echo   |    T001   / 123456  (teacher)                    |
echo   |    STU001 / 123456  (student)                    |
echo   +--------------------------------------------------+
echo.

set /p START_NOW="Launch frontend dev server now? (Y/N): "
if /i "!START_NOW!"=="Y" (
    echo Starting npm run dev ...
    cd frontend
    call npm run dev
)

:end
pause
endlocal
