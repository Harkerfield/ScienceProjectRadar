# Radar Application - Universal Setup Launcher (PowerShell)
# Detects OS and runs appropriate setup script

Write-Host "🌍 Radar Application - Cross-Platform Setup" -ForegroundColor Cyan
Write-Host ""

# Detect OS
$OSType = if ($PSVersionTable.PSVersion.Major -ge 6 -and $PSVersionTable.Platform -eq "Unix") {
    # PowerShell Core on Unix
    if ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::Linux)) {
        if ((Get-Content "/proc/device-tree/model" -ErrorAction SilentlyContinue) -match "Raspberry Pi") {
            "raspberry_pi"
        } else {
            "linux"
        }
    } elseif ([System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform([System.Runtime.InteropServices.OSPlatform]::OSX)) {
        "macos"
    } else {
        "unknown"
    }
} else {
    # Windows PowerShell (version 5.1)
    "windows"
}

Write-Host "📱 Detected OS: $OSType" -ForegroundColor Yellow
Write-Host ""

switch ($OSType) {
    "raspberry_pi" {
        Write-Host "🍓 Raspberry Pi detected" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Choose setup mode:" -ForegroundColor Yellow
        Write-Host "  1) App Mode (Recommended - Kiosk display)" -ForegroundColor White
        Write-Host "  2) Full Stack (Advanced - Multiple services)" -ForegroundColor White
        Write-Host ""
        $choice = Read-Host "Enter choice (1-2)"
        
        if ($choice -eq "1") {
            Write-Host "Starting App Mode setup..." -ForegroundColor Cyan
            bash ../linux/app-setup.sh
        } elseif ($choice -eq "2") {
            Write-Host "Starting Full Stack setup..." -ForegroundColor Cyan
            bash ../linux/raspi-kiosk-setup.sh
        } else {
            Write-Host "Invalid choice" -ForegroundColor Red
            exit 1
        }
    }
    
    "linux" {
        Write-Host "🐧 Linux detected" -ForegroundColor Cyan
        Write-Host "Starting Linux setup..." -ForegroundColor Yellow
        bash ../linux/app-setup.sh
    }
    
    "macos" {
        Write-Host "🍎 macOS detected" -ForegroundColor Cyan
        Write-Host "Starting macOS setup..." -ForegroundColor Yellow
        bash ../linux/app-setup.sh
    }
    
    "windows" {
        Write-Host "🪟 Windows detected" -ForegroundColor Cyan
        Write-Host "Starting Windows setup..." -ForegroundColor Yellow
        .\windows\win-setup.ps1
    }
    
    default {
        Write-Host "❌ Unknown OS type" -ForegroundColor Red
        Write-Host "Please run the setup manually from the platform-specific folder" -ForegroundColor Yellow
        exit 1
    }
}
