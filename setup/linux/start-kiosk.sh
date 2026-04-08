#!/bin/bash
# Radar Kiosk Start Script
# Launches Chromium in fullscreen kiosk mode pointing to the local server

set -e

# Configuration
SERVER_URL="http://localhost:3000"
CHROME_CACHE_DIR="/tmp/chromium-cache"
CHROME_DATA_DIR="/tmp/chromium-data"

echo "[$(date)] Starting Radar Kiosk..." >> /home/pi/radar-kiosk.log

# Create temporary directories for Chrome
mkdir -p "$CHROME_CACHE_DIR" "$CHROME_DATA_DIR"
chmod 700 "$CHROME_CACHE_DIR" "$CHROME_DATA_DIR"

# Wait for server to be ready (max 30 seconds)
echo "[$(date)] Waiting for server at $SERVER_URL..." >> /home/pi/radar-kiosk.log
for i in {1..30}; do
    if curl -s "$SERVER_URL/health" > /dev/null 2>&1; then
        echo "[$(date)] Server is ready!" >> /home/pi/radar-kiosk.log
        break
    fi
    echo "[$(date)] Attempt $i: Server not ready yet, waiting..." >> /home/pi/radar-kiosk.log
    sleep 1
done

# Launch Chromium in kiosk mode
echo "[$(date)] Launching Chromium in kiosk mode..." >> /home/pi/radar-kiosk.log

/usr/bin/chromium-browser \
    --new-window \
    --kiosk \
    --start-fullscreen \
    --disable-translate \
    --disable-background-networking \
    --disable-background-timer-throttling \
    --disable-backgrounding-occluded-windows \
    --disable-breakpad \
    --disable-client-side-phishing-detection \
    --disable-component-extensions-with-background-pages \
    --disable-component-update \
    --disable-default-apps \
    --disable-default-browser-check \
    --disable-device-discovery-notifications \
    --disable-extensions \
    --disable-extensions-except \
    --disable-extensions-file-access-check \
    --disable-extensions-http-throttling \
    --disable-extensions-ui \
    --disable-external-extensions-allowlisting \
    --disable-features=TranslateUI,Translate \
    --disable-field-trial-config \
    --disable-file-system \
    --disable-preconnect \
    --disable-printing \
    --disable-prompt-on-repost \
    --disable-sync \
    --disable-plugins \
    --disable-plugin-power-saver \
    --disable-popup-blocking \
    --disable-background-app \
    --no-default-browser-check \
    --no-first-run \
    --no-pings \
    --no-service-autorun \
    --homepage="$SERVER_URL" \
    --user-data-dir="$CHROME_DATA_DIR" \
    --disk-cache-dir="$CHROME_CACHE_DIR" \
    --disk-cache-size=10485760 \
    --media-cache-size=10485760 \
    "$SERVER_URL" \
    2>> /home/pi/radar-kiosk.log
