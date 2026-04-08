#!/bin/bash
# Radar Kiosk Service Manager
# Easy command-line control of all radar services

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Services
SERVICES=("radar-server" "radar-display" "radar-kiosk")

show_help() {
    cat << EOF
Radar Kiosk Service Manager

Usage: $(basename "$0") [COMMAND] [OPTIONS]

Commands:
    status              Show status of all services
    start               Start all services
    stop                Stop all services
    restart             Restart all services
    restart-server      Restart just the server
    restart-kiosk       Restart just the kiosk display
    logs                Show live logs from all services
    logs-server         Show live logs from server
    logs-kiosk          Show live logs from kiosk
    logs-display        Show live logs from display
    enable              Enable auto-start on boot
    disable             Disable auto-start on boot

Examples:
    $(basename "$0") status
    $(basename "$0") restart
    $(basename "$0") logs-server

EOF
}

show_status() {
    echo -e "${BLUE}Service Status:${NC}"
    for service in "${SERVICES[@]}"; do
        if systemctl is-active --quiet "$service"; then
            echo -e "  ${GREEN}✓${NC} $service - ${GREEN}Active${NC}"
        else
            echo -e "  ${RED}✗${NC} $service - ${RED}Inactive${NC}"
        fi
    done
    echo ""
    
    # Show resource usage
    echo -e "${BLUE}Resource Usage:${NC}"
    echo "  Memory: $(free -h | grep Mem | awk '{print $3 " / " $2}')"
    echo "  Disk: $(df -h / | tail -1 | awk '{print $3 " / " $2}')"
    echo "  CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
    echo "  Temperature: $(vcgencmd measure_temp 2>/dev/null | grep -o '[0-9.]*'°C || echo 'N/A')"
}

show_extended_status() {
    echo -e "${BLUE}Extended Service Status:${NC}"
    for service in "${SERVICES[@]}"; do
        echo ""
        echo -e "${YELLOW}$service:${NC}"
        systemctl status "$service" || true
    done
}

start_services() {
    echo -e "${YELLOW}Starting services...${NC}"
    for service in "${SERVICES[@]}"; do
        echo "  Starting $service..."
        sudo systemctl start "$service" || echo -e "    ${RED}Failed${NC}"
    done
    show_status
}

stop_services() {
    echo -e "${YELLOW}Stopping services...${NC}"
    for service in "${SERVICES[@]}"; do
        echo "  Stopping $service..."
        sudo systemctl stop "$service" || echo -e "    ${RED}Failed${NC}"
    done
    echo -e "${GREEN}Services stopped${NC}"
}

restart_services() {
    echo -e "${YELLOW}Restarting services...${NC}"
    for service in "${SERVICES[@]}"; do
        echo "  Restarting $service..."
        sudo systemctl restart "$service" || echo -e "    ${RED}Failed${NC}"
    done
    echo -e "${YELLOW}Waiting for services to start...${NC}"
    sleep 3
    show_status
}

restart_server() {
    echo -e "${YELLOW}Restarting radar-server...${NC}"
    sudo systemctl restart radar-server
    echo -e "${GREEN}Server restarted${NC}"
    sleep 2
    show_status
}

restart_kiosk() {
    echo -e "${YELLOW}Restarting radar-kiosk...${NC}"
    sudo systemctl restart radar-kiosk
    echo -e "${GREEN}Kiosk restarted${NC}"
    sleep 2
}

show_logs() {
    echo -e "${YELLOW}Showing live logs (Ctrl+C to exit)...${NC}"
    journalctl -u radar-server -u radar-kiosk -u radar-display -f
}

show_logs_server() {
    echo -e "${YELLOW}Showing server logs (Ctrl+C to exit)...${NC}"
    journalctl -u radar-server -f
}

show_logs_kiosk() {
    echo -e "${YELLOW}Showing kiosk logs (Ctrl+C to exit)...${NC}"
    journalctl -u radar-kiosk -f
}

show_logs_display() {
    echo -e "${YELLOW}Showing display logs (Ctrl+C to exit)...${NC}"
    journalctl -u radar-display -f
}

enable_autostart() {
    echo -e "${YELLOW}Enabling auto-start...${NC}"
    for service in "${SERVICES[@]}"; do
        echo "  Enabling $service..."
        sudo systemctl enable "$service"
    done
    echo -e "${GREEN}Auto-start enabled${NC}"
}

disable_autostart() {
    echo -e "${YELLOW}Disabling auto-start...${NC}"
    for service in "${SERVICES[@]}"; do
        echo "  Disabling $service..."
        sudo systemctl disable "$service"
    done
    echo -e "${GREEN}Auto-start disabled${NC}"
}

# Main
if [ $# -eq 0 ]; then
    show_status
else
    case "$1" in
        status)
            show_extended_status
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        restart-server)
            restart_server
            ;;
        restart-kiosk)
            restart_kiosk
            ;;
        logs)
            show_logs
            ;;
        logs-server)
            show_logs_server
            ;;
        logs-kiosk)
            show_logs_kiosk
            ;;
        logs-display)
            show_logs_display
            ;;
        enable)
            enable_autostart
            ;;
        disable)
            disable_autostart
            ;;
        help|--help|-h|?)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown command: $1${NC}"
            echo "Run '$(basename "$0") help' for usage information"
            exit 1
            ;;
    esac
fi
