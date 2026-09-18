@echo off
chcp 65001 >nul
title TaiWei Cloud Palace 3D Viewer
echo.
echo   ╔══════════════════════════════════════╗
echo   ║     太微云宫 · 三维巡游 启动器      ║
echo   ╚══════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM Check files exist
if not exist "taiwei_web.glb" (
    echo [ERROR] taiwei_web.glb not found in %~dp0
    echo Please ensure the GLB file is in the same directory as this script.
    pause
    exit /b 1
)
if not exist "taiwei_viewer.html" (
    echo [ERROR] taiwei_viewer.html not found in %~dp0
    pause
    exit /b 1
)

set PORT=8766

REM Kill any existing server on this port
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "LISTEN" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo Starting local server on port %PORT%...
echo.

REM Start Python HTTP server in background
start /min "" python -m http.server %PORT% --bind 127.0.0.1

REM Wait a moment for server to start
timeout /t 2 /nobreak >nul

REM Open browser
echo Opening browser...
start "" "http://127.0.0.1:%PORT%/taiwei_viewer.html"

echo.
echo Server running at http://127.0.0.1:%PORT%/
echo.
echo Press any key to stop the server and exit...
pause >nul

REM Cleanup: kill the Python server
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "LISTEN" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo Server stopped. Goodbye!
