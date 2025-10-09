# Installation Checklist

## 📋 Pre-Installation Requirements

### Hardware:
- [ ] Raspberry Pi 4 (4GB+) or Pi 5
- [ ] SD card with Raspberry Pi OS installed
- [ ] Network connection (WiFi or Ethernet)
- [ ] USB camera (optional, for timelapse)
- [ ] 3D printer with USB connection

### Network Setup:
- [ ] Pi has static IP or DHCP reservation (recommended)  
- [ ] `/share` directory mounted and accessible
- [ ] Your main Tdarr server running at `192.168.1.210:8266`
- [ ] SSH access to Pi enabled

### Files Ready:
- [ ] This `raspberry-pi-printstack/` folder copied to Pi
- [ ] All scripts executable (`chmod +x *.sh`)

## 🚀 Installation Steps

### Step 1: Copy Files
```bash
# From your main computer:
scp -r raspberry-pi-printstack/ pi@your-pi-ip:~/
```
- [ ] All files copied successfully
- [ ] Can SSH to Pi: `ssh pi@your-pi-ip`

### Step 2: Run Setup
```bash
# On the Pi:
cd raspberry-pi-printstack/
./setup-printstack.sh
```
- [ ] Docker installed successfully
- [ ] All directories created at `/srv/printstack/`
- [ ] All Docker images pulled
- [ ] Configuration files created
- [ ] Samba shares configured
- [ ] Systemd services created (optional)

### Step 3: Configure Printer
```bash
# Find your printer's serial port:
ls /dev/serial/by-id/

# Edit printer configuration:
nano /srv/printstack/config/klipper/printer.cfg
```
- [ ] Serial port identified and configured
- [ ] Printer specifications added (stepper motors, heaters, etc.)
- [ ] MCU configuration updated
- [ ] File saved with your printer's settings

### Step 4: Test Printing Stack
```bash
./start-klipper-stack.sh
```
- [ ] All containers start successfully
- [ ] Mainsail accessible at `http://pi-ip`
- [ ] Camera stream working at `http://pi-ip:8080` (if camera connected)
- [ ] Printer connects without errors
- [ ] SMB shares accessible from Windows/Mac
- [ ] Can upload G-code files via network share

### Step 5: Test Tdarr Node
```bash
./start-tdarr-node.sh
```
- [ ] Tdarr node container starts
- [ ] `/share` directory accessible
- [ ] `/share/trans` created automatically
- [ ] Node connects to server at `192.168.1.210:8266`
- [ ] Node appears in main Tdarr server interface
- [ ] GPU acceleration detected (if available)

### Step 6: Test Mode Switching
```bash
# Switch between modes:
./start-tdarr-node.sh      # Should stop Klipper first
./start-klipper-stack.sh   # Should stop Tdarr first
./stop-all-services.sh     # Should stop everything
```
- [ ] Only one stack runs at a time
- [ ] Switching works without conflicts
- [ ] Services stop/start cleanly

## ✅ Post-Installation Verification

### Network Shares (Test from Windows/Mac):
- [ ] `\\pi-ip\Printer-Config` - Can browse and edit files
- [ ] `\\pi-ip\Printer-GCodes` - Can upload .gcode files
- [ ] `\\pi-ip\Printer-Timelapse` - Can download videos

### Web Interfaces:
- [ ] Mainsail: `http://pi-ip` loads correctly
- [ ] Camera: `http://pi-ip:8080` shows video stream
- [ ] Moonraker API: `http://pi-ip:7125` returns JSON

### Tdarr Integration:
- [ ] Node shows as online in main Tdarr server
- [ ] Node name: `your-hostname-node`
- [ ] Can assign transcode jobs to Pi node
- [ ] Files accessible through `/share` path mapping

### Status Monitoring:
```bash
./check-status.sh
```
- [ ] Shows correct service status
- [ ] System resources displayed
- [ ] Network connectivity confirmed
- [ ] GPU status reported correctly

## 🔄 Optional Auto-Start Setup

### Enable Services to Start on Boot:
```bash
# For automatic Klipper startup:
sudo systemctl enable printstack-klipper

# For automatic Tdarr startup:
sudo systemctl enable printstack-tdarr
```
- [ ] Choose appropriate auto-start service
- [ ] Test reboot behavior
- [ ] Services start automatically after reboot

## 🛠️ Troubleshooting Common Issues

### If Setup Fails:
- [ ] Check internet connection
- [ ] Verify Docker is running: `docker info`
- [ ] Check disk space: `df -h`
- [ ] Review setup script output for errors

### If Printer Won't Connect:
- [ ] Verify USB cable connection
- [ ] Check serial port: `ls /dev/serial/by-id/`
- [ ] Test serial permissions: `groups` (should include dialout)
- [ ] Review Klipper logs: `docker logs klipper -f`

### If Tdarr Node Missing:
- [ ] Verify main server is running
- [ ] Test network connection: `ping 192.168.1.210`
- [ ] Check port accessibility: `telnet 192.168.1.210 8266`
- [ ] Review node logs: `docker logs tdarr-node -f`

### If SMB Shares Don't Work:
- [ ] Check Samba container: `docker logs printer-samba`
- [ ] Verify network firewall settings
- [ ] Test from Pi: `smbclient -L localhost -U%`

## ✅ Installation Complete!

When all items above are checked:
- [ ] Installation is complete and verified
- [ ] Both printing and transcoding modes work
- [ ] Network shares accessible
- [ ] System ready for daily use

---

**Next Steps:**
1. Bookmark this folder for future reference
2. Start your first print with `./start-klipper-stack.sh`
3. Test transcoding with `./start-tdarr-node.sh`
4. Use `./check-status.sh` whenever you need to see what's running