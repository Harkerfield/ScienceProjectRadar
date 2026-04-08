# Deploy Radar Project to Raspberry Pi
# PowerShell script for Windows - Copies repo and runs setup on Pi
# Usage: .\deploy-to-pi.ps1 -PiHost raspberrypi.local -PiUser pi

param(
    [string]$PiHost = "raspberrypi.local",
    [string]$PiUser = "pi",
    [string]$ProjectPath = ".",
    [string]$PiProjectDir = "/home/pi/RadarProject"
)

$ErrorActionPreference = "Stop"

Write-Host "`n" -ForegroundColor Cyan
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         RADAR PROJECT - DEPLOY TO RASPBERRY PI                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Configuration
Write-Host "Configuration:" -ForegroundColor Green
Write-Host "  Pi Host:        $PiHost"
Write-Host "  Pi User:        $PiUser"
Write-Host "  Project Dir:    $ProjectPath"
Write-Host "  Destination:    $PiProjectDir"
Write-Host ""

# Check if SSH is available
Write-Host "Checking prerequisites..." -ForegroundColor Yellow
$sshAvailable = (ssh -V 2>$null)
$scpAvailable = (scp 2>&1 | Select-String "usage")

if (-not $sshAvailable) {
    Write-Host "ERROR: SSH not found. Please install OpenSSH or PuTTY tools." -ForegroundColor Red
    exit 1
}

Write-Host "✓ SSH tools available" -ForegroundColor Green
Write-Host ""

# Test connection
Write-Host "Testing connection to $PiHost..." -ForegroundColor Yellow
try {
    $testConn = ssh $PiUser@$PiHost "echo 'Connection OK'" 2>&1
    if ($testConn -match "Connection OK") {
        Write-Host "✓ Connected to Pi successfully" -ForegroundColor Green
    } else {
        Write-Host "⚠ Connection test returned: $testConn" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ERROR: Cannot connect to $PiUser@$PiHost" -ForegroundColor Red
    Write-Host "Make sure:" -ForegroundColor Yellow
    Write-Host "  1. Raspberry Pi is powered on and connected"
    Write-Host "  2. Hostname is correct (check with 'ping $PiHost')"
    Write-Host "  3. SSH is enabled on Pi"
    Write-Host ""
    exit 1
}

Write-Host ""

# Option 1: Clone from Git (Recommended)
Write-Host "Deployment Method:" -ForegroundColor Green
Write-Host "  1. Clone from Git repository (recommended)"
Write-Host "  2. Copy via SCP (local copy)"
Write-Host ""

$method = Read-Host "Select method (1 or 2) [default: 1]"
if ([string]::IsNullOrEmpty($method)) { $method = "1" }

Write-Host ""

if ($method -eq "1") {
    # Git clone method
    Write-Host "Using Git clone method..." -ForegroundColor Cyan
    Write-Host ""
    
    $gitUrl = Read-Host "Enter Git repository URL (e.g., https://github.com/user/RadarProject.git)"
    
    if ([string]::IsNullOrEmpty($gitUrl)) {
        Write-Host "ERROR: Git URL required" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "Cloning repository to Pi..." -ForegroundColor Yellow
    
    ssh $PiUser@$PiHost @"
set -e
echo "Creating project directory..."
mkdir -p `$(dirname $PiProjectDir)
cd `$(dirname $PiProjectDir)

if [ -d $(basename $PiProjectDir) ]; then
    echo "Project directory already exists, updating..."
    cd $(basename $PiProjectDir)
    git pull origin main
else
    echo "Cloning repository..."
    git clone $gitUrl $(basename $PiProjectDir)
    cd $(basename $PiProjectDir)
fi

echo "Repository ready at $PiProjectDir"
"@
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Repository cloned successfully" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Git clone failed" -ForegroundColor Red
        exit 1
    }

} else {
    # SCP copy method
    Write-Host "Using SCP copy method..." -ForegroundColor Cyan
    Write-Host ""
    
    if (-not (Test-Path $ProjectPath)) {
        Write-Host "ERROR: Project path not found: $ProjectPath" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Creating destination directory on Pi..." -ForegroundColor Yellow
    ssh $PiUser@$PiHost "mkdir -p $PiProjectDir"
    
    Write-Host "Copying files to Pi (this may take a minute)..." -ForegroundColor Yellow
    # Use rsync if available, otherwise scp
    ssh $PiUser@$PiHost "which rsync" >$null 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        # Use rsync
        Write-Host "Using rsync for efficient copy..." -ForegroundColor Cyan
        ssh $PiUser@$PiHost @"
rsync -avz --delete \
  --exclude 'node_modules' \
  --exclude '.env' \
  --exclude '.git' \
  --exclude 'dist' \
  $ProjectPath/ $PiProjectDir/
"@
    } else {
        # Fallback to robocopy on Windows
        Write-Host "Copying with robocopy..." -ForegroundColor Cyan
        $rSource = (Resolve-Path $ProjectPath).Path
        robocopy "$rSource" "\\$PiHost\$PiProjectDir" /E /XD node_modules .git dist /XF .env > $null
    }
    
    if ($LASTEXITCODE -in @(0,1)) {
        Write-Host "✓ Files copied successfully" -ForegroundColor Green
    } else {
        Write-Host "⚠ Copy completed with code: $LASTEXITCODE" -ForegroundColor Yellow
    }
}

Write-Host ""

# Download and run setup script on Pi
Write-Host "Downloading setup script..." -ForegroundColor Yellow
$setupScript = @'
#!/bin/bash
set -e

echo "============================================================"
echo "RASPBERRY PI SETUP - Radar Project"
echo "============================================================"
echo ""

PROJECT_DIR="{PROJECT_DIR}"
cd "$PROJECT_DIR"

echo "[1/6] Updating system packages..."
sudo apt-get update -q
sudo apt-get upgrade -y -q

echo "[2/6] Installing required packages..."
sudo apt-get install -y -q \
    git \
    curl \
    build-essential \
    python3-dev \
    python3-pip

echo "[3/6] Enabling UART/Serial..."
if ! grep -q "dtoverlay=disable-bt" /boot/firmware/config.txt 2>/dev/null && \
   ! grep -q "dtoverlay=disable-bt" /boot/config.txt 2>/dev/null; then
    echo "Adding UART configuration..."
    if [ -f /boot/firmware/config.txt ]; then
        sudo tee -a /boot/firmware/config.txt > /dev/null <<EOF

# UART Configuration for Radar Project
enable_uart=1
dtoverlay=disable-bt
EOF
    elif [ -f /boot/config.txt ]; then
        sudo tee -a /boot/config.txt > /dev/null <<EOF

# UART Configuration for Radar Project
enable_uart=1
dtoverlay=disable-bt
EOF
    fi
    echo "UART enabled. Reboot required for changes to take effect."
    REBOOT_NEEDED=1
else
    echo "UART already enabled"
fi

echo "[4/6] Installing Node.js (v18)..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y -q nodejs
    echo "Node.js installed: $(node --version)"
else
    echo "Node.js already installed: $(node --version)"
fi

echo "[5/6] Installing project dependencies..."
cd "$PROJECT_DIR/RaspberryPiRadarFullStackApplicationAndStepperController"

# Install server dependencies
echo "  Installing server dependencies..."
npm install > /dev/null 2>&1

# Install client dependencies
echo "  Installing client dependencies..."
cd client
npm install > /dev/null 2>&1
cd ..

cd "$PROJECT_DIR"

echo "[6/6] Creating systemd service..."
sudo tee /etc/systemd/system/radar-app.service > /dev/null <<EOF
[Unit]
Description=Radar Application
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR/RaspberryPiRadarFullStackApplicationAndStepperController
ExecStart=/usr/bin/npm run server:start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable radar-app.service
echo "Service created: radar-app.service"

echo ""
echo "============================================================"
echo "SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Run: sudo systemctl start radar-app"
echo "  2. Visit: http://raspberrypi.local:3000"
echo ""

if [ $REBOOT_NEEDED -eq 1 ]; then
    echo "IMPORTANT: Reboot Pi for UART changes to take effect:"
    echo "  sudo reboot"
    echo ""
fi

echo "Logs: sudo journalctl -u radar-app -f"
'@

$setupScript = $setupScript -replace "{PROJECT_DIR}", $PiProjectDir

Write-Host "Running setup on Pi..." -ForegroundColor Yellow
Write-Host ""

# Create and run setup script
ssh $PiUser@$PiHost "cat > /tmp/setup-radar.sh" <<< $setupScript
ssh $PiUser@$PiHost "chmod +x /tmp/setup-radar.sh && bash /tmp/setup-radar.sh"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Setup completed successfully!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "⚠ Setup completed with warnings" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    DEPLOYMENT SUMMARY                          ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Project Location:  $PiProjectDir" -ForegroundColor Cyan
Write-Host "Start Service:     sudo systemctl start radar-app" -ForegroundColor Cyan
Write-Host "Check Status:      sudo systemctl status radar-app" -ForegroundColor Cyan
Write-Host "View Logs:         sudo journalctl -u radar-app -f" -ForegroundColor Cyan
Write-Host "Access App:        http://$PiHost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "SSH to Pi:         ssh $PiUser@$PiHost" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: Check if UART reboot was needed" -ForegroundColor Yellow
Write-Host "If UART was enabled, run: sudo reboot" -ForegroundColor Yellow
Write-Host ""
