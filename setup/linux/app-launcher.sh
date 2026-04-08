#!/bin/bash
# Radar Application Launcher
# Comprehensive startup script that:
# 1. Builds the client (if needed)
# 2. Starts the Node.js server
# 3. Launches Chromium as a standalone app

set -e

# Configuration
PROJECT_ROOT="/home/pi/radar-project"
SERVER_DIR="$PROJECT_ROOT/RaspberryPiRadarFullStackApplicationAndStepperController/server"
CLIENT_DIR="$PROJECT_ROOT/RaspberryPiRadarFullStackApplicationAndStepperController/client"
SERVER_PORT=3000
SERVER_URL="http://localhost:$SERVER_PORT"

# Logging
LOG_FILE="/home/pi/radar-app.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

log() {
    echo "[$TIMESTAMP] $1" >> "$LOG_FILE"
    echo "$1"
}

log_error() {
    echo "[$TIMESTAMP] [ERROR] $1" >> "$LOG_FILE"
    echo "[ERROR] $1"
}

# Initialize log
{
    echo ""
    echo "======================================"
    echo "Radar Application Startup"
    echo "======================================"
    echo "Time: $TIMESTAMP"
    echo "PID: $$"
} >> "$LOG_FILE"

log "Starting Radar Application..."

# ============================================================
# Step 1: Check if directories exist
# ============================================================
log "Checking project directories..."

if [ ! -d "$SERVER_DIR" ]; then
    log_error "Server directory not found: $SERVER_DIR"
    exit 1
fi

if [ ! -d "$CLIENT_DIR" ]; then
    log_error "Client directory not found: $CLIENT_DIR"
    exit 1
fi

log "✓ Directories verified"

# ============================================================
# Step 2: Install/Update server dependencies if needed
# ============================================================
log "Checking server dependencies..."

if [ ! -d "$SERVER_DIR/node_modules" ]; then
    log "Installing server dependencies..."
    cd "$SERVER_DIR"
    npm install --production >> "$LOG_FILE" 2>&1
    log "✓ Server dependencies installed"
else
    log "✓ Server dependencies already installed"
fi

# ============================================================
# Step 3: Build client if needed
# ============================================================
log "Checking client build..."

DIST_DIR="$CLIENT_DIR/dist"
if [ ! -d "$DIST_DIR" ] || [ -z "$(ls -A "$DIST_DIR" 2>/dev/null)" ]; then
    log "Building client application..."
    cd "$CLIENT_DIR"
    
    if [ ! -d "$CLIENT_DIR/node_modules" ]; then
        log "Installing client dependencies..."
        npm install --production >> "$LOG_FILE" 2>&1
    fi
    
    log "Running build process..."
    npm run build >> "$LOG_FILE" 2>&1
    log "✓ Client build completed"
else
    log "✓ Client already built"
fi

# ============================================================
# Step 4: Start Node.js server in background
# ============================================================
log "Starting Node.js server..."

cd "$SERVER_DIR"

# Start server with output to log and background
nohup npm start >> "$LOG_FILE" 2>&1 &
SERVER_PID=$!
log "Server started (PID: $SERVER_PID)"

# ============================================================
# Step 5: Wait for server to be ready
# ============================================================
log "Waiting for server to be ready..."

MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s "$SERVER_URL/health" >/dev/null 2>&1 || curl -s "$SERVER_URL" >/dev/null 2>&1; then
        log "✓ Server is ready and responding"
        break
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
    if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
        log "  Waiting... (attempt $ATTEMPT/$MAX_ATTEMPTS)"
        sleep 1
    fi
done

if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
    log_error "Server did not respond after $MAX_ATTEMPTS seconds"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# ============================================================
# Step 6: Launch Chromium as standalone app
# ============================================================
log "Launching Chromium application..."

# Create app window class for better window management
export DISPLAY=:0
export XAUTHORITY=/home/pi/.Xauthority

# Chromium flags for app mode
/usr/bin/chromium-browser \
    --app="$SERVER_URL" \
    --start-maximized \
    --no-first-run \
    --no-default-browser-check \
    --disable-sync \
    --disable-background-networking \
    --disable-client-side-phishing-detection \
    --disable-component-update \
    --disable-default-apps \
    --disable-extensions \
    --disable-extensions-file-access-check \
    --disable-extensions-http-throttling \
    --disable-field-trial-config \
    --disable-preconnect \
    --disable-printing \
    --disable-prompt-on-repost \
    --disable-translate \
    --disable-features=TranslateUI \
    --disable-features=Translate \
    --disable-plugins \
    --metrics-recording-only \
    --mute-audio \
    --disable-media-session-api \
    --disable-default-apps \
    --disable-popup-blocking \
    --disable-breakpad \
    --disable-client-side-phishing-detection \
    --no-service-autorun \
    --enable-features=OverlayScrollbar \
    2>> "$LOG_FILE" &

CHROME_PID=$!
log "Chromium launched (PID: $CHROME_PID)"

# ============================================================
# Step 7: Cleanup on exit
# ============================================================
cleanup() {
    log "Shutting down application..."
    
    # Kill Chromium
    if kill -0 $CHROME_PID 2>/dev/null; then
        kill $CHROME_PID 2>/dev/null || true
        sleep 1
        kill -9 $CHROME_PID 2>/dev/null || true
    fi
    
    # Kill server
    if kill -0 $SERVER_PID 2>/dev/null; then
        kill $SERVER_PID 2>/dev/null || true
        sleep 1
        kill -9 $SERVER_PID 2>/dev/null || true
    fi
    
    log "Application shutdown complete"
}

trap cleanup EXIT

# Wait for Chromium to close
log "Application running. Close Chromium window to exit."
wait $CHROME_PID 2>/dev/null || true

log "Chromium closed"
exit 0
