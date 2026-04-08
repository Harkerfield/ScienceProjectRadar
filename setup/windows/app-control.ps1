# Radar Application - Windows Control (PowerShell)
# Manage server/client processes and check status

param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("status", "start", "stop", "kill", "test", "logs", "debug")]
    [string]$Command
)

function Get-ServerStatus {
    $server = Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "npm.*start" }
    return $server
}

function Get-ClientStatus {
    $client = Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "npm.*dev" }
    return $client
}

function Test-Port($port) {
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $asyncResult = $tcpClient.BeginConnect("127.0.0.1", $port, $null, $null)
        $asyncResult.WaitHandle.WaitOne(1000) | Out-Null
        $connected = $tcpClient.Connected
        $tcpClient.Close()
        return $connected
    } catch {
        return $false
    }
}

switch ($Command) {
    "status" {
        Write-Host "`n📊 Radar Application Status" -ForegroundColor Cyan
        
        $serverProc = Get-ServerStatus
        $clientProc = Get-ClientStatus
        $port3000 = Test-Port 3000
        $port5173 = Test-Port 5173
        
        Write-Host "`n🖥️  Server:"
        if ($serverProc) {
            Write-Host "   ✅ Running (PID: $($serverProc.Id))" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Not running" -ForegroundColor Red
        }
        Write-Host "   Port 3000: $(if ($port3000) { '✅ Responding' } else { '❌ Not responding' })" -ForegroundColor $(if ($port3000) { 'Green' } else { 'Red' })
        
        Write-Host "`n🎨 Client:"
        if ($clientProc) {
            Write-Host "   ✅ Running (PID: $($clientProc.Id))" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Not running" -ForegroundColor Red
        }
        Write-Host "   Port 5173: $(if ($port5173) { '✅ Responding' } else { '❌ Not responding' })" -ForegroundColor $(if ($port5173) { 'Green' } else { 'Red' })
        Write-Host "`n"
    }
    
    "start" {
        Write-Host "🚀 Starting Radar..." -ForegroundColor Cyan
        & .\run-windows.ps1
    }
    
    "stop" {
        Write-Host "🛑 Stopping Radar..." -ForegroundColor Yellow
        Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "npm" } | Stop-Process -Force
        Write-Host "✅ Stopped" -ForegroundColor Green
    }
    
    "kill" {
        Write-Host "💣 Force killing all npm processes..." -ForegroundColor Red
        Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force
        Write-Host "✅ Killed" -ForegroundColor Green
    }
    
    "test" {
        Write-Host "`n🧪 Testing connectivity..." -ForegroundColor Cyan
        
        Write-Host "`n  Testing server on port 3000..." -ForegroundColor Yellow
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction Stop
            Write-Host "  ✅ Server responding: $($response.StatusCode)" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ Server not responding: $($_.Exception.Message)" -ForegroundColor Red
        }
        
        Write-Host "`n  Testing client on port 5173..." -ForegroundColor Yellow
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 5 -ErrorAction Stop
            Write-Host "  ✅ Client responding: $($response.StatusCode)" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ Client not responding: $($_.Exception.Message)" -ForegroundColor Red
        }
        Write-Host "`n"
    }
    
    "logs" {
        Write-Host "`n📋 Recent processes:" -ForegroundColor Cyan
        Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "npm" } | Format-Table Name, Id, ProcessName, @{Name="Command";Expression={$_.CommandLine.Substring(0,[Math]::Min(60,$_.CommandLine.Length))}}
    }
    
    "debug" {
        Write-Host "`n🔍 Debug Information" -ForegroundColor Cyan
        Write-Host "`n  Node.js version:" -ForegroundColor Yellow
        node --version
        Write-Host "`n  npm version:" -ForegroundColor Yellow
        npm --version
        Write-Host "`n  Environment:" -ForegroundColor Yellow
        Write-Host "    NODE_ENV: $env:NODE_ENV"
        Write-Host "    PORT: $env:PORT"
        Write-Host "`n  Listening ports:" -ForegroundColor Yellow
        netstat -ano | Select-String ":3000|:5173" | ForEach-Object { Write-Host "    $_" }
        Write-Host "`n  Running processes:" -ForegroundColor Yellow
        Get-Process -Name node -ErrorAction SilentlyContinue | Format-Table Name, Id
    }
}
