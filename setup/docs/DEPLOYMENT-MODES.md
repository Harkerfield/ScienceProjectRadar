# Deployment Modes - Setup Options

Choose the setup that best fits your use case.

## 🎯 Quick Decision Guide

| Need | Choose | Time |
|------|--------|------|
| **Kiosk mode, simplest setup** | **App Mode** | ~10 min |
| **Advanced control, separate services** | Full Stack | ~20 min |
| **Testing, development** | Manual | Varies |

---

## 1️⃣ APP MODE (Recommended for Kiosk)

**Best for:** Kiosk displays, embedded systems, simplicity

### Single Command Setup
```bash
sudo bash setup/app-setup.sh
sudo reboot
```

### What It Does
- 🔹 Builds client automatically
- 🔹 Starts server automatically  
- 🔹 Launches Chromium as app automatically
- 🔹 **One systemd service** (radar-app)
- 🔹 Auto-recovery on crash

### Daily Usage
```bash
./setup/app-control.sh status      # Check status
./setup/app-control.sh logs        # View logs
./setup/app-control.sh restart     # Restart
```

### Pros
✅ Simplest setup  
✅ Single service to manage  
✅ Automatic client build  
✅ Automatic recovery  
✅ Perfect for kiosk  

### Cons
❌ Less granular control  
❌ All-or-nothing restart  
❌ Can't stop just server  

### Files
- `app-setup.sh` - Initial setup
- `app-launcher.sh` - Application launcher
- `app-control.sh` - Daily management
- `systemd/radar-app.service` - Service definition
- `APP-MODE-SETUP.md` - Full documentation

---

## 2️⃣ FULL STACK MODE (Advanced Control)

**Best for:** Production deployments, advanced monitoring, separate service management

### Multi-Command Setup
```bash
sudo bash setup/raspi-kiosk-setup.sh
sudo reboot
```

### What It Does
- 🔹 Enables X11 display (radar-display.service)
- 🔹 Starts server (radar-server.service)
- 🔹 Launches Chromium (radar-kiosk.service)
- 🔹 **Three independent systemd services**
- 🔹 Granular service control

### Daily Usage
```bash
./setup/service-manager.sh status              # All services
./setup/service-manager.sh restart-server      # Just server
./setup/service-manager.sh logs-server         # Server logs
./setup/service-manager.sh logs-kiosk          # Browser logs
```

### Pros
✅ Granular control  
✅ Can manage services separately  
✅ More monitoring options  
✅ Production-ready logging  
✅ Easy to debug issues  

### Cons
❌ More complex setup  
❌ Multiple services to manage  
❌ More resource usage  
❌ Manual client build  

### Services
- `radar-display.service` - X11 server
- `radar-server.service` - Node.js on :3000
- `radar-kiosk.service` - Chromium browser

### Files
- `raspi-kiosk-setup.sh` - Initial setup
- `quick-setup.sh` - Fast setup (deps only)
- `service-manager.sh` - Service control
- `start-kiosk.sh` - Browser launcher
- `validate-system.sh` - Health check
- `RASPI_KIOSK_SETUP.md` - Full documentation

---

## 3️⃣ MANUAL MODE (Development/Testing)

**Best for:** Development, testing, custom deployments

### Manual Steps
```bash
# Terminal 1: Build client
cd client
npm install
npm run build

# Terminal 2: Start server
cd server
npm install
npm start

# Terminal 3: Launch browser
DISPLAY=:0 chromium-browser --app=http://localhost:3000
```

### Pros
✅ Full control  
✅ Easy debugging  
✅ Ideal for development  
✅ No systemd services  
✅ Quick iteration  

### Cons
❌ Must manage manually  
❌ No auto-recovery  
❌ Complex multi-terminal workflow  
❌ Not suitable for production  

---

## Feature Comparison

| Feature | App Mode | Full Stack | Manual |
|---------|----------|-----------|--------|
| **Setup Time** | ~10 min | ~20 min | Varies |
| **Services** | 1 | 3 | 0 |
| **Setup Script** | Yes | Yes | No |
| **Auto-Start** | Yes | Yes | No |
| **Client Build** | Auto | Manual | Manual |
| **Granular Control** | No | Yes | Yes* |
| **Auto-Recovery** | Yes | Yes | No |
| **Monitoring** | Basic | Advanced | None |
| **Production Ready** | Yes | Yes | No |
| **Complexity** | Low | Medium | Custom |

\* In manual mode, you have full control but must manage everything

---

## Configuration Files

### App Mode
- `.env.production` - Server configuration

### Full Stack
- `.env.production` - Server configuration
- `/boot/config.txt` - System configuration

### Manual
- Create `.env` as needed

---

## UART Enablement

**All modes enable UART automatically.**

To verify:
```bash
# Check UART is enabled
grep enable_uart /boot/config.txt

# Check device exists
ls -la /dev/ttyAMA0

# Test connection
curl http://localhost:3000/api/stepper/status
```

---

## Switching Between Modes

### From App Mode → Full Stack
```bash
./setup/app-control.sh disable
sudo bash setup/raspi-kiosk-setup.sh
sudo reboot
```

### From Full Stack → App Mode
```bash
./setup/service-manager.sh disable
sudo bash setup/app-setup.sh
sudo reboot
```

### To Manual
```bash
./setup/app-control.sh disable        # App mode
# OR
./setup/service-manager.sh disable    # Full stack
# OR just don't start any scripts
```

---

## Recommended for Different Use Cases

### 🖥️ Living Room Display Kiosk
**→ APP MODE**
- Simple, single service
- Auto-recovery
- No management needed

### 📊 Office Dashboard
**→ FULL STACK MODE**
- Better monitoring
- Can restart components
- Advanced logging

### 🧪 Development/Testing
**→ MANUAL MODE**
- Full control
- Easy debugging
- Quick iteration

### 🏭 Production Deployment
**→ FULL STACK MODE**
- Proven architecture
- Service isolation
- Better troubleshooting

### 🎯 Kiosk (Budget/Simple)
**→ APP MODE**
- Minimal setup
- Minimal dependencies
- Fast boot time

---

## Getting Help

### App Mode Issues
```bash
./setup/app-control.sh logs
# See APP-MODE-SETUP.md for detailed guide
```

### Full Stack Issues
```bash
./setup/service-manager.sh status
./setup/validate-system.sh
# See RASPI_KIOSK_SETUP.md for detailed guide
```

### Manual Issues
```bash
# Check each component separately
npm start                          # Server
DISPLAY=:0 chromium-browser 'http://localhost:3000'  # Browser
```

---

## Performance Characteristics

### Startup Times
**App Mode:** 30-60 seconds (+ build on first boot)  
**Full Stack:** 45-90 seconds  
**Manual:** Instant (operator starts each component)

### Runtime Memory Usage
**App Mode:** ~150-200 MB  
**Full Stack:** ~180-250 MB  
**Manual:** ~150-200 MB  

### CPU Usage
**App Mode:** Low (auto-optimized)  
**Full Stack:** Low-Medium  
**Manual:** Varies by operator

---

## Troubleshooting by Mode

### App Mode: "Chromium won't display"
```bash
./setup/app-control.sh logs | grep -i display
DISPLAY=:0 /home/pi/app-launcher.sh  # Test manually
```

### Full Stack: "Services not starting"
```bash
./setup/service-manager.sh status
journalctl -u radar-* -n 50
```

### Manual: "Connection refused"
```bash
curl http://localhost:3000         # Server running?
echo $DISPLAY                       # Display set?
ps aux | grep chromium             # Browser running?
```

---

## Upgrading Your Setup

### Add Features in App Mode
Edit `.env` file:
```bash
nano ~/radar-project/.../server/.env
./setup/app-control.sh restart
```

### Rebuild Client in App Mode
```bash
cd ~/radar-project/.../client
npm run build
./setup/app-control.sh restart
```

### Update Dependencies
```bash
# App mode
cd ~/radar-project/.../server
npm update
./setup/app-control.sh restart

# Full stack (same process)
```

---

## Final Recommendation

**Start with APP MODE:**
- ✅ Simplest
- ✅ Works out of box
- ✅ Perfect for kiosk
- ✅ Upgrade to Full Stack later if needed

```bash
# Copy to Pi and run:
sudo bash setup/app-setup.sh
sudo reboot
# Done!
```

That's it. Everything else is automatic.

---

**Choose your mode above, then follow the quick start in:**
- **App Mode:** `APP-MODE-SETUP.md`
- **Full Stack:** `RASPI_KIOSK_SETUP.md`
- **Manual:** Your own procedure

Happy deploying! 🚀
