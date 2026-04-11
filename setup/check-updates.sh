#!/bin/bash
# Auto-Update Checker
# Runs on system startup to check and pull latest code if internet available

# Auto-detect the actual user (when running with sudo)
ACTUAL_USER="${SUDO_USER:-$(whoami)}"
PROJECT_DIR="/home/$ACTUAL_USER/RadarProject"
GIT_URL="https://github.com/Harkerfield/ScienceProjectRadar.git"

    
LOG="/tmp/radar-update-check.log"

{
    echo "[$(date)] Update check started"
    
    # Check for internet
    if ! ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        echo "[$(date)] No internet, skipping update"
        exit 0
    fi
    
    echo "[$(date)] Internet available, checking for updates..."
    cd "$PROJECT_DIR"
    
    # Fetch latest
    if ! git fetch origin main >/dev/null 2>&1; then
        echo "[$(date)] Failed to fetch"
        exit 1
    fi
    
    # Compare local vs remote
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)
    
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "[$(date)] Updates available, pulling..."
        git pull origin main >/dev/null 2>&1
        
        # Reinstall dependencies
        cd "$PROJECT_DIR/RadarApp-FullStack"
        npm install --production >/dev/null 2>&1
        
        
        if [ -d "client" ]; then
            cd client
            npm install >/dev/null 2>&1
            npm run build >/dev/null 2>&1
        fi
        
        echo "[$(date)] Updates installed, restarting server..."
        systemctl restart radar-server
    else
        echo "[$(date)] Already up to date"
    fi
    
} >>"$LOG" 2>&1

exit 0
