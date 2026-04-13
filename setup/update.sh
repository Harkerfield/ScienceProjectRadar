#!/bin/bash
# Radar Application - Update Client, Server, and Restart Services
# Rebuilds client, updates server dependencies, and restarts all services

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m'

echo -e "\n${BLUE}╔═════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   radar APPLICATION - UPDATE & RESTART            ║${NC}"
echo -e "${BLUE}╚═════════════════════════════════════════════════════╝${NC}\n"

# Get project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo -e "${YELLOW}Project directory: $PROJECT_DIR${NC}\n"

# Verify directories exist
if [ ! -d "$PROJECT_DIR/RadarApp-FullStack" ]; then
    echo -e "${RED}✗ RadarApp-FullStack directory not found${NC}"
    exit 1
fi

# Step 1: Update Server
echo -e "${YELLOW}[1/3] Updating Server dependencies...${NC}"
cd "$PROJECT_DIR/RadarApp-FullStack/server"

echo "  Installing server packages..."
npm install -q 2>&1 | grep -v '^npm WARN' || true

echo -e "${GREEN}✓ Server dependencies updated${NC}"

# Step 2: Update Client
echo -e "\n${YELLOW}[2/3] Rebuilding Client...${NC}"
cd "$PROJECT_DIR/RadarApp-FullStack/client"

echo "  Cleaning build artifacts..."
rm -rf dist node_modules/.cache

echo "  Installing client packages..."
npm install -q 2>&1 | grep -v '^npm WARN' || true

echo "  Building Vue.js application..."
npm run build 2>&1 | grep -v '^npm WARN' || true

echo -e "${GREEN}✓ Client rebuilt successfully${NC}"

# Step 3: Restart Services
echo -e "\n${YELLOW}[3/3] Restarting services...${NC}"

echo "  Stopping services..."
sudo systemctl stop radar-server radar-client 2>/dev/null || true
sleep 1

echo "  Restarting server..."
sudo systemctl start radar-server

echo "  Restarting client..."
sudo systemctl start radar-client

sleep 2

# Verify services are running
echo ""
echo -e "${BLUE}Service Status:${NC}"
echo ""

SERVER_status=$(sudo systemctl is-active radar-server 2>/dev/null || echo "inactive")
CLIENT_status=$(sudo systemctl is-active radar-client 2>/dev/null || echo "inactive")

if [ "$SERVER_status" = "active" ]; then
    echo -e "${GREEN}✓ Server: active${NC}"
else
    echo -e "${RED}✗ Server: $SERVER_status${NC}"
fi

if [ "$CLIENT_status" = "active" ]; then
    echo -e "${GREEN}✓ Client: active${NC}"
else
    echo -e "${RED}✗ Client: $CLIENT_status${NC}"
fi

echo ""

# Summary
echo -e "${BLUE}╔═════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              UPDATE COMPLETE!                     ║${NC}"
echo -e "${BLUE}╚═════════════════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}Access the application:${NC}"
echo "  • Local:     http://localhost:3000"
echo "  • Network:   http://$(hostname -I | awk '{print $1}'):3000"
echo "  • mDNS:      http://$(hostname).local:3000"
echo ""

echo -e "${YELLOW}Useful commands:${NC}"
echo "  • Status:    sudo systemctl status radar-server"
echo "  • Logs:      sudo journalctl -u radar-server -f"
echo "  • Stop:      sudo systemctl stop radar-server radar-client"
echo "  • Restart:   sudo systemctl restart radar-server"
echo ""

if [ "$SERVER_status" != "active" ]; then
    echo -e "${RED}⚠️  Server not running. Check logs:${NC}"
    echo "  sudo journalctl -u radar-server -n 50"
    echo ""
fi
