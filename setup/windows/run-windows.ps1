# Radar Application - Windows Launcher (PowerShell)
# Starts server and client in parallel with monitoring

$ErrorActionPreference = "Continue"
Write-Host "🚀 Starting Radar Application..." -ForegroundColor Cyan

$serverPath = "RaspberryPiRadarFullStackApplicationAndStepperController\server"
$clientPath = "RaspberryPiRadarFullStackApplicationAndStepperController\client"

# Function to check port
function Test-Port($port) {
    $result = $false
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $asyncResult = $tcpClient.BeginConnect("127.0.0.1", $port, $null, $null)
        $asyncResult.WaitHandle.WaitOne(1000) | Out-Null
        if ($tcpClient.Connected) { $result = $true }
        $tcpClient.Close()
    } catch { }
    return $result
}

Write-Host "`n📋 Checking ports..." -ForegroundColor Yellow
$port3000 = Test-Port 3000
$port5173 = Test-Port 5173

if ($port3000) { Write-Host "  ⚠️  Port 3000 in use" -ForegroundColor Yellow }
if ($port5173) { Write-Host "  ⚠️  Port 5173 in use" -ForegroundColor Yellow }

# Start server
Write-Host "`n🖥️  Starting server..." -ForegroundColor Cyan
Push-Location $serverPath
$ServerJob = Start-Job -ScriptBlock {
    Set-Location $using:serverPath
    npm start 2>&1
} -Name "RadarServer"
Pop-Location

Write-Host "   PID: $($ServerJob.Id)" -ForegroundColor Gray
Start-Sleep 3

# Wait for server to be ready
Write-Host "`n⏳ Waiting for server to start..." -ForegroundColor Yellow
$timeout = 30
$elapsed = 0
while ($elapsed -lt $timeout) {
    if (Test-Port 3000) {
        Write-Host "   ✅ Server ready on port 3000" -ForegroundColor Green
        break
    }
    Write-Host "   ⏳  Still waiting..." -ForegroundColor Cyan
    Start-Sleep 2
    $elapsed += 2
}

# Start client
Write-Host "`n🎨 Starting client..." -ForegroundColor Cyan
Push-Location $clientPath
$ClientJob = Start-Job -ScriptBlock {
    Set-Location $using:clientPath
    npm run dev 2>&1
} -Name "RadarClient"
Pop-Location

Write-Host "   PID: $($ClientJob.Id)" -ForegroundColor Gray
Start-Sleep 2

# Open browser
Write-Host "`n🌐 Opening dashboard..." -ForegroundColor Cyan
$browser = @(
    "chrome.exe",
    "msedge.exe",
    "firefox.exe"
) | ForEach-Object {
    $(Get-Command $_ -CommandType Application -ErrorAction SilentlyContinue) | Select-Object -First 1
} | Where-Object { $_ } | Select-Object -First 1

if ($browser) {
    Start-Process "http://localhost:5173"
    Write-Host "   ✅ Browser opening..." -ForegroundColor Green
} else {
    Write-Host "   ℹ️  Open http://localhost:5173 in your browser" -ForegroundColor Cyan
}

Write-Host "`n✨ Everything is running!" -ForegroundColor Green
Write-Host "   Server: http://localhost:3000" -ForegroundColor Cyan
Write-Host "   Client: http://localhost:5173" -ForegroundColor Cyan
Write-Host "`n📌 To stop: Close this window or run app-control.ps1 stop" -ForegroundColor Yellow

# Monitor jobs
while ($true) {
    if (-not (Get-Job -Name "RadarServer" -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Running" })) {
        Write-Host "`n⚠️  Server stopped" -ForegroundColor Yellow
        break
    }
    Start-Sleep 5
}

# Cleanup
Write-Host "`n🧹 Cleaning up..." -ForegroundColor Yellow
Get-Job -Name "RadarServer", "RadarClient" | Stop-Job -ErrorAction SilentlyContinue
Get-Job -Name "RadarServer", "RadarClient" | Remove-Job -ErrorAction SilentlyContinue
Write-Host "✅ Stopped" -ForegroundColor Green
