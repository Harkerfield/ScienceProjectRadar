#!/bin/bash
# Radar Project - Update Checker on Startup
# Runs at system startup to check for updates from Git
# If updates found, pulls latest and restarts service
# Place this in /opt/radar-update/check-updates.sh
# Create systemd timer to run on startup

set -e

PROJECT_DIR="/home/pi/RadarProject"
PROJECT_SUBDIR="RaspberryPiRadarFullStackApplicationAndStepperController"
SERVICE_NAME="radar-app"
LOG_FILE="/var/log/radar-app-updates.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting update check..." >> "$LOG_FILE"

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Project directory not found: $PROJECT_DIR" >> "$LOG_FILE"
    exit 1
fi

cd "$PROJECT_DIR"

# Check for updates
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking for updates..." >> "$LOG_FILE"

# Fetch latest commits (without pulling yet)
git fetch origin main > /dev/null 2>&1 || {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Git fetch failed" >> "$LOG_FILE"
    exit 1
}

# Compare local vs remote
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] No updates available (already up to date)" >> "$LOG_FILE"
    exit 0
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Updates found! Pulling latest code..." >> "$LOG_FILE"

# Pull latest
git pull origin main >> "$LOG_FILE" 2>&1

# Reinstall dependencies
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Installing dependencies..." >> "$LOG_FILE"

cd "$PROJECT_DIR/$PROJECT_SUBDIR"

npm install >> "$LOG_FILE" 2>&1

if [ -d "client" ]; then
    cd client
    npm install >> "$LOG_FILE" 2>&1
    npm run build >> "$LOG_FILE" 2>&1
    cd ..
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Dependencies updated" >> "$LOG_FILE"

# Restart service
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restarting service: $SERVICE_NAME" >> "$LOG_FILE"

sudo systemctl restart "$SERVICE_NAME" >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Update complete! Service restarted." >> "$LOG_FILE"
