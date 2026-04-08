#!/bin/bash
# Start Radar Client in Kiosk Mode
# Runs Chromium fullscreen on local display
# Server is still accessible from network on port 3000

set -e

SERVER="http://localhost:3000"
CACHE="/tmp/chromium-cache"
DATA="/tmp/chromium-data"
LOG="/tmp/radar-client.log"

echo "[$(date)] Starting client in kiosk mode" >> "$LOG"

# Create cache dirs
mkdir -p "$CACHE" "$DATA"
chmod 700 "$CACHE" "$DATA"

# Wait for server
for i in {1..30}; do
    if curl -s "$SERVER" >/dev/null 2>&1; then
        echo "[$(date)] Server ready" >> "$LOG"
        break
    fi
    sleep 1
done

# Start Chromium fullscreen
/usr/bin/chromium-browser \
    --kiosk \
    --start-fullscreen \
    --no-first-run \
    --no-default-browser-check \
    --disable-sync \
    --disable-translate \
    --disable-extensions \
    --disable-plugins \
    --homepage="$SERVER" \
    --user-data-dir="$DATA" \
    --disk-cache-dir="$CACHE" \
    "$SERVER" \
    2>>"$LOG"
