# 🌍 Cross-Platform Support Guide

The Radar Application now works on **Windows**, **Linux**, and **Raspberry Pi** with platform-specific optimizations.

## 🚀 Universal Start

The simplest way to get started on any platform:

### Option 1: Bash (Linux/Raspberry Pi/Mac)
```bash
cd setup
bash setup.sh
```

### Option 2: PowerShell (Windows)
```powershell
cd setup
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup.ps1
```

Both scripts automatically detect your platform and run the appropriate setup!

---

## 📊 Platform Quick Reference

| Feature | Windows | Linux | Raspberry Pi |
|---------|---------|-------|--------------|
| **Development** | ✅ | ✅ | ✅ |
| **Production** | ⚠️ | ✅ | ✅ |
| **UART Support** | ❌ | ❌ | ✅ |
| **Kiosk Mode** | ❌ | ⚠️ | ✅ |
| **Auto-Start** | ❌ | ⚠️ | ✅ |
| **Setup Scripts** | Batch/PS1 | Bash | Bash |
| **Run Scripts** | Batch/PS1 | Bash | Systemd |
| **Control** | PowerShell | Bash | Bash |

---

## 🪟 Windows

### Installation
1. Install Node.js from https://nodejs.org/ (LTS)
2. Check "Add to PATH" during installation
3. Restart PowerShell/CMD

### Quick Start
```powershell
cd setup
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup.ps1
# Choose Windows setup automatically
```

### Manual Start
```powershell
.\run-windows.ps1
# OR
run-windows.bat
```

### Daily Commands
```powershell
# Check status
.\app-control.ps1 status

# View logs
.\app-control.ps1 logs

# Test connectivity
.\app-control.ps1 test

# Stop
.\app-control.ps1 stop
```

### Ports
- Server: http://localhost:3000
- Dev Client: http://localhost:5173
- Browser auto-opens on start

---

## 🍓 Raspberry Pi

### Installation
```bash
cd ~/radar-project/setup
bash setup.sh
# Choose option 1 or 2
```

### After Setup
- Reboot: `sudo reboot`
- Everything starts automatically
- Dashboard displays on HDMI
- UART ready for Pico Master

### Daily Commands
```bash
# App Mode
./app-control.sh status
./app-control.sh logs

# Full Stack
./service-manager.sh status
./service-manager.sh logs-server
```

### Ports
- Server: http://localhost:3000 (local) or http://<pi-ip>:3000 (network)
- Kiosk: Fullscreen Chromium display
- UART: /dev/ttyAMA0 (115200 baud)

---

## 🐧 Linux

### Installation
```bash
cd ~/radar-project/setup
bash setup.sh
# Automatically runs for Linux
```

### Manual Start
```bash
# Terminal 1 - Server
cd server
npm start

# Terminal 2 - Client
cd client
npm run dev
```

### Daily Commands
```bash
# Manual process management
ps aux | grep node

# Kill if needed
pkill -f "npm start"
```

### Ports
- Server: http://localhost:3000
- Dev Client: http://localhost:5173

---

## 📁 Scripts by Platform

### Windows Only
- `win-setup.ps1` - Setup (PowerShell, recommended)
- `win-setup.bat` - Setup (Batch, legacy)
- `run-windows.ps1` - Start servers (PowerShell, recommended)
- `run-windows.bat` - Start servers (Batch, legacy)
- `app-control.ps1` - Control (PowerShell, recommended)
- `app-control.bat` - Control (Batch, legacy)

### Linux/Raspberry Pi Only
- `app-setup.sh` - App mode setup
- `raspi-kiosk-setup.sh` - Full stack setup
- `quick-setup.sh` - Deps-only setup
- `service-manager.sh` - Service control
- `validate-system.sh` - System diagnostics
- `app-launcher.sh` - Systemd launcher

### Universal (Any Platform)
- `setup.sh` - Auto-detect and setup (Bash)
- `setup.ps1` - Auto-detect and setup (PowerShell)

---

## Configuration by Platform

### Windows
```
.env
├── NODE_ENV=development
├── PORT=3000
├── PICO_UART_ENABLED=false (no UART on Windows)
└── VUE_APP_API_BASE_URL=http://localhost:3000/api
```

### Raspberry Pi
```
.env
├── NODE_ENV=production
├── PORT=3000
├── PICO_UART_ENABLED=true
├── PICO_UART_PORT=/dev/ttyAMA0
├── PICO_UART_BAUD_RATE=115200
└── VUE_APP_API_BASE_URL=http://localhost:3000/api
```

### Linux
```
.env
├── NODE_ENV=development
├── PORT=3000
├── PICO_UART_ENABLED=false
└── VUE_APP_API_BASE_URL=http://localhost:3000/api
```

---

## Universal APIs

All platforms support these via the REST API:

```bash
# Server status
curl http://localhost:3000/api/status

# Stepper control (Linux/Pi only - UART needed)
curl http://localhost:3000/api/stepper/status
curl -X PUT http://localhost:3000/api/stepper/move -d "angle=90"

# Actuator control (Linux/Pi only - UART needed)
curl http://localhost:3000/api/actuator/status
curl -X PUT http://localhost:3000/api/actuator/open
```

---

## Development Workflow

### Windows Developer
```
1. .\setup.ps1 (one time)
2. .\run-windows.ps1 (daily)
3. .\app-control.ps1 test (verify)
4. Edit code → Auto-reload
5. .\app-control.ps1 stop (when done)
```

### Raspberry Pi
```
1. sudo bash setup.sh (one time)
2. sudo reboot
3. ./app-control.sh logs (monitor)
4. Connect Pico Master
5. Use dashboard
```

### Linux Developer
```
1. bash setup.sh (one time)
2. cd server && npm start &
3. cd ../client && npm run dev
4. Edit code → Auto-reload
5. pkill -f "npm start" (when done)
```

---

## Troubleshooting by Platform

### Windows Issues
```powershell
# PowerShell execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Node.js not found
$env:Path -split ';' | Select-String "nodejs"
# Reinstall with PATH option

# Port in use
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# View logs
.\app-control.ps1 logs
.\app-control.ps1 debug
```

### Raspberry Pi Issues
```bash
# Service won't start
./app-control.sh logs
sudo systemctl status radar-app

# UART not working
ls -la /dev/ttyAMA0
grep enable_uart /boot/config.txt

# Reboot required
sudo reboot
```

### Linux Issues
```bash
# Node.js not found
which node
# Install via package manager

# Port in use
lsof -i :3000
kill -9 <PID>

# View processes
ps aux | grep node
```

---

## Port Management

### Windows
```powershell
# Find what's using port 3000
netstat -ano | findstr :3000

# Kill process
taskkill /PID <PID> /F

# Use different port
$env:PORT=3001
```

### Linux/Mac
```bash
# Find what's using port 3000
lsof -i :3000

# Kill process
kill -9 <PID>

# Use different port
PORT=3001 npm start
```

### Raspberry Pi
```bash
# Ports are managed by systemd
# Change in .env file
nano server/.env
# Edit PORT=3001
./app-control.sh restart
```

---

## Environment Variables

### Common (All Platforms)
```bash
NODE_ENV=development|production
PORT=3000
VUE_APP_API_BASE_URL=http://localhost:3000/api
LOG_LEVEL=debug|info
```

### Raspberry Pi Only
```bash
PICO_UART_ENABLED=true
PICO_UART_PORT=/dev/ttyAMA0
PICO_UART_BAUD_RATE=115200
```

### Windows/Linux
```bash
PICO_UART_ENABLED=false  # No UART hardware support
```

---

## Performance Comparison

| Operation | Windows | Linux | Raspberry Pi |
|-----------|---------|-------|--------------|
| Setup time | ~10 min | ~10 min | ~10 min |
| First boot | N/A | N/A | ~2-3 min |
| Server start | 5-10 sec | 5-10 sec | ~5 sec (systemd) |
| Client dev build | 30-60 sec | 30-60 sec | 60-120 sec |
| Client prod build | 20-40 sec | 20-40 sec | 40-80 sec |
| Dashboard load | 2-3 sec | 2-3 sec | 3-5 sec |

---

## Deployment Scenarios

### Scenario 1: Develop on Windows, Deploy on Pi
```
1. ./setup.ps1 (Windows)
2. .\run-windows.ps1 (test)
3. Git push changes
4. ssh pi@<ip> "cd radar-project && git pull && sudo reboot"
5. Pi deploys automatically
```

### Scenario 2: Linux Server Production
```
1. bash setup.sh (Linux)
2. npm run build (both)
3. pm2 start server
4. Configure nginx reverse proxy
5. Setup monitoring/logging
```

### Scenario 3: Raspberry Pi Kiosk
```
1. bash setup.sh (choose option 1 or 2)
2. sudo reboot
3. Connect Pico Master
4. Dashboard displays automatically
5. Use ./app-control.sh for monitoring
```

---

## Getting Technical Help

### For Windows
```powershell
.\app-control.ps1 debug
.\app-control.ps1 test
# Check output for specific errors
```

### For Raspberry Pi
```bash
./validate-system.sh          # Full diagnostics
./app-control.sh logs         # Recent logs
journalctl -u radar-app -fn 50 # System logs
```

### For Linux
```bash
ps aux | grep node
tail -f logs/*.log
journalctl -u radar-server -f
```

---

## Supported Versions

### Node.js
- Windows/Linux/Pi: v16+ (v18+ recommended)

### Operating Systems
- Windows: 10, 11
- Linux: Ubuntu 20.04+, Debian 10+, Others with Node.js
- Raspberry Pi: OS Lite (64-bit recommended), OS Desktop

### Browsers
- Chrome/Chromium (all platforms)
- Firefox (all platforms)
- Safari (macOS, iOS - remote access)
- Edge (Windows)

---

## What Works Where

| Feature | Windows | Linux | Pi |
|---------|---------|-------|-----|
| Dashboard | ✅ | ✅ | ✅ |
| API endpoints | ✅ | ✅ | ✅ |
| Stepper control | ❌ | ❌ | ✅ |
| Actuator control | ❌ | ❌ | ✅ |
| Radar data | ❌ | ❌ | ✅ |
| UART | ❌ | ❌ | ✅ |
| WebSocket | ✅ | ✅ | ✅ |
| Real-time updates | ✅ | ✅ | ✅ |

---

## Next Steps

1. **Choose platform:** Windows/Linux/Pi?
2. **Run setup:** `bash setup.sh` or `.\setup.ps1`
3. **Follow prompts:** Scripts guide you through
4. **Start application:** Platform-specific launcher
5. **Test connectivity:** `curl http://localhost:3000`
6. **Use dashboard:** Access in browser

---

## Quick Reference Card

```
╔════════════════════════════════════════════════════╗
║           RADAR CROSS-PLATFORM QUICK START         ║
╠════════════════════════════════════════════════════╣
║                                                    ║
║  WINDOWS                                           ║
║  ├─ .\setup.ps1              (Setup)              ║
║  ├─ .\run-windows.ps1        (Start)              ║
║  └─ .\app-control.ps1 status (Control)            ║
║                                                    ║
║  LINUX                                             ║
║  ├─ bash setup.sh            (Setup)              ║
║  ├─ npm start & npm run dev  (Start)              ║
║  └─ ps aux | grep node       (Monitor)            ║
║                                                    ║
║  RASPBERRY PI                                      ║
║  ├─ bash setup.sh            (Setup)              ║
║  ├─ sudo reboot              (Auto-start)         ║
║  └─ ./app-control.sh logs    (Monitor)            ║
║                                                    ║
║  Server: http://localhost:3000                     ║
║  Client: http://localhost:5173 (dev)              ║
║  Pi Kiosk: Fullscreen display on HDMI              ║
║                                                    ║
╚════════════════════════════════════════════════════╝
```

---

**Version:** 2.0 (Full Cross-Platform)  
**Supported Platforms:** Windows, Linux, Raspberry Pi  
**Status:** Production Ready  
**Updated:** April 2026
