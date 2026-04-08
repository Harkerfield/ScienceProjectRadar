#!/bin/bash
# Simplified Radar App Setup
# Single-service setup using app-launcher

set -e

echo "=========================================="
echo "Radar Application - Simplified Setup"
echo "=========================================="

# Step 1: Update system
echo "[1/5] Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Step 2: Install required packages
echo "[2/5] Installing required packages..."
sudo apt-get install -y \
    nodejs npm \
    chromium-browser \
    xserver-xorg xinit \
    python3 python3-pip \
    curl

# Step 3: Enable UART
echo "[3/5] Enabling UART for Pico communication..."
sudo bash -c 'cat >> /boot/config.txt << EOF

# UART Configuration for Pico Master
enable_uart=1
dtoverlay=disable-bt
gpu_mem=128
dtparam=audio=off
EOF'

sudo sed -i 's/console=serial0,115200 //' /boot/cmdline.txt

echo "✓ UART enabled (requires reboot)"

# Step 4: Setup application launcher scripts
echo "[4/5] Setting up application launcher..."

# Make app launcher executable
chmod +x /home/pi/radar-project/setup/app-launcher.sh
cp /home/pi/radar-project/setup/app-launcher.sh /home/pi/
chmod +x /home/pi/app-launcher.sh

# Create environment file
cat > /home/pi/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/server/.env << ENV_FILE
NODE_ENV=production
PORT=3000
LOG_LEVEL=info

# Pico UART Configuration
PICO_UART_ENABLED=true
PICO_UART_PORT=/dev/ttyAMA0
PICO_UART_BAUD_RATE=115200
PICO_DATA_TIMEOUT=5000

# Client URL
CLIENT_URL=http://localhost:3000
VUE_APP_API_BASE_URL=http://localhost:3000/api

# Feature Flags
FEATURE_STEPPER=true
FEATURE_ACTUATOR=true
FEATURE_RADAR=true
FEATURE_PICO_COMM=true
ENV_FILE

# Step 5: Create systemd service
echo "[5/5] Creating systemd service..."

sudo cp /home/pi/radar-project/setup/systemd/radar-app.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable radar-app.service

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review environment: nano /home/pi/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/server/.env"
echo "2. Reboot: sudo reboot"
echo ""
echo "After reboot:"
echo "  • Server will start automatically"
echo "  • Client will build (first time)"
echo "  • Chromium will display app"
echo ""
echo "Check status:"
echo "  systemctl status radar-app"
echo "  journalctl -u radar-app -f"
echo ""
