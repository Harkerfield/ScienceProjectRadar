#!/bin/bash
# Radar Project - Installation from Git
# Run this on your Raspberry Pi to clone and set up the project
# Usage: bash install-from-git.sh [REPO_URL] [INSTALL_DIR]

set -e

# Configuration
REPO_URL="${1:-https://github.com/YOUR_USERNAME/RadarProject.git}"
INSTALL_DIR="${2:-/home/pi/RadarProject}"
PROJECT_SUBDIR="RaspberryPiRadarFullStackApplicationAndStepperController"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         RADAR PROJECT - GIT INSTALLATION                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Validate repo URL
if [[ ! "$REPO_URL" =~ ^https?://.*\.git$ ]]; then
    echo "ERROR: Invalid repository URL format"
    echo "Expected: https://github.com/username/repo.git"
    echo "Got: $REPO_URL"
    exit 1
fi

echo "Configuration:"
echo "  Repository: $REPO_URL"
echo "  Install Dir: $INSTALL_DIR"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v git &> /dev/null; then
    echo "Installing git..."
    sudo apt-get update -q
    sudo apt-get install -y -q git
fi

if ! command -v node &> /dev/null; then
    echo "Installing Node.js v18..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y -q nodejs
fi

echo "✓ Prerequisites installed"
echo ""

# Clone or update repository
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Repository already exists at $INSTALL_DIR, updating..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "Cloning repository..."
    mkdir -p "$(dirname "$INSTALL_DIR")"
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo "✓ Repository ready"
echo ""

# Install dependencies
echo "Installing dependencies..."
cd "$INSTALL_DIR/$PROJECT_SUBDIR"

echo "  Installing server dependencies..."
npm install > /dev/null 2>&1 || npm install

if [ -d "client" ]; then
    echo "  Installing client dependencies..."
    cd client
    npm install > /dev/null 2>&1 || npm install
    npm run build > /dev/null 2>&1 || npm run build
    cd ..
fi

echo "✓ Dependencies installed"
echo ""

# Optional: Enable UART
read -p "Enable UART for Pico communication? (y/n) [n]: " -r enable_uart
if [[ $enable_uart =~ ^[Yy]$ ]]; then
    echo "Enabling UART..."
    
    for CONFIG_FILE in /boot/firmware/config.txt /boot/config.txt; do
        if [ -f "$CONFIG_FILE" ]; then
            if ! grep -q "dtoverlay=disable-bt" "$CONFIG_FILE" 2>/dev/null; then
                sudo tee -a "$CONFIG_FILE" > /dev/null <<EOF

# UART Configuration for Radar Project
enable_uart=1
dtoverlay=disable-bt
EOF
                echo "✓ UART enabled in $CONFIG_FILE"
                echo "⚠ REBOOT REQUIRED: Run 'sudo reboot' to apply changes"
            else
                echo "✓ UART already configured"
            fi
            break
        fi
    done
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                 INSTALLATION COMPLETE!                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Start the application:"
echo "     sudo systemctl start radar-app"
echo ""
echo "  2. Check status:"
echo "     sudo systemctl status radar-app"
echo ""
echo "  3. View logs:"
echo "     sudo journalctl -u radar-app -f"
echo ""
echo "  4. Access web interface:"
echo "     http://raspberrypi.local:3000"
echo ""
