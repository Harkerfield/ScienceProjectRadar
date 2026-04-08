@echo off
REM Radar Application - Windows Launcher (Batch)
REM Opens two terminal windows for server and client

setlocal enabledelayedexpansion

echo Radar Application - Starting...
echo.

REM Check ports
netstat -ano 2>nul | find ":3000 " >nul
if not errorlevel 1 (
    echo WARNING: Port 3000 already in use
)

netstat -ano 2>nul | find ":5173 " >nul
if not errorlevel 1 (
    echo WARNING: Port 5173 already in use
)

echo.
echo Starting server...
start "Radar Server" npm --prefix RaspberryPiRadarFullStackApplicationAndStepperController\server start

timeout /t 3 /nobreak

echo Starting client...
start "Radar Client" npm --prefix RaspberryPiRadarFullStackApplicationAndStepperController\client run dev

echo.
echo ======================================
echo Servers started in separate windows
echo Server: http://localhost:3000
echo Client: http://localhost:5173
echo======================================
echo.

start http://localhost:5173
