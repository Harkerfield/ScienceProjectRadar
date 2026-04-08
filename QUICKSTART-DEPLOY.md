# Quick Start - Deploy to Raspberry Pi

## 30-Second Deploy

### Windows
```powershell
cd F:\RadarProject
.\deploy-to-pi.ps1
# Choose deployment method when prompted
# Wait 5-15 minutes
# Access app at: http://raspberrypi.local:3000
```

### Linux/Mac
```bash
cd ~/RadarProject
chmod +x deploy-to-pi.sh
./deploy-to-pi.sh
# Choose deployment method when prompted
# Wait 5-15 minutes
# Access app at: http://raspberrypi.local:3000
```

## What Happens

1. ✓ Connects to your Raspberry Pi via SSH
2. ✓ Copies project files (Git clone or SCP)
3. ✓ Updates system packages
4. ✓ Installs Node.js
5. ✓ Enables UART for Pico communication
6. ✓ Installs npm dependencies
7. ✓ Builds Vue.js frontend
8. ✓ Creates auto-launch service
9. ✓ Gives you access URL

## Default Values

| Setting | Default | Override |
|---------|---------|----------|
| Pi Hostname | `raspberrypi.local` | Use `-PiHost 192.168.1.100` |
| Pi Username | `pi` | Use `-PiUser myuser` |
| Installation Dir | `/home/pi/RadarProject` | Use `-PiProjectDir /opt/radar` |

## After Deploy

- **Access app:** Open browser to `http://raspberrypi.local:3000`
- **Check status:** `ssh pi@raspberrypi.local` then `sudo systemctl status radar-app`
- **View logs:** `sudo journalctl -u radar-app -f`
- **IMPORTANT:** If UART was enabled, **reboot the Pi**: `sudo reboot`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Can't connect to Pi | Use IP instead: `-PiHost 192.168.1.100` |
| Git clone fails | Choose "SCP Copy" method instead |
| App won't start | Check logs: `sudo journalctl -u radar-app -n 50` |
| UART not working | Reboot Pi: `sudo reboot` |
| SSH key prompts | Run once manually: `ssh pi@raspberrypi.local` |

## Full Commands

### Windows with Custom IP
```powershell
.\deploy-to-pi.ps1 -PiHost 192.168.1.55 -PiUser pi
```

### Linux with Custom IP
```bash
./deploy-to-pi.sh -h 192.168.1.55 -u pi
```

## Full Documentation

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed guide with troubleshooting, manual steps, and advanced options.

## Need Help?

1. Run the deploy script
2. Watch for error messages
3. Check Pi connectivity: `ping raspberrypi.local`
4. Try this: `ssh pi@raspberrypi.local` (test SSH first)
5. Read [DEPLOYMENT.md](./DEPLOYMENT.md) troubleshooting section
