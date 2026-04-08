# 🎯 Getting Started Guide

## TL;DR - Start Here!

```bash
# Windows:
.\setup-windows.ps1

# Linux/Raspberry Pi:
bash setup-linux.sh
```

That's it. Choose an option from the menu. Everything else is handled.

---

## 📁 What's In This Project?

### Root Level Scripts (YOU ARE HERE)
- **`setup-windows.ps1`** - Interactive setup wizard for Windows
- **`setup-windows.bat`** - Alternative for Command Prompt
- **`setup-linux.sh`** - Interactive setup wizard for Linux/Pi
- **`README.md`** - Complete documentation
- **`QUICKSTART.md`** - 30-second quick start
- **`.env.example`** - Environment variable template

### `setup/` Folder - All The Scripts
Organized by platform:
- **`windows/`** - Windows PowerShell & Batch scripts
- **`linux/`** - Linux & Raspberry Pi shell scripts
- **`shared/`** - Cross-platform launchers
- **`docs/`** - Complete documentation
- **`systemd/`** - Raspberry Pi auto-start services

### `RaspberryPiRadarFullStackApplicationAndStepperController/` - The Application
- **`server/`** - Node.js backend (Express.js, REST API)
- **`client/`** - Vue.js frontend (Vite, Dashboard)
- **`package.json`** - Dependencies

### `RaspberryPiPicoRadarAndServerController/` - Firmware
- Pico microcontroller code (not needed for this setup guide)

---

## 🚀 Three Ways to Start

### Option 1: Easiest (Interactive Menu)
```bash
# Windows
.\setup-windows.ps1

# Linux/Pi
bash setup-linux.sh
```
Just pick an option from the menu!

### Option 2: Quick Setup Script (Automated)
```bash
# Windows
.\setup\windows\win-setup.ps1

# Linux/Pi App Mode (Recommended)
sudo bash setup/linux/app-setup.sh

# Linux/Pi Full Stack (Advanced)
sudo bash setup/linux/raspi-kiosk-setup.sh
```

### Option 3: Manual (Advanced Users)
```bash
# Install dependencies
cd RaspberryPiRadarFullStackApplicationAndStepperController

# Server
cd server && npm install
npm start

# Client (new terminal)
cd client && npm install
npm run dev
```

---

## 🎮 What Each Menu Option Does

### Windows Menu
1. **SETUP** - Install npm packages, create `.env` files (one-time)
2. **START** - Launch server and client, open browser
3. **CHECK STATUS** - See running processes and ports
4. **STOP SERVERS** - Kill all npm processes
5. **EXIT** - Close menu

### Linux/Pi Menu
1. **SETUP** - Install packages and configure (one-time)
2. **START SERVERS** - Launch application
3. **CHECK STATUS** - View service status
4. **STOP SERVERS** - Stop all processes
5. **LOGS** - View application output
6. **EXIT** - Close menu

---

## 💡 Key Concepts

### First-Time Setup
The script will:
- Check that Node.js is installed
- Install npm dependencies
- Create `.env` files with defaults
- On Pi: Enable UART and set up auto-start

### Daily Use
After setup:
- **Windows:** Run setup script, choose "START"
- **Linux:** Run setup script, choose "START"  
- **Raspberry Pi:** Just power it on—everything starts automatically!

### Dashboard
Once running, open:
- **Windows/Linux Dev:** http://localhost:5173
- **Windows/Linux Production:** http://localhost:3000
- **Raspberry Pi:** Displays on HDMI or open http://localhost:3000
- **Remote:** http://[device-ip]:3000

---

## 🔧 Environment Setup

### Automatic (Recommended)
The setup scripts create `.env` automatically:
```bash
NODE_ENV=development
PORT=3000
VUE_APP_API_BASE_URL=http://localhost:3000/api
PICO_UART_ENABLED=false
LOG_LEVEL=debug
```

### Manual (If Needed)
1. Copy `.env.example` to `.env`
2. Edit values for your platform
3. For server: Copy to `server/.env`
4. For client: Copy to `client/.env` (Vite reads src/.env)

---

## 📊 Platform Comparison

| | Windows | Linux | Raspberry Pi |
|---|---------|-------|-------------|
| **Setup** | .\setup-windows.ps1 | bash setup-linux.sh | bash setup-linux.sh |
| **Port** | 3000 + 5173 | 3000 + 5173 | 3000 only |
| **Dashboard** | Browser (5173 dev) | Browser (5173 dev) | HDMI display |
| **UART** | ❌ | ❌ | ✅ |
| **Auto-start** | ❌ | ❌ | ✅ |
| **Best For** | Development | Development | Production |

---

## ✨ Common Workflows

### "I'm a Windows Developer"
```
1. Run: .\setup-windows.ps1
2. Choose: 1 (SETUP) - Wait for npm install
3. Choose: 2 (START) - Browser opens to dashboard
4. Edit code → Auto-reloads in browser
5. When done → Choose 4 (STOP)
```

### "I'm Setting Up a Raspberry Pi Kiosk"
```
1. Run: bash setup-linux.sh
2. Choose: 1 (SETUP) → 1 (App Mode)
3. Wait for installation to complete
4. Reboot when prompted
5. Power on → Dashboard displays on HDMI
6. Done! No more setup needed.
```

### "I'm Deploying on Linux Server"
```
1. Run: bash setup-linux.sh
2. Choose: 1 (SETUP)
3. Configure as needed (edit .env)
4. Deploy/run in background
5. Access at http://[server-ip]:3000
```

---

## 🆘 Troubleshooting Quick Fixes

### "Script won't run" (Windows)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup-windows.ps1
```

### "Permission denied" (Linux/Pi)
```bash
sudo bash setup-linux.sh
```

### "Port already in use"
```powershell
# Windows - Find and kill:
netstat -ano | findstr :3000
taskkill /PID [PID] /F

# Linux - Find and kill:
lsof -i :3000
kill -9 [PID]
```

### "Nothing appears on Pi HDMI"
- Check HDMI cable (sometimes monitors need it plugged in FIRST)
- Try: `bash setup-linux.sh` → Choose "5) LOGS"
- Reboot: `sudo reboot`

### "Can't find Node.js / npm"
```
Windows: Install from nodejs.org (check "Add to PATH")
Linux/Pi: $ sudo apt install nodejs npm
```

---

## 📞 Where to Find Help

| Question | Read |
|----------|------|
| How do I...? | This file (Getting Started) |
| Complete guide | [README.md](README.md) |
| Platform comparison | [setup/docs/CROSS-PLATFORM.md](setup/docs/CROSS-PLATFORM.md) |
| API reference | [setup/docs/DEPLOYMENT-MODES.md](setup/docs/DEPLOYMENT-MODES.md) |
| All documentation | [setup/docs/INDEX.md](setup/docs/INDEX.md) |

---

## 🎯 Next Steps

### Pick Your Scenario:

**"I just want to run it"**
→ Follow "[TL;DR - Start Here!](#tldr---start-here)" above

**"I'm not sure which platform I'm on"**
→ Run `setup-windows.ps1` or `setup-linux.sh` - They auto-detect

**"I want to understand the full system"**
→ Read [README.md](README.md)

**"I need help with a specific platform"**
→ Go to [setup/docs/CROSS-PLATFORM.md](setup/docs/CROSS-PLATFORM.md)

---

## ✅ Verify It Works

**Windows/Linux:**
```
Open browser to: http://localhost:5173
Should see: Radar Dashboard
```

**Raspberry Pi:**
```
Check HDMI: Dashboard displays fullscreen
Or browser: http://[pi-ip]:3000
```

---

**Done! You're ready to go! 🚀**

If something doesn't work, start with the menu (run the setup script again) and choose "STATUS" or "LOGS" to see what's happening.
