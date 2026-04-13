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
    
    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        echo "[$(date)] WARNING: curl not found, trying wget..."
        if command -v wget &> /dev/null; then
            for i in {1..60}; do
                if wget -O /dev/null -q "$SERVER" 2>/dev/null; then
                    echo "[$(date)] Server is ready!"
                    break
                fi
                echo "[$(date)] Waiting... ($i/60)"
                sleep 1
            done
        else
            echo "[$(date)] WARNING: Neither curl nor wget available, skipping server check"
        fi
    else
        for i in {1..60}; do
            if curl -s "$SERVER" >/dev/null 2>&1; then
                echo "[$(date)] Server is ready!"
                break
            fi
            echo "[$(date)] Waiting... ($i/60)"
            sleep 1
        done
    fi
    
    # Check if server is running
    if command -v curl &> /dev/null; then
        if ! curl -s "$SERVER" >/dev/null 2>&1; then
            echo "[$(date)] error: Server not responding at $SERVER"
            echo "[$(date)] Chromium will attempt to connect when server is ready"
        fi
    fi
    
    # Check if display is available
    if [ -z "$DISPLAY" ] || ! xset -display "$DISPLAY" q >/dev/null 2>&1; then
        echo "[$(date)] WARNING: No X display available. Running in headless mode."
        echo "[$(date)] The web interface is still accessible from other computers."
        exit 0
    fi
    
    echo "[$(date)] Starting Chromium on $DISPLAY..."
    
    # Find Chromium browser (try multiple locations)
    CHROMIUM_BIN=""
    for browser in /usr/bin/chromium-browser /usr/bin/chromium /snap/bin/chromium /usr/bin/google-chrome /usr/bin/google-chrome-stable; do
        if [ -x "$browser" ]; then
            CHROMIUM_BIN="$browser"
            echo "[$(date)] Found browser at: $CHROMIUM_BIN"
            break
        fi
    done
    
    if [ -z "$CHROMIUM_BIN" ]; then
        echo "[$(date)] error: Chromium browser not found at any known location"
        echo "[$(date)] Tried: /usr/bin/chromium-browser, /usr/bin/chromium, /snap/bin/chromium, /usr/bin/google-chrome"
        echo "[$(date)] Install with: sudo apt-get install chromium-browser"
        exit 1
    fi
    
    # Start Chromium fullscreen
    export DISPLAY
    "$CHROMIUM_BIN" \
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
