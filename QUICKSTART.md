# ⚡ QUICKSTART - 30 Seconds to Running

## Pick Your Platform

### 🪟 Windows?
```powershell
.\setup-windows.ps1
```
→ Choose "1) SETUP" (first time only)  
→ Choose "2) START"  
→ ✅ Done! Dashboard opens automatically

### 🍓 Raspberry Pi?
```bash
bash setup-linux.sh
# Choose "1) SETUP" 
# Let it finish, then power cycle
# Everything auto-starts!
```

### 🐧 Linux?
```bash
bash setup-linux.sh
# Choose "1) SETUP"
# Choose "2) START"
# Open http://localhost:3000
```

---

## What Happens?

✅ **Server** starts on port 3000  
✅ **Dashboard** opens on port 5173 (Windows/Linux) or display (Pi)  
✅ **API** ready at http://localhost:3000/api  
✅ **WebSocket** real-time updates enabled  

---

## ⚙️ First Time Only (Setup)

**Windows:**
- Installs npm dependencies
- Creates `.env` files
- Ready to use!

**Raspberry Pi:**
- Installs npm dependencies
- Enables UART (GPIO 14/15)
- Configures auto-start
- Reboots automatically

**Linux:**
- Installs npm dependencies
- Configures environment
- Ready to use!

---

## 🎮 Daily Use

**Windows:**
```
Run: .\setup-windows.ps1
Every day, just choose "2) START"
```

**Raspberry Pi:**
```
Just power on!
Everything starts automatically
Dashboard displays on HDMI
```

**Linux:**
```
Run: bash setup-linux.sh
Every day, just choose "2) START"
```

---

## 🆘 Need Help?

| Issue | Solution |
|-------|----------|
| "Permission denied" (Linux/Pi) | Run with `sudo` |
| "Port already in use" | Run status to find it, kill the process |
| "Can't connect to dashboard" | Run status/logs to check what's happening |
| "UART not working" (Pi) | Make sure you rebooted after setup |

---

## 📊 Dashboard URL

| Platform | URL |
|----------|-----|
| **Windows/Linux** | http://localhost:5173 (dev) or http://localhost:3000 |
| **Raspberry Pi** | Displays on HDMI automatically OR Open browser to http://localhost:3000 |
| **Remote Access** | http://[device-ip]:3000 |

---

## ✅ Verify It Works

### Windows/Linux:
```powershell
# Open in browser:
http://localhost:3000

# Or test via command:
curl http://localhost:3000
```

### Raspberry Pi:
- Check HDMI display (should show dashboard)
- Or open browser: http://[pi-ip]:3000

---

**That's it! 🎉**

For more details, see [README.md](README.md) or run the setup script and choose your platform.
