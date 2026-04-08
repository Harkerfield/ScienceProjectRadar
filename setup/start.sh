#!/bin/bash
# Radar Application - Simple Control Script
# Menu for common tasks

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

show_menu() {
    clear
    echo -e "\n${BLUE}╔═════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   RADAR APPLICATION - CONTROL        ║${NC}"
    echo -e "${BLUE}╚═════════════════════════════════════════╝${NC}\n"
    echo -e "${YELLOW}Choose action:${NC}\n"
    echo "  1) INSTALL (first time only)"
    echo "  2) START   (server + client)"
    echo "  3) STOP    (all services)"
    echo "  4) STATUS  (check services)"
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
            read -p "Press Enter to continue"
            ;;
        2)
            echo -e "\n${GREEN}Starting services...${NC}"
            sudo systemctl start radar-server radar-client
            echo -e "${GREEN}✓ Started${NC}"
            echo -e "Access at: http://localhost:3000"
            read -p "Press Enter to continue"
            ;;
        3)
            echo -e "\n${YELLOW}Stopping services...${NC}"
            sudo systemctl stop radar-server radar-client
            echo -e "${GREEN}✓ Stopped${NC}"
            read -p "Press Enter to continue"
            ;;
        4)
            clear
            echo -e "\n${BLUE}Server Status:${NC}"
            sudo systemctl status radar-server --no-pager || true
            echo ""
            echo -e "${BLUE}Client Status:${NC}"
            sudo systemctl status radar-client --no-pager || true
            read -p "Press Enter to continue"
            ;;
        5)
            clear
            echo -e "\n${BLUE}Recent Logs (Ctrl+C to exit):${NC}\n"
            sudo journalctl -u radar-server -n 30 --no-pager
            read -p "Press Enter to continue"
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
