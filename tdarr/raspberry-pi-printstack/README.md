# Raspberry Pi Klipper + Tdarr Docker Stack

A complete Docker-based setup for your Raspberry Pi that can switch between:
- **🖨️ 3D Printing Mode**: Klipper, Moonraker, Mainsail, Camera, Samba shares
- **🎬 Transcoding Mode**: Tdarr node that connects to your existing Tdarr server

## 📁 What's In This Folder

### Core Scripts:
- **`setup-printstack.sh`** - Complete installation script (run once)
- **`start-klipper-stack.sh`** - Start 3D printing services
- **`start-tdarr-node.sh`** - Start transcoding node (connects to your Tdarr server)
- **`stop-all-services.sh`** - Stop everything safely
- **`check-status.sh`** - Comprehensive status check

### Configuration Files:
These will be created on the Pi at `/srv/printstack/` after running setup:
- Klipper configuration templates
- Moonraker API configuration  
- Tdarr node configuration (matches your betterstrap setup)
- Docker Compose files for both stacks

## 🚀 Quick Start Guide

### 1. Copy to Your Raspberry Pi
```bash
# From your current machine:
scp -r raspberry-pi-printstack/ pi@your-pi-ip:~/
```

### 2. Run Initial Setup (One Time Only)
```bash
# SSH to your Pi:
ssh pi@your-pi-ip

# Go to the folder:
cd raspberry-pi-printstack/

# Run the complete setup:
./setup-printstack.sh
```

### 3. Daily Usage
```bash
# For 3D printing:
./start-klipper-stack.sh

# For transcoding (when not printing):
./start-tdarr-node.sh

# Stop everything:
./stop-all-services.sh

# Check what's running:
./check-status.sh
```

## 🌐 Access Points After Setup

### When Running Klipper Stack:
- **Mainsail**: http://your-pi-ip (main printer interface)
- **Camera**: http://your-pi-ip:8080 (webcam stream)
- **Moonraker API**: http://your-pi-ip:7125

### Network Shares (Always Available):
- **Config**: `\\your-pi-ip\Printer-Config` (edit printer.cfg remotely)
- **G-codes**: `\\your-pi-ip\Printer-GCodes` (upload files)  
- **Timelapse**: `\\your-pi-ip\Printer-Timelapse` (download videos)

### When Running Tdarr Node:
- **Your Main Tdarr Server**: http://192.168.1.210:8265 (check node connection)
- Node will appear as: `your-hostname-node` in the Nodes tab

## 📋 What Gets Installed

### System Packages:
- Docker & Docker Compose
- Samba (for file sharing)
- System utilities (curl, git, etc.)

### Docker Containers:
- **mkuf/klipper:latest** - 3D printer firmware
- **mkuf/moonraker:latest** - API server for Klipper
- **ghcr.io/mainsail-crew/mainsail:latest** - Web interface
- **mkuf/ustreamer:latest** - Camera streaming
- **dperson/samba:latest** - Network file shares
- **haveagitgat/tdarr_node:latest** - Media transcoding node (auto-matches server version)

### Directory Structure (Created at `/srv/printstack/`):
```
/srv/printstack/
├── config/
│   ├── klipper/          # printer.cfg and configs
│   ├── moonraker/        # API configuration
│   └── tdarr/           # Tdarr node config
├── data/
│   ├── gcodes/          # G-code files (SMB accessible)
│   ├── timelapse/       # Timelapse videos (SMB accessible)  
│   └── tdarr/           # Tdarr working files
├── scripts/             # Management scripts
├── logs/               # Service logs
├── klipper-compose.yml  # Klipper stack definition
└── tdarr-compose.yml    # Tdarr node definition
```

## ⚙️ Configuration Required

### Before First Print:
1. Edit `/srv/printstack/config/klipper/printer.cfg`
2. Find your printer's serial port: `ls /dev/serial/by-id/`
3. Update the `[mcu]` section with your serial port
4. Customize stepper motors, heaters, etc. for your printer

### Tdarr Connection:
- Default server: `192.168.1.210:8266` (matches your betterstrap setup)
- Node name: `your-hostname-node`
- Media access: `/share` → `/media` (in container)
- Temp files: `/share/trans` → `/tmp` (in container)

## 🔧 Key Features

### Smart Resource Management:
- Only one stack runs at a time (prevents conflicts)
- Automatic switching between printing/transcoding modes
- Resource limits prevent Pi overload

### Hardware Support:
- **Camera**: USB cameras at /dev/video0 (automatic detection)
- **GPU**: Intel + NVIDIA acceleration for Tdarr (if available)
- **Serial**: USB and GPIO serial connections for printers

### Network Integration:
- **Guest SMB shares** (no password required)
- **Automatic hostname detection**
- **Port conflict avoidance**

### Reliability Features:
- **Health checks** for all services
- **Automatic restarts** on failure
- **Comprehensive logging**
- **Safe shutdown** procedures

## 🛠️ Troubleshooting

### Common Issues:

**"Docker not found"**
```bash
sudo systemctl start docker
sudo usermod -aG docker pi
# Then log out and back in
```

**"Camera not working"**
```bash
# Check camera device:
ls /dev/video*
# Update klipper-compose.yml if using different device
```

**"Printer not connecting"**
```bash
# Find serial port:
ls /dev/serial/by-id/
# Edit /srv/printstack/config/klipper/printer.cfg
```

**"Tdarr node not appearing"**
```bash
# Check server connection:
./check-status.sh
# Verify server IP in start-tdarr-node.sh (line 31)
```

### View Logs:
```bash
docker logs klipper -f
docker logs moonraker -f  
docker logs tdarr-node -f
```

### Reset Everything:
```bash
./stop-all-services.sh
docker system prune -f
./setup-printstack.sh  # Run setup again
```

## 🔄 Updates

### Update Docker Images:
```bash
cd /srv/printstack
docker compose -f klipper-compose.yml pull
docker compose -f tdarr-compose.yml pull
# Then restart the appropriate stack
```

### Update Scripts:
```bash
# Re-download this folder and copy to Pi
```

## 📝 Notes

- **Based on your betterstrap/tdarr setup**: Same configuration, server IP, path mappings
- **Requires /share directory**: Must be mounted for Tdarr node to work
- **Camera optional**: Printing works without camera, just no timelapse
- **Single-mode operation**: Run either printing OR transcoding, not both simultaneously
- **Guest network access**: SMB shares accessible without authentication (secure your network!)

## 🆘 Getting Help

1. **Check status first**: `./check-status.sh`
2. **View logs**: `docker logs <container-name> -f`
3. **Test connections**: Scripts include connection testing
4. **Restart services**: Stop and start the appropriate stack
5. **Full reset**: Run setup script again if needed

---

**Generated**: $(date)  
**Compatible with**: Raspberry Pi 4/5, Raspberry Pi OS  
**Requires**: Docker, /share directory mounted, internet connection