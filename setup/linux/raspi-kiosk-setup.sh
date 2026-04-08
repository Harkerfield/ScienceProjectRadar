#!/bin/bash
# Raspberry Pi Full-Stack Kiosk Setup
# This script configures the Raspberry Pi for full kiosk mode with auto-start server

set -e

echo "=========================================="
echo "Raspberry Pi Radar Full-Stack Setup"
echo "=========================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVER_DIR="$PROJECT_ROOT/RaspberryPiRadarFullStackApplicationAndStepperController/server"
CLIENT_DIR="$PROJECT_ROOT/RaspberryPiRadarFullStackApplicationAndStepperController/client"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[1/8] Updating system packages...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

echo -e "${YELLOW}[2/8] Installing required packages...${NC}"
sudo apt-get install -y \
    nodejs npm \
    chromium-browser \
    xserver-xorg xinit \
    python3 python3-pip \
    git curl wget \
    build-essential \
    libpython3-dev

echo -e "${YELLOW}[3/8] Enabling UART for Pico communication...${NC}"
# Enable UART on GPIO pins
echo "Enabling UART..."

# Backup original config
sudo cp /boot/config.txt /boot/config.txt.backup

# Enable UART and disable Bluetooth
sudo bash -c 'cat >> /boot/config.txt << EOF

# UART Configuration for Pico Master
enable_uart=1
dtoverlay=disable-bt

# GPU Memory
gpu_mem=128

# Audio disable (frees up memory)
dtparam=audio=off
EOF'

# Disable serial console on UART0 to free it for Pico
sudo sed -i 's/.*console=\/dev\/ttyAMA0.*//g' /boot/cmdline.txt
sudo sed -i 's/console=serial0,115200 //' /boot/cmdline.txt

echo -e "${GREEN}✓ UART enabled (requires reboot to take effect)${NC}"

echo -e "${YELLOW}[4/8] Building Node.js server...${NC}"
cd "$SERVER_DIR"
npm install
npm run build 2>/dev/null || true

echo -e "${YELLOW}[5/8] Building Vue.js client...${NC}"
cd "$CLIENT_DIR"
npm install
npm run build

echo -e "${YELLOW}[6/8] Creating systemd services...${NC}"

# Create server service
sudo bash -c 'cat > /etc/systemd/system/radar-server.service << EOF
[Unit]
Description=Radar Full-Stack Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory='$SERVER_DIR'
EnvironmentFile='$SERVER_DIR'/.env
ExecStart=/usr/bin/node index.js
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF'

# Create kiosk browser service
sudo bash -c 'cat > /etc/systemd/system/radar-kiosk.service << EOF
[Unit]
Description=Radar Kiosk Display
After=display-manager.service radar-server.service
Wants=radar-server.service

[Service]
Type=simple
User=pi
Display=:0
DISPLAY=:0
ExecStart=/home/pi/start-kiosk.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=graphical.target
EOF'

# Create X server/display service
sudo bash -c 'cat > /etc/systemd/system/radar-display.service << EOF
[Unit]
Description=Radar Display Server
Before=radar-kiosk.service

[Service]
Type=forking
User=pi
ExecStart=/usr/bin/startx
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical.target
EOF'

echo -e "${GREEN}✓ Systemd services created${NC}"

echo -e "${YELLOW}[7/8] Creating startup scripts...${NC}"

# Create kiosk start script
cat > /home/pi/start-kiosk.sh << 'KIOSK_SCRIPT'
#!/bin/bash
# Wait for server to be ready
sleep 5

# Start Chromium in kiosk mode
export DISPLAY=:0
/usr/bin/chromium-browser \
    --new-window \
    --kiosk \
    --start-fullscreen \
    --no-first-run \
    --no-default-browser-check \
    --disable-sync \
    --disable-features=TranslateUI \
    --disable-background-networking \
    --disable-default-apps \
    --disable-extensions \
    --disable-plugins \
    --disable-preconnect \
    http://localhost:3000
KIOSK_SCRIPT

chmod +x /home/pi/start-kiosk.sh

# Create environment file for server
cat > "$SERVER_DIR/.env" << ENV_FILE
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

# API Base URL
VUE_APP_API_BASE_URL=http://localhost:3000/api

# Socket.io configuration
SOCKETIO_CORS_ORIGIN=http://localhost:3000
ENV_FILE

echo -e "${GREEN}✓ Startup scripts created${NC}"

echo -e "${YELLOW}[8/8] Enabling services...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable radar-server.service
sudo systemctl enable radar-kiosk.service
sudo systemctl enable radar-display.service

echo ""
echo -e "${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit $SERVER_DIR/.env if needed"
echo "2. Configure /boot/config.txt if needed"
echo "3. Reboot the Raspberry Pi: sudo reboot"
echo ""
echo "Services will auto-start:"
echo "  • radar-server.service (Node.js server on :3000)"
echo "  • radar-display.service (X server)"
echo "  • radar-kiosk.service (Chromium browser in kiosk mode)"
echo ""
echo "To check service status:"
echo "  systemctl status radar-server"
echo "  systemctl status radar-kiosk"
echo "  systemctl status radar-display"
echo ""
echo "To view logs:"
echo "  journalctl -u radar-server -f"
echo "  journalctl -u radar-kiosk -f"
echo ""
