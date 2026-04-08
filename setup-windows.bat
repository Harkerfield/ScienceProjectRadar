@echo off
REM ============================================
REM  Radar Application - Quick Setup (Windows)
REM ============================================

setlocal enabledelayedexpansion

cls
echo.
echo ============================================
echo    RADAR APPLICATION - SETUP WIZARD
echo ============================================
echo.
echo Choose your action:
echo.
echo   1) Setup (first time only)
echo   2) Start servers and dashboard
echo   3) Check status
echo   4) Stop servers
echo   5) Exit
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    goto setup
) else if "%choice%"=="2" (
    goto start
) else if "%choice%"=="3" (
    goto status
) else if "%choice%"=="4" (
    goto stop
) else if "%choice%"=="5" (
    goto exit
) else (
    echo Invalid choice
    timeout /t 2 >nul
    goto menu
)

:setup
cls
echo Installing Node.js dependencies...
call setup\windows\win-setup.bat
goto menu

:start
cls
echo Starting Radar Application...
call setup\windows\run-windows.ps1
goto menu

:status
cls
call setup\windows\app-control.ps1 status
pause
goto menu

:stop
cls
call setup\windows\app-control.ps1 stop
echo Stopped.
pause
goto menu

:menu
goto start_menu

:start_menu
timeout /t 2 >nul
cls
goto begin

:begin
REM Initial menu
setlocal enabledelayedexpansion
cls
echo ============================================
echo    RADAR APPLICATION - SETUP WIZARD
echo ============================================
echo.
echo Choose your action:
echo.
echo   1) Setup (first time only)
echo   2) Start servers and dashboard
echo   3) Check status
echo   4) Stop servers
echo   5) Exit
echo.
set /p choice="Enter your choice (1-5): "
if "%choice%"=="1" goto setup
if "%choice%"=="2" goto start
if "%choice%"=="3" goto status
if "%choice%"=="4" goto stop
if "%choice%"=="5" goto exit
echo Invalid choice
timeout /t 2 >nul
goto begin

:exit
exit /b 0
