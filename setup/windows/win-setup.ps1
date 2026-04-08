# Radar Application - Windows Setup (PowerShell)
# Detects Node.js, installs dependencies, and configures environment

param(
    [switch]$Production = $false
)

$ErrorActionPreference = "Stop"
Write-Host "🚀 Radar Application - Windows Setup" -ForegroundColor Cyan

# Check Node.js
Write-Host "`n📋 Checking Node.js..." -ForegroundColor Yellow
$nodeVersion = node --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Node.js not found!" -ForegroundColor Red
    Write-Host "📥 Please install from https://nodejs.org/ (LTS recommended)" -ForegroundColor Yellow
    Write-Host "   Make sure to check 'Add to PATH' during installation" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Node.js $nodeVersion found" -ForegroundColor Green

# Check npm
Write-Host "`n📋 Checking npm..." -ForegroundColor Yellow
$npmVersion = npm --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ npm not found!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ npm $npmVersion found" -ForegroundColor Green

# Create .env files
Write-Host "`n⚙️  Setting up environment..." -ForegroundColor Yellow

# Root .env
$rootEnv = @"
NODE_ENV=$($Production ? 'production' : 'development')
PORT=3000
PICO_UART_ENABLED=false
VUE_APP_API_BASE_URL=http://localhost:3000/api
"@

# Server .env
$serverEnv = @"
NODE_ENV=$($Production ? 'production' : 'development')
PORT=3000
PICO_UART_ENABLED=false
VUE_APP_API_BASE_URL=http://localhost:3000/api
LOG_LEVEL=debug
"@

# Client .env
$clientEnv = @"
VITE_API_BASE_URL=http://localhost:3000/api
"@

@(
    @{path = ".env"; content = $rootEnv}
    @{path = "RaspberryPiRadarFullStackApplicationAndStepperController\server\.env"; content = $serverEnv}
    @{path = "RaspberryPiRadarFullStackApplicationAndStepperController\client\.env"; content = $clientEnv}
) | ForEach-Object {
    $dir = Split-Path $_.path -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if (-not (Test-Path $_.path)) {
        Set-Content -Path $_.path -Value $_.content
        Write-Host "  ✅ Created $($_.path)" -ForegroundColor Green
    } else {
        Write-Host "  ⏭️  $($_.path) already exists" -ForegroundColor Cyan
    }
}

# Install dependencies
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Yellow
$serverPath = "RaspberryPiRadarFullStackApplicationAndStepperController\server"
$clientPath = "RaspberryPiRadarFullStackApplicationAndStepperController\client"

if (Test-Path $serverPath) {
    Write-Host "  📦 Server dependencies..." -ForegroundColor Cyan
    Push-Location $serverPath
    npm install 2>&1 | Select-Object -Last 5
    Pop-Location
    Write-Host "  ✅ Server setup complete" -ForegroundColor Green
}

if (Test-Path $clientPath) {
    Write-Host "  📦 Client dependencies..." -ForegroundColor Cyan
    Push-Location $clientPath
    npm install 2>&1 | Select-Object -Last 5
    Pop-Location
    Write-Host "  ✅ Client setup complete" -ForegroundColor Green
}

Write-Host "`n✨ Setup complete! Next:" -ForegroundColor Cyan
Write-Host "   Run: .\run-windows.ps1" -ForegroundColor Yellow
Write-Host "   Or:  .\run-windows.bat" -ForegroundColor Yellow
