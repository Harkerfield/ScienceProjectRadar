# Radar Application - Quick Setup (PowerShell)
# Interactive setup wizard for easy first-time setup and daily use

param(
    [ValidateSet("setup", "start", "status", "stop")]
    [string]$QuickCommand = $null
)

function Show-Menu {
    Write-Host "`n" -NoNewline
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "   RADAR APPLICATION - SETUP WIZARD" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "`n"
    Write-Host "Choose your action:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   1) " -NoNewline; Write-Host "SETUP (first time only)" -ForegroundColor Green
    Write-Host "   2) " -NoNewline; Write-Host "START servers and dashboard" -ForegroundColor Green
    Write-Host "   3) " -NoNewline; Write-Host "CHECK status" -ForegroundColor Cyan
    Write-Host "   4) " -NoNewline; Write-Host "STOP servers" -ForegroundColor Yellow
    Write-Host "   5) " -NoNewline; Write-Host "EXIT" -ForegroundColor Gray
    Write-Host ""
}

function Do-Setup {
    Write-Host "`n🔧 Running setup..." -ForegroundColor Cyan
    & ".\setup\windows\win-setup.ps1"
    Write-Host "`n✅ Setup complete!" -ForegroundColor Green
    Read-Host "Press Enter to continue"
}

function Do-Start {
    Write-Host "`n🚀 Starting Radar Application..." -ForegroundColor Cyan
    & ".\setup\windows\run-windows.ps1"
}

function Do-Status {
    Write-Host "`n📊 Checking status..." -ForegroundColor Cyan
    & ".\setup\windows\app-control.ps1" status
    Read-Host "Press Enter to continue"
}

function Do-Stop {
    Write-Host "`n🛑 Stopping servers..." -ForegroundColor Yellow
    & ".\setup\windows\app-control.ps1" stop
    Write-Host "`n✅ Stopped!" -ForegroundColor Green
    Read-Host "Press Enter to continue"
}

# Handle quick commands
if ($QuickCommand) {
    switch ($QuickCommand) {
        "setup" { Do-Setup; exit }
        "start" { Do-Start; exit }
        "status" { Do-Status; exit }
        "stop" { Do-Stop; exit }
    }
}

# Interactive menu loop
while ($true) {
    Show-Menu
    $choice = Read-Host "Enter your choice (1-5)"
    
    switch ($choice) {
        "1" { Do-Setup }
        "2" { Do-Start }
        "3" { Do-Status }
        "4" { Do-Stop }
        "5" { 
            Write-Host "`n👋 Goodbye!" -ForegroundColor Cyan
            exit 
        }
        default { 
            Write-Host "`n❌ Invalid choice. Please try again." -ForegroundColor Red
        }
    }
}
