@echo off
setlocal enabledelayedexpansion
title Build EduMgmt Installer
cd /d "%~dp0"

if not defined IN_SCRIPT (
    set IN_SCRIPT=1
    cmd /k "%~f0" %*
    exit /b
)

echo.
echo ============================================================
echo   EduMgmt Installer Builder v3.0
echo ============================================================
echo.

set ALL_OK=1

echo Checking prerequisites...
echo.

set NSIS=
if exist "C:\Program Files (x86)\NSIS\makensis.exe" set "NSIS=C:\Program Files (x86)\NSIS\makensis.exe"
if exist "C:\Program Files\NSIS\makensis.exe" set "NSIS=C:\Program Files\NSIS\makensis.exe"
if "%NSIS%"=="" (
    echo [MISS] NSIS not found - install https://nsis.sourceforge.io/Download
    set ALL_OK=0
) else (
    echo [OK]   NSIS found
)

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [MISS] Python not in PATH
    set ALL_OK=0
) else (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo [OK]   Python %%v
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [MISS] Node.js not in PATH
    set ALL_OK=0
) else (
    for /f "tokens=2" %%v in ('node --version 2^>^&1') do echo [OK]   Node.js %%v
)

if "%ALL_OK%"=="0" (
    echo.
    echo Install missing tools and re-run.
    pause
    exit /b 1
)

echo.
echo [1/5] Building frontend...
pushd frontend
if not exist "node_modules\" call npm install
call npm run build
popd
:: Vite may exit non-zero on Windows due to libuv cleanup race,
:: even though build succeeded. Check the actual output instead.
if not exist "frontend\dist\index.html" (
    echo [ERROR] Frontend build failed - frontend\dist\index.html not found
    pause
    exit /b 1
)
echo [OK] frontend\dist ready

echo.
echo [2/5] Embedded Python...
set EMBED_DIR=%CD%\dist-bundle\python-embed
if exist "%EMBED_DIR%\python.exe" goto :python_ready
if not exist "dist-bundle" mkdir "dist-bundle"
echo Downloading Python 3.11.9 embed...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile '%TEMP%\py-embed.zip'"
if not exist "%TEMP%\py-embed.zip" (
    echo [ERROR] Download failed
    pause
    exit /b 1
)
powershell -Command "Expand-Archive -Path '%TEMP%\py-embed.zip' -DestinationPath '%EMBED_DIR%' -Force"
del "%TEMP%\py-embed.zip" 2>nul
powershell -Command "$f=Get-ChildItem '%EMBED_DIR%' -Filter 'python*._pth'|Select-Object -First 1; Add-Content -Path $f.FullName -Value 'import site' -Encoding UTF8"
echo Installing pip...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%EMBED_DIR%\get-pip.py'"
"%EMBED_DIR%\python.exe" "%EMBED_DIR%\get-pip.py" --no-warn-script-location
del "%EMBED_DIR%\get-pip.py" 2>nul
echo Installing project deps...
"%EMBED_DIR%\python.exe" -m pip install --no-warn-script-location Flask flask-cors PyJWT PyMySQL SQLAlchemy bcrypt openpyxl reportlab pandas python-dotenv coverage marshmallow
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed
    pause
    exit /b 1
)
:python_ready
echo [OK] Embedded Python ready

echo.
echo [3/5] VC++ Redist...
set VC_REDIST=%CD%\dist-bundle\vc_redist.x64.exe
if not exist "%VC_REDIST%" (
    echo Downloading...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile '%VC_REDIST%'"
    if not exist "%VC_REDIST%" echo [WARN] VC++ download failed, skipped
)
echo [OK] VC++ Redist ready

echo.
echo [4/5] Assembling package...
copy /Y "run.bat"  "dist-bundle\run.bat"  >nul
copy /Y "stop.bat" "dist-bundle\stop.bat" >nul
echo [OK] Package assembled

echo.
echo [5/5] Compiling NSIS installer...
"%NSIS%" "%CD%\setup.nsi"
if %errorlevel% neq 0 (
    echo [ERROR] NSIS compilation failed
    pause
    exit /b 1
)

set SIZE_MB=?
for %%f in ("EduMgmt-Setup-3.0.0.exe") do (
    set SZ=%%~zf
    set /a SIZE_MB=!SZ! / 1048576
)

echo.
echo ============================================================
echo   BUILD SUCCESS
echo   Output: %CD%\EduMgmt-Setup-3.0.0.exe
echo   Size:   %SIZE_MB% MB
echo ============================================================
echo.
pause
endlocal
