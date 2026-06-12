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
echo   [1] LAN / same campus network (direct IP)
echo   [2] IPv6 direct (campus network IPv6)
echo   [3] Internet / WAN (public IP or hostname)
echo.
echo   For Chinese campus networks without public IPv4,
echo   try IPv6 first: ask the host for their IPv6 address.
echo.

set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

set /p CONN_TYPE="Select [1-3]: "

if "%CONN_TYPE%"=="1" goto :lan
if "%CONN_TYPE%"=="2" goto :ipv6
if "%CONN_TYPE%"=="3" goto :remote
echo Invalid option, defaulting to LAN
goto :lan

:: =================================================================
:lan
:: =================================================================
echo.
echo [LAN MODE] Enter the host server's local IP address
echo.
echo   Ask your partner for their LAN IP.
echo   They can run server_control.bat and select [6].
echo   Usually looks like: 192.168.x.x or 10.x.x.x
echo.
set /p HOST_ADDR="Host IP (e.g. 192.168.1.100): "
if "%HOST_ADDR%"=="" (
    echo   No IP entered, using localhost
    set "HOST_ADDR=localhost"
)
set "PROTO=http"
goto :config

:: =================================================================
:ipv6
:: =================================================================
echo.
echo [IPv6 MODE] Enter the host's IPv6 address
echo.
echo   Most Chinese campus networks assign public IPv6
echo   addresses to every device. This is the easiest
echo   way to get external access without any tools.
echo.
echo   The host can find their IPv6 by running:
echo     ipconfig ^| findstr "IPv6"
echo.
echo   Use the address that does NOT start with:
echo     fe80:: (link-local) or ::1 (loopback)
echo.
echo   Example: 2001:da8:1234:5678::1
echo.
echo   IMPORTANT: The address must be enclosed in brackets
echo   The script will handle this automatically.
echo.
set /p HOST_ADDR="Host IPv6 (e.g. 2001:da8:xxxx:xxxx::1): "
if "%HOST_ADDR%"=="" (
    echo   No address entered, aborting.
    pause
    goto :end
)
:: Strip brackets if user already added them
set "HOST_ADDR=%HOST_ADDR:[=%"
set "HOST_ADDR=%HOST_ADDR:]=%"
set "PROTO=http"
:: IPv6 with port
set "HOST_ADDR=[%HOST_ADDR%]:5000"
goto :config

:: =================================================================
:remote
:: =================================================================
echo.
echo [INTERNET MODE] Enter the server hostname or IP:port
echo.
echo   For servers with public IP / domain / port forwarding:
echo     Public IP with port:  12.34.56.78:5000
echo     Hostname:             myserver.example.com:5000
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
if "%HOST_ADDR:~-1%"=="/" set "HOST_ADDR=%HOST_ADDR:~0,-1%"

:: Determine protocol
echo %HOST_ADDR% | findstr /i "ngrok" >nul
if %errorlevel% equ 0 (
    set "PROTO=https"
) else (
    set "PROTO=http"
)
goto :config

:: =================================================================
:config
:: =================================================================
echo   Target: !PROTO!://%HOST_ADDR%

echo.
echo   Configuring frontend API proxy target...

:: IPv6 addresses already have port baked in from :ipv6
:: For LAN and remote, check if port is specified
if "%CONN_TYPE%"=="1" (
    echo %HOST_ADDR% | findstr ":" >nul
    if %errorlevel% neq 0 (
        set "HOST_ADDR=%HOST_ADDR%:5000"
    )
)

:: Build the API target URL
:: IPv6 already has brackets and port from the :ipv6 section
if "%CONN_TYPE%"=="2" (
    set "API_TARGET=http://%HOST_ADDR%"
) else if "%PROTO%"=="https" (
    set "API_TARGET=https://%HOST_ADDR%"
) else (
    set "API_TARGET=http://%HOST_ADDR%"
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
