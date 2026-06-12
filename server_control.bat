@echo off
setlocal enabledelayedexpansion
title 教务管理系统 - 服务器控制面板
echo ============================================================
echo   教务管理系统 v3.0 - 服务器控制面板
echo ============================================================
echo.

set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

:: =================================================================
:: 获取本机 IP
:: =================================================================
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    for /f "tokens=*" %%b in ("%%a") do (
        set "LOCAL_IP=%%b"
        goto :menu
    )
)
:menu
echo   本机 IP: %LOCAL_IP%
echo   项目路径: %PROJECT_DIR%
echo.
echo ────────────────────────────────────────────
echo   [1] 启动服务器 (仅本机访问 localhost)
echo   [2] 启动服务器 (局域网公开 --public)
echo   [3] 停止服务器
echo   [4] 查看服务器状态
echo   [5] 重新构建前端并启动
echo   [6] 伙伴连接信息查看
echo   [7] 打包分发给伙伴
echo   [0] 退出
echo ────────────────────────────────────────────
echo.

set /p CHOICE="请选择操作 [0-7]: "

if "%CHOICE%"=="1" goto :start_local
if "%CHOICE%"=="2" goto :start_public
if "%CHOICE%"=="3" goto :stop
if "%CHOICE%"=="4" goto :status
if "%CHOICE%"=="5" goto :rebuild
if "%CHOICE%"=="6" goto :partner_info
if "%CHOICE%"=="7" goto :distribute
if "%CHOICE%"=="0" goto :end
echo 无效选项，请重试
pause
cls
goto :menu

:: =================================================================
:: 启动服务器 (仅本机)
:: =================================================================
:start_local
echo.
echo   正在启动服务器 (仅本机)...
echo   访问地址: http://localhost:5000
echo.
start http://localhost:5000
python run.py
goto :end

:: =================================================================
:: 启动服务器 (局域网公开)
:: =================================================================
:start_public
echo.
echo   正在启动服务器 (局域网公开)...
echo   本机访问: http://localhost:5000
echo   伙伴访问: http://%LOCAL_IP%:5000
echo   确保防火墙已开放 5000 端口!
echo.
start http://localhost:5000
python run.py --public
goto :end

:: =================================================================
:: 停止服务器
:: =================================================================
:stop
echo.
echo   正在查找运行中的 Flask 进程...
for /f "tokens=2" %%a in ('tasklist ^| findstr /i "python.exe"') do (
    echo   发现 python.exe 进程 PID=%%a
    taskkill /F /PID %%a >nul 2>&1
)
echo   服务器进程已终止。
pause
goto :end

:: =================================================================
:: 查看状态
:: =================================================================
:status
echo.
echo   ─── 服务器状态 ───
tasklist 2>nul | findstr /i "python.exe" >nul
if %errorlevel% equ 0 (
    echo   服务器状态: 运行中
    tasklist | findstr /i "python.exe"
    echo.
    echo   本机访问: http://localhost:5000
    echo   伙伴访问: http://%LOCAL_IP%:5000
) else (
    echo   服务器状态: 未运行
)

echo.
echo   ─── 防火墙规则 ───
netsh advfirewall firewall show rule name="EduMgmt Flask 5000" 2>nul
netsh advfirewall firewall show rule name="SQL Server 1433" 2>nul

echo.
echo   ─── 数据库 ───
sc query MSSQL$SQLEXPRESS 2>nul | findstr "STATE"
sc query MSSQLSERVER 2>nul | findstr "STATE"

echo.
echo   ─── 网络 ───
echo   本机 IP: %LOCAL_IP%
ping -n 1 %LOCAL_IP% 2>nul | findstr "TTL"

pause
goto :end

:: =================================================================
:: 重新构建前端
:: =================================================================
:rebuild
echo.
echo   正在构建前端...
cd frontend
call npm run build
cd ..
echo   前端构建完成!
echo   启动服务器...
start http://localhost:5000
python run.py --public
goto :end

:: =================================================================
:: 显示伙伴连接信息
:: =================================================================
:partner_info
echo.
echo   ╔══════════════════════════════════════════════════════╗
echo   ║          开发伙伴连接信息                          ║
echo   ╠══════════════════════════════════════════════════════╣
echo   ║                                                    ║
echo   ║  网页访问 (浏览器直接打开):                        ║
echo   ║    http://%LOCAL_IP%:5000                          ║
for /f "delims=" %%a in ('echo %LOCAL_IP%') do set "IP_PAD=%%a                      "
echo   ║                                                    ║
echo   ║  前端开发代理 (vite.config.js 的 API_TARGET):       ║
echo   ║    http://%LOCAL_IP%:5000                          ║
echo   ║                                                    ║
echo   ║  数据库连接 (SSMS / SQL 工具):                     ║
echo   ║    服务器: %LOCAL_IP%\SQLEXPRESS                   ║
echo   ║    用户: sa                                        ║
echo   ║    密码: (你在 config.ini 中配置的密码)            ║
echo   ║                                                    ║
echo   ║  默认账号:                                         ║
echo   ║    管理员 admin / 123456                           ║
echo   ║    教师   T001  / 123456                           ║
echo   ║    学生   STU001 / 123456                          ║
echo   ║                                                    ║
echo   ║  项目地址: https://github.com/camdies/Software-Engineering
echo   ║  配置指引: SETUP_PARTNER.md                        ║
echo   ╚══════════════════════════════════════════════════════╝
echo.
pause
goto :end

:: =================================================================
:: 打包分发给伙伴 (不包含 node_modules 和数据库密码)
:: =================================================================
:distribute
echo.
echo   正在打包项目（排除 node_modules、__pycache__、config.ini 密码）...

set "PACKAGE_NAME=edu-mgmt-dist.zip"
set "PACKAGE_DIR=%PROJECT_DIR%..\edu-mgmt-dist"

:: 复制到临时目录
if exist "%PACKAGE_DIR%" rmdir /s /q "%PACKAGE_DIR%"
mkdir "%PACKAGE_DIR%"

:: 使用 robocopy 复制，排除不必要的文件
robocopy "%PROJECT_DIR%" "%PACKAGE_DIR%" /E /NFL /NDL /NJH /NJS ^
    /XD node_modules __pycache__ .git .claude .vscode .idea ^
    /XF *.pyc *.bak .env
if %errorlevel% geq 8 (
    echo   复制过程出现问题，但继续打包...
)

:: 恢复 config.ini.example 为干净的模板
if exist "%PACKAGE_DIR%\backend\config\config.ini" (
    del "%PACKAGE_DIR%\backend\config\config.ini"
)
if exist "%PACKAGE_DIR%\backend\config\config.ini.example" (
    copy "%PACKAGE_DIR%\backend\config\config.ini.example" "%PACKAGE_DIR%\backend\config\config.ini" >nul
)

:: 打包
powershell -Command "Compress-Archive -Path '%PACKAGE_DIR%\*' -DestinationPath '%PROJECT_DIR%..\%PACKAGE_NAME%' -Force"

:: 清理临时目录
rmdir /s /q "%PACKAGE_DIR%"

set "SIZE=0"
for %%f in ("%PROJECT_DIR%..\%PACKAGE_NAME%") do set /a "SIZE=%%~zf / 1048576"

echo.
echo   ✅ 打包完成!
echo   文件: %PROJECT_DIR%..\%PACKAGE_NAME%
echo   大小: !SIZE! MB (约)
echo.
echo   将 %PACKAGE_NAME% 发给伙伴，ta 解压后:
echo   1. 编辑 backend\config\config.ini 填入你的数据库连接信息
echo   2. 或在 vite.config.js 中将 API_TARGET 设为 http://%LOCAL_IP%:5000
echo   3. npm install ^&^& npm run build ^&^& pip install -r requirements.txt
echo   4. 浏览器打开 http://%LOCAL_IP%:5000 (如果连你的数据库)
echo.
pause
goto :end

:end
endlocal
