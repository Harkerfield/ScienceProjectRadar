# Git Install - Quick Commands

## Installation (Choose One Method)

### Method 1: One-Liner (Fastest)
```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/RadarProject/main/install-from-git.sh | bash
```

### Method 2: Manual Download
```bash
ssh pi@raspberrypi.local
wget https://raw.githubusercontent.com/YOUR_USERNAME/RadarProject/main/install-from-git.sh
chmod +x install-from-git.sh
./install-from-git.sh
```

### Method 3: Custom Path
```bash
./install-from-git.sh https://github.com/yourname/RadarProject.git /opt/my-radar
```

---

## Auto-Update on Startup (5-Minute Setup)

```bash
# SSH to Pi and go to project directory
ssh pi@raspberrypi.local
cd /home/pi/RadarProject

# Create update script directory
sudo mkdir -p /opt/radar-update

# Copy update checker
sudo cp setup/radar-update-check.sh /opt/radar-update/
sudo chmod +x /opt/radar-update/check-updates.sh

# Install systemd service
sudo cp setup/systemd/radar-update-check.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable radar-update-check.service

# Test it works
sudo systemctl start radar-app
```

---

## After Installation

| Command | Purpose |
|---------|---------|
| `sudo systemctl status radar-app` | Check if running |
| `http://raspberrypi.local:3000` | Open web interface |
| `sudo journalctl -u radar-app -f` | View live logs |
| `tail -f /var/log/radar-app-updates.log` | View update logs |
| `sudo systemctl restart radar-app` | Restart application |

---

## Update Checks

✅ **Automatic:** Runs every system boot  
✅ **Manual:** `sudo systemctl start radar-update-check.service`  
📝 **Logs:** `/var/log/radar-app-updates.log`

---

## Replace URLs

Before running any command, replace:
- `YOUR_USERNAME` → Your actual GitHub username  
- `raspberrypi.local` → Your Pi's hostname/IP

---

## Troubleshooting

**Can't connect to Pi:**
```bash
ping raspberrypi.local
ssh pi@192.168.1.X  # Try IP directly
```

**Git clone fails:**
- Check internet on Pi: `ssh pi@host 'ping 8.8.8.8'`
- Verify GitHub URL is correct
- For private repos: set up SSH keys

**Updates not working:**
```bash
sudo systemctl status radar-update-check.service
tail -20 /var/log/radar-app-updates.log
```

**See full guide:** [GIT-INSTALL.md](./GIT-INSTALL.md)
