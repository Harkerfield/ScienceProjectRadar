#!/bin/bash
# Deploy Radar Project to Raspberry Pi
# Bash script for Linux/Mac - Copies repo and runs setup on Pi
# Usage: ./deploy-to-pi.sh -h raspberrypi.local -u pi

set -e

# Defaults
PI_HOST="${PI_HOST:-raspberrypi.local}"
PI_USER="${PI_USER:-pi}"
PROJECT_PATH="${PROJECT_PATH:-.}"
PI_PROJECT_DIR="${PI_PROJECT_DIR:-/home/pi/RadarProject}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            PI_HOST="$2"
            shift 2
            ;;
        -u|--user)
            PI_USER="$2"
            shift 2
            ;;
        -p|--path)
            PROJECT_PATH="$2"
            shift 2
            ;;
        -d|--dest)
            PI_PROJECT_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         RADAR PROJECT - DEPLOY TO RASPBERRY PI                ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
echo -e "${GREEN}Configuration:${NC}"
echo "  Pi Host:        $PI_HOST"
echo "  Pi User:        $PI_USER"
echo "  Project Dir:    $PROJECT_PATH"
echo "  Destination:    $PI_PROJECT_DIR"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v ssh &> /dev/null; then
    echo -e "${RED}ERROR: SSH not found. Please install openssh-client.${NC}"
    exit 1
fi

if ! command -v scp &> /dev/null; then
    echo -e "${RED}ERROR: SCP not found.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ SSH tools available${NC}"
echo ""

# Test connection
echo -e "${YELLOW}Testing connection to $PI_HOST...${NC}"
if ssh $PI_USER@$PI_HOST "echo 'Connection OK'" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connected to Pi successfully${NC}"
else
    echo -e "${RED}ERROR: Cannot connect to $PI_USER@$PI_HOST${NC}"
    echo -e "${YELLOW}Make sure:${NC}"
    echo "  1. Raspberry Pi is powered on and connected"
    echo "  2. Hostname is correct (check with 'ping $PI_HOST')"
    echo "  3. SSH is enabled on Pi"
    echo ""
    exit 1
fi

echo ""

# Deployment method
echo -e "${GREEN}Deployment Method:${NC}"
echo "  1. Clone from Git repository (recommended)"
echo "  2. Copy via SCP/rsync (local copy)"
echo ""

read -p "Select method (1 or 2) [default: 1]: " method
method=${method:-1}

echo ""

if [ "$method" = "1" ]; then
    # Git clone method
    echo -e "${CYAN}Using Git clone method...${NC}"
    echo ""
    
    read -p "Enter Git repository URL: " GIT_URL
    
    if [ -z "$GIT_URL" ]; then
        echo -e "${RED}ERROR: Git URL required${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${YELLOW}Cloning repository to Pi...${NC}"
    
    ssh $PI_USER@$PI_HOST bash <<EOF
set -e
echo "Creating project directory..."
mkdir -p \$(dirname $PI_PROJECT_DIR)
cd \$(dirname $PI_PROJECT_DIR)

if [ -d \$(basename $PI_PROJECT_DIR) ]; then
    echo "Project directory already exists, updating..."
    cd \$(basename $PI_PROJECT_DIR)
    git pull origin main
else
    echo "Cloning repository..."
    git clone $GIT_URL \$(basename $PI_PROJECT_DIR)
    cd \$(basename $PI_PROJECT_DIR)
fi

echo "Repository ready at $PI_PROJECT_DIR"
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Repository cloned successfully${NC}"
    else
        echo -e "${RED}ERROR: Git clone failed${NC}"
        exit 1
    fi

else
    # SCP/rsync copy method
    echo -e "${CYAN}Using SCP/rsync copy method...${NC}"
    echo ""
    
    if [ ! -d "$PROJECT_PATH" ]; then
        echo -e "${RED}ERROR: Project path not found: $PROJECT_PATH${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Creating destination directory on Pi...${NC}"
    ssh $PI_USER@$PI_HOST "mkdir -p $PI_PROJECT_DIR"
    
    echo -e "${YELLOW}Copying files to Pi (this may take a minute)...${NC}"
    
    # Check if rsync is available
    if ssh $PI_USER@$PI_HOST "which rsync" > /dev/null 2>&1; then
        echo -e "${CYAN}Using rsync for efficient copy...${NC}"
        rsync -avz --delete \
            --exclude 'node_modules' \
            --exclude '.env' \
            --exclude '.git' \
            --exclude 'dist' \
            --exclude '.vscode' \
            "$PROJECT_PATH/" "$PI_USER@$PI_HOST:$PI_PROJECT_DIR/"
    else
        echo -e "${YELLOW}rsync not available, using scp...${NC}"
        # Recursive copy with scp
        scp -r "$PROJECT_PATH/"* "$PI_USER@$PI_HOST:$PI_PROJECT_DIR/"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Files copied successfully${NC}"
    else
        echo -e "${YELLOW}⚠ Copy completed with warnings${NC}"
    fi
fi

echo ""

# Run setup script on Pi
echo -e "${YELLOW}Running setup on Pi...${NC}"
echo ""

ssh $PI_USER@$PI_HOST bash <<'SETUP_SCRIPT'
set -e

echo "============================================================"
echo "RASPBERRY PI SETUP - Radar Project"
echo "============================================================"
echo ""

PROJECT_DIR="{{PROJECT_DIR}}"
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
    python3-pip \
    rsync

echo "[3/6] Enabling UART/Serial..."
UART_ENABLED=0
for CONFIG_FILE in /boot/firmware/config.txt /boot/config.txt; do
    if [ -f "$CONFIG_FILE" ]; then
        if ! grep -q "dtoverlay=disable-bt" "$CONFIG_FILE" 2>/dev/null; then
            echo "Adding UART configuration to $CONFIG_FILE..."
            sudo tee -a "$CONFIG_FILE" > /dev/null <<EOF

# UART Configuration for Radar Project
enable_uart=1
dtoverlay=disable-bt
EOF
            UART_ENABLED=1
        else
            echo "UART already configured"
        fi
        break
    fi
done

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
if [ -d "client" ]; then
    echo "  Installing client dependencies..."
    cd client
    npm install > /dev/null 2>&1
    npm run build > /dev/null 2>&1
    cd ..
fi

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
Environment="NODE_ENV=production"
Environment="PORT=3000"

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
echo "  1. Start service: sudo systemctl start radar-app"
echo "  2. Check status: sudo systemctl status radar-app"
echo "  3. View logs: sudo journalctl -u radar-app -f"
echo ""

if [ "$UART_ENABLED" = "1" ]; then
    echo "IMPORTANT: Reboot Pi for UART changes to take effect:"
    echo "  sudo reboot"
    echo ""
fi
SETUP_SCRIPT

SETUP_STATUS=$?

if [ $SETUP_STATUS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Setup completed successfully!${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠ Setup completed with warnings${NC}"
fi

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    DEPLOYMENT SUMMARY                          ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Project Location:  $PI_PROJECT_DIR${NC}"
echo -e "${CYAN}Start Service:     sudo systemctl start radar-app${NC}"
echo -e "${CYAN}Check Status:      sudo systemctl status radar-app${NC}"
echo -e "${CYAN}View Logs:         sudo journalctl -u radar-app -f${NC}"
echo -e "${CYAN}Access App:        http://$PI_HOST:3000${NC}"
echo ""
echo -e "${CYAN}SSH to Pi:         ssh $PI_USER@$PI_HOST${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT: Check if UART reboot was needed${NC}"
echo -e "${YELLOW}If UART was configured, run: sudo reboot${NC}"
echo ""
