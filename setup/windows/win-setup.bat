@echo off
REM Radar Application - Windows Setup (Batch)
REM Simple setup for development

setlocal enabledelayedexpansion

echo.
echo ======================================
echo   Radar Application - Windows Setup
echo ======================================
echo.

REM Check Node.js
echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found!
    echo Please install from https://nodejs.org/ (LTS recommended)
    echo Make sure to check "Add to PATH" during installation
    exit /b 1
)
echo OK: Node.js found

REM Check npm
echo Checking npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm not found!
    exit /b 1
)
echo OK: npm found

REM Create .env files
echo.
echo Setting up environment files...
if not exist ".env" (
    (
        echo NODE_ENV=development
        echo PORT=3000
        echo PICO_UART_ENABLED=false
        echo VUE_APP_API_BASE_URL=http://localhost:3000/api
    ) > .env
    echo Created .env
) else (
    echo .env already exists
)

if not exist "RaspberryPiRadarFullStackApplicationAndStepperController\server\.env" (
    mkdir RaspberryPiRadarFullStackApplicationAndStepperController\server 2>nul
    (
        echo NODE_ENV=development
        echo PORT=3000
        echo PICO_UART_ENABLED=false
        echo LOG_LEVEL=debug
    ) > RaspberryPiRadarFullStackApplicationAndStepperController\server\.env
    echo Created server\.env
)

if not exist "RaspberryPiRadarFullStackApplicationAndStepperController\client\.env" (
    mkdir RaspberryPiRadarFullStackApplicationAndStepperController\client 2>nul
    (
        echo VITE_API_BASE_URL=http://localhost:3000/api
    ) > RaspberryPiRadarFullStackApplicationAndStepperController\client\.env
    echo Created client\.env
)

REM Install dependencies
echo.
echo Installing dependencies...
if exist "RaspberryPiRadarFullStackApplicationAndStepperController\server" (
    echo Installing server dependencies...
    cd RaspberryPiRadarFullStackApplicationAndStepperController\server
    call npm install
    cd ..\..
    echo Server setup complete
)

if exist "RaspberryPiRadarFullStackApplicationAndStepperController\client" (
    echo Installing client dependencies...
    cd RaspberryPiRadarFullStackApplicationAndStepperController\client
    call npm install
    cd ..\..
    echo Client setup complete
)

echo.
echo ======================================
echo Setup complete! Next:
echo   Run: run-windows.ps1 (recommended)
echo   Or:  run-windows.bat
echo ======================================
echo.
pause
