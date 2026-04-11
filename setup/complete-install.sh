#!/bin/bash
# Radar Application - Complete Install/Build/Restart
# Comprehensive setup script that handles first-time installation OR updates existing environment
# Ensures all dependencies are installed, builds the application, and restarts services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# ============================================================================
# INITIALIZATION
# ============================================================================

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Auto-detect the actual user (when running with sudo)
ACTUAL_USER="${INSTALL_USER:-${SUDO_USER:-$(whoami)}}"

# Prevent direct root execution
if [ "$ACTUAL_USER" = "root" ] && [ -z "$SUDO_USER" ]; then
    echo -e "\n${RED}✗ ERROR: Cannot install as root directly${NC}"
    echo -e "${YELLOW}Run via:${NC}"
    echo -e "  bash setup/complete-install.sh"
    echo -e "  ${YELLOW}or${NC}"
    echo -e "  INSTALL_USER=username sudo bash setup/complete-install.sh"
    echo ""
    exit 1
fi

# Detect if running on Raspberry Pi or local machine
IS_RPI=false
if [ -f /boot/cmdline.txt ] || [ -f /boot/firmware/cmdline.txt ]; then
    IS_RPI=true
fi

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  $1${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"
}

print_step() {
    echo -e "${YELLOW}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${MAGENTA}ℹ $1${NC}"
}

is_installed() {
    command -v "$1" &> /dev/null
}

check_directory() {
    if [ ! -d "$1" ]; then
        print_error "Directory not found: $1"
        return 1
    fi
    return 0
}

# ============================================================================
# MAIN SCRIPT
# ============================================================================

print_header "  RADAR APPLICATION - COMPLETE INSTALL/BUILD/RESTART"

echo -e "${YELLOW}Environment Detection:${NC}"
echo "  User: $ACTUAL_USER"
echo "  Project: $PROJECT_DIR"
if [ "$IS_RPI" = true ]; then
    echo -e "  Platform: ${GREEN}Raspberry Pi${NC}"
else
    echo -e "  Platform: ${YELLOW}Local/Desktop${NC}"
fi
echo ""

# ============================================================================
# STEP 1: VALIDATE SUDO ACCESS (Only for Pi)
# ============================================================================

if [ "$IS_RPI" = true ]; then
    print_step "[1/8] Validating sudo access..."
    
    sudo -v
    if [ $? -ne 0 ]; then
        print_error "Cannot proceed without sudo access"
        exit 1
    fi
    print_success "Sudo authenticated"
else
    echo -e "${MAGENTA}⊘ Skipping sudo validation (not on Raspberry Pi)${NC}"
fi

# ============================================================================
# STEP 2: VALIDATE PROJECT STRUCTURE
# ============================================================================

print_step "[2/8] Validating project structure..."

if ! check_directory "$PROJECT_DIR/RadarApp-FullStack"; then
    exit 1
fi

if ! check_directory "$PROJECT_DIR/RadarApp-FullStack/server"; then
    exit 1
fi

if ! check_directory "$PROJECT_DIR/RadarApp-FullStack/client"; then
    exit 1
fi

print_success "Project structure valid"

# ============================================================================
# STEP 3: INSTALL SYSTEM DEPENDENCIES (RPI only)
# ============================================================================

if [ "$IS_RPI" = true ]; then
    print_step "[3/8] Installing system prerequisites..."
    
    sudo bash -c "
        apt-get update -qq 2>/dev/null
        apt-get install -y -qq \
            git curl wget \
            build-essential \
            nodejs python3 python3-pip \
            chromium xserver-xorg xinit x11-xserver-utils unclutter \
            >/dev/null 2>&1
    " || print_error "Some packages may have failed to install (non-critical)"
    
    print_success "System packages installed/verified"
else
    print_step "[3/8] Checking for required tools (Local machine)..."
    
    # Check for Node.js
    if is_installed node; then
        echo "  Node.js: $(node --version)"
    else
        print_error "Node.js not found. Please install from https://nodejs.org/"
        exit 1
    fi
    
    # Check for npm
    if is_installed npm; then
        echo "  npm: $(npm --version)"
    else
        print_error "npm not found. Please install Node.js"
        exit 1
    fi
    
    print_success "Required tools verified"
fi

# ============================================================================
# STEP 4: INSTALL/UPDATE SERVER DEPENDENCIES
# ============================================================================

print_step "[4/8] Installing server dependencies..."

cd "$PROJECT_DIR/RadarApp-FullStack/server"

# Suppress npm warnings
npm install -q 2>&1 | grep -E "^(npm ERR|added|removed|up to date)" || true

if [ -f package-lock.json ]; then
    print_success "Server dependencies installed"
else
    print_error "Server dependencies installation may have failed"
    exit 1
fi

# ============================================================================
# STEP 5: INSTALL/UPDATE CLIENT DEPENDENCIES
# ============================================================================

print_step "[5/8] Installing client dependencies..."

cd "$PROJECT_DIR/RadarApp-FullStack/client"

npm install -q 2>&1 | grep -E "^(npm ERR|added|removed|up to date)" || true

if [ -f package-lock.json ]; then
    print_success "Client dependencies installed"
else
    print_error "Client dependencies installation may have failed"
    exit 1
fi

# ============================================================================
# STEP 6: BUILD CLIENT
# ============================================================================

print_step "[6/8] Building Vue.js client application..."

echo "  Cleaning build cache..."
rm -rf node_modules/.cache 2>/dev/null || true

echo "  Building application..."
npm run build -q 2>&1 | grep -E "^(npm|File|Building)" || true

if [ -d dist ] && [ -f "dist/index.html" ]; then
    print_success "Client built successfully ($(du -sh dist | cut -f1))"
else
    print_error "Client build failed - dist/index.html not found"
    exit 1
fi

# ============================================================================
# STEP 7: CREATE/UPDATE ENVIRONMENT CONFIGURATION
# ============================================================================

print_step "[7/8] Creating server configuration..."

cd "$PROJECT_DIR/RadarApp-FullStack/server"

cat > .env <<EOF
NODE_ENV=production
PORT=3000
LOG_LEVEL=info
EOF

print_success "Configuration created"

# ============================================================================
# STEP 8: RESTART SERVICES (RPI only)
# ============================================================================

if [ "$IS_RPI" = true ]; then
    print_step "[8/8] Restarting services..."
    
    # Stop services if they exist
    sudo systemctl stop radar-server 2>/dev/null || true
    sudo systemctl stop radar-client 2>/dev/null || true
    sleep 1
    
    # Start services
    echo "  Starting server..."
    sudo systemctl start radar-server 2>/dev/null || print_info "radar-server.service may not be installed yet"
    
    echo "  Starting client..."
    sudo systemctl start radar-client 2>/dev/null || print_info "radar-client.service may not be installed yet"
    
    sleep 2
    
    # Check service status
    echo ""
    echo -e "${BLUE}Service Status:${NC}"
    
    SERVER_STATUS=$(sudo systemctl is-active radar-server 2>/dev/null || echo "unknown")
    CLIENT_STATUS=$(sudo systemctl is-active radar-client 2>/dev/null || echo "unknown")
    
    if [ "$SERVER_STATUS" = "active" ]; then
        echo -e "  ${GREEN}✓ Server: active${NC}"
    else
        echo -e "  ${YELLOW}⚠ Server: $SERVER_STATUS${NC}"
    fi
    
    if [ "$CLIENT_STATUS" = "active" ]; then
        echo -e "  ${GREEN}✓ Client: active${NC}"
    else
        echo -e "  ${YELLOW}⚠ Client: $CLIENT_STATUS${NC}"
    fi
else
    print_step "[8/8] Service restart (skipped on local machine)"
    echo -e "  ${MAGENTA}To start the server locally:${NC}"
    echo "    cd $PROJECT_DIR/RadarApp-FullStack/server"
    echo "    npm start"
fi

# ============================================================================
# SUMMARY
# ============================================================================

print_header "  ✓ INSTALLATION COMPLETE!"

echo -e "${YELLOW}Application Status:${NC}"
echo "  Project directory: $PROJECT_DIR"
echo "  Server status: Ready to run"
echo "  Client status: Built and ready"
echo ""

if [ "$IS_RPI" = true ]; then
    echo -e "${YELLOW}Access the application:${NC}"
    echo "  • Local:    http://localhost:3000"
    HOSTNAME=$(hostname)
    echo "  • Network:  http://$HOSTNAME.local:3000"
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    if [ -n "$LOCAL_IP" ]; then
        echo "  • IP:       http://$LOCAL_IP:3000"
    fi
    echo ""
    
    echo -e "${YELLOW}Useful commands:${NC}"
    echo "  View server logs:     sudo journalctl -u radar-server -f"
    echo "  View client logs:     sudo journalctl -u radar-client -f"
    echo "  Service status:       sudo systemctl status radar-server"
    echo "  Rebuild & restart:    bash setup/complete-install.sh"
else
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  cd $PROJECT_DIR/RadarApp-FullStack/server"
    echo "  npm start"
    echo ""
    echo -e "${YELLOW}Then access at:${NC}"
    echo "  http://localhost:3000"
fi

echo ""
