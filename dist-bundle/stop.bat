@echo off
title EduMgmt System v3.0 - Stop Services
echo Stopping all EduMgmt services...
echo.
taskkill /FI "WINDOWTITLE eq EduMgmt Flask" /F 2>nul
taskkill /FI "WINDOWTITLE eq EduMgmt MySQL" /F 2>nul
taskkill /FI "WINDOWTITLE eq EduMgmt MySQL Init" /F 2>nul
echo.
echo All services stopped. Press any key to close...
pause >nul
