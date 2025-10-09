# Quick Reference Cheat Sheet

## 🚀 Daily Commands (Run on Pi)

```bash
# ONE TIME SETUP (after copying folder to Pi)
./setup-printstack.sh

# START 3D PRINTING
./start-klipper-stack.sh

# START TRANSCODING  
./start-tdarr-node.sh

# STOP EVERYTHING
./stop-all-services.sh

# CHECK STATUS
./check-status.sh
```

## 🌐 Web Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Mainsail | `http://pi-ip` | 3D printer control |
| Camera | `http://pi-ip:8080` | Webcam stream |
| Moonraker | `http://pi-ip:7125` | API endpoint |
| Tdarr Server | `http://192.168.1.210:8265` | Your main Tdarr server |

## 📁 Network Shares (Windows/Mac)

```
\\pi-ip\Printer-Config    (edit printer.cfg)
\\pi-ip\Printer-GCodes    (upload G-code files)
\\pi-ip\Printer-Timelapse (download videos)
```

## 🔧 Essential File Locations (On Pi)

```bash
# Main config file (EDIT THIS FOR YOUR PRINTER):
/srv/printstack/config/klipper/printer.cfg

# Find printer serial port:
ls /dev/serial/by-id/

# View logs:
docker logs klipper -f
docker logs moonraker -f
docker logs tdarr-node -f
```

## ❗ Quick Fixes

**Printer won't connect?**
1. `ls /dev/serial/by-id/` (find serial port)
2. Edit `/srv/printstack/config/klipper/printer.cfg`
3. Update `[mcu] serial:` line
4. `docker restart klipper`

**Tdarr node missing?**  
1. `./check-status.sh` (test server connection)
2. Check node appears at `http://192.168.1.210:8265`

**Services won't start?**
1. `./stop-all-services.sh`
2. `docker system prune -f`
3. Try starting again

## 📦 What This Setup Does

**🖨️ Printing Mode:**
- Klipper (3D printer firmware)
- Mainsail (web interface)  
- Camera streaming
- SMB file shares
- Automatic timelapse

**🎦 Transcoding Mode:**
- Tdarr node connects to your main server
- Access to /share directory
- GPU acceleration (if available)
- Automatic version matching with server
- Automatic server discovery

**🔄 Smart Switching:**
- Only one mode active at a time
- Prevents resource conflicts
- Safe startup/shutdown