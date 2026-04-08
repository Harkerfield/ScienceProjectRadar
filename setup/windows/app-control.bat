@echo off
REM Radar Application - Windows Control (Batch)
REM Manage server/client processes

if "%1"=="" (
    echo Usage: app-control.bat [status^|start^|stop^|kill^|test]
    echo.
    echo Commands:
    echo   status   - Show server and client status
    echo   start    - Start servers
    echo   stop     - Stop servers
    echo   kill     - Force kill all npm processes
    echo   test     - Test server connectivity
    exit /b 1
)

setlocal enabledelayedexpansion

if /i "%1"=="status" (
    echo.
    echo === Server Status ===
    tasklist | findstr /i "node" >nul
    if errorlevel 1 (
        echo No Node processes running
    ) else (
        echo Node processes:
        tasklist | findstr /i "node"
    )
    echo.
    netstat -ano 2>nul | findstr ":3000 " >nul && echo Port 3000: IN USE
    netstat -ano 2>nul | findstr ":5173 " >nul && echo Port 5173: IN USE
    echo.
)

if /i "%1"=="start" (
    echo Starting Radar...
    call run-windows.bat
)

if /i "%1"=="stop" (
    echo Stopping servers...
    taskkill /F /IM node.exe 2>nul >nul
    echo Done
)

if /i "%1"=="kill" (
    echo Force killing npm processes...
    taskkill /F /IM node.exe
    taskkill /F /IM npm.cmd
    echo Done
)

if /i "%1"=="test" (
    echo.
    echo Testing connectivity...
    echo Testing port 3000...
    timeout /t 1 /nobreak >nul
    powershell -NoProfile -Command "try { Invoke-WebRequest http://localhost:3000 -TimeoutSec 5 | Write-Host 'OK'; } catch { Write-Host 'FAIL: ' $_.Exception.Message }"
    
    echo Testing port 5173...
    timeout /t 1 /nobreak >nul
    powershell -NoProfile -Command "try { Invoke-WebRequest http://localhost:5173 -TimeoutSec 5 | Write-Host 'OK'; } catch { Write-Host 'FAIL: ' $_.Exception.Message }"
    echo.
)
