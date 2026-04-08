#!/bin/bash
# Radar Application - First Time Installation
# Installs prerequisites, clones project, installs dependencies, configures system

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m'

PROJECT_DIR="/home/pi/RadarProject"
GIT_URL="https://github.com/Harkerfield/ScienceProjectRadar.git"

echo -e "\n${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   RADAR APPLICATION - INSTALLATION SCRIPT        ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}\n"

# Step 1: Install system prerequisites
echo -e "${YELLOW}[1/6] Installing system prerequisites...${NC}"
sudo apt-get update -qq
sudo apt-get install -y -qq \
    git \
    curl \
    wget \
    build-essential \
    nodejs \
    python3 python3-pip \
    chromium \
    xserver-xorg xinit x11-xserver-utils \
    unclutter

echo -e "${GREEN}✓ System packages installed${NC}"

# Step 2: Clone project from GitHub
echo -e "\n${YELLOW}[2/6] Downloading project from GitHub...${NC}"

if [ -d "$PROJECT_DIR" ]; then
    echo "  Directory exists, updating..."
    cd "$PROJECT_DIR"
    # Force clean update from remote
    git fetch
    git checkout -f
    git reset --hard @{u}
    git clean -fd
else
    echo "  Cloning from GitHub..."
    git clone "$GIT_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

echo -e "${GREEN}✓ Project ready at $PROJECT_DIR${NC}"

# Step 3: Install Node dependencies
echo -e "\n${YELLOW}[3/6] Installing Node.js dependencies...${NC}"

cd "$PROJECT_DIR/RaspberryPiRadarFullStackApplicationAndStepperController"

# Make sure pi user owns the project directory
sudo chown -R pi:pi "$PROJECT_DIR"

echo "  Server dependencies..."
cd server
su - pi -c "cd $PROJECT_DIR/RaspberryPiRadarFullStackApplicationAndStepperController/server && npm install -q 2>&1 | grep -v '^npm WARN' || true"
cd ..

echo "  Client dependencies..."
cd client
su - pi -c "cd $PROJECT_DIR/RaspberryPiRadarFullStackApplicationAndStepperController/client && npm install -q 2>&1 | grep -v '^npm WARN' || true"
su - pi -c "cd $PROJECT_DIR/RaspberryPiRadarFullStackApplicationAndStepperController/client && npm run build 2>&1 | grep -v '^npm WARN' || true"
cd ..

echo -e "${GREEN}✓ Node dependencies installed${NC}"

# Step 4: Configure UART for Pico communication
echo -e "\n${YELLOW}[4/6] Configuring UART...${NC}"

UART_CONFIG_NEEDED=0

# Determine which config file to use
if [ -f /boot/firmware/config.txt ]; then
    CONFIG_FILE="/boot/firmware/config.txt"
elif [ -f /boot/config.txt ]; then
    CONFIG_FILE="/boot/config.txt"
else
    echo -e "${RED}✗ Cannot find config.txt${NC}"
    exit 1
fi

# Check if UART is already configured
if ! sudo grep -q "enable_uart=1" "$CONFIG_FILE" 2>/dev/null; then
    echo "  Enabling UART..."
    
    sudo tee -a "$CONFIG_FILE" >/dev/null <<EOF

# Radar Project - UART Configuration
enable_uart=1
dtoverlay=disable-bt
EOF
    
    # Disable serial console if present
    sudo sed -i 's/serial0,115200 //' /boot/cmdline.txt 2>/dev/null || true
    
    UART_CONFIG_NEEDED=1
    echo -e "${YELLOW}  ⚠ UART enabled (reboot required)${NC}"
else
    echo "  UART already enabled"
fi

echo -e "${GREEN}✓ UART configured${NC}"

# Step 5: Create systemd services
echo -e "\n${YELLOW}[5/6] Creating system services...${NC}"

# Server service
sudo tee /etc/systemd/system/radar-server.service >/dev/null <<EOF
[Unit]
Description=Radar Application Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=$PROJECT_DIR/RaspberryPiRadarFullStackApplicationAndStepperController
ExecStart=/usr/bin/npm run server:start
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment="NODE_ENV=production"
Environment="PORT=3000"

[Install]
WantedBy=multi-user.target
EOF

# Client service (kiosk mode + network accessible)
sudo tee /etc/systemd/system/radar-client.service >/dev/null <<EOF
[Unit]
Description=Radar Application Client (Kiosk Display)
After=network-online.target radar-server.service
Wants=radar-server.service

[Service]
Type=simple
User=pi
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/pi/.Xauthority"
ExecStart=/bin/bash $PROJECT_DIR/setup/start-client.sh
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Auto-update check service (runs on startup)
sudo tee /etc/systemd/system/radar-update-check.service >/dev/null <<EOF
[Unit]
Description=Radar - Auto Update Check
After=network-online.target

[Service]
Type=oneshot
ExecStart=/bin/bash $PROJECT_DIR/setup/check-updates.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable radar-server.service radar-client.service radar-update-check.service
sudo systemctl enable radar-server.service
sudo systemctl enable radar-client.service  
sudo systemctl enable radar-update-check.service

echo -e "${GREEN}✓ Services created and enabled for auto-start${NC}"

# Step 6: Create config file
echo -e "\n${YELLOW}[6/6] Creating configuration...${NC}"

mkdir -p "$PROJECT_DIR/RaspberryPiRadarFullStackApplicationAndStepperController/server"

cat > "$PROJECT_DIR/RaspberryPiRadarFullStackApplicationAndStepperController/server/.env" <<EOF
NODE_ENV=production
PORT=3000
LOG_LEVEL=info
EOF

echo -e "${GREEN}✓ Configuration created${NC}"

# Summary
echo -e "\n${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              INSTALLATION COMPLETE!              ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}\n"

if [ $UART_CONFIG_NEEDED -eq 1 ]; then
    echo -e "${YELLOW}⚠️  REBOOT REQUIRED FOR UART${NC}\n"
    echo -e "${GREEN}Auto-start is configured!${NC}"
    echo -e "After reboot, services will start automatically:"
    echo "  • Update checker (runs first)"
    echo "  • Server (Node.js on port 3000)"
    echo "  • Client (Chromium kiosk fullscreen)"
    echo ""
    echo -e "${YELLOW}Complete setup:${NC}"
    echo "  sudo reboot"
    echo ""
else
    echo -e "${GREEN}✅ Ready - Services will auto-start on reboot${NC}\n"
    echo -e "${GREEN}To start now:${NC}"
    echo "  sudo reboot"
    echo ""
    echo -e "${GREEN}Or manually:${NC}"
    echo "  sudo systemctl start radar-server radar-client"
    echo ""
fi

echo -e "${YELLOW}Access the application:${NC}"
echo "  • Local kiosk: Auto-displays on HDMI after startup"
echo "  • Network: http://raspberrypi.local:3000"
echo "  • IP: http://\$(hostname -I | awk '{print \$1}'):3000"
echo ""

echo -e "${YELLOW}Useful commands:${NC}"
echo "  • Status: sudo systemctl status radar-server"
echo "  • Logs: sudo journalctl -u radar-server -f"
echo "  • Stop: sudo systemctl stop radar-server radar-client"
echo "  • Restart: sudo systemctl restart radar-server"
echo "  • Check auto-start: sudo systemctl is-enabled radar-server"
echo ""

if [ $UART_CONFIG_NEEDED -eq 1 ]; then
    echo -e "${YELLOW}⚠️  IMPORTANT: Reboot to enable UART${NC}"
    echo -e "${YELLOW}Services will auto-start after reboot.${NC}\n"
fi
