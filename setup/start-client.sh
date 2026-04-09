#!/bin/bash
# Start Radar Client in Kiosk Mode
# Runs Chromium fullscreen on local display
# Server is still accessible from network on port 3000

# Don't exit on error - log and continue
set +e

SERVER="http://localhost:3000"
DISPLAY="${DISPLAY:-:0}"
CACHE="/tmp/chromium-cache"
DATA="/tmp/chromium-data"
LOG="/tmp/radar-client.log"

{
    echo "[$(date)] Starting client in kiosk mode on DISPLAY=$DISPLAY"
    
    # Create cache dirs
    mkdir -p "$CACHE" "$DATA"
    chmod 700 "$CACHE" "$DATA"
    
    # Wait for server
    echo "[$(date)] Waiting for server at $SERVER..."
    for i in {1..60}; do
        if curl -s "$SERVER" >/dev/null 2>&1; then
            echo "[$(date)] Server is ready!"
            break
        fi
        echo "[$(date)] Waiting... ($i/60)"
        sleep 1
    done
    
    # Check if server is running
    if ! curl -s "$SERVER" >/dev/null 2>&1; then
        echo "[$(date)] ERROR: Server not responding at $SERVER"
        echo "[$(date)] Chromium will attempt to connect when server is ready"
    fi
    
    # Check if display is available
    if [ -z "$DISPLAY" ] || ! xset -display "$DISPLAY" q >/dev/null 2>&1; then
        echo "[$(date)] WARNING: No X display available. Running in headless mode."
        echo "[$(date)] The web interface is still accessible from other computers."
        exit 0
    fi
    
    echo "[$(date)] Starting Chromium on $DISPLAY..."
    
    # Start Chromium fullscreen
    export DISPLAY
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
        2>&1
    
    RESULT=$?
    echo "[$(date)] Chromium exited with code: $RESULT"
    
} >> "$LOG" 2>&1
