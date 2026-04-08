# Hostname-Based Access Setup Guide

This guide explains how to access the Radar application using the Raspberry Pi hostname instead of IP addresses.

## Quick Access Methods

### 1. **Automatic mDNS (Recommended) - Works Everywhere**

Once the Raspberry Pi is running the application:

```
http://raspberrypi.local:3000
```

Replace `raspberrypi` with your actual Pi hostname if different.

**Setup Requirements:**
- **Raspberry Pi OS:** Already has mDNS enabled by default
- **Windows:** Requires [Apple Bonjour](https://support.apple.com/downloads/bonjour) or Windows 10/11 with mDNS support
- **macOS:** Already has mDNS enabled by default  
- **Linux:** Install `avahi-daemon`: `sudo apt install avahi-daemon`

### 2. **Direct Hostname Access**

If mDNS is not available, use the hostname directly:

```
http://your-pi-hostname:3000
```

This works if the Pi is on your network and your device can resolve hostnames.

### 3. **IP Address (Fallback)**

```
http://192.168.x.x:3000
```

## Configuration

### Auto-Detection (Default)

The application automatically detects your access method and routes to the correct API:

- **Client Service:** `client/src/services/apiService.js` auto-detects the hostname
- **Socket.io Service:** `client/src/services/socketService.js` auto-detects the hostname

✅ **No configuration needed** - Just access via any hostname and it works

### Manual Configuration (Optional)

Edit `.env` in the project root if you want to override auto-detection:

```env
# Force specific API backend
VUE_APP_API_BASE_URL=http://my-radar-pi.local:3000/api

# Force specific Socket.io server
VUE_APP_SOCKET_URL=http://my-radar-pi.local:3000
```

## Server Configuration

The Node.js server is configured to accept requests from:

- `localhost` and `127.0.0.1`
- Your Raspberry Pi hostname (e.g., `raspberrypi`)
- Your hostname with `.local` suffix (e.g., `raspberrypi.local`)
- Any configured environment variable sources

**CORS Origins are dynamically added** - no manual configuration needed.

## Finding Your Raspberry Pi's Hostname

### On the Raspberry Pi Terminal:
```bash
hostname
```

### From Windows PowerShell:
```powershell
nslookup raspberrypi.local
```

### From macOS/Linux Terminal:
```bash
nslookup raspberrypi.local
```

### Using mDNS Browser:
- **Windows:** Download Bonjour Browser (mDNS Browser)
- **macOS:** Download Bonjour Browser or use Finder
- **Linux:** Install `avahi-discover` and browse local network

## Raspberry Pi Setup

When running on Raspberry Pi, the server logs all access points on startup:

```
========== ACCESS POINTS ==========
Local:    http://localhost:3000
Hostname: http://raspberrypi:3000
mDNS:     http://raspberrypi.local:3000

CORS Origins Allowed:
  - http://localhost:3000
  - http://localhost:8080
  - http://raspberrypi:3000
  - http://raspberrypi.local:3000
===================================
```

## Troubleshooting

### Cannot access `hostname.local`

**Solution 1: Enable mDNS on your device**
- Windows: Install Bonjour for Windows
- Linux: `sudo apt install avahi-daemon && sudo systemctl start avahi-daemon`

**Solution 2: Use direct hostname**
- Replace `.local` with just the hostname: `http://raspberrypi:3000`

**Solution 3: Use IP address**
- Find your Pi's IP: `hostname -I` on the Pi
- Access via: `http://192.168.x.x:3000`

### CORS Errors in Browser Console

The server allows requests from:
- Same hostname used to access the app
- localhost/127.0.0.1
- Explicitly configured in `.env`

**Solution:** Make sure you're accessing via the same hostname in both URL bar and API calls.

### Socket.io Connection Fails

**Solution 1:** Check browser console for error details
```javascript
// Check what URL the app is trying to connect to
console.log(window.location.hostname)
```

**Solution 2:** Verify server is running and accessible
```bash
curl http://raspberrypi.local:3000/health
```

**Solution 3:** Check firewall is not blocking port 3000
```bash
sudo ufw allow 3000/tcp  # On Pi: enable if using UFW
```

## Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| PORT | 3000 | Server port |
| NODE_ENV | development | Environment mode |
| VUE_APP_API_BASE_URL | (auto-detect) | API endpoint for frontend |
| VUE_APP_SOCKET_URL | (auto-detect) | WebSocket endpoint |
| LOG_LEVEL | debug | Logging verbosity |

## Network Architecture

```
┌─────────────────────────────────────────────┐
│ Your Device (Windows/Mac/Linux/Mobile)      │
│ Browser: http://hostname.local:3000         │
└────────────────┬────────────────────────────┘
                 │ mDNS or Hostname DNS
                 │ Resolution
┌────────────────▼────────────────────────────┐
│ Raspberry Pi on Network                     │
│ Hostname: raspberrypi                       │
│ mDNS: raspberrypi.local                     │
│ Port: 3000 (Node.js Server)                │
└────────────────┬────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
    ┌───▼────┐       ┌────▼────┐
    │ API    │       │ Socket   │
    │ Routes │       │ IO       │
    │ (REST) │       │ (Real-   │
    │        │       │  time)   │
    └────────┘       └──────────┘
```

## Tips for Production

1. **Use a fixed Pi hostname** - Configure in `/etc/hostname`
2. **Set static IP** - Ensure Pi doesn't change IP address
3. **Enable mDNS on all clients** - Standard on macOS, built-in on Pi
4. **Consider DNS** - Set Pi as hostname in your router's DHCP settings
5. **Use HTTPS** - For remote access, configure SSL/TLS

## See Also

- [README.md](README.md) - Main project documentation
- [GETTING-STARTED.md](GETTING-STARTED.md) - Setup instructions
- [.env.example](.env.example) - Environment configuration template
