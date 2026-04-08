# 🚀 Radar Application

**Get started in 30 seconds!**

## ⚡ Quick Start

### 🪟 Windows Users
```powershell
# Run the setup wizard:
.\setup-windows.ps1

# OR use batch version:
setup-windows.bat
```

### 🍓 Raspberry Pi Users
```bash
# Run the setup wizard:
bash setup-linux.sh

# OR direct setup:
sudo bash setup/linux/app-setup.sh && sudo reboot
```

### 🐧 Linux Users  
```bash
# Run the setup wizard:
bash setup-linux.sh

# OR direct setup:
bash setup/linux/app-setup.sh
```

---

## 📋 What These Scripts Do

### `setup-windows.ps1` / `setup-windows.bat` 
Interactive menu to:
- ✅ **SETUP** - Install dependencies (first time only)
- 🚀 **START** - Launch servers and open dashboard
- 📊 **STATUS** - Check if everything is running
- 🛑 **STOP** - Stop all servers

### `setup-linux.sh`
Interactive menu for Linux/Pi with:
- ✅ **SETUP** - Install and configure (auto-detects Pi vs Linux)
- 🚀 **START** - Launch dashboard
- 📊 **STATUS** - Check services
- 🛑 **STOP** - Stop servers
- 📋 **LOGS** - View application logs

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

## 📚 Full Documentation

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
├── RaspberryPiRadarFullStackApplicationAndStepperController/
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
└── RaspberryPiPicoRadarAndServerController/
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
