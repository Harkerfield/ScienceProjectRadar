# Deployment Scripts & Documentation

This directory contains automated deployment tools for the Radar Project.

## Files Overview

### Deployment Scripts

| File | Platform | Purpose |
|------|----------|---------|
| **`deploy-to-pi.ps1`** | Windows (PowerShell 5+) | Automated deployment script with SSH and SCP |
| **`deploy-to-pi.sh`** | Linux/Mac (Bash 4+) | Automated deployment script with SSH/rsync |

### Documentation

| File | Purpose |
|------|---------|
| **`QUICKSTART-DEPLOY.md`** | ⚡ Quick 30-second reference guide |
| **`DEPLOYMENT.md`** | 📖 Complete deployment guide with troubleshooting |
| **`DEPLOYMENT-FILES.md`** | 📋 This file - overview of all deployment resources |

---

## Usage Quick Links

### I'm on Windows
```powershell
.\deploy-to-pi.ps1 -PiHost raspberrypi.local -PiUser pi
```
→ See [QUICKSTART-DEPLOY.md](./QUICKSTART-DEPLOY.md)

### I'm on Linux/Mac
```bash
chmod +x deploy-to-pi.sh
./deploy-to-pi.sh -h raspberrypi.local -u pi
```
→ See [QUICKSTART-DEPLOY.md](./QUICKSTART-DEPLOY.md)

### I need detailed instructions
→ Read [DEPLOYMENT.md](./DEPLOYMENT.md) for:
- Prerequisites checklist
- Parameter reference
- Deployment method comparison
- Manual installation steps
- Post-deploy verification
- Troubleshooting guide

---

## What Gets Deployed

The scripts deploy the entire Radar Project stack:

```
Raspberry Pi
├─ /home/pi/RadarProject/
│  ├─ RaspberryPiPicoRadarAndServerController/
│  │  ├─ main.py (Pico master controller)
│  │  ├─ config/ (Pico settings)
│  │  └─ src/ (UART slaves)
│  │
│  └─ RaspberryPiRadarFullStackApplicationAndStepperController/
│     ├─ server/ (Node.js backend)
│     │  ├─ controllers/
│     │  ├─ routes/
│     │  └─ package.json
│     │
│     └─ client/ (Vue.js frontend)
│        ├─ src/
│        ├─ public/
│        └─ package.json
│
└─ Services
   └─ /etc/systemd/system/radar-app.service (auto-start)
```

---

## Features

### Automated Script Features

✅ **Connection Testing**
- Verifies SSH access before deployment
- Tests network connectivity
- Provides clear error messages

✅ **Flexible Deployment Methods**
- Git clone (recommended, keeps history)
- SCP/rsync copy (for offline Pi or local dev)
- Automatic fallback if rsync unavailable

✅ **Complete System Setup**
- OS package updates
- UART/serial port configuration
- Node.js v18 installation
- npm dependency installation
- Vue.js client build
- Systemd service auto-start

✅ **User Feedback**
- Color-coded output (Windows & Linux)
- Real-time progress indicators
- Clear success/error messages
- Post-deploy next steps
- Logs and troubleshooting reference

---

## Platform Differences

### Windows Script (PowerShell)

**Requirements:**
- Windows 10/11 with PowerShell 5.0+
- SSH client (built-in on Win10+, or install Git Bash)

**Features:**
- Running from current directory
- Parameter validation
- Automatic SSH detection
- Color-coded output
- Progress indicators

**Example:**
```powershell
.\deploy-to-pi.ps1 `
    -PiHost "192.168.1.55" `
    -PiUser "pi" `
    -PiProjectDir "/home/pi/RadarApp"
```

### Linux/Mac Script (Bash)

**Requirements:**
- Bash 4.0+
- SSH/SCP or rsync
- Coreutils (standard on Linux/Mac)

**Features:**
- Environment variable support
- Automatic rsync detection
- Fallback to SCP if needed
- ANSI color output
- Progress tracking

**Example:**
```bash
export PI_HOST="192.168.1.55"
export PI_USER="pi"
./deploy-to-pi.sh
```

---

## Deployment Process (10-30 minutes)

1. **Test Connection** (30 sec)
   - Verify SSH works
   - Confirm Pi is reachable

2. **Copy Files** (2-10 min)
   - Git clone or SCP copy
   - Progress indicator shown

3. **Update System** (2-5 min)
   - apt-get update/upgrade
   - Install system packages

4. **Enable UART** (1 min)
   - Configure /boot/config.txt
   - Enable ttyAMA0

5. **Install Node.js** (3-8 min)
   - Download & install v18
   - Verify installation

6. **Install Dependencies** (3-10 min)
   - npm install (server)
   - npm install + build (client)

7. **Configure Service** (1 min)
   - Create systemd unit
   - Enable auto-start

8. **Report Status** (30 sec)
   - Show next steps
   - Provide access URL

---

## After Deployment

### Access the Application
```
http://raspberrypi.local:3000
http://192.168.1.100:3000  (if using IP)
```

### Check Service Status
```bash
ssh pi@raspberrypi.local
sudo systemctl status radar-app
```

### View Real-time Logs
```bash
sudo journalctl -u radar-app -f
```

### Reboot If Needed
```bash
# If UART was enabled, reboot is required
sudo reboot
```

---

## Troubleshooting

### Common Issues

**"Cannot connect to host"**
- Check Pi hostname: `ping raspberrypi.local`
- Try IP instead: `-PiHost 192.168.1.100`
- Verify SSH is enabled on Pi

**"Git clone failed"**
- Choose SCP method instead
- Check Pi internet: `ssh pi@host 'ping google.com'`

**"App won't start"**
- Check logs: `sudo journalctl -u radar-app -n 50`
- Verify Node.js: `node --version`
- See [DEPLOYMENT.md](./DEPLOYMENT.md) for full troubleshooting

---

## Moving Forward

### One-Time Setup (Done!)
✅ Network access configured
✅ UART enabled for Pico communication
✅ Services auto-starting
✅ Application accessible

### Regular Operations
- Start: `sudo systemctl start radar-app`
- Stop: `sudo systemctl stop radar-app`
- Logs: `sudo journalctl -u radar-app -f`
- Restart: `sudo systemctl restart radar-app`

### Updates
```bash
cd /home/pi/RadarProject
git pull origin main
cd RaspberryPiRadarFullStackApplicationAndStepperController/
npm install
sudo systemctl restart radar-app
```

---

## Support & Documentation

- **Quick Reference:** [QUICKSTART-DEPLOY.md](./QUICKSTART-DEPLOY.md)
- **Full Guide:** [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Project README:** [README.md](./README.md)
- **Hostname Setup:** [HOSTNAME_ACCESS.md](./RaspberryPiRadarFullStackApplicationAndStepperController/HOSTNAME_ACCESS.md)
- **HB100 Sensor:** [HB100_SETUP.md](./RaspberryPiPicoRadarAndServerController/src/uart_Slave_Radar/tester/HB100_SETUP.md)

---

## Script Source Code

### deploy-to-pi.ps1
- **Type:** PowerShell 5.0+ Script
- **Size:** ~500 lines
- **Features:** SSH connection test, Git/SCP deploy, Full setup automation
- **Location:** `./deploy-to-pi.ps1`

### deploy-to-pi.sh
- **Type:** Bash 4.0+ Script
- **Size:** ~450 lines
- **Features:** SSH connection test, rsync/SCP deploy, Full setup automation
- **Location:** `./deploy-to-pi.sh`

Both scripts are self-contained and include all setup commands directly.

---

**Last Updated:** 2025
**Status:** Ready for Production
**Tested On:** Raspberry Pi OS (Lite & Desktop), Windows 10/11, Ubuntu 20.04+, macOS
