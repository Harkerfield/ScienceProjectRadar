# Deployment Guide - Radar Project to Raspberry Pi

This guide covers deploying the Radar Project to a Raspberry Pi using automated deployment scripts.

## Quick Start

### Windows (PowerShell)

```powershell
# Open PowerShell as regular user (not Admin needed)
cd F:\RadarProject
.\deploy-to-pi.ps1 -PiHost raspberrypi.local -PiUser pi
```

### Linux/Mac (Bash)

```bash
cd /path/to/RadarProject
chmod +x deploy-to-pi.sh
./deploy-to-pi.sh -h raspberrypi.local -u pi
```

## Prerequisites

### On Windows
- **PowerShell 5.0+** (built-in)
- **SSH client** (included in Windows 10+, or install [Git Bash](https://git-scm.com/download/win) or [PuTTY](https://www.putty.org/))
- **Network access** to Raspberry Pi

### On Linux/Mac
- **Bash 4+**
- **SSH client** (usually pre-installed)
- **rsync or SCP** (for file transfer)
- **Network access** to Raspberry Pi

### On Raspberry Pi
- **Raspberry Pi OS** (Lite or Desktop) - any recent version
- **SSH enabled** (usually enabled by default)
- **Network connection** (Ethernet or WiFi)
- **Power supply** (5V, 2.5A minimum)

## What the Script Does

The deployment script automates:

1. **Connection Test** - Verifies SSH access to Pi
2. **File Transfer** - Copies project using Git clone or SCP/rsync
3. **System Update** - Updates Pi OS packages
4. **UART Setup** - Enables serial communication for Pico devices
5. **Node.js Install** - Installs Node.js v18 if needed
6. **Dependencies** - Installs npm packages for server and client
7. **Build Client** - Builds Vue.js client application
8. **Service Setup** - Creates systemd service for auto-start
9. **Configuration** - Sets environment variables and permissions

**Total time:** 10-30 minutes depending on Pi speed and internet connection

## Detailed Usage

### PowerShell (Windows)

#### Basic usage (defaults to raspberrypi.local):
```powershell
.\deploy-to-pi.ps1
```

#### Specify custom hostname:
```powershell
.\deploy-to-pi.ps1 -PiHost 192.168.1.100 -PiUser pi
```

#### All parameters:
```powershell
.\deploy-to-pi.ps1 `
    -PiHost "raspberry-pi.local" `
    -PiUser "pi" `
    -ProjectPath "." `
    -PiProjectDir "/home/pi/RadarProject"
```

**Parameters:**
- `-PiHost`: Hostname or IP of Raspberry Pi (default: `raspberrypi.local`)
- `-PiUser`: Username on Pi (default: `pi`)
- `-ProjectPath`: Local project path (default: current directory)
- `-PiProjectDir`: Where to install on Pi (default: `/home/pi/RadarProject`)

### Bash (Linux/Mac)

#### Basic usage:
```bash
./deploy-to-pi.sh
```

#### With custom hostname:
```bash
./deploy-to-pi.sh -h 192.168.1.100 -u pi
```

#### Environment variables:
```bash
export PI_HOST="radar-pi.local"
export PI_USER="pi"
./deploy-to-pi.sh
```

**Options:**
- `-h, --host`: Hostname/IP of Pi (default: `raspberrypi.local`)
- `-u, --user`: Username (default: `pi`)
- `-p, --path`: Local project path (default: current directory)
- `-d, --dest`: Destination on Pi (default: `/home/pi/RadarProject`)

## Deployment Methods

When prompted, choose your deployment method:

### Method 1: Git Clone (Recommended)
- **Best for:** Keeping code updated, easy updates
- **Requires:** GitHub access from Pi
- **Time:** 5-10 minutes
- **Steps:**
  1. Pi clones from your Git repository
  2. Automatically pulls latest version
  3. Ideal for continuous updates

### Method 2: SCP/rsync Copy
- **Best for:** Offline Pi, local development
- **Requires:** Files on your local machine
- **Time:** 10-15 minutes depending on file size
- **Steps:**
  1. Copies all files from your computer
  2. Works without internet on Pi
  3. Good for testing without commits

## After Deployment

### Check Status
```bash
ssh pi@raspberrypi.local
sudo systemctl status radar-app
```

### View Logs
```bash
ssh pi@raspberrypi.local
sudo journalctl -u radar-app -f
```

### Access Application
```
http://raspberrypi.local:3000
```

Or with IP address:
```
http://192.168.1.100:3000
```

### Start/Stop Service
```bash
# Start
sudo systemctl start radar-app

# Stop
sudo systemctl stop radar-app

# Restart
sudo systemctl restart radar-app

# Disable auto-start
sudo systemctl disable radar-app
```

## UART Configuration

The script automatically enables UART for Pico communication.

**If UART changes were made**, you **MUST reboot** the Pi:
```bash
ssh pi@raspberrypi.local sudo reboot
```

**Verify UART is working:**
```bash
ls -la /dev/ttyAMA0
# Should show: crw-rw---- 1 root dialout ... ttyAMA0
```

**Check UART settings:**
```bash
sudo raspi-config
# Navigate to Interface Options → Serial Port
# Should show: Serial console disabled, Serial port hardware enabled
```

## Troubleshooting

### Cannot Connect to Pi

**Problem:** `ERROR: Cannot connect to user@host`

**Solutions:**
1. Check Pi is powered on and connected
2. Verify hostname: `ping raspberrypi.local`
3. Try IP instead: `ssh pi@192.168.1.100`
4. Verify SSH is enabled on Pi
5. Check firewall isn't blocking SSH (port 22)

### SSH Key Authentication Fails

**Problem:** Prompted for password repeatedly

**Solution 1 - Set up SSH key (recommended):**
```bash
# Windows PowerShell
ssh-keygen -t rsa -b 4096 -f $env:USERPROFILE\.ssh\id_rsa
ssh-copy-id -i $env:USERPROFILE\.ssh\id_rsa.pub pi@raspberrypi.local

# Linux/Mac
ssh-keygen -t rsa -b 4096
ssh-copy-id -i ~/.ssh/id_rsa.pub pi@raspberrypi.local
```

**Solution 2 - Use password authentication:**
```bash
ssh pi@raspberrypi.local # Will prompt for password
```

### Git Clone Fails

**Problem:** Hangs or fails during clone

**Solutions:**
1. Verify Pi has internet access: `ssh pi@host 'ping google.com'`
2. Check Git is installed: `ssh pi@host 'git --version'`
3. Use HTTP instead of SSH for Git URL
4. Try SCP method instead (Method 2)

### Node.js Installation Fails

**Problem:** npm is missing or errors during install

**Solutions:**
1. Check Node.js version: `node --version`
2. Try manual install:
   ```bash
   ssh pi@raspberrypi.local
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

### UART Not Working After Setup

**Problem:** Serial communication not detected

**Solutions:**
1. Confirm reboot happened: Did the script say "Reboot needed"?
2. Manually reboot: `sudo reboot`
3. Check UART is enabled: `raspi-config → Interface Options`
4. Verify GPIO pins: 14 (RX), 15 (TX), GND
5. Check Pico firmware is loaded

### Application Won't Start

**Problem:** Service failed to start or crashes

**Solutions:**
1. Check logs: `sudo journalctl -u radar-app -n 50`
2. Verify npm installed: `npm --version`
3. Check Node.js: `node --version`
4. Try manual start:
   ```bash
   cd /home/pi/RadarProject/RaspberryPiRadarFullStackApplicationAndStepperController
   npm run server:start
   ```
5. Check port 3000 is available: `sudo netstat -tuln | grep 3000`

## Manual Installation

If the automated script fails, you can install manually:

```bash
# SSH to Pi
ssh pi@raspberrypi.local

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Enable UART
sudo raspi-config  # Interface Options → Serial Port → Enable

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Clone project
git clone https://github.com/yourrepo/RadarProject.git
cd RadarProject/RaspberryPiRadarFullStackApplicationAndStepperController

# Install dependencies
npm install
cd client && npm install && npm run build && cd ..

# Test run
npm run server:start
```

## Updates After First Deployment

### Update from Git
```bash
cd /home/pi/RadarProject
git pull origin main
cd RaspberryPiRadarFullStackApplicationAndStepperController
npm install
sudo systemctl restart radar-app
```

### Redeploy Everything
```bash
# Windows
.\deploy-to-pi.ps1 -PiHost raspberrypi.local -PiUser pi

# Linux/Mac
./deploy-to-pi.sh -h raspberrypi.local -u pi
```

## Performance Tips

- **First boot:** Takes 5-10 minutes for npm install
- **Subsequent boots:** ~20 seconds for service to start
- **Memory:** Application uses ~150-200MB RAM
- **Disk:** Requires ~500MB for node_modules
- **Network:** Monitor runs on same network as Pi

## Uninstalling

If you need to remove the application:

```bash
ssh pi@raspberrypi.local

# Stop service
sudo systemctl stop radar-app
sudo systemctl disable radar-app

# Remove service
sudo rm /etc/systemd/system/radar-app.service
sudo systemctl daemon-reload

# Remove project files
rm -rf /home/pi/RadarProject

# Optional: Remove Node.js
sudo apt-get autoremove nodejs
```

## Support

If deployment fails:

1. Check the full error message
2. Verify prerequisites are installed
3. Try manual installation steps
4. Check network/SSH connectivity
5. Review logs on Pi: `sudo journalctl -u radar-app -n 100`

## See Also

- [README.md](../README.md) - Main project documentation
- [QUICKSTART.md](../QUICKSTART.md) - Quick start guide
- [HOSTNAME_ACCESS.md](../HOSTNAME_ACCESS.md) - Access via hostname
- [HB100_SETUP.md](./RaspberryPiPicoRadarAndServerController/src/uart_Slave_Radar/tester/HB100_SETUP.md) - Sensor setup
