# Raspberry Pi Kiosk Mode Setup Guide

## Overview
This guide provides step-by-step instructions to configure a Raspberry Pi 4 as a full kiosk display for the Radar Full-Stack application with automatic server startup and UART enabled for Pico communication.

## Prerequisites
- Raspberry Pi 4 (4GB+ recommended)
- Fresh Raspberry Pi OS (64-bit recommended)
- Current project code cloned to `/home/pi/radar-project`
- HDMI display connected
- Internet connection (for initial setup)

## Hardware Setup

### UART Connection (Pico Master Communication)
Connect the Pico Master to Raspberry Pi GPIO UART:
```
Pico UART0 >> Raspberry Pi UART0 (GPIO14/GPIO15)
Pico TX  (GPIO0)  >> Pi RX  (GPIO15 / Pin 10)
Pico RX  (GPIO1)  >> Pi TX  (GPIO14 / Pin 8)
Pico GND         >> Pi GND (Pin 6, 9, 14, 20, 25, 30, 34, 39)
Pico 3V3         >> Pi 3V3 (Pin 1, 17)
```

Note: Use 3.3V levels (Pico is already 3.3V compatible)

## Installation Steps

### 1. Prepare Raspberry Pi OS

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Git if not present
sudo apt-get install -y git

# Clone project (if not already cloned)
cd /home/pi
git clone <your-repo-url> radar-project
cd radar-project
```

### 2. Run Automated Setup

```bash
# Make setup script executable
chmod +x setup/raspi-kiosk-setup.sh

# Run the setup script (requires sudo)
sudo bash setup/raspi-kiosk-setup.sh
```

This script will:
- ✅ Update all system packages
- ✅ Install Node.js, npm, Chromium, X11, and required build tools
- ✅ Enable UART for Pico communication
- ✅ Build Node.js server and Vue.js client
- ✅ Create systemd services for auto-start
- ✅ Configure environment variables

### 3. Manual UART Configuration (Already done by setup script)

If running manually, enable UART:

```bash
# Edit boot configuration
sudo nano /boot/config.txt

# Add these lines:
enable_uart=1
dtoverlay=disable-bt
gpu_mem=128
dtparam=audio=off

# Save (Ctrl+X, Y, Enter)

# Disable serial console
sudo sed -i 's/console=serial0,115200 //' /boot/cmdline.txt
```

### 4. Configure Environment

Edit the server environment configuration:

```bash
nano /home/pi/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/server/.env
```

Key settings:
```
NODE_ENV=production
PORT=3000
PICO_UART_ENABLED=true
PICO_UART_PORT=/dev/ttyAMA0
PICO_UART_BAUD_RATE=115200
```

### 5. Reboot System

```bash
sudo reboot
```

The system will automatically:
1. Start the X11 display server
2. Start the Node.js server (port 3000)
3. Launch Chromium in fullscreen kiosk mode
4. Connect to the local server at http://localhost:3000

## Service Management

### Check Status
```bash
# Check all services
systemctl status radar-server
systemctl status radar-display
systemctl status radar-kiosk

# Or check all three
systemctl status radar-*.service
```

### View Logs
```bash
# Server logs
journalctl -u radar-server -f

# Kiosk logs
journalctl -u radar-kiosk -f

# Display logs
journalctl -u radar-display -f

# All radar services
journalctl -u radar-* -f

# Yesterday's logs
journalctl --since yesterday -u radar-server
```

### Start/Stop/Restart Services
```bash
# Restart server
sudo systemctl restart radar-server

# Restart kiosk
sudo systemctl restart radar-kiosk

# Stop all services
sudo systemctl stop radar-server radar-display radar-kiosk

# Start all services
sudo systemctl start radar-server radar-display radar-kiosk

# Disable auto-start
sudo systemctl disable radar-server radar-display radar-kiosk

# Enable auto-start
sudo systemctl enable radar-server radar-display radar-kiosk
```

## UART Troubleshooting

### Check UART Status
```bash
# List available serial ports
ls -la /dev/tty*

# Check if UART0 is available
ls -la /dev/ttyAMA0

# Check UART settings
sudo stty -a -F /dev/ttyAMA0
```

### Test UART Connection
```bash
# Install minicom for serial testing
sudo apt-get install -y minicom

# Test connection (Ctrl+X to exit)
sudo minicom -D /dev/ttyAMA0 -b 115200

# Or use screen
screen /dev/ttyAMA0 115200
# Exit with Ctrl+A, then Ctrl+D
```

### UART Not Working
1. Verify connections with multimeter (3.3V)
2. Check `/boot/config.txt` has `enable_uart=1`
3. Verify `console_uart` is disabled in cmdline.txt
4. Reboot after changes: `sudo reboot`
5. Check device: `ls -la /dev/ttyAMA0`
6. Check permissions: Should be readable by user

## Kiosk Mode Customization

### Change Display URL
Edit `/home/pi/start-kiosk.sh`:
```bash
SERVER_URL="http://192.168.1.100:3000"  # Change this
```

### Modify Chromium Startup Options
Edit `/home/pi/start-kiosk.sh` and adjust these flags:
```bash
--kiosk                    # Fullscreen kiosk mode
--start-fullscreen         # Start maximized
--disable-translate        # Disable translation
--disable-sync             # Disable Chrome sync
```

### Auto-restart on Crash
Already configured in systemd services with:
```ini
Restart=on-failure
RestartSec=5
```

## Network Configuration

### Static IP (Optional)
For reliable kiosk access:
```bash
sudo nano /etc/dhcpcd.conf

# Add:
interface eth0
static ip_address=192.168.1.50/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1
```

### Hostname Configuration
```bash
sudo raspi-config
# Navigate to System Options > Hostname
# Or manually:
sudo nano /etc/hostname
```

## Performance Optimization

### Reduce Memory Usage
```bash
# GPU memory (already set in setup)
echo "gpu_mem=128" | sudo tee -a /boot/config.txt

# Disable unnecessary services
sudo systemctl disable bluetooth.service
sudo systemctl disable avahi-daemon.service
```

### Monitor System
```bash
# Install system monitor
sudo apt-get install -y htop

# Check resource usage
htop

# Check temperature
vcgencmd measure_temp
```

## Troubleshooting Common Issues

### Server Won't Start
```bash
# Check logs
journalctl -u radar-server -n 50

# Test manually
cd /home/pi/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/server
npm start
```

### Kiosk Won't Display
```bash
# Check logs
journalctl -u radar-kiosk -f

# Ensure DISPLAY variable is set
echo $DISPLAY

# Start manually
DISPLAY=:0 /home/pi/start-kiosk.sh
```

### UART Communication Issues
```bash
# Check if Pico is responding
curl http://localhost:3000/api/stepper/status

# View error logs
journalctl -u radar-server | grep -i uart
journalctl -u radar-server | grep -i pico
```

### Network Connectivity
```bash
# Check internet
ping 8.8.8.8

# Check server access
curl http://localhost:3000/api/status

# Check from another device
curl http://<pi-ip>:3000/api/status
```

## Features Enabled

After setup, all these features are enabled and active:

- ✅ **Stepper Motor Control** - Full UART-based control
- ✅ **Actuator/Servo Control** - Extended/retract via Pico
- ✅ **Radar Sensor Data** - Continuous distance/detection data
- ✅ **Web Dashboard** - Full Vue.js UI
- ✅ **Real-time Updates** - WebSocket connections
- ✅ **Kiosk Display** - Auto-start fullscreen browser
- ✅ **Auto-Recovery** - Services auto-restart on failure
- ✅ **UART Communication** - Pico Master communication enabled

## Production Checklist

Before deploying to production:

- [ ] Test all UART connections thoroughly
- [ ] Verify server starts automatically after reboot
- [ ] Test kiosk display auto-recovery
- [ ] Configure static IP if needed
- [ ] Set up system monitoring/logging
- [ ] Test with actual Pico hardware
- [ ] Configure network security (firewall rules)
- [ ] Document any custom modifications
- [ ] Create backup of working configuration
- [ ] Test power cycle behavior

## Maintenance

### Weekly
- Check service health: `systemctl status radar-*.service`
- Monitor disk usage: `df -h`

### Monthly
- Update packages: `sudo apt-get update && sudo apt-get upgrade -y`
- Review logs: `journalctl --since "1 month ago" -u radar-server`

### Quarterly
- Full system backup
- Update Node.js if needed
- Review and optimize performance

## Support & Logs

All system logs are stored in journal:
```bash
# Last 100 lines of all radar services
journalctl -u radar-server -u radar-kiosk -u radar-display -n 100

# Real-time monitoring
journalctl -u radar-* -f

# Specific date range
journalctl -u radar-server --since "2026-04-01" --until "2026-04-08"
```

Error logs available at:
- `/var/log/` - System logs
- `journalctl` (systemd journal) - Service logs
- `/home/pi/radar-kiosk.log` - Kiosk browser startup log
- `/home/pi/radar-project/RaspberryPiRadarFullStackApplicationAndStepperController/server/logs/` - Application logs

## Advanced Configuration

### Remote SSH Access
```bash
# Enable SSH (if not already)
sudo raspi-config
# System Options > SSH > Enable

# Generate SSH keys
ssh-keygen -t ed25519

# Connect from remote
ssh pi@<pi-ip>
```

### VNC Remote Display
```bash
# Enable VNC
sudo raspi-config
# Display Options > VNC > Enable

# Connect from remote PC with VNC viewer
```

### Scheduled Reboot
```bash
# Edit crontab
sudo crontab -e

# Add (reboot daily at 3 AM):
0 3 * * * /sbin/shutdown -r now
```

## Next Steps

1. ✅ Run the setup script
2. ✅ Reboot the Raspberry Pi
3. ✅ Connect Pico Master via UART
4. ✅ Access web interface at http://<pi-ip>:3000
5. ✅ Test stepper/actuator/radar controls
6. ✅ Monitor logs for any issues

## Support

For issues or questions:
1. Check logs: `journalctl -u radar-* -f`
2. Verify UART connections
3. Test services individually
4. Review this guide thoroughly
5. Check GitHub issues/documentation
