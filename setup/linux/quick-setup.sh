#!/bin/bash
# Quick Kiosk Setup - Fast version of the full setup
# Run this for a simplified setup

echo "=========================================="
echo "Radar Kiosk - Quick Setup"
echo "=========================================="

# Step 1: Core packages
echo "Installing packages..."
sudo apt-get update
sudo apt-get install -y nodejs npm chromium-browser xserver-xorg xinit python3 python3-pip git curl

# Step 2: Enable UART
echo "Enabling UART..."
echo "enable_uart=1" | sudo tee -a /boot/config.txt
echo "dtoverlay=disable-bt" | sudo tee -a /boot/config.txt
sudo sed -i 's/console=serial0,115200 //' /boot/cmdline.txt

# Step 3: Install dependencies
echo "Installing server dependencies..."
cd /home/pi/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/server
npm install

echo "Installing client dependencies..."
cd /home/pi/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/client
npm install

# Step 4: Copy scripts
echo "Setting up startup scripts..."
sudo cp /home/pi/radar-project/setup/systemd/radar-server.service /etc/systemd/system/
sudo cp /home/pi/radar-project/setup/systemd/radar-kiosk.service /etc/systemd/system/
cp /home/pi/radar-project/setup/start-kiosk.sh /home/pi/
chmod +x /home/pi/start-kiosk.sh

# Step 5: Enable services
echo "Enabling auto-start services..."
sudo systemctl daemon-reload
sudo systemctl enable radar-server.service
sudo systemctl enable radar-kiosk.service

echo ""
echo "=========================================="
echo "Quick setup complete!"
echo "=========================================="
echo ""
echo "IMPORTANT: Now reboot with: sudo reboot"
echo ""
echo "After reboot:"
echo "  - Server will start automatically"
echo "  - Browser will launch in fullscreen"
echo "  - UART will be available for Pico"
echo ""
echo "Check status:"
echo "  systemctl status radar-server"
echo "  systemctl status radar-kiosk"
echo ""
