# Raspberry Pi Kiosk Setup Package

Complete automated setup for configuring a Raspberry Pi as a full-featured kiosk display with auto-starting web server and Chromium app display, plus UART communication with Pico microcontroller.

## ⚡ Quick Start - Choose Your Platform

### 🪟 Windows PC (Development)
```powershell
# 1. Install Node.js from https://nodejs.org/
# 2. Open PowerShell as Administrator
cd C:\path\to\setup
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\win-setup.ps1
.\run-windows.ps1
# Opens localhost:5173 automatically
```

### 🍓 Raspberry Pi (Kiosk - Recommended)
```bash
# 1. SSH into Pi or use terminal
cd ~/radar-project/setup

# 2. Run setup (one time)
sudo bash app-setup.sh
sudo reboot

# After reboot: Everything auto-starts!
# Dashboard displays on HDMI, UART ready for Pico
```

### 🐧 Linux PC/Server (Development)
```bash
# 1. Install Node.js (apt, dnf, etc.)
cd ~/radar-project/setup

# 2. Run setup
bash app-setup.sh

# 3. Start manually
cd server && npm start &
cd ../client && npm run dev
# Opens localhost:5173
```

**[Full cross-platform guide →](CROSS-PLATFORM.md)**

## Multiple Setup Options

Want more control? Choose your deployment mode:

- **📱 [APP MODE](APP-MODE-SETUP.md)** - Single service, automatic everything (Raspberry Pi Recommended)
- **⚙️ [FULL STACK](RASPI_KIOSK_SETUP.md)** - Three services, granular control (Production)
- **🧪 [MANUAL](DEPLOYMENT-MODES.md)** - Development/testing

**[Compare all modes →](DEPLOYMENT-MODES.md)**

**[Cross-platform details →](CROSS-PLATFORM.md)**

## Scripts Overview

### App Mode (Recommended) ⭐

The easiest way to get started with automatic building and launching.

- **`app-setup.sh`** - One-command setup
- **`app-launcher.sh`** - Automatic build + start + display
- **`app-control.sh`** - Daily management
- **`APP-MODE-SETUP.md`** - Full documentation

**[Getting Started with App Mode →](APP-MODE-SETUP.md)**

### Full Stack Mode (Advanced)

Multiple independent services for granular control.

- **`raspi-kiosk-setup.sh`** - Complete setup
- **`quick-setup.sh`** - Fast alternative
- **`service-manager.sh`** - Service control
- **`validate-system.sh`** - System diagnostics
- **`start-kiosk.sh`** - Browser launcher
- **`RASPI_KIOSK_SETUP.md`** - Full documentation

**[Getting Started with Full Stack →](RASPI_KIOSK_SETUP.md)**

### Deployment Modes

Compare options and choose what's best for you.

**[See all options →](DEPLOYMENT-MODES.md)**

### 1. **raspi-kiosk-setup.sh** (Main Setup - Recommended)
**Purpose:** Complete automated setup of entire kiosk system

**What it does:**
- Updates all system packages
- Installs Node.js, npm, Chromium, X11, Python
- Enables UART for Pico communication
- Builds server and client
- Creates systemd services
- Configures environment variables
- Sets up startup scripts

**Run:** `sudo bash setup/raspi-kiosk-setup.sh`

**Time:** ~15-20 minutes

---

### 2. **quick-setup.sh** (Fast Alternative)
**Purpose:** Simplified setup for experienced users who know Raspberry Pi

**What it does:**
- Installs core packages only
- Enables UART
- Installs npm dependencies
- Copies and enables systemd services

**Run:** `sudo bash setup/quick-setup.sh`

**Time:** ~10 minutes

**Use when:** You want minimal setup with manual configuration

---

### 3. **service-manager.sh** (Daily Use)
**Purpose:** Easy command-line control of all services

**Commands:**
```bash
./service-manager.sh status              # Show service status
./service-manager.sh restart             # Restart all services
./service-manager.sh restart-server      # Restart just server
./service-manager.sh logs                # Show live logs  
./service-manager.sh logs-server         # Show server logs
./service-manager.sh enable              # Enable auto-start
./service-manager.sh disable             # Disable auto-start
./service-manager.sh help                # Show all commands
```

**Run:** `bash setup/service-manager.sh` (no sudo needed for status/logs)

**Use for:** Daily monitoring, troubleshooting, service restarts

---

### 4. **validate-system.sh** (Diagnostics)
**Purpose:** Check if system is correctly configured

**Checks:**
- Hardware status (CPU, memory, disk, temperature)
- UART configuration
- Systemd services
- Network connectivity
- Server status
- Display/X11 status
- Project files
- Environment configuration

**Run:** `bash setup/validate-system.sh`

**Output:** Pass/Warn/Fail summary with specific issues

**Use after:**
- Initial setup
- System updates
- Service failures
- Network issues

---

### 5. **start-kiosk.sh** (Browser Launcher)
**Purpose:** Launch Chromium in fullscreen kiosk mode

**Features:**
- Waits for server to be ready
- Starts browser fullscreen
- Disables most features (extensions, sync, etc.)
- Logs to `/home/pi/radar-kiosk.log`

**Run:** Automatically starts via `radar-kiosk.service`

**Manual run:** 
```bash
DISPLAY=:0 /home/pi/start-kiosk.sh
```

---

## Configuration Files

### **.env.production**
Environment configuration for the production server
- UART port and baud rate
- Server port and features
- Feature flags
- Logging configuration

**Location:** `server/.env.production`

**Key settings:**
```
PICO_UART_ENABLED=true          # Enable Pico communication
PICO_UART_PORT=/dev/ttyAMA0     # UART device
NODE_ENV=production              # Production mode
PORT=3000                         # Server port
```

---

### **Systemd Services** (in `/etc/systemd/system/`)

#### **radar-server.service**
- Runs Node.js server on port 3000
- Auto-restarts on failure
- Starts automatically on boot

#### **radar-kiosk.service**
- Launches Chromium in fullscreen
- Depends on server being ready
- Auto-restarts on failure

#### **radar-display.service**
- Starts X11 display server
- Required for GUI

---

## Directory Structure

```
setup/
├── raspi-kiosk-setup.sh          ← Main setup script
├── quick-setup.sh                 ← Fast alternative
├── service-manager.sh             ← Daily service control
├── validate-system.sh             ← System diagnostics
├── start-kiosk.sh                 ← Browser launcher
├── RASPI_KIOSK_SETUP.md          ← Full documentation
├── systemd/
│   ├── radar-server.service       ← Server systemd service
│   ├── radar-kiosk.service        ← Browser systemd service
│   └── radar-display.service      ← X11 display service
└── README.md                      ← This file
```

---

## Installation Flow

```
1. raspi-kiosk-setup.sh (full) OR quick-setup.sh (fast)
   └─ Creates: systemd services, startup scripts, .env file
   
2. sudo reboot
   └─ Automatic start sequence:
      - radar-display.service (X11)
      - radar-server.service (Node.js)
      - radar-kiosk.service (Chromium)
   
3. validate-system.sh
   └─ Verify everything is working
   
4. service-manager.sh
   └─ Daily management (logs, restart, etc.)
```

---

## What Gets Enabled

### System Level
- ✅ UART communication on /dev/ttyAMA0
- ✅ Systemd auto-start services
- ✅ X11 display server
- ✅ Chromium in kiosk mode
- ✅ Node.js server

### Application Level
- ✅ Stepper motor control (full UART support)
- ✅ Actuator/servo control
- ✅ Radar sensor data streaming
- ✅ Real-time WebSocket updates
- ✅ Full Vue.js dashboard

### Features by Service

**radar-server (Node.js)**
- API endpoints (REST)
- WebSocket connection handling
- File serving (Vue app)
- Pico device communication

**radar-kiosk (Chromium)**
- Full-screen display
- No user customization possible
- Auto-reconnects to server
- Responsive dashboard

**radar-display (X11)**
- Graphical environment
- Display management
- Window management

---

## Troubleshooting Quick Reference

### "Services not running"
```bash
service-manager.sh status
service-manager.sh restart
```

### "Can't connect to server"
```bash
service-manager.sh logs-server
curl http://localhost:3000
```

### "UART not working"
```bash
validate-system.sh          # Check UART section
ls -la /dev/ttyAMA0         # Verify device exists
grep "enable_uart" /boot/config.txt  # Check config
```

### "Browser won't display"
```bash
service-manager.sh logs-kiosk
DISPLAY=:0 /home/pi/start-kiosk.sh  # Try manual start
```

### "Performance issues"
```bash
service-manager.sh status   # Check RAM/CPU
free -h                      # Memory usage
df -h                        # Disk usage
vcgencmd measure_temp        # CPU temperature
```

---

## Common Tasks

### Fix UART Issue
```bash
sudo nano /boot/config.txt
# Add these lines:
enable_uart=1
dtoverlay=disable-bt

sudo reboot
```

### View Real-time Logs
```bash
service-manager.sh logs        # All services
service-manager.sh logs-server # Just server
```

### Restart Specific Service
```bash
service-manager.sh restart-server   # Server only
service-manager.sh restart-kiosk    # Browser only
service-manager.sh restart          # All services
```

### Check System Health
```bash
validate-system.sh
```

### Change Browser URL
```bash
sudo nano /home/pi/start-kiosk.sh
# Edit the SERVER_URL variable
```

### Disable Auto-Start (for development)
```bash
service-manager.sh disable
# Make changes
service-manager.sh enable
```

---

## Advanced Usage

### SSH Management
```bash
# From another computer
ssh pi@<pi-ip>
service-manager.sh status
journalctl -u radar-server -f
```

### Remote Reboot
```bash
ssh pi@<pi-ip> sudo reboot
```

### Build Dependencies Locally
```bash
# On development machine
cd RaspberryPiRadarFullStackApplicationAndStepperController
npm run build
# Copy dist/ to Pi
```

### Monitor from Stats
```bash
watch -n 1 'service-manager.sh status'  # Auto-refresh status
```

---

## Maintenance Schedule

### Daily
- Check service status: `service-manager.sh status`

### Weekly
- Review logs: `journalctl -u radar-* -f`
- Check storage: `df -h`

### Monthly
- Update packages: `sudo apt-get update && sudo apt-get upgrade -y`
- Full system backup

### Quarterly
- Reboot and test recovery
- Update Node.js and npm

---

## Performance Tips

1. **Reduce memory usage:**
   ```bash
   # Already done by setup, but verify:
   grep "gpu_mem=" /boot/config.txt
   systemctl disable bluetooth.service  # If not needed
   ```

2. **Improve UART reliability:**
   - Use quality USB-UART adapter if needed
   - Keep cables under 1 meter
   - Use 3.3V levels only
   - Add 0.1µF capacitors on UART lines

3. **Optimize browser:**
   - Kiosk script already disables most features
   - Pre-cache critical assets
   - Monitor network bandwidth

---

## Support & Help

### Check Logs
```bash
# All services
journalctl -u radar-* -n 100

# Specific service
journalctl -u radar-server -f

# Time range
journalctl -u radar-server --since "2 hours ago"
```

### Validate System
```bash
validate-system.sh
```

### Manual Testing
```bash
# Test server
curl http://localhost:3000/api/status

# Test UART
ls -la /dev/ttyAMA0
stty -a -F /dev/ttyAMA0
```

### Documentation
- Full setup guide: `RASPI_KIOSK_SETUP.md`
- Hardware connections: See `PINOUT_AND_CONNECTIONS.md`
- API documentation: See server README

---

## Uninstall / Reset

To revert all changes:

```bash
# Stop services
sudo systemctl stop radar-*.service

# Disable auto-start
sudo systemctl disable radar-*.service

# Remove services
sudo rm /etc/systemd/system/radar-*.service
sudo systemctl daemon-reload

# Restore /boot/config.txt
sudo cp /boot/config.txt.backup /boot/config.txt

# Remove startup scripts
rm /home/pi/start-kiosk.sh /home/pi/service-manager.sh

sudo reboot
```

---

## Support Contact

For issues:
1. Run `validate-system.sh` and save output
2. Check logs: `journalctl -u radar-* -f`
3. Review `RASPI_KIOSK_SETUP.md` troubleshooting section
4. Check GitHub issues
5. Contact: [Your support email/link]

---

**Created:** April 2026  
**Version:** 1.0  
**Status:** Production Ready
