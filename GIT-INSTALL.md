# Git Installation & Auto-Update Setup

This guide shows how to install the Radar Project from Git and set up automatic update checking on startup.

## Quick Installation (One-Line Command)

### On Raspberry Pi

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/RadarProject/main/install-from-git.sh | bash
```

Or download and run locally:

```bash
# SSH to Pi first
ssh pi@raspberrypi.local

# Download and run installer
wget https://raw.githubusercontent.com/YOUR_USERNAME/RadarProject/main/install-from-git.sh
chmod +x install-from-git.sh
./install-from-git.sh
```

### With Custom Repository

```bash
./install-from-git.sh https://github.com/myrepo/RadarProject.git /home/pi/MyRadar
```

**Parameters:**
- Arg 1: Git repository URL (default: official repo)
- Arg 2: Installation directory (default: `/home/pi/RadarProject`)

## Setup Auto-Update on Startup

This creates a service that checks for updates every time the Pi boots.

### Step 1: Copy Update Script

```bash
# Create directory
sudo mkdir -p /opt/radar-update

# Copy the update check script
sudo cp setup/radar-update-check.sh /opt/radar-update/
sudo chmod +x /opt/radar-update/check-updates.sh
```

### Step 2: Install Systemd Service

```bash
# Copy service file
sudo cp setup/systemd/radar-update-check.service /etc/systemd/system/

# Enable the service (runs at every startup)
sudo systemctl daemon-reload
sudo systemctl enable radar-update-check.service

# Optional: Test it now
sudo systemctl start radar-update-check.service
```

### Step 3: Verify Setup

```bash
# Check service is enabled
sudo systemctl is-enabled radar-update-check.service
# Should output: enabled

# View update logs
sudo journalctl -u radar-update-check.service -f

# Or view persistent log
tail -f /var/log/radar-app-updates.log
```

## How It Works

### Installation Script (`install-from-git.sh`)

1. ✅ Installs Git if needed
2. ✅ Installs Node.js v18 if needed
3. ✅ Clones or updates repository
4. ✅ Installs npm dependencies (server + client)
5. ✅ Builds Vue.js client
6. ✅ (Optional) Enables UART for Pico communication

**Usage:**
```bash
./install-from-git.sh [REPO_URL] [INSTALL_DIR]
```

**Example:**
```bash
./install-from-git.sh https://github.com/username/RadarProject.git /home/pi/RadarProject
```

### Update Checker Script (`radar-update-check.sh`)

**Runs at system startup and:**

1. Fetches latest from Git (without modifying local)
2. Compares local vs. remote versions
3. If updates found:
   - Pulls latest code
   - Reinstalls npm dependencies
   - Rebuilds client
   - Restarts service automatically
4. Logs all activity to `/var/log/radar-app-updates.log`

**Log file location:** 
```bash
/var/log/radar-app-updates.log
```

**View live logs:**
```bash
sudo tail -f /var/log/radar-app-updates.log
```

## Installation Workflow

### Complete Fresh Setup

```bash
# SSH to Raspberry Pi
ssh pi@raspberrypi.local

# Download and run installer
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/RadarProject/main/install-from-git.sh | bash

# When asked: Enable UART? → y (if using Pico boards)

# Wait for "Installation complete"

# Clone the repo locally to get setup scripts
cd /home/pi
git clone https://github.com/YOUR_USERNAME/RadarProject.git

# Install and enable auto-update
cd RadarProject
sudo mkdir -p /opt/radar-update
sudo cp setup/radar-update-check.sh /opt/radar-update/
sudo chmod +x /opt/radar-update/check-updates.sh
sudo cp setup/systemd/radar-update-check.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable radar-update-check.service

# Start application
sudo systemctl start radar-app

# Check it's running
sudo systemctl status radar-app

# Optional: Reboot if UART was enabled
# sudo reboot
```

### On Next Boot

The system will automatically:
1. 🔄 Check for updates from Git
2. 📥 Pull latest code if available
3. 🔨 Rebuild dependencies
4. 🔄 Restart the application
5. 📝 Log everything to `/var/log/radar-app-updates.log`

## Manual Update (Without Waiting for Startup)

```bash
# Run update check manually
sudo systemctl start radar-update-check.service

# Watch progress
sudo journalctl -u radar-update-check.service -f
```

## Troubleshooting

### Installation Fails on Git Clone

**Problem:** Repository not found or access denied

**Solutions:**
1. Verify Git URL is correct:
   ```bash
   https://github.com/USERNAME/RadarProject.git
   ```
2. For private repos, set up SSH keys or use HTTPS token:
   ```bash
   git config --global user.credentials store
   ```

### Update Check Fails

**Symptoms:** Service shows as failed or logs show error

**Check logs:**
```bash
sudo journalctl -u radar-update-check.service -n 30
```

**Common issues:**
- Network not ready on boot (service waits for network)
- Permission issues on `/var/log`
- Git credentials not configured

**Fix permissions:**
```bash
sudo touch /var/log/radar-app-updates.log
sudo chown pi:pi /var/log/radar-app-updates.log
sudo chmod 644 /var/log/radar-app-updates.log
```

### Service Won't Start

**Check service file:**
```bash
sudo systemctl status radar-update-check.service
sudo journalctl -u radar-update-check.service -n 50
```

**Verify paths exist:**
```bash
ls -la /opt/radar-update/check-updates.sh
cat /etc/systemd/system/radar-update-check.service
```

**Reload and retry:**
```bash
sudo systemctl daemon-reload
sudo systemctl start radar-update-check.service
```

## Managing Updates

### Disable Auto-Update on Startup

```bash
sudo systemctl disable radar-update-check.service
```

### Re-enable Auto-Update

```bash
sudo systemctl enable radar-update-check.service
```

### Check Update History

```bash
# Recent updates
tail -20 /var/log/radar-app-updates.log

# All updates
cat /var/log/radar-app-updates.log

# Updates from last boot
sudo journalctl -u radar-update-check.service --since today
```

### Force Update Right Now

```bash
# Pull and update immediately
cd /home/pi/RadarProject
git pull origin main
cd RaspberryPiRadarFullStackApplicationAndStepperController
npm install
npm run build
sudo systemctl restart radar-app
```

## Environment Setup

The installation script sets up:

- **Git:** For cloning and pulling code
- **Node.js v18:** For running the server
- **npm:** For dependency management
- **Optional - UART:** For Pico communication

All scripts use standard paths:
- Project: `/home/pi/RadarProject`
- Update checker: `/opt/radar-update/check-updates.sh`
- Log file: `/var/log/radar-app-updates.log`
- Service: `/etc/systemd/system/radar-update-check.service`

## Security Notes

- Update checker runs with `pi` user (configurable in service file)
- Log file created with standard permissions
- Git operations use configured credentials
- No sudo required for Git operations (only for service restart)

## See Also

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Complete Deployment Guide
- [QUICKSTART-DEPLOY.md](./QUICKSTART-DEPLOY.md) - Quick Start
- [PRE-DEPLOYMENT-CHECKLIST.md](./PRE-DEPLOYMENT-CHECKLIST.md) - Pre-Flight Checks
