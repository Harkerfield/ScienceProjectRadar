#!/bin/bash
# Radar Application - Universal Setup Launcher (Bash)
# Detects OS and runs appropriate setup script

set -e

echo "🌍 Radar Application - Cross-Platform Setup"
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
    if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        OS_TYPE="raspberry_pi"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS_TYPE="windows"
else
    OS_TYPE="unknown"
fi

echo "📱 Detected OS: $OS_TYPE"
echo ""

case "$OS_TYPE" in
    raspberry_pi)
        echo "🍓 Raspberry Pi detected"
        echo ""
        echo "Choose setup mode:"
        echo "  1) App Mode (Recommended - Kiosk display)"
        echo "  2) Full Stack (Advanced - Multiple services)"
        echo ""
        read -p "Enter choice (1-2): " choice
        
        if [ "$choice" = "1" ]; then
            echo "Starting App Mode setup..."
            sudo bash ../linux/app-setup.sh
        elif [ "$choice" = "2" ]; then
            echo "Starting Full Stack setup..."
            sudo bash ../linux/raspi-kiosk-setup.sh
        else
            echo "Invalid choice"
            exit 1
        fi
        ;;
    
    linux)
        echo "🐧 Linux detected"
        echo "Starting Linux setup..."
        bash ../linux/app-setup.sh
        ;;
    
    macos)
        echo "🍎 macOS detected"
        echo "Starting macOS setup (using Linux scripts)..."
        bash ../linux/app-setup.sh
        ;;
    
    windows)
        echo "🪟 Windows detected"
        echo "Please use: .\setup.ps1 (PowerShell) or .\win-setup.ps1"
        exit 1
        ;;
    
    *)
        echo "❌ Unknown OS type"
        echo "Please run the setup manually from the platform-specific folder"
        exit 1
        ;;
esac
