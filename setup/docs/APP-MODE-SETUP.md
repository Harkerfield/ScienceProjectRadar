# Radar Application - Simplified Setup Guide

## Overview

This is a simplified, unified setup that:
- Automatically builds the Vue.js client
- Starts the Node.js server
- Launches Chromium as a standalone application
- Manages everything as a single systemd service

Perfect for kiosk mode or embedded display applications.

## Quick Start (Recommended)

### 1. Copy Setup to Raspberry Pi

```bash
# On Raspberry Pi
git clone <your-repo> /home/pi/radar-project
cd /home/pi/radar-project/setup
```

### 2. Run Setup

```bash
# Make script executable
chmod +x app-setup.sh

# Run setup (requires sudo)
sudo bash app-setup.sh
```

This will:
- ✅ Update system packages
- ✅ Install Node.js, npm, Chromium, X11
- ✅ Enable UART for Pico
- ✅ Create application launcher
- ✅ Configure systemd service

### 3. Reboot

```bash
sudo reboot
```

Everything auto-starts! The system will:
1. Start X11 display server
2. Build client (first time only)
3. Start Node.js server on port 3000
4. Launch Chromium as app displaying the dashboard

## Daily Usage

### Check Status
```bash
./app-control.sh status
```

### View Logs
```bash
./app-control.sh logs              # Live logs
./app-control.sh logs-short        # Last 50 lines
```

### Control Application
```bash
./app-control.sh restart           # Restart app
./app-control.sh stop              # Stop app
./app-control.sh start             # Start app
```

### Enable/Disable Auto-Start
```bash
./app-control.sh enable            # Auto-start on boot
./app-control.sh disable           # Don't auto-start
```

## What Happens at Startup

### Timeline
```
System boots
    ↓
X11 displays
    ↓
Systemd launches radar-app.service
    ↓
app-launcher.sh runs:
    ├─ Check directories
    ├─ Install server dependencies (if needed)
    ├─ Build client (if needed)
    ├─ Start Node.js server on :3000
    ├─ Wait for server to respond
    └─ Launch Chromium with --app flag
    ↓
Chromium displays app fullscreen
    ↓
Dashboard ready to use
```

### Build Behavior
- **First Boot:** Client builds (takes ~2 minutes)
- **Subsequent Boots:** Uses cached build
- **Auto-Rebuild:** If client code changes, manually run:
  ```bash
  cd ~/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/client
  npm run build
  ```

## Architecture

### Single Service Design
```
radar-app.service
    └── app-launcher.sh
        ├── npm install (server)
        ├── npm install (client)
        ├── npm run build (client)
        ├── npm start (server on :3000)
        └── chromium --app (displays app)
```

### Chromium App Mode
- `--app` flag makes it run as standalone application
- No address bar, no tabs
- Behaves like native app
- Window chrome hidden
- Integrates with Wayland/X11

## Configuration

### Server Settings
Edit: `/home/pi/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/server/.env`

Key settings:
```
NODE_ENV=production              # Production mode
PORT=3000                        # Server port
PICO_UART_ENABLED=true          # Pico communication
PICO_UART_PORT=/dev/ttyAMA0     # UART device
PICO_UART_BAUD_RATE=115200      # Baud rate
```

### Environment Variables
All created automatically by setup script. To modify:

```bash
# Edit environment
nano ~/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/server/.env

# Restart for changes to take effect
./app-control.sh restart
```

## Troubleshooting

### Application Won't Start
```bash
./app-control.sh status          # Check status
./app-control.sh logs            # View logs
journalctl -u radar-app -n 100   # Last 100 lines
```

### Server Issues
```bash
# Test server manually
cd ~/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/server
npm start

# Check port 3000
curl http://localhost:3000
```

### Chromium Not Displaying
```bash
# Test X11
echo $DISPLAY
ls -la ~/.Xauthority

# Try manual launch
DISPLAY=:0 /home/pi/app-launcher.sh
```

### UART Not Working
```bash
# Check device
ls -la /dev/ttyAMA0

# Verify config
grep enable_uart /boot/config.txt
grep disable-bt /boot/config.txt

# Reboot required if just enabled
sudo reboot
```

### Client Build Fails
```bash
# Check dependencies
cd ~/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/client
npm install

# Build manually
npm run build

# Check logs
journalctl -u radar-app -n 100 | grep -i build
```

## Advanced Operations

### Manual Startup
```bash
# Start server manually
cd ~/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/server
npm start

# In another terminal, launch app
DISPLAY=:0 /home/pi/app-launcher.sh
```

### Rebuild Client
```bash
cd ~/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/client
npm run build

# Restart to use new build
~/setup/app-control.sh restart
```

### Change Startup URL
The app always opens `http://localhost:3000` (you can modify in app-launcher.sh):

```bash
# Edit launcher
nano ~/app-launcher.sh

# Find this line and modify URL:
SERVER_URL="http://localhost:3000"

# Restart
./app-control.sh restart
```

### Remote Access
From another computer:
```bash
ssh pi@<pi-ip> ./setup/app-control.sh status
ssh pi@<pi-ip> ./setup/app-control.sh logs
ssh pi@<pi-ip> ./setup/app-control.sh restart
```

## File Structure

```
setup/
├── app-setup.sh                  ← Main setup (run once)
├── app-launcher.sh               ← Application launcher
├── app-control.sh                ← Daily management
├── systemd/
│   └── radar-app.service         ← Systemd service
├── deploy-modes.md               ← This file
└── Original files (deprecated)
```

## Features

✅ **Automatic Build**
- Client builds on first boot
- Uses cache on subsequent boots
- Can be manually triggered

✅ **Automatic Server Start**
- Starts after build completes
- Waits for responsiveness
- Confirms before launching app

✅ **Chromium App Mode**
- Fullscreen display
- No chrome/toolbars
- Behaves like native app
- Touch-friendly UI

✅ **Auto-Recovery**
- Restarts on crash
- Logs all events
- System resource monitoring

✅ **UART for Pico**
- Automatic enablement
- 115200 baud configured
- Ready for Pico Master communication

## Performance Tips

1. **First Boot**
   - Normal: 2-3 minutes to build client
   - Subsequent: 10-15 seconds to start

2. **Memory Optimization**
   - Already configured
   - GPU memory: 128MB
   - Audio disabled
   - Bluetooth disabled

3. **Network
   - Configure static IP for consistency
   - Use HDMI for display (faster than SSH)

## Maintenance

### Weekly
```bash
./app-control.sh status            # Check health
df -h                              # Disk usage
free -h                            # Memory usage
```

### Monthly
```bash
sudo apt-get update && sudo apt-get upgrade -y
./app-control.sh restart
```

### Quarterly
- Full system backup
- Node.js update check
- Performance review

## Logs Location

All logs go to systemd journal:
```bash
# Current session
journalctl -u radar-app -f

# Since yesterday
journalctl -u radar-app --since yesterday

# Last 100 lines
journalctl -u radar-app -n 100

# By time
journalctl -u radar-app --since "2 hours ago"
```

## Uninstall

```bash
# Stop service
sudo systemctl stop radar-app.service

# Disable auto-start
sudo systemctl disable radar-app.service

# Remove service
sudo rm /etc/systemd/system/radar-app.service
sudo systemctl daemon-reload

# Remove scripts
rm /home/pi/app-launcher.sh /home/pi/app-control.sh

# Remove environment
sudo cp /boot/config.txt.backup /boot/config.txt

sudo reboot
```

## Comparison: Old vs New Setup

| Feature | Previous | New |
|---------|----------|-----|
| Services | 3 (display, server, kiosk) | 1 (app) |
| Startup | Multiple stages | Single flow |
| Complexity | Moderate | Simple |
| Dependencies | Separate | Integrated |
| Build Client | Manual | Automatic |
| UART | Configured separately | Integrated |
| Control | Complex manager | Simple control |
| Logs | Multiple sources | Single log |

## Support

### Quick Diagnostics
```bash
./app-control.sh status            # See everything
journalctl -u radar-app -n 50      # Recent logs
curl http://localhost:3000         # Server check
```

### Common Issues
```bash
# App won't start
journalctl -u radar-app | grep ERROR

# UART not working
ls -la /dev/ttyAMA0
journalctl -u radar-app | grep -i uart

# Chromium not displaying
ps aux | grep chromium
journalctl -u radar-app | grep -i display
```

## Next Steps

1. ✅ Run `app-setup.sh`
2. ✅ Reboot
3. ✅ Access at http://<pi-ip>:3000 from any device on network
4. ✅ Connect Pico Master via UART
5. ✅ Test controls in dashboard
6. ✅ Use `app-control.sh` for daily management

---

**Version:** 1.0  
**Updated:** April 2026  
**Status:** Production Ready
