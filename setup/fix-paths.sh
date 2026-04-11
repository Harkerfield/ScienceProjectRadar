#!/bin/bash
# Fix incorrect hardcoded paths in systemd services
# Use this if your installation created paths like /home/root/ instead of the correct user home

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m'

echo -e "\n${BLUE}╔═════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   RADAR - FIX INCORRECT INSTALLATION PATHS         ║${NC}"
echo -e "${BLUE}╚═════════════════════════════════════════════════════╝${NC}\n"

# Get actual user
ACTUAL_USER="${SUDO_USER:-$(whoami)}"

# Prevent running as root
if [ "$ACTUAL_USER" = "root" ] && [ -z "$SUDO_USER" ]; then
    echo -e "${RED}✗ ERROR: Must run with sudo as regular user, not as root${NC}"
    echo -e "${YELLOW}Usage: sudo bash $0${NC}"
    exit 1
fi

echo -e "${YELLOW}Current user: $ACTUAL_USER${NC}"
echo -e "${YELLOW}Expected project directory: /home/$ACTUAL_USER/RadarProject${NC}\n"

# Check if project directory exists
PROJECT_DIR="/home/$ACTUAL_USER/RadarProject"
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}✗ Project directory not found at $PROJECT_DIR${NC}"
    echo -e "${YELLOW}Please ensure the project is installed at: $PROJECT_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Project directory found${NC}\n"

# Stop services before making changes
echo -e "${YELLOW}Stopping services...${NC}"
sudo systemctl stop radar-server radar-client 2>/dev/null || true
echo -e "${GREEN}✓ Services stopped${NC}\n"

# Fix radar-server service
echo -e "${YELLOW}Updating radar-server.service...${NC}"
sudo bash -c "cat > /etc/systemd/system/radar-server.service << 'EOF'
[Unit]
Description=Radar Application Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$PROJECT_DIR/RadarApp-FullStack/server
ExecStart=/usr/bin/npm run server:start
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=\"NODE_ENV=production\"
Environment=\"PORT=3000\"

[Install]
WantedBy=multi-user.target
EOF
"
echo -e "${GREEN}✓ radar-server.service updated${NC}"

# Fix radar-client service
echo -e "${YELLOW}Updating radar-client.service...${NC}"
sudo bash -c "cat > /etc/systemd/system/radar-client.service << 'EOF'
[Unit]
Description=Radar Application Client (Kiosk Display)
After=network-online.target radar-server.service
Wants=radar-server.service

[Service]
Type=simple
User=$ACTUAL_USER
Environment=\"DISPLAY=:0\"
Environment=\"XAUTHORITY=/home/$ACTUAL_USER/.Xauthority\"
ExecStart=/bin/bash $PROJECT_DIR/setup/start-client.sh
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
"
echo -e "${GREEN}✓ radar-client.service updated${NC}"

# Fix radar-update-check service
echo -e "${YELLOW}Updating radar-update-check.service...${NC}"
sudo bash -c "cat > /etc/systemd/system/radar-update-check.service << 'EOF'
[Unit]
Description=Radar - Auto Update Check
After=network-online.target

[Service]
Type=oneshot
User=$ACTUAL_USER
ExecStart=/bin/bash $PROJECT_DIR/setup/check-updates.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
"
echo -e "${GREEN}✓ radar-update-check.service updated${NC}\n"

# Reload systemd
echo -e "${YELLOW}Reloading systemd services...${NC}"
sudo systemctl daemon-reload
echo -e "${GREEN}✓ Services reloaded${NC}\n"

# Verify the changes
echo -e "${YELLOW}Verifying service configuration...${NC}"
echo ""
echo "Server service ExecStart:"
sudo grep "ExecStart=" /etc/systemd/system/radar-server.service
echo ""
echo "Client service ExecStart:"
sudo grep "ExecStart=" /etc/systemd/system/radar-client.service
echo ""
echo "Client service User:"
sudo grep "User=" /etc/systemd/system/radar-client.service

echo ""
echo -e "${GREEN}✓ All services updated${NC}\n"

# Ready to start
echo -e "${YELLOW}Ready to start services:${NC}"
echo -e "  sudo systemctl start radar-server"
echo -e "  sudo systemctl start radar-client"
echo ""
echo -e "${YELLOW}Or use the control script:${NC}"
echo -e "  bash $PROJECT_DIR/setup/start.sh"
echo ""
