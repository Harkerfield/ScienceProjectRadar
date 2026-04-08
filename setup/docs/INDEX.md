# 🚀 Radar Application - Setup & Documentation

Welcome! Choose your platform to get started.

## 🎯 Quick Start by Platform

### 🪟 Windows
```powershell
cd setup\windows
.\win-setup.ps1       # One-time setup
.\run-windows.ps1     # Start servers
.\app-control.ps1 status  # Check status
```

### 🍓 Raspberry Pi
```bash
cd setup/linux
sudo bash app-setup.sh    # One-time setup (App Mode, recommended)
sudo reboot               # Auto-starts after reboot
./app-control.sh status   # Check status
```

### 🐧 Linux
```bash
cd setup/shared
bash setup.sh             # Auto-detects and guides setup
```

---

## 📁 Folder Structure

```
setup/
├── windows/           # Windows-specific scripts
│   ├── win-setup.ps1
│   ├── win-setup.bat
│   ├── run-windows.ps1
│   ├── run-windows.bat
│   ├── app-control.ps1
│   └── app-control.bat
│
├── linux/            # Linux/Raspberry Pi scripts
│   ├── app-setup.sh
│   ├── raspi-kiosk-setup.sh
│   ├── app-launcher.sh
│   ├── app-control.sh
│   ├── service-manager.sh
│   ├── validate-system.sh
│   └── ...
│
├── shared/           # Cross-platform launchers
│   ├── setup.sh      # Auto-detects OS and runs setup
│   └── setup.ps1     # PowerShell version
│
├── docs/             # All documentation
│   ├── README.md
│   ├── CROSS-PLATFORM.md
│   ├── CROSS-PLATFORM-SETUP.md
│   ├── APP-MODE-SETUP.md
│   ├── RASPI_KIOSK_SETUP.md
│   └── ...
│
└── systemd/          # Systemd service files (Pi only)
    ├── radar-app.service
    ├── radar-display.service
    └── ...
```

---

## 📚 Documentation by Platform

### 🪟 Windows Setup
- **Quick Start:** `windows\win-setup.ps1`
- **Launch:** `windows\run-windows.ps1`
- **Control:** `windows\app-control.ps1`
- **Full Guide:** [docs/CROSS-PLATFORM.md](docs/CROSS-PLATFORM.md#-windows)

### 🍓 Raspberry Pi Setup
- **Recommended:** `linux\app-setup.sh` (App Mode)
- **Advanced:** `linux\raspi-kiosk-setup.sh` (Full Stack)
- **Control:** `linux\app-control.sh`
- **Full Guide:** [docs/CROSS-PLATFORM.md](docs/CROSS-PLATFORM.md#-raspberry-pi)

### 🐧 Linux Setup
- **Auto-Detect:** `shared\setup.sh`
- **Manual:** Check [docs/README.md](docs/README.md)
- **Full Guide:**  [docs/CROSS-PLATFORM.md](docs/CROSS-PLATFORM.md#-linux)

---

## 🔗 All Documentation Files

| Document | Purpose |
|----------|---------|
| [README.md](docs/README.md) | Quick reference for all platforms |
| [CROSS-PLATFORM.md](docs/CROSS-PLATFORM.md) | Complete guide for all platforms |
| [CROSS-PLATFORM-SETUP.md](docs/CROSS-PLATFORM-SETUP.md) | Technical deep dive |
| [APP-MODE-SETUP.md](docs/APP-MODE-SETUP.md) | Raspberry Pi kiosk setup |
| [RASPI_KIOSK_SETUP.md](docs/RASPI_KIOSK_SETUP.md) | Raspberry Pi advanced setup |
| [DEPLOYMENT-MODES.md](docs/DEPLOYMENT-MODES.md) | Compare deployment options |
| [STRUCTURE.md](docs/STRUCTURE.md) | Project file structure |
| [MANIFEST.md](docs/MANIFEST.md) | Package/file manifest |

---

## ⚡ Platform Quick Reference

| Feature | Windows | Linux | Pi |
|---------|---------|-------|-----|
| **Setup** | Batch/PowerShell | Bash | Bash |
| **Run** | `run-windows.ps1` | Manual/systemd | Auto-starts |
| **Control** | `app-control.ps1` | Shell cmds | `app-control.sh` |
| **UART** | ❌ | ❌ | ✅ |
| **Kiosk** | ❌ | ⚠️ | ✅ |
| **Auto-Start** | ❌ | ⚠️ | ✅ |

---

## 🚀 Common Commands

### Windows
```powershell
# All from windows\ folder:
.\win-setup.ps1              # Setup
.\run-windows.ps1            # Start
.\app-control.ps1 status     # Check status
.\app-control.ps1 stop       # Stop
```

### Linux/Pi
```bash
# All from linux\ or ./setup paths:
bash app-setup.sh            # Setup (one time)
./app-control.sh status      # Check status
./app-control.sh logs        # View logs
./app-control.sh restart     # Restart
```

### Any Platform
```bash
# From shared\ folder:
bash setup.sh                # Auto-detect OS and run setup
.\setup.ps1                  # PowerShell version
```

---

## ✨ What Each Folder Does

###  `windows/`
Contains Windows-specific scripts for:
- Installing dependencies (PowerShell & Batch)
- Launching servers in parallel
- Monitoring and controlling processes
- Checking ports and system status

### `linux/`
Contains Linux/Raspberry Pi scripts for:
- App mode setup (recommended for kiosk)
- Full stack setup (advanced)
- Service management
- System validation and UART configuration

### `shared/`
Contains universal launchers that:
- Automatically detect your operating system
- Route to the appropriate platform setup
- Work on any platform with bash or PowerShell

### `docs/`
Contains all documentation for:
- Platform-specific guides
- Troubleshooting
- Configuration reference
- Deployment scenarios
- Architecture overview

### `systemd/`
Contains Raspberry Pi systemd service files for:
- Auto-starting services on boot
- Service management and monitoring
- Log aggregation

---

## 🎯 Choose Your Setup

**New to this and just want it working?**
→ Run `.\setup.ps1` (Windows) or `bash setup.sh` (Linux/Pi)

**Developing on Windows?**
→ Read [docs/CROSS-PLATFORM.md](docs/CROSS-PLATFORM.md#-windows)

**Building a Kiosk on Raspberry Pi?**
→ Run `linux/app-setup.sh` then `sudo reboot`

**Deploying on Linux Server?**
→ Read [docs/README.md](docs/README.md)

---

## ❓ FAQ

**Q: Which setup should I use on Raspberry Pi?**
```
App Mode (app-setup.sh) - Simpler, perfect for kiosk displays
Full Stack (raspi-kiosk-setup.sh) - More control, production-ready
```

**Q: Can I run this on Windows for development?**
```
Yes! Use windows\win-setup.ps1 and run windows\run-windows.ps1
Full development and testing, but no UART/hardware support
```

**Q: What happens after Raspberry Pi setup?**
```
1. Everything auto-starts on boot
2. Dashboard displays on HDMI
3. UART ready for Pico Master at /dev/ttyAMA0
4. Use app-control.sh to manage
```

**Q: Where do I find logs?**
```
Windows: app-control.ps1 logs (or check process output)
Linux/Pi: app-control.sh logs (or journalctl if using systemd)
```

---

## 🆘 Quick Troubleshooting

**Port already in use:**
```powershell
# Windows
netstat -ano | findstr :3000

# Linux/Pi
lsof -i :3000
```

**Service won't start:**
```bash
./app-control.sh logs         # Check logs
./validate-system.sh          # Full diagnostics
```

**UART not working (Pi only):**
```bash
ls -la /dev/ttyAMA0           # Check device
grep enable_uart /boot/config.txt  # Check config
sudo reboot                   # Reboot if just enabled
```

---

## 📞 Next Steps

1. **Choose your platform** (Windows/Linux/Pi)
2. **Run the setup script** for your platform
3. **Follow the prompts** (they guide you)
4. **Start the application** (platform-specific command)
5. **Open dashboard** (usually http://localhost:5173 or :3000)

---

**Version:** 2.0 Cross-Platform  
**Updated:** April 2026  
**Status:** ✅ Production Ready

🚀 **Ready? Pick your platform and start setup!**
