# 🚀 Radar Application

**Linux/Raspberry Pi Only**

## ⚡ Quick Start

### First Time Installation



**Step 0: Cleanup**
sudo rm -rf /home/pi/RadarProject


**Step 1: Clone this repository**
```bash
sudo git clone https://github.com/Harkerfield/ScienceProjectRadar.git /home/pi/RadarProject
cd /home/pi/RadarProject
```


**Step 2: Run the setup script**
```bash
bash setup/start.sh
# Choose option 1: INSTALL
```

Takes ~15-25 minutes. Downloads everything from GitHub and configures for auto-start.

### After Installation - That's It!
Just reboot and everything starts automatically:

```bash
sudo reboot
```

---

## 🎯 What Auto-Starts On Boot

When you power on the Raspberry Pi, these start automatically:

✅ **Update Checker** (runs first)
   - Checks GitHub for new code
   - Auto-installs updates if internet available
   - Restarts server if updates found

✅ **Server** (Node.js on port 3000)
   - Serves API and dashboard
   - Communicates with Pico via UART
   - Accessible from other computers

✅ **Client** (Chromium Kiosk)
   - Displays fullscreen on HDMI
   - Connects to server automatically
   - Still accessible from network

**No manual steps needed - it all just works!**

---

## 🌐 Access Dashboard

### Local (on Pi)
Chromium displays automatically on HDMI monitor in fullscreen

### From Other Computers (Ethernet or WiFi)
```
http://raspberrypi.local:3000
http://192.168.x.x:3000
```

---

## 🎯 Common Tasks

### Check if Running
```bash
bash setup/start.sh
# Choose option 4: STATUS
```

### View Logs (Any service)
```bash
bash setup/start.sh
# Choose option 5: LOGS

# Or manually:
sudo journalctl -u radar-server -f         # Server logs
sudo journalctl -u radar-client -f         # Client logs
sudo journalctl -u radar-update-check -f   # Update check logs
```

### Stop Everything
```bash
bash setup/start.sh
# Choose option 3: STOP

# Or manually:
sudo systemctl stop radar-server radar-client
```

### Restart Services
```bash
# Restart everything
sudo systemctl restart radar-server radar-client

# Or just server (client auto-restarts after)
sudo systemctl restart radar-server
```

### Manual Service Control
```bash
# Start
sudo systemctl start radar-server radar-client

# Stop
sudo systemctl stop radar-server radar-client

# Check if auto-start is enabled
sudo systemctl is-enabled radar-server   # Should show "enabled"

# Check status
sudo systemctl status radar-server
sudo systemctl status radar-client
sudo systemctl status radar-update-check
```

### Update Code Manually
Auto-update runs on every boot. To update now:
```bash
cd /home/pi/RadarProject
git pull origin main
sudo systemctl restart radar-server
```

---

## 🔧 Technical Details

| Component | Port | Status | Auto-Start |
|-----------|------|--------|-----------|
| **Server** | 3000 | Node.js backend | ✅ Yes |
| **Client** | 3000 | Chromium kiosk | ✅ Yes |
| **Update Check** | — | Git auto-update | ✅ Yes |
| **UART** | /dev/ttyAMA0 | Pico comm | ✅ Configured |

---

## 📁 Setup Files

All scripts in `setup/`:

```
setup/start.sh          ← Run anytime for menu
setup/install.sh        ← Run once (during install)
setup/check-updates.sh  ← Auto-runs on boot
setup/start-client.sh   ← Auto-runs by systemd
```

For more info: `cat setup/README.md`

---

## 📚 Full Documentation

- [setup/README.md](setup/README.md) - Setup & troubleshooting
- [setup/docs/DEPLOYMENT.md](setup/docs/DEPLOYMENT.md) - Remote Pi deployment

---

## ✨ Quick Reference

```bash
# First time only
bash setup/start.sh && choose 1

# After that, just reboot
sudo reboot

# Or start manually
sudo systemctl start radar-server radar-client

# Check what's running
bash setup/start.sh && choose 4

# View logs
bash setup/start.sh && choose 5
```

---

**Version:** 2.0  
**Platform:** Linux (Raspberry Pi)  
**Auto-Start:** ✅ Yes  
**Status:** ✅ Production Ready

🎉 **Auto-starts on boot - no daily setup needed!**

---

## 🎯 Usage Examples

### Windows - Step by Step
```powershell
# 1. First time setup
.\setup-windows.ps1
# → Choose "1) SETUP"
# → Wait for npm install to finish

# 2. Daily use - Start everything
.\setup-windows.ps1
# → Choose "2) START"
# → Browser opens automatically

# 3. Check what's running
.\setup-windows.ps1
# → Choose "3) CHECK STATUS"

# 4. Stop when done
.\setup-windows.ps1
# → Choose "4) STOP SERVERS"
```

### Raspberry Pi - One Time Setup
```bash
# Run setup wizard
bash setup-linux.sh
# → Choose "1) SETUP"
# → Choose setup mode (1 for Kiosk, recommended)
# → Let it install
# → Reboot with "sudo reboot"
# → Everything auto-starts after reboot!

# View status anytime
bash setup-linux.sh
# → Choose "3) CHECK STATUS"
```

### Linux - Quick Development
```bash
# Setup
bash setup-linux.sh
# → Choose "1) SETUP"

# Start
bash setup-linux.sh
# → Choose "2) START SERVERS"

# Monitor logs
bash setup-linux.sh
# → Choose "5) LOGS"
```

---

## � Deploy to Raspberry Pi

Want to deploy to a **physical Raspberry Pi**? Use our automated deployment script!

### Prerequisites
- **Raspberry Pi** with Raspberry Pi OS installed
- **SSH enabled** on the Pi (enabled by default)
- **Network connection** between your computer and Pi
- **Windows/Linux/Mac** with SSH client (usually pre-installed)

### Step 1: Transfer Project to Pi

**From Windows (PowerShell):**
```powershell
# Navigate to the project root
cd F:\RadarProject

# Run the deployment script
.\setup\deployment\deploy-to-pi.ps1 -PiHost raspberrypi.local -PiUser pi

# Follow the prompts:
# - Choose deployment method (1 for Git clone, 2 for local copy)
# - Wait for files to copy
# - Wait for setup to complete
```

**From Linux/Mac (Bash):**
```bash
# Navigate to the project root
cd /path/to/RadarProject

# Make script executable
chmod +x setup/deployment/deploy-to-pi.sh

# Run the deployment script
./setup/deployment/deploy-to-pi.sh -h raspberrypi.local -u pi

# Follow the prompts:
# - Choose deployment method (1 for Git clone, 2 for local copy)
# - Wait for files to copy
# - Wait for setup to complete
```

### Step 2: After Deployment Completes

The script will:
1. ✅ Copy all project files to Pi
2. ✅ Install Node.js and dependencies
3. ✅ Enable UART for Pico communication
4. ✅ Create systemd service for auto-start
5. ✅ Print access instructions

### Step 3: Start the Application

After deployment:

```bash
# SSH into the Pi (from your computer)
ssh pi@raspberrypi.local

# On the Pi - start the application
sudo systemctl start radar-app

# Check if it's running
sudo systemctl status radar-app

# View logs (live)
sudo journalctl -u radar-app -f
```

**If UART configuration was needed**, reboot the Pi:
```bash
sudo reboot
```

### Access the Dashboard

Once running, open your browser and go to:
```
http://raspberrypi.local:3000
```

Or use the Pi's IP address if hostname doesn't resolve:
```
http://192.168.x.x:3000
```

### Advanced Options

**Custom Pi hostname or user:**
```bash
./setup/deployment/deploy-to-pi.sh -h pi.yourdomain.com -u myuser
```

**Custom project directory on Pi:**
```bash
./setup/deployment/deploy-to-pi.sh -d /opt/radar-project
```

**View deployment logs:**
```bash
# On Pi - tail the service logs
sudo journalctl -u radar-app -f --lines=100

# On Pi - view full logs
sudo systemctl status radar-app
```

**Stop/restart service:**
```bash
# Stop
sudo systemctl stop radar-app

# Restart
sudo systemctl restart radar-app

# Check status
sudo systemctl status radar-app
```

---

## �📚 Full Documentation

All detailed documentation is in the `setup/docs/` folder:

| Document | Read If... |
|----------|-----------|
| [setup/docs/INDEX.md](setup/docs/INDEX.md) | You want the complete guide |
| [setup/docs/README.md](setup/docs/README.md) | You want a quick reference |
| [setup/docs/CROSS-PLATFORM.md](setup/docs/CROSS-PLATFORM.md) | You're comparing platforms |

---

## 🌍 What's Included

### 📲 Dashboard
Web UI for:
- Real-time sensor data
- Stepper motor control
- Actuator control (Raspberry Pi only)
- Radar visualization
- System status

### 🔗 REST API
Access all features via HTTP:
```
Server: http://localhost:3000
API: http://localhost:3000/api
WebSocket: ws://localhost:3000
```

### 🍓 Raspberry Pi Features (Auto-Enabled)
- UART communication with Pico Master
- Stepper motor control
- Actuator control
- Kiosk display mode
- Auto-start on boot

### 💻 Windows/Linux Features
- Full dashboard access
- API testing
- Development environment
- No hardware support (expected)

---

## 🔧 Platform Comparison

| Feature | Windows | Linux | Raspberry Pi |
|---------|---------|-------|-------------|
| **Development** | ✅ | ✅ | ✅ |
| **Dashboard** | ✅ | ✅ | ✅ |
| **API** | ✅ | ✅ | ✅ |
| **UART/Pico** | ❌ | ❌ | ✅ |
| **Hardware Control** | ❌ | ❌ | ✅ |
| **Auto-Start** | ❌ | ❌ | ✅ |
| **Kiosk Display** | ❌ | ❌ | ✅ |

---

## 🏃 Common Tasks

### Windows

**First Time**
```powershell
.\setup-windows.ps1
# Choose 1 (SETUP), then 2 (START)
```

**Every Day**
```powershell
.\setup-windows.ps1
# Choose 2 (START)
# Browser opens automatically
```

**Troubleshoot**
```powershell
.\setup-windows.ps1
# Choose 3 (STATUS) to see what's running
```

### Raspberry Pi

**First Time (and only time!)**
```bash
bash setup-linux.sh
# Choose 1 (SETUP)
# Reboot when done
# Everything auto-starts!
```

**Daily Use**
```bash
# Just power on - everything starts automatically
# Check status:
bash setup-linux.sh
# Choose 3 (CHECK STATUS)
```

**View Dashboard Remotely**
```
Open browser to: http://<pi-ip>:3000
```

### Linux

**First Time**
```bash
bash setup-linux.sh
# Choose 1 (SETUP)
```

**Daily Development**
```bash
bash setup-linux.sh
# Choose 2 (START SERVERS)
# Browser opens
```

---

## 🆘 Quick Troubleshooting

### "Setup won't run" (Windows)
```powershell
# Set execution policy:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Then try again:
.\setup-windows.ps1
```

### "Port already in use" (Windows)
```powershell
# Check what's using it:
netstat -ano | findstr :3000
# Kill it if needed:
taskkill /PID <PID> /F
```

### "Can't connect to dashboard" (Any platform)
```bash
# Check if server is running:
ps aux | grep node

# Test port:
curl http://localhost:3000

# Check if firewall is blocking
```

### "UART not working" (Raspberry Pi only)
```bash
# Verify device exists:
ls -la /dev/ttyAMA0

# Check if enabled:
grep enable_uart /boot/config.txt

# If not enabled, reboot after setup
```

---

## 📁 File Structure

```
RadarProject/
├── setup-windows.ps1     ← Windows quick start
├── setup-windows.bat     ← Windows alternative
├── setup-linux.sh        ← Linux/Pi quick start
│
├── setup/
│   ├── windows/          ← Windows scripts
│   │   ├── win-setup.ps1
│   │   ├── run-windows.ps1
│   │   └── app-control.ps1
│   │
│   ├── linux/            ← Linux/Pi scripts
│   │   ├── app-setup.sh
│   │   ├── app-control.sh
│   │   └── ...
│   │
│   ├── shared/           ← Universal launchers
│   │   └── setup.sh
│   │
│   └── docs/             ← Full documentation
│       ├── README.md
│       ├── CROSS-PLATFORM.md
│       └── INDEX.md
│
├── RadarApp-FullStack/
│   ├── server/           ← Node.js backend
│   │   ├── index.js
│   │   ├── package.json
│   │   └── ...
│   │
│   └── client/           ← Vue.js frontend
│       ├── src/
│       ├── package.json
│       └── ...
│
└── RadarApp-Microcontroller/
    └── ... (Pico firmware)
```

---

## ✨ Next Steps

### Pick Your Platform:

**🪟 Windows Developer?**
```
Run: .\setup-windows.ps1
Choose: 1 (Setup), then 2 (Start)
Open: http://localhost:5173
```

**🍓 Raspberry Pi Kiosk?**
```
Run: bash setup-linux.sh
Choose: 1 (Setup)
Wait: For reboot
Done: Dashboard displays automatically
```

**🐧 Linux Server?**
```
Run: bash setup-linux.sh
Choose: 1 (Setup), then 2 (Start)
Open: http://localhost:3000
```

---

## 💡 Pro Tips

- **First time?** Just run the setup script for your platform and follow the prompts.
- **On Raspberry Pi?** After setup, NEVER need to run setup again—just reboot and everything starts.
- **Windows developer?** Can't connect to Pi hardware, but dashboard works perfectly for testing.
- **Stuck?** Run the setup script and choose "STATUS" or "LOGS" to see what's happening.

---

## 🤝 Support

- **Quick help:** See the status/logs from the menu
- **Full documentation:** Read [setup/docs/INDEX.md](setup/docs/INDEX.md)
- **Platform guides:** Check [setup/docs/CROSS-PLATFORM.md](setup/docs/CROSS-PLATFORM.md)
- **Server logs:** `bash setup-linux.sh` → Choose Logs

---

## 📞 Quick Command Reference

| Task | Windows | Linux/Pi |
|------|---------|---------|
| Setup | `.\setup-windows.ps1` → 1 | `bash setup-linux.sh` → 1 |
| Start | `.\setup-windows.ps1` → 2 | `bash setup-linux.sh` → 2 |
| Status | `.\setup-windows.ps1` → 3 | `bash setup-linux.sh` → 3 |
| Stop | `.\setup-windows.ps1` → 4 | `bash setup-linux.sh` → 4 |
| Logs | `app-control.ps1 logs` | `bash setup-linux.sh` → 5 |

---

**Version:** 2.0  
**Status:** ✅ Production Ready  
**Updated:** April 2026

🎉 **Ready? Pick your platform above and run the setup script!**
