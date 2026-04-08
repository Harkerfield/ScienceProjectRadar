#!/bin/bash
# Radar Kiosk Hardware & Configuration Validator
# Checks UART, services, network, and hardware status

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASS=0
FAIL=0
WARN=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARN++))
}

echo -e "${BLUE}=========================================="
echo "Radar Kiosk Hardware & Configuration Check"
echo "==========================================${NC}"
echo ""

# ============================================================
# Hardware Checks
# ============================================================
echo -e "${BLUE}[1] Hardware Status${NC}"

# CPU Temperature
TEMP=$(vcgencmd measure_temp 2>/dev/null | grep -o '[0-9.]*' || echo "0")
TEMP_INT=${TEMP%.*}
if [ "$TEMP_INT" -lt 60 ]; then
    check_pass "CPU Temperature: ${TEMP}°C (Normal)"
elif [ "$TEMP_INT" -lt 80 ]; then
    check_warn "CPU Temperature: ${TEMP}°C (Warm)"
else
    check_fail "CPU Temperature: ${TEMP}°C (Critical)"
fi

# Memory
TOTAL_MEM=$(free -h | grep Mem | awk '{print $2}')
USED_MEM=$(free -h | grep Mem | awk '{print $3}')
USED_PERCENT=$(free | grep Mem | awk '{printf("%.0f", $3/$2*100)}')
if [ "$USED_PERCENT" -lt 80 ]; then
    check_pass "Memory: $USED_MEM / $TOTAL_MEM ($USED_PERCENT% used)"
else
    check_warn "Memory: $USED_MEM / $TOTAL_MEM ($USED_PERCENT% used - high)"
fi

# Disk Space
DISK_USED=$(df -h / | tail -1 | awk '{print $3}')
DISK_TOTAL=$(df -h / | tail -1 | awk '{print $2}')
DISK_PERCENT=$(df / | tail -1 | awk '{printf("%.0f", $3/$2*100)}')
if [ "$DISK_PERCENT" -lt 80 ]; then
    check_pass "Disk Space: $DISK_USED / $DISK_TOTAL ($DISK_PERCENT% used)"
else
    check_fail "Disk Space: $DISK_USED / $DISK_TOTAL ($DISK_PERCENT% used - full)"
fi

echo ""

# ============================================================
# UART Checks
# ============================================================
echo -e "${BLUE}[2] UART Configuration${NC}"

# Check if UART device exists
if [ -e /dev/ttyAMA0 ]; then
    check_pass "UART Device /dev/ttyAMA0 exists"
else
    check_fail "UART Device /dev/ttyAMA0 not found"
fi

# Check UART permissions
if [ -r /dev/ttyAMA0 ] && [ -w /dev/ttyAMA0 ]; then
    check_pass "UART permissions OK (readable and writable)"
else
    check_fail "UART permissions issue (not readable/writable)"
fi

# Check boot config
if grep -q "enable_uart=1" /boot/config.txt; then
    check_pass "UART enabled in /boot/config.txt"
else
    check_fail "UART not enabled in /boot/config.txt"
fi

# Check serial console disabled
if ! grep -q "console=serial" /boot/cmdline.txt && ! grep -q "console=ttyAMA0" /boot/cmdline.txt; then
    check_pass "Serial console disabled"
else
    check_fail "Serial console still enabled - may conflict with Pico"
fi

# Check Bluetooth disabled
if grep -q "dtoverlay=disable-bt" /boot/config.txt; then
    check_pass "Bluetooth disabled (frees UART)"
else
    check_warn "Bluetooth not disabled (uses same UART pins)"
fi

echo ""

# ============================================================
# Service Checks
# ============================================================
echo -e "${BLUE}[3] Systemd Services${NC}"

for service in radar-server radar-kiosk radar-display; do
    if systemctl is-enabled --quiet "$service" 2>/dev/null; then
        check_pass "Service $service is enabled for auto-start"
    else
        check_warn "Service $service is NOT enabled for auto-start"
    fi
    
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        check_pass "Service $service is currently running"
    else
        check_fail "Service $service is NOT running"
    fi
done

echo ""

# ============================================================
# Network Checks
# ============================================================
echo -e "${BLUE}[4] Network Configuration${NC}"

# Check hostname
HOSTNAME=$(hostname)
check_pass "Hostname: $HOSTNAME"

# Check IP address
IP_ADDR=$(hostname -I | awk '{print $1}')
if [ -n "$IP_ADDR" ]; then
    check_pass "IP Address: $IP_ADDR"
else
    check_fail "No IP address assigned"
fi

# Check DNS
if grep -q "nameserver" /etc/resolv.conf; then
    DNS=$(grep "nameserver" /etc/resolv.conf | head -1 | awk '{print $2}')
    check_pass "DNS configured: $DNS"
else
    check_fail "DNS not configured"
fi

# Check internet connectivity
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    check_pass "Internet connectivity OK"
else
    check_warn "No internet connectivity (may be OK for local use)"
fi

echo ""

# ============================================================
# Server Checks
# ============================================================
echo -e "${BLUE}[5] Server Status${NC}"

# Check if server is responding
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    check_pass "Server responding on http://localhost:3000"
else
    check_fail "Server not responding on localhost:3000"
fi

# Check server on network IP
if [ -n "$IP_ADDR" ]; then
    if curl -s http://"$IP_ADDR":3000 >/dev/null 2>&1; then
        check_pass "Server accessible from network ($IP_ADDR:3000)"
    else
        check_fail "Server not accessible from network"
    fi
fi

echo ""

# ============================================================
# Display/X11 Checks
# ============================================================
echo -e "${BLUE}[6] Display (X11/Chromium)${NC}"

# Check if X is running
if pgrep -x "X" >/dev/null; then
    check_pass "X11 server is running"
else
    check_fail "X11 server is NOT running"
fi

# Check if Chromium is running
if pgrep -x "chromium" >/dev/null || pgrep -x "chrome" >/dev/null; then
    check_pass "Chromium browser is running"
else
    check_fail "Chromium browser is NOT running"
fi

# Check DISPLAY variable
if [ -n "$DISPLAY" ]; then
    check_pass "DISPLAY variable set: $DISPLAY"
else
    check_warn "DISPLAY variable not set (may be OK for service context)"
fi

echo ""

# ============================================================
# File/Directory Checks
# ============================================================
echo -e "${BLUE}[7] Project Files${NC}"

# Check main directories
for dir in server client; do
    DIR_PATH="/home/pi/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/$dir"
    if [ -d "$DIR_PATH" ]; then
        check_pass "Directory $dir exists"
    else
        check_fail "Directory $dir NOT found"
    fi
done

# Check node_modules
SERVER_MODULES="/home/pi/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/server/node_modules"
if [ -d "$SERVER_MODULES" ]; then
    check_pass "Server dependencies installed"
else
    check_warn "Server node_modules not found (run npm install)"
fi

# Check startup scripts
for script in start-kiosk.sh service-manager.sh; do
    if [ -f "/home/pi/$script" ]; then
        check_pass "Startup script $script exists"
    else
        check_fail "Startup script $script NOT found"
    fi
done

echo ""

# ============================================================
# Environment Checks
# ============================================================
echo -e "${BLUE}[8] Environment Configuration${NC}"

ENV_FILE="/home/pi/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/server/.env"
if [ -f "$ENV_FILE" ]; then
    check_pass ".env file exists"
    
    # Check specific settings
    if grep -q "PICO_UART_ENABLED=true" "$ENV_FILE"; then
        check_pass "UART communication enabled in .env"
    else
        check_fail "UART communication NOT enabled in .env"
    fi
else
    check_fail ".env file NOT found"
fi

echo ""

# ============================================================
# Summary
# ============================================================
echo -e "${BLUE}=========================================="
echo "Check Summary"
echo "==========================================${NC}"
echo -e "${GREEN}Passed:${NC}  $PASS"
echo -e "${YELLOW}Warnings:${NC} $WARN"
echo -e "${RED}Failed:${NC}  $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    if [ $WARN -eq 0 ]; then
        echo -e "${GREEN}✓ All checks passed! System ready.${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ System ready but has warnings.${NC}"
        exit 0
    fi
else
    echo -e "${RED}✗ System has failures that need attention.${NC}"
    exit 1
fi
