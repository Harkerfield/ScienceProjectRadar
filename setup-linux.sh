#!/bin/bash
# Radar Application - Quick Setup (Linux/Raspberry Pi)
# Interactive setup wizard for easy first-time setup and daily use

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

# Detect if running on Raspberry Pi
IS_PI=false
if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    IS_PI=true
fi

show_menu() {
    clear
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}   RADAR APPLICATION - SETUP WIZARD${NC}"
    echo -e "${BLUE}============================================${NC}\n"
    echo -e "${YELLOW}Choose your action:${NC}\n"
    echo -e "   1) ${GREEN}SETUP (first time only)${NC}"
    echo -e "   2) ${GREEN}START servers and dashboard${NC}"
    echo -e "   3) ${BLUE}CHECK status${NC}"
    echo -e "   4) ${YELLOW}STOP servers${NC}"
    echo -e "   5) ${YELLOW}LOGS${NC}"
    echo -e "   6) Exit\n"
}

do_setup() {
    clear
    echo -e "${BLUE}🔧 Running setup...${NC}\n"
    
    if [ "$IS_PI" = true ]; then
        echo -e "${YELLOW}Raspberry Pi detected${NC}"
        echo -e "\nChoose setup mode:"
        echo "   1) App Mode (Recommended - Kiosk display)"
        echo "   2) Full Stack (Advanced - Multiple services)"
        echo ""
        read -p "Enter choice (1-2): " pi_choice
        
        if [ "$pi_choice" = "1" ]; then
            sudo bash setup/linux/app-setup.sh
        elif [ "$pi_choice" = "2" ]; then
            sudo bash setup/linux/raspi-kiosk-setup.sh
        else
            echo "Invalid choice"
            read -p "Press Enter to continue"
            return
        fi
    else
        echo -e "${BLUE}Linux detected${NC}"
        bash setup/linux/app-setup.sh
    fi
    
    echo -e "\n${GREEN}✅ Setup complete!${NC}"
    read -p "Press Enter to continue"
}

do_start() {
    clear
    echo -e "${BLUE}🚀 Starting Radar Application...${NC}\n"
    
    if [ "$IS_PI" = true ]; then
        echo -e "${GREEN}Raspberry Pi - Check your HDMI display${NC}"
        sudo reboot
    else
        cd setup/linux
        bash app-setup.sh &
        cd ../..
    fi
}

do_status() {
    clear
    echo -e "${BLUE}📊 Checking status...${NC}\n"
    bash setup/linux/app-control.sh status
    read -p "Press Enter to continue"
}

do_stop() {
    clear
    echo -e "${YELLOW}🛑 Stopping servers...${NC}\n"
    bash setup/linux/app-control.sh stop
    echo -e "${GREEN}✅ Stopped!${NC}\n"
    read -p "Press Enter to continue"
}

do_logs() {
    clear
    echo -e "${BLUE}📋 Application logs:${NC}\n"
    bash setup/linux/app-control.sh logs
    read -p "Press Enter to continue"
}

# Handle command line arguments
if [ $# -gt 0 ]; then
    case "$1" in
        setup) do_setup; exit 0 ;;
        start) do_start; exit 0 ;;
        status) do_status; exit 0 ;;
        stop) do_stop; exit 0 ;;
        logs) do_logs; exit 0 ;;
    esac
fi

# Interactive menu loop
while true; do
    show_menu
    read -p "Enter your choice (1-6): " choice
    
    case $choice in
        1) do_setup ;;
        2) do_start ;;
        3) do_status ;;
        4) do_stop ;;
        5) do_logs ;;
        6) 
            echo -e "\n${BLUE}👋 Goodbye!${NC}\n"
            exit 0
            ;;
        *) 
            echo -e "${RED}❌ Invalid choice. Please try again.${NC}"
            sleep 1
            ;;
    esac
done
