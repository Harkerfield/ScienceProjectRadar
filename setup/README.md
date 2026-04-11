# Radar Application Setup - Linux Only

Simple scripts to install and manage the Radar Application on Raspberry Pi.

## Auto-Start (Fully Automatic!)

🎉 **After installation, everything starts automatically on boot!**

No daily manual setup needed. Just power on the Pi:

1. **Update Checker** starts first (pulls latest code if internet available)
2. **Server** starts (Node.js on port 3000)
3. **Client** starts (Chromium fullscreen kiosk + network accessible)

---

## Quick Start

### First Time Installation

```bash
cd /path/to/RadarProject
bash setup/start.sh
# Choose option 1: INSTALL
```

**Time:** 15-25 minutes. Configures everything for auto-start.

### After Installation

```bash
sudo reboot
# That's it! Everything starts automatically
```

Access at:
- **Local:** HDMI monitor (auto-displays fullscreen)
- **Network:** http://raspberrypi.local:3000

---

## Available Commands

```bash
# Interactive menu
bash setup/start.sh

# Direct commands:
bash setup/start.sh install     # First time setup
bash setup/start.sh start       # Start services manually
bash setup/start.sh stop        # Stop services
bash setup/start.sh status      # Check status
bash setup/start.sh logs        # View recent logs
```

---

## Manual Service Control

```bash
# Start services (if not auto-started)
sudo systemctl start radar-server radar-client

# Stop services
sudo systemctl stop radar-server radar-client

# Restart services
sudo systemctl restart radar-server radar-client

# Check current status
sudo systemctl status radar-server
sudo systemctl status radar-client
sudo systemctl status radar-update-check

# Verify auto-start is enabled
sudo systemctl is-enabled radar-server
# Should output: enabled
```

---

## View Logs

```bash
# Server logs (real-time)
sudo journalctl -u radar-server -f

# Client logs (real-time)
sudo journalctl -u radar-client -f

# Update checker logs (real-time)
sudo journalctl -u radar-update-check -f

# Last 50 lines of server logs
sudo journalctl -u radar-server -n 50 --no-pager

# Search logs for errors
sudo journalctl -u radar-server | grep -i error
```

---

## Access the Application

### Local (on Raspberry Pi)
- Chromium displays automatically in fullscreen on HDMI

### From Other Computers (Ethernet or WiFi)
```
http://raspberrypi.local:3000
http://192.168.x.x:3000
```

Find Pi's IP:
```bash
hostname -I
```

---

## What Gets Installed

### Scripts
- `install.sh` - Full installation (run once)
- `start.sh` - Menu/control interface
- `start-client.sh` - Client launcher (called by systemd)
- `check-updates.sh` - Auto-update checker (runs on boot)

### System Services (Auto-Start Enabled)

1. **radar-server.service**
   - Node.js backend on port 3000
   - Starts after network is ready
   - Auto-restarts if crashes
   - Communicates with Pico via UART

2. **radar-client.service**
   - Chromium fullscreen kiosk display
   - Starts after server is ready
   - Displays on HDMI monitor
   - Still accessible from network on port 3000
   - Auto-restarts if crashes

3. **radar-update-check.service**
   - Runs on every system startup
   - Checks GitHub for updates
   - Auto-pulls latest if available
   - Reinstalls dependencies if needed
   - Restarts server if updated

### System Configuration
- UART enabled at /dev/ttyAMA0 (115200 baud)
- Bluetooth disabled (avoids UART conflicts)
- Chromium cache in /tmp
- Auto-update checking on system startup
- All services enabled for auto-start

---

## Features

✅ **Single Install** - Everything set up once
✅ **Fully Automatic** - All three services auto-start on boot
✅ **Auto-Restart** - Services restart if they crash
✅ **Auto-Update** - Checks GitHub and updates every boot
✅ **Network Access** - Access from other computers
✅ **Kiosk Display** - Fullscreen on HDMI + still accessible from network
✅ **UART Ready** - Pico communication enabled
✅ **Simple Control** - Easy menu for all tasks

---

## Troubleshooting

### Services Won't Auto-Start

```bash
# Check service status
sudo systemctl status radar-server

# View detailed errors
sudo journalctl -u radar-server -n 50

# Manually restart
sudo systemctl restart radar-server

# Verify auto-start is enabled
sudo systemctl is-enabled radar-server
# Should show: enabled

# If not enabled, enable it:
sudo systemctl enable radar-server
sudo systemctl enable radar-client
sudo systemctl enable radar-update-check
```

### Can't Access Dashboard from Another Computer

```bash
# 1. Check server is running
sudo systemctl status radar-server
# Should show: Active (running)

# 2. Find Pi's IP address
hostname -I
# Use this IP with :3000

# 3. Check firewall isn't blocking port 3000
sudo ufw status
# If enabled: sudo ufw allow 3000

# 4. View server logs for errors
sudo journalctl -u radar-server -f
```

### UART Not Working

```bash
# Check if configured
grep enable_uart /boot/config.txt
# Should show: enable_uart=1

# Check device exists
ls -la /dev/ttyAMA0
# Should exist

# If not present after checking config, reboot
sudo reboot
```

### Client (Kiosk) Won't Display

```bash
# Check client service
sudo systemctl status radar-client

# View client logs
sudo journalctl -u radar-client -f

# Restart client service
sudo systemctl restart radar-client

# Check if X11 display is available
echo $DISPLAY
# Should show :0 or similar
```

### Low Disk Space

```bash
# Check available space
df -h

# Clean npm cache
npm cache clean --force

# Clean package manager cache
sudo apt-get clean

# Remove old logs
sudo journalctl --vacuum=100M
```

---

## Useful Commands Reference

```bash
# Reboot system
sudo reboot

# Shutdown system
sudo shutdown -h now

# SSH into Pi
ssh pi@raspberrypi.local

# Find Pi's IP
hostname -I

# Check disk space
df -h

# Check memory
free -h

# Check running processes
ps aux | grep node

# Kill a process
sudo kill -9 <PID>

# View full system logs
sudo journalctl -f

# Clear old logs
sudo journalctl --vacuum=30d
```

---

## Files & Locations

```
Setup Scripts:
/home/pi/RadarProject/setup/
├── install.sh
├── start.sh
├── start-client.sh
└── check-updates.sh

Systemd Services:
/etc/systemd/system/
├── radar-server.service
├── radar-client.service
└── radar-update-check.service

Project Files:
/home/pi/RadarProject/
├── RadarApp-FullStack/
│   ├── server/
│   └── client/
└── RadarApp-Microcontroller/
```

---

## System Requirements

- Raspberry Pi (any current model: 4, 4B, 5, etc.)
- Raspberry Pi OS (32-bit or 64-bit, any recent version)
- 500MB+ free disk space
- Network connection (Ethernet or WiFi)
- HDMI monitor (optional - still accessible from network if not present)

---

## Notes

- **First boot after install:** Takes ~2-3 minutes for services to fully start
- **Updates:** Auto-checked every boot when internet available
- **UART:** Requires system reboot on first setup (done automatically)
- **Logs:** Check with `sudo journalctl -u radar-server -f`
- **Kiosk display:** Fullscreen but server still accessible from network
- **Default port:** 3000 for both server and client access

---

**Version:** 1.0  
**Platform:** Linux (Raspberry Pi)  
**Auto-Start:** ✅ Fully Enabled  
**Updated:** April 2026
