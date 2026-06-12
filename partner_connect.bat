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

set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

:: =================================================================
:: Step 1: Get host IP
:: =================================================================
echo [1/4] Enter the host server IP address
echo.
echo   Ask your partner (the person running the server) for their IP.
echo   They can run server_control.bat and select [6] to see it.
echo.
set /p HOST_IP="Host IP (e.g. 192.168.1.100): "
if "%HOST_IP%"=="" (
    echo   No IP entered, using localhost
    set "HOST_IP=localhost"
)
echo   Host IP: %HOST_IP%

:: =================================================================
:: Step 2: Configure Vite proxy
:: =================================================================
echo.
echo [2/4] Configuring frontend API proxy to point at host...

:: Write .env.local for Vite
echo VITE_API_TARGET=http://%HOST_IP%:5000 > frontend\.env.local
echo   Created: frontend\.env.local
echo   VITE_API_TARGET=http://%HOST_IP%:5000

:: =================================================================
:: Step 3: Verify connectivity
:: =================================================================
echo.
echo [3/4] Checking connectivity to host...
ping -n 1 -w 2000 %HOST_IP% >nul 2>&1
if %errorlevel% equ 0 (
    echo   ping %HOST_IP% - OK, network reachable
) else (
    echo   [WARNING] ping %HOST_IP% failed
    echo   Make sure both computers are on the same LAN.
    echo   If on different networks, use ngrok: ngrok http 5000
)

:: =================================================================
:: Step 4: Summary
:: =================================================================
echo.
echo [4/4] Setup complete!
echo.
echo   +--------------------------------------------------+
echo   |  Connection Summary                              |
echo   +--------------------------------------------------+
echo   |                                                  |
echo   |  Option A: Browser (no install needed)           |
echo   |    http://%HOST_IP%:5000                        |
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

pause
endlocal
