#!/bin/bash
# Radar Application - Simple Control Script
# Menu for common tasks

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

# Ensure user isn't running this directly as root
if [ "$(whoami)" = "root" ]; then
    echo -e "${RED}✗ error: Do not run this script as root${NC}"
    echo -e "${YELLOW}Run as regular user:${NC} bash setup/start.sh"
    exit 1
fi

# Get the actual user (works when called with or without sudo)
ACTUAL_USER="${SUDO_USER:-$(whoami)}"

# Handle Ctrl+C gracefully
trap 'echo -e "\n${GREEN}Exiting...${NC}\n"; exit 0' INT TERM

show_menu() {
    clear
    echo -e "\n${BLUE}╔═════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   RADAR APPLICATION - CONTROL        ║${NC}"
    echo -e "${BLUE}╚═════════════════════════════════════════╝${NC}\n"
    echo -e "${YELLOW}Choose action:${NC}\n"
    echo "  1) INSTALL (first time only)"
    echo "  2) START   (server + client)"
    echo "  3) stop    (all services)"
    echo "  4) status  (check services)"
    echo "  5) LOGS    (view logs)"
    echo "  6) EXIT"
    echo ""
}

# Parse command line
if [ $# -gt 0 ]; then
    case "$1" in
        install) sudo bash setup/install.sh; exit 0 ;;
        start) sudo systemctl start radar-server radar-client; exit 0 ;;
        stop) sudo systemctl stop radar-server radar-client; exit 0 ;;
        status) sudo systemctl status radar-server; echo ""; sudo systemctl status radar-client; exit 0 ;;
        logs) sudo journalctl -u radar-server -f; exit 0 ;;
    esac
fi

# Interactive menu
while true; do
    show_menu
    read -p "Choose (1-6): " choice
    
    case $choice in
        1)
            clear
            sudo bash setup/install.sh
            read -p $'\nPress Enter to return to menu...' dummy
            ;;
        2)
            echo -e "\n${GREEN}Starting services...${NC}"
            sudo systemctl start radar-server radar-client
            echo -e "${GREEN}✓ Started${NC}"
            echo -e "Access at: http://localhost:3000 or http://$(hostname -I | awk '{print $1}'):3000"
            read -p $'\nPress Enter to return to menu...' dummy
            ;;
        3)
            echo -e "\n${YELLOW}Stopping services...${NC}"
            sudo systemctl stop radar-server radar-client
            echo -e "${GREEN}✓ Stopped${NC}"
            read -p $'\nPress Enter to return to menu...' dummy
            ;;
        4)
            clear
            echo -e "\n${BLUE}Server Status:${NC}"
            sudo systemctl status radar-server --no-pager || true
            echo ""
            echo -e "${BLUE}Client Status:${NC}"
            sudo systemctl status radar-client --no-pager || true
            echo ""
            read -p "Press Enter to return to menu: " dummy
            ;;
        5)
            clear
            echo -e "\n${BLUE}Recent Logs (Ctrl+C to exit):${NC}\n"
            sudo journalctl -u radar-server -n 100 --no-pager
            read -p $'\nPress Enter to return to menu...' dummy
            ;;
        6)
            echo -e "\n${GREEN}Goodbye!${NC}\n"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            sleep 1
            ;;
    esac
done
