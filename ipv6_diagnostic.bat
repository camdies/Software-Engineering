@echo off
setlocal enabledelayedexpansion
title IPv6 Connectivity Diagnostic

echo.
echo   ============================================================
echo     IPv6 PUBLIC ACCESS DIAGNOSTIC
echo   ============================================================
echo.

:: Get IPv6 addresses
set "IPV6_ADDR="
for /f "tokens=*" %%a in ('powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv6 | Where-Object {$_.InterfaceAlias -notlike '*Loopback*' -and $_.IPAddress -notlike 'fe80*' -and $_.IPAddress -notlike '::1'}).IPAddress | Select-Object -First 1" 2^>nul') do (
    if not "%%a"=="" set "IPV6_ADDR=%%a"
)

echo   FOUND THESE IPv6 ADDRESSES:
powershell -NoProfile -Command "Get-NetIPAddress -AddressFamily IPv6 | Where-Object {$_.IPAddress -notlike 'fe80*' -and $_.IPAddress -notlike '::1' -and $_.IPAddress -notlike '198.18*' -and $_.IPAddress -notlike '198.19*'} | ForEach-Object { Write-Host \"    $($_.IPAddress)  [$($_.SuffixOrigin)]  interface: $($_.InterfaceAlias)\" }"

echo.
echo   ============================================================
echo   TEST 1: Does your PC have a public IPv6?
echo   ============================================================
echo.
set "IS_PUBLIC=0"
echo %IPV6_ADDR% | findstr /r "^2" >nul && set "IS_PUBLIC=1"
echo %IPV6_ADDR% | findstr /r "^3" >nul && set "IS_PUBLIC=1"

if %IS_PUBLIC% equ 1 (
    echo   [PASS] Your IPv6 %IPV6_ADDR% is a GLOBAL UNICAST address.
    echo   This address IS routable on the public internet.
) else (
    echo   [FAIL] Your IPv6 is NOT a public address. This means your
    echo   campus network does not provide public IPv6, or your PC
    echo   is behind NAT64/CGN. External access not possible via IPv6.
    goto :test4
)

echo.
echo   ============================================================
echo   TEST 2: Windows Firewall - IPv6 port 5000
echo   ============================================================
echo.

netsh advfirewall firewall show rule name="EduMgmt Flask 5000" verbose 2>nul | findstr /i "Enabled Direction Protocol LocalPort" >nul 2>&1
if %errorlevel% equ 0 (
    echo   Firewall rule "EduMgmt Flask 5000" exists. Checking details...
    netsh advfirewall firewall show rule name="EduMgmt Flask 5000" verbose 2>nul | findstr /i "Enabled Direction Protocol LocalPort RemoteIP"
) else (
    echo   [WARN] No firewall rule for port 5000!
    echo.
    echo   This is the #1 reason IPv6 access fails. The firewall blocks
    echo   incoming connections from the internet.
    echo.
    set /p ADD_RULE="Add firewall rule now? (Y/N): "
    if /i "!ADD_RULE!"=="Y" (
        netsh advfirewall firewall add rule name="EduMgmt Flask 5000" dir=in action=allow protocol=TCP localport=5000
        echo   Rule added.
    )
)

echo.
echo   ============================================================
echo   TEST 3: Is your Flask server running and listening?
echo   ============================================================
echo.

tasklist /FI "IMAGENAME eq python.exe" /FO TABLE /NH 2>nul | findstr /i "python" >nul
if %errorlevel% equ 0 (
    echo   [OK] Python is running.
    echo   Check: netstat -an ^| findstr ":5000"
    netstat -an 2>nul | findstr ":5000"
    echo.
    echo   If you see "0.0.0.0:5000" above = listening on all interfaces
    echo   If you see "127.0.0.1:5000" only = localhost only (need --public)
) else (
    echo   [WARN] Python (Flask) is not running.
    echo   Start it with: python run.py --public
    echo   (--public is required for IPv6 access!)
)

echo.
echo   ============================================================
echo   TEST 4: Self-connect test via IPv6
echo   ============================================================
echo.

if not "%IPV6_ADDR%"=="" (
    echo   Trying to connect to http://[%IPV6_ADDR%]:5000 ...
    curl -s -o nul -w "HTTP Status: %%{http_code}" --connect-timeout 5 "http://[%IPV6_ADDR%]:5000" 2>nul
    echo.
    if %errorlevel% equ 0 (
        echo   [PASS] Self-connection via IPv6 works on this machine!
        echo   This means your local setup is correct.
        echo.
        echo   If others still can't reach you, the problem is:
        echo   - Campus perimeter firewall blocking inbound IPv6
        echo   - Partner doesn't have IPv6 on their network
        echo   - Partner's firewall blocking outbound IPv6
    ) else (
        echo   [FAIL] Cannot reach yourself via IPv6. Possible causes:
        echo   - Flask not running with --public
        echo   - Windows Firewall blocking the connection
        echo   - Wrong IPv6 address (privacy/temporary address used)
    )
)

echo.
echo   ============================================================
echo   TEST 5: Can your partner reach IPv6 sites?
echo   ============================================================
echo.
echo   On YOUR PARTNER'S computer, have them open:
echo     https://test-ipv6.com
echo.
echo   If it shows "10/10" or similar = they have IPv6
echo   If it shows "0/10" = they don't have IPv6, can't use IPv6 to reach you
echo.

echo   ============================================================
echo   DIAGNOSTIC SUMMARY
echo   ============================================================
echo.
echo   +--------------------------------------------------------+
echo   ^|  MOST COMMON FIXES:                                   ^|
echo   +--------------------------------------------------------+
echo   ^|                                                        ^|
echo   ^|  1. Add firewall rule (run as Admin):                  ^|
echo   ^|     netsh advfirewall firewall add rule                ^|
echo   ^|       name="EduMgmt Flask 5000" dir=in                ^|
echo   ^|       action=allow protocol=TCP localport=5000        ^|
echo   ^|                                                        ^|
echo   ^|  2. Start Flask with --public (NOT localhost only):    ^|
echo   ^|     python run.py --public                            ^|
echo   ^|                                                        ^|
echo   ^|  3. Partner must have IPv6 too (test-ipv6.com)        ^|
echo   ^|                                                        ^|
echo   ^|  4. If 1-3 are OK but still fails:                    ^|
echo   ^|     Campus firewall is blocking inbound connections.  ^|
echo   ^|     Use ZeroTier or frp instead (option [B] in        ^|
echo   ^|     server_control.bat).                              ^|
echo   ^|                                                        ^|
echo   ^|  5. IPv6 privacy address changes daily. Fix:          ^|
echo   ^|     Admin PowerShell:                                  ^|
echo   ^|     Set-NetIPv6Protocol -RandomizeIdentifiers Disabled ^|
echo   ^|                                                        ^|
echo   +--------------------------------------------------------+
echo.

echo   Press any key to exit...
pause >nul
