# Radar Application - Cross-Platform Setup Guide

Complete setup instructions for **Windows**, **Linux (Raspberry Pi)**, and **Linux (PC/Server)**.

## 🎯 Quick Platform Selection

### 🪟 Windows PC (Development)
- **Best for:** Development, testing before deployment
- **Setup Time:** ~10 minutes
- **Scripts:** `win-setup.ps1` or `win-setup.bat`
- **Daily Use:** `app-control.ps1`
- **Run:** `run-windows.ps1` or `run-windows.bat`

### 🍓 Raspberry Pi (Kiosk/Embedded)
- **Best for:** Production kiosk displays, embedded systems
- **Setup Time:** ~10-20 minutes
- **Scripts:** `app-setup.sh` or `raspi-kiosk-setup.sh`
- **Daily Use:** `app-control.sh` or `service-manager.sh`
- **UART:** Pico Master communication enabled

### 🐧 Linux PC/Server (Development/Production)
- **Best for:** Server deployments, Linux development
- **Setup Time:** ~10 minutes
- **Scripts:** Same as Raspberry Pi
- **Daily Use:** `service-manager.sh`
- **UART:** No UART support (not available on PC USB)

---

## 🪟 Windows Setup

### Prerequisites
- Windows 10 or later
- Administrator access (for some installations)
- Git (optional but recommended)
- Node.js 16+ or later

### Step 1: Install Node.js

1. Download from https://nodejs.org/
2. Choose LTS version
3. Run installer
4. **Important:** Check "Add to PATH" during installation
5. Verify:
   ```powershell
   node --version
   npm --version
   ```

### Step 2: Run Setup

**Option A: PowerShell (Recommended)**
```powershell
# Open PowerShell as Administrator
cd C:\path\to\RadarProject\setup
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\win-setup.ps1
```

**Option B: Command Prompt (Legacy)**
```cmd
cd C:\path\to\RadarProject\setup
win-setup.bat
```

### Step 3: Start Application

**Option A: PowerShell Script**
```powershell
.\run-windows.ps1
```

**Option B: Batch Script**
```cmd
run-windows.bat
```

**Option C: Manual (Multiple Terminals)**
```powershell
# Terminal 1 - Server
cd RaspberryPiRadarFullStackApplicationAndStepperController\server
npm start

# Terminal 2 - Client dev server
cd RaspberryPiRadarFullStackApplicationAndStepperController\client
npm run dev

# Open browser to: http://localhost:5173
```

### Daily Use

```powershell
# Check status
.\app-control.ps1 status

# View logs
.\app-control.ps1 logs

# Test connectivity
.\app-control.ps1 test

# Debug info
.\app-control.ps1 debug

# Stop services
.\app-control.ps1 stop

# Restart
.\app-control.ps1 restart
```

### Troubleshooting Windows

**"PowerShell scripts disabled"**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**"npm not found"**
- Node.js not in PATH
- Restart PowerShell/CMD after installing Node.js
- Verify installation: `where npm`

**"Port already in use"**
```powershell
# Find what's using port 3000
netstat -ano | findstr :3000
# Kill process
taskkill /PID [PID] /F
# Or use different port
$env:PORT=3001
```

**"Cannot build client"**
```powershell
cd client
npm cache clean --force
npm install
npm run build
```

---

## 🍓 Raspberry Pi Setup (Kiosk Mode)

### Prerequisites
- Raspberry Pi 4 or 5
- Fresh Raspberry Pi OS (64-bit recommended)
- Internet connection
- HDMI display connected
- Pico Master (optional, for UART)

### Step 1: Get Project on Pi

```bash
cd ~
git clone <your-repo-url> radar-project
cd radar-project/setup
```

### Step 2: Run Setup

**APP MODE (Recommended - Simple)**
```bash
chmod +x app-setup.sh
sudo bash app-setup.sh
sudo reboot
```

**FULL STACK (Advanced - More Control)**
```bash
chmod +x raspi-kiosk-setup.sh
sudo bash raspi-kiosk-setup.sh
sudo reboot
```

### What Happens on Boot
1. X11 display server starts
2. Systemd launches application service
3. Application automatically:
   - Builds client (if needed)
   - Starts Node.js server
   - Launches Chromium in fullscreen
4. Dashboard displays

### Daily Use

```bash
# APP MODE:
./app-control.sh status
./app-control.sh logs
./app-control.sh restart

# FULL STACK:
./service-manager.sh status
./service-manager.sh logs-server
./service-manager.sh restart
```

### UART for Pico Master

**Hardware Connection:**
```
Pico TX  (GPIO0)  → Pi RX  (GPIO15 / Pin 10)
Pico RX  (GPIO1)  → Pi TX  (GPIO14 / Pin 8)
Pico GND         → Pi GND  (Pin 6, 9, 14, 20, 25, 30, 34, 39)
Pico 3.3V        → Pi 3.3V (Pin 1, 17)
```

**Verify UART:**
```bash
ls -la /dev/ttyAMA0          # Device exists?
grep enable_uart /boot/config.txt  # Enabled?
```

---

## 🐧 Linux PC/Server Setup

### Prerequisites
- Linux distribution (Ubuntu, Debian, etc.)
- Terminal/SSH access
- Node.js 16+ or later
- 1GB+ free disk space

### Step 1: Install Node.js

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y nodejs npm
```

**CentOS/RHEL:**
```bash
sudo dnf install -y nodejs npm
```

**Fedora:**
```bash
sudo dnf install -y nodejs npm
```

### Step 2: Run Setup

```bash
cd ~/radar-project/setup
chmod +x app-setup.sh
bash app-setup.sh  # No sudo needed for development
```

### Step 3: Start Application

**Quick Start:**
```bash
./run-windows.ps1
# OR manually:
cd server && npm start &
cd ../client && npm run dev
```

**Manual Control:**
```bash
# Terminal 1
cd server
npm start

# Terminal 2
cd client
npm run dev

# Open browser to: http://localhost:5173
```

### Daily Use

```bash
# Check processes
ps aux | grep node

# View logs
journalctl -u radar-server
# OR
tail -f server/logs/*.log

# Stop services
pkill -f "npm start"

# Restart
./service-manager.sh restart
```

### Production Deployment

For production on Linux server:

```bash
# Install PM2 for process management
sudo npm install -g pm2

# Start with PM2
cd server && pm2 start npm --name "radar-server" -- start
cd ../client && npm run build && npm start

# Monitor
pm2 status
pm2 logs
```

---

## Environment Configuration

### Windows (.env)
```
NODE_ENV=development
PORT=3000
LOG_LEVEL=debug
PICO_UART_ENABLED=false
VUE_APP_API_BASE_URL=http://localhost:3000/api
```

### Raspberry Pi (.env)
```
NODE_ENV=production
PORT=3000
LOG_LEVEL=info
PICO_UART_ENABLED=true
PICO_UART_PORT=/dev/ttyAMA0
PICO_UART_BAUD_RATE=115200
VUE_APP_API_BASE_URL=http://localhost:3000/api
```

### Linux PC (.env)
```
NODE_ENV=development
PORT=3000
LOG_LEVEL=debug
PICO_UART_ENABLED=false
VUE_APP_API_BASE_URL=http://localhost:3000/api
```

---

## Port Numbers

| Service | Default | Change Via |
|---------|---------|-----------|
| Node Server | 3000 | `PORT=3001` env var |
| Dev Client | 5173 | `VITE_PORT=5174` env var |
| Pico UART | /dev/ttyAMA0 | `.env` (Pi only) |

---

## Comparison: Platforms

| Feature | Windows | Raspberry Pi | Linux PC |
|---------|---------|--------------|----------|
| **Setup Time** | ~10 min | ~10 min | ~10 min |
| **UART Support** | ❌ | ✅ | ❌ |
| **Kiosk Mode** | ❌ | ✅ | ⚠️ (manual) |
| **Auto-Start** | ❌ | ✅ | ⚠️ (manual) |
| **Development** | ✅ | ✅ | ✅ |
| **Production Ready** | ⚠️ | ✅ | ✅ |
| **Scripts** | PowerShell/Batch | Bash | Bash |

---

## Workflow Examples

### Windows Development
```powershell
# Initial setup
.\win-setup.ps1

# Daily development
.\run-windows.ps1

# Check status
.\app-control.ps1 status

# Debug
.\app-control.ps1 test
```

### Raspberry Pi Kiosk
```bash
# Initial setup (one time)
sudo bash setup/app-setup.sh
sudo reboot

# After reboot, everything auto-starts

# Daily monitoring
./app-control.sh status
./app-control.sh logs
```

### Linux Server
```bash
# Initial setup
bash app-setup.sh

# Manual control
cd server && npm start &
cd ../client && npm run dev

# Monitor
ps aux | grep node
```

---

## Cross-Platform Scripts

| Purpose | Windows | Raspberry Pi | Linux |
|---------|---------|--------------|-------|
| Setup | `win-setup.ps1` / `win-setup.bat` | `app-setup.sh` | `app-setup.sh` |
| Run | `run-windows.ps1` / `run-windows.bat` | Auto (systemd) | Manual |
| Control | `app-control.ps1` | `app-control.sh` | Process mgmt |
| Validate | `app-control.ps1 test` | `validate-system.sh` | Process check |

---

## Getting Help

### Windows Issues
```powershell
.\app-control.ps1 help
.\app-control.ps1 debug
```

### Raspberry Pi Issues
```bash
./app-control.sh logs
./validate-system.sh
```

### Linux Issues
```bash
ps aux | grep node
tail -f logs/*.log
journalctl -u radar-*
```

---

## File Structure (By Platform)

```
setup/
├── 📁 Windows
│   ├── win-setup.bat              # Batch setup
│   ├── win-setup.ps1              # PowerShell setup
│   ├── run-windows.bat            # Start servers
│   ├── run-windows.ps1            # Start servers (advanced)
│   └── app-control.ps1            # Control app
│
├── 📁 Raspberry Pi / Linux
│   ├── app-setup.sh               # App mode setup
│   ├── raspi-kiosk-setup.sh       # Full stack setup
│   ├── app-launcher.sh            # Auto launcher
│   ├── app-control.sh             # Control app
│   ├── service-manager.sh         # Service control
│   └── validate-system.sh         # System check
│
└── 📁 Documentation
    ├── WINDOWS-SETUP.md           # Windows guide (this file)
    ├── LINUX-SETUP.md             # Linux guide
    └── Cross-platform documentation
```

---

## Recommended Setup Paths

### "I want to develop on Windows"
1. Install Node.js from nodejs.org
2. Run: `.\win-setup.ps1`
3. Run: `.\run-windows.ps1`
4. Code and test locally

### "I want a Kiosk on Raspberry Pi"
1. Get project on Pi: `git clone ...`
2. Run: `sudo bash setup/app-setup.sh`
3. Reboot
4. Everything auto-starts

### "I want to deploy on Linux Server"
1. Install Node.js (apt/dnf/etc)
2. Run: `bash setup/app-setup.sh`
3. Run: `cd server && npm start`
4. Configure nginx/Apache reverse proxy

---

## Performance Considerations

### Windows
- Development mode (npm run dev) is slower
- Use `npm run build` for testing production
- Keep Terminal windows visible for debugging

### Raspberry Pi
- First boot takes 2-3 minutes (client build)
- Subsequent boots ~10-15 seconds
- 4GB RAM minimum recommended
- Auto-recovery restarts on crash

### Linux Server
- Fast once deployed
- Consider PM2 or systemd for auto-start
- Monitor resource usage
- Plan for scaling

---

## Production Deploy Checklist

### Windows PC
- ❌ Not recommended for production

### Raspberry Pi
- ✅ Enable auto-start with service-manager
- ✅ Connect Pico Master for UART
- ✅ Configure static IP
- ✅ Monitor CPU/memory/temp
- ✅ Set up log rotation
- ✅ Test recovery after reboot

### Linux Server
- ✅ Use PM2 or systemd
- ✅ Configure firewall
- ✅ Set up reverse proxy (nginx)
- ✅ Enable HTTPS
- ✅ Monitor resource usage
- ✅ Plan backups
- ✅ Set up monitoring/alerting

---

**Version:** 2.0 (Cross-Platform)  
**Updated:** April 2026  
**Platforms Supported:** Windows, Raspberry Pi, Linux  
**Status:** Production Ready
