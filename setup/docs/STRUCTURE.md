# Setup Package Structure

Complete overview of all files in the `/setup` directory.

## Directory Layout

```
setup/
│
├── 🚀 APP MODE (RECOMMENDED) ⭐
│   ├── app-setup.sh                    ← Run this first (ONE-TIME)
│   ├── app-launcher.sh                 ← Auto builds + starts + displays
│   ├── app-control.sh                  ← Daily management
│   ├── APP-MODE-SETUP.md               ← Complete guide
│   └── systemd/
│       └── radar-app.service           ← Single unified service
│
├── ⚙️ FULL STACK MODE (Advanced)
│   ├── raspi-kiosk-setup.sh            ← Full setup (ONE-TIME)
│   ├── quick-setup.sh                  ← Fast deps-only setup
│   ├── service-manager.sh              ← Service control
│   ├── validate-system.sh              ← System diagnostics
│   ├── start-kiosk.sh                  ← Browser launcher
│   ├── RASPI_KIOSK_SETUP.md            ← Complete guide
│   └── systemd/
│       ├── radar-server.service        ← Node.js server
│       ├── radar-display.service       ← X11 display
│       ├── radar-kiosk.service         ← Chromium browser
│       └── radar-app.service           ← Simplified version
│
├── 📋 DOCUMENTATION
│   ├── README.md                       ← Quick start & overview (START HERE)
│   ├── DEPLOYMENT-MODES.md             ← Compare all options
│   ├── APP-MODE-SETUP.md               ← App mode complete guide
│   ├── RASPI_KIOSK_SETUP.md            ← Full stack complete guide
│   └── STRUCTURE.md                    ← This file
│
└── 📁 Configuration
    └── .env.production                 ← Server environment config
```

## By Use Case

### 📱 "I Just Want Kiosk Mode" (You Here)
```
1. Copy setup/ to Raspberry Pi
2. Navigate: cd ~/radar-project/setup
3. Run: sudo bash app-setup.sh
4. Reboot: sudo reboot
5. Done! ✨

Files used: app-setup.sh, app-launcher.sh, app-control.sh
Read: APP-MODE-SETUP.md
```

### ⚙️ "I Need Advanced Control"
```
1. Copy setup/ to Raspberry Pi
2. Navigate: cd ~/radar-project/setup
3. Run: sudo bash raspi-kiosk-setup.sh
4. Reboot: sudo reboot
5. Manage: ./service-manager.sh

Files used: raspi-kiosk-setup.sh, service-manager.sh, validate-system.sh
Read: RASPI_KIOSK_SETUP.md
```

### 🧪 "I'm Developing"
```
1. Manual: Don't use any setup scripts
2. Build: npm run build (client)
3. Start: npm start (server)
4. Display: DISPLAY=:0 chromium-browser http://localhost:3000

Files used: None (manual control)
Read: Any relevant docs for guidance
```

## File Descriptions

### Setup Scripts (Run ONE TIME)

| File | Mode | Purpose | Time |
|------|------|---------|------|
| `app-setup.sh` | App | Complete app setup | ~10 min |
| `raspi-kiosk-setup.sh` | Full | Complete full stack | ~20 min |
| `quick-setup.sh` | Full | Just dependencies | ~10 min |

### Control Scripts (Daily Use)

| File | Purpose | Usage | Needs Sudo |
|------|---------|-------|-----------|
| `app-control.sh` | Start/stop/logs app | `./app-control.sh status` | Sometimes |
| `service-manager.sh` | Start/stop services | `./service-manager.sh restart` | Sometimes |
| `validate-system.sh` | System diagnostics | `./validate-system.sh` | No |

### Launcher Scripts (Automatic)

| File | Purpose | Runs | How |
|------|---------|------|-----|
| `app-launcher.sh` | Build+start+display | Systemd | Automatically |
| `start-kiosk.sh` | Launch browser | Systemd | Automatically |

### Documentation Files

| File | For | When to Read |
|------|-----|--------------|
| `README.md` | Quick overview | First |
| `DEPLOYMENT-MODES.md` | Choosing modes | Before deciding |
| `APP-MODE-SETUP.md` | App mode details | After choosing app mode |
| `RASPI_KIOSK_SETUP.md` | Full stack details | After choosing full stack |
| `STRUCTURE.md` | This overview | Understanding layout |

### SystemD Service Files

Located in `systemd/` subdirectory

**App Mode:**
- `radar-app.service` - Single unified service

**Full Stack:**
- `radar-server.service` - Node.js server
- `radar-display.service` - X11 display server
- `radar-kiosk.service` - Chromium browser

### Configuration Files

**Server Configuration:**
- `.env.production` - Environment variables for server (UART, port, features)

**System Configuration:**
- Automatically modified in `/boot/config.txt` (UART enablement)
- Automatically modified in `/boot/cmdline.txt` (serial console)

## Decision Tree

```
START HERE: README.md
    ↓
Want simple kiosk?
    ├─ YES → Read APP-MODE-SETUP.md
    │        Run: sudo bash app-setup.sh
    │        Use: ./app-control.sh
    │
    └─ NO → Need more control?
            ├─ YES → Read RASPI_KIOSK_SETUP.md
            │        Run: sudo bash raspi-kiosk-setup.sh
            │        Use: ./service-manager.sh
            │
            └─ NO → Manual development
                    Read: Relevant docs
                    Run: npm commands directly
```

## Quick Command Reference

### App Mode
```bash
# Setup
sudo bash setup/app-setup.sh
sudo reboot

# Daily use
./app-control.sh status              # Check status
./app-control.sh logs                # View logs
./app-control.sh restart             # Restart service
```

### Full Stack
```bash
# Setup
sudo bash setup/raspi-kiosk-setup.sh
sudo reboot

# Daily use
./service-manager.sh status          # Check all services
./service-manager.sh logs-server     # Server logs
./service-manager.sh restart         # Restart services
```

### Validation
```bash
# Both modes
./validate-system.sh                 # Full health check
curl http://localhost:3000           # Test server
ls -la /dev/ttyAMA0                  # Check UART
```

## File Dependencies

### App Mode
```
app-setup.sh
  └── Installs → radar-app.service
  └── Copies → app-launcher.sh
  └── Creates → .env file

app-launcher.sh (runs at boot)
  └── Builds → client
  └── Starts → server
  └── Launches → chromium

app-control.sh
  └── Controls → radar-app.service
```

### Full Stack
```
raspi-kiosk-setup.sh
  └── Installs → all systemd services
  └── Copies → start-kiosk.sh
  └── Creates → .env file

radar-display.service (runs at boot)
  └── Starts → X11

radar-server.service (runs at boot)
  └── Starts → node server

radar-kiosk.service (runs at boot)
  └── Uses → start-kiosk.sh
  └── Launches → chromium
```

## What Each Does at Startup

### App Mode Boot Sequence
```
1. X11 starts automatically
2. Systemd launches radar-app.service
3. app-launcher.sh runs:
   a. Check directories
   b. Install/update dependencies
   c. Build client (if needed)
   d. Start server on :3000
   e. Confirm server responds
   f. Launch Chromium in --app mode
4. Dashboard displays
```

### Full Stack Boot Sequence
```
1. Systemd launches radar-display.service
   → X11 display starts
2. Systemd launches radar-server.service
   → Node.js starts on :3000
3. Systemd launches radar-kiosk.service
   → Waits for server ready
   → Runs start-kiosk.sh
   → Chromium launches fullscreen
4. Dashboard displays
```

## Switching Between Modes

### App Mode to Full Stack
```bash
./app-control.sh disable
sudo bash raspi-kiosk-setup.sh
sudo reboot
```

### Full Stack to App Mode
```bash
./service-manager.sh disable
sudo bash app-setup.sh
sudo reboot
```

## Version History

| Version | Date | Mode | Notes |
|---------|------|------|-------|
| 1.0 | Apr 2026 | Full Stack | Initial release |
| 2.0 | Apr 2026 | + App Mode | Added simplified app mode |
| Latest | Apr 2026 | Both | Documented both options |

## Support Tools

All modes include diagnostic tools:

```
validate-system.sh          // Check hardware, UART, services, etc
journalctl -u radar-app     // View logs (App mode)
journalctl -u radar-*       // View all logs (Full stack)
curl http://localhost:3000  // Test server connectivity
```

## Storage Requirements

**Minimum:**
- 100 MB project files
- 200 MB Node.js modules
- 100 MB built client
- = ~400 MB total

**Recommended:**
- 1+ GB free for build cache and logs
- 2+ GB free for system headroom

## Network Requirements

**Setup Phase:**
- Internet connection needed (package downloads)

**Runtime:**
- Local network optional (server runs on localhost)
- Remote access optional (accessible from network)

## Security Notes

All scripts:
- ✅ Create backups before modifying system files
- ✅ Use restrictive permissions on sensitive files
- ✅ Log all operations
- ✅ Auto-restart on failure
- ⚠️ Still need:
  - Firewall configuration
  - Network security review
  - Access control setup

## Troubleshooting by File

**Can't run setup scripts?**
→ Check permissions: `chmod +x *.sh`

**Service won't start?**
→ Check logs: `journalctl -u radar-*`

**UART not working?**
→ Run validate: `./validate-system.sh`

**Server won't respond?**
→ Test: `curl http://localhost:3000`

**Chromium won't display?**
→ Check logs: `./app-control.sh logs`

## Next Steps

1. **Choose mode:** [DEPLOYMENT-MODES.md](DEPLOYMENT-MODES.md)
2. **Read guide:** `APP-MODE-SETUP.md` or `RASPI_KIOSK_SETUP.md`
3. **Run setup:** One of the setup scripts
4. **Reboot:** `sudo reboot`
5. **Manage:** Use control script daily

---

**Latest Update:** April 2026  
**Status:** Production Ready  
**Modes:** 2 (App + Full Stack)  
**Scripts:** 9 (setup + control + docs)
