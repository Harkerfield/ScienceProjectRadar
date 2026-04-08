# Pre-Deployment Checklist

Use this checklist to verify everything is ready before deploying to Raspberry Pi.

## Prerequisites Check

### On Your Computer (Windows/Linux/Mac)

#### Required Tools
- [ ] OpenSSH client installed
  - **Windows:** Built-in on Win10+; run `ssh -V` to verify
  - **Linux/Mac:** Usually pre-installed; run `ssh -V`
  - **Alternative:** Install [Git Bash](https://git-scm.com/download/win) (Windows)

- [ ] Deployment script available
  - [ ] `deploy-to-pi.ps1` (Windows)
  - [ ] `deploy-to-pi.sh` (Linux/Mac)
  - [ ] Scripts are executable: `ls -l deploy-to-pi.*`

#### Recommended Tools
- [ ] Git installed (if using Git clone method)
  - Run: `git --version`
  
- [ ] Text editor or IDE
  - For reviewing logs and config files
  - VS Code, nano, vim, etc.

### On Raspberry Pi

#### Hardware
- [ ] Raspberry Pi powered on and connected to network
- [ ] Ethernet cable OR WiFi connected
- [ ] Power supply: USB-C 5V, 2.5A minimum

#### Software
- [ ] Raspberry Pi OS installed
  - Check: `cat /etc/os-release` (if already SSH'd in)
  - Supported: Desktop, Lite, or Server editions
  - Minimum: Any recent version (2020+)

- [ ] SSH enabled (usually default)
  - Check: `sudo raspi-config` → Interface Options → SSH
  - Should show "SSH enabled"

- [ ] Internet access on Pi
  - Check: `ping 8.8.8.8` (or after deployment)

#### Pico Boards
- [ ] Pico boards connected via GPIO 14/15 (UART)
- [ ] Pico firmware loaded with UART slave code
- [ ] Devices: Radar (0x20), Stepper (0x10), Servo (0x11)

### Network

- [ ] Stable network connection
  - WiFi or Ethernet, consistent for 20-30 minutes

- [ ] Can reach Pi from your computer
  - Run: `ping raspberrypi.local`
  - If fails, try: `ping 192.168.1.X` (find Pi's IP)

- [ ] Port 22 (SSH) accessible
  - Run: `ssh pi@raspberrypi.local`
  - Should prompt for password (first time)

- [ ] Sufficient bandwidth
  - Node.js download: ~50-100 MB
  - npm packages: ~200-300 MB
  - Total: Plan for ~500 MB download

## Directory & File Check

On your development machine:

```
RadarProject/
├─ deploy-to-pi.ps1          [ ] EXISTS
├─ deploy-to-pi.sh           [ ] EXISTS
├─ DEPLOYMENT.md             [ ] EXISTS
├─ QUICKSTART-DEPLOY.md      [ ] EXISTS
├─ DEPLOYMENT-FILES.md       [ ] EXISTS
├─ README.md                 [ ] EXISTS
├─ RaspberryPiPicoRadarAndServerController/
│  ├─ main.py               [ ] EXISTS
│  ├─ config/               [ ] EXISTS
│  └─ src/                  [ ] EXISTS
│
└─ RaspberryPiRadarFullStackApplicationAndStepperController/
   ├─ server/               [ ] EXISTS
   │  └─ package.json       [ ] EXISTS
   │
   └─ client/               [ ] EXISTS
      └─ package.json       [ ] EXISTS
```

## Configuration Decisions

Before running the script, decide:

### 1. Deployment Method
- [ ] I prefer **Git clone** (recommended)
  - Pro: Keeps update history
  - Con: Needs Pi internet access
  - Need GitHub repo URL

- [ ] I prefer **SCP/rsync** (local copy)
  - Pro: Works offline
  - Con: No update history
  - Need all files on your computer

### 2. Raspberry Pi Details
- [ ] Pi hostname: `___________________`
  - Default: `raspberrypi.local`
  - Or IP: `192.168.___._____`

- [ ] Pi username: `___________________`
  - Default: `pi`
  - Or: `ubuntu`, `root` (if different)

- [ ] Pi password known: `[ ] YES [ ] NO`
  - You'll need it for first deployment

### 3. Installation Location
- [ ] Installation directory on Pi: `___________________`
  - Default: `/home/pi/RadarProject`
  - Common alt: `/opt/radar`

### 4. Network Configuration
- [ ] How will I access the app?
  - [ ] `http://raspberrypi.local:3000`
  - [ ] `http://192.168.1.X:3000`
  - [ ] Both

## Pre-Deployment Steps

### 1. Test SSH Connection (Important!)
```bash
# Windows PowerShell
ssh pi@raspberrypi.local

# Linux/Mac
ssh pi@raspberrypi.local

# If this works, you're good to go
# If it fails, troubleshoot now before running deploy scripts
```

**If SSH fails:**
- [ ] Check Pi hostname: `ping raspberrypi.local`
- [ ] Try IP address: `ssh pi@192.168.1.100`
- [ ] Check SSH enabled: `sudo raspi-config`
- [ ] Test from different network?
- [ ] Are you on the right network?

### 2. Free Up Space on Pi
```bash
ssh pi@raspberrypi.local
df -h
# Should show > 500MB available
```

**If disk low:**
- [ ] Remove unnecessary packages
- [ ] Clear apt cache: `sudo apt-get clean`
- [ ] Expand filesystem: `sudo raspi-config`

### 3. Update Pi OS (Optional but Recommended)
```bash
ssh pi@raspberrypi.local
sudo apt-get update
sudo apt-get upgrade -y
# This takes 5-10 minutes
```

- [ ] Done (or skip if time-sensitive)

### 4. Backup Current Configuration (If Updating)
```bash
# If replacing old installation:
ssh pi@raspberrypi.local
sudo cp -r /home/pi/RadarProject /home/pi/RadarProject.bak
```

- [ ] Not needed (fresh install)
- [ ] Done (backing up old version)

### 5. Choose Git Repository URL (If Using Git Method)

If deploying via Git:
- [ ] Repository URL: `https://github.com/___/___`
- [ ] Repository is public OR you have deploy key
- [ ] Main branch is `main` (or specify during script)

## Environmental Notes

### Special Circumstances

- [ ] **Firewall:** Corporate network blocks port 22
  - Workaround: Use VPN or direct connection

- [ ] **Multiple Users:** Shared Pi
  - Plan: Run as separate user with own project dir

- [ ] **Limited Bandwidth:** Slow internet
  - Plan: Use SCP method to copy files (faster locally)
  - Or: Pre-stage files on USB drive

- [ ] **Air-Gapped:** No external internet
  - Plan: Use SCP method, offline installation only

## Go/No-Go Decision

Before running the deployment script:

**Go (All green, proceed):**
- [ ] ✅ SSH connection works (`ssh pi@host` succeeds)
- [ ] ✅ Network connected and stable
- [ ] ✅ Disk space available on Pi (> 500MB)
- [ ] ✅ Project files on this computer
- [ ] ✅ Deployment method chosen (Git or SCP)
- [ ] ✅ Pi details confirmed (hostname, username)
- [ ] ✅ Time available (20-30 minutes uninterrupted)

**No-Go (Issues to resolve first):**
- [ ] ❌ SSH connection fails - FIX: troubleshoot connectivity
- [ ] ❌ Project files missing - FIX: clone or copy repo
- [ ] ❌ No Pi access - FIX: set up Pi first
- [ ] ❌ Low disk space - FIX: free up space on Pi
- [ ] ❌ No network - FIX: connect Pi to network

## Running Deployment

### Windows (PowerShell)
```powershell
cd F:\RadarProject
.\deploy-to-pi.ps1 -PiHost raspberrypi.local -PiUser pi
```

### Linux/Mac (Bash)
```bash
cd ~/RadarProject
chmod +x deploy-to-pi.sh
./deploy-to-pi.sh -h raspberrypi.local -u pi
```

### During Script
- [ ] Watch progress output
- [ ] Note any error messages
- [ ] When asked: Choose deployment method (1 or 2)
- [ ] When prompted: Provide Git URL or confirm SCP
- [ ] Script will show setup progress (6 steps)

## Post-Deployment Steps

After script completes:

### 1. Check Service Status
```bash
ssh pi@raspberrypi.local
sudo systemctl status radar-app
```
- [ ] Shows "active (running)"
- [ ] Shows "enabled"

### 2. If UART Was Enabled, Reboot Pi
```bash
ssh pi@raspberrypi.local
sudo reboot
```
- [ ] Pi reboots (wait 30 seconds)
- [ ] Can't connect during reboot (normal)
- [ ] Reconnect after: `ssh pi@raspberrypi.local`

### 3. Access Application
```
http://raspberrypi.local:3000
```
- [ ] Page loads
- [ ] Dashboard visible
- [ ] No connection errors

### 4. Check Application Logs
```bash
ssh pi@raspberrypi.local
sudo journalctl -u radar-app -n 20
```
- [ ] No critical errors
- [ ] Shows startup messages
- [ ] Shows server listening on port 3000

## Troubleshooting If Issues Occur

| Problem | Immediate Action | Document |
|---------|-----------------|----------|
| Script fails to connect | Check SSH works first | DEPLOYMENT.md |
| Git clone hangs | Choose SCP method | DEPLOYMENT.md |
| npm install fails | Check internet, retry | DEPLOYMENT.md |
| Service won't start | Check logs: `journalctl -u radar-app -n 50` | DEPLOYMENT.md |
| Can't access web app | Verify Pi IP, check firewall | HOSTNAME_ACCESS.md |
| UART not working | Reboot Pi | DEPLOYMENT.md |

## Getting Help

1. **Check Logs:** `sudo journalctl -u radar-app -f`
2. **Read Docs:** [DEPLOYMENT.md](./DEPLOYMENT.md)
3. **Manual Test:** SSH to Pi, run setup commands manually
4. **Review Script:** Open `.ps1` or `.sh` file to see what it does

---

**Checklist Status:** `[ ] Not Started  [ ] In Progress  [ ] Ready to Deploy`

**Date:** __________ 

**Notes:** _______________________________________________________________________

________________________________________________________________

________________________________________________________________
