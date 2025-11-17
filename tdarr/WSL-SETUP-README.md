# WSL Tdarr Node Setup with SSH Access

Complete automation for running Tdarr Node on Windows WSL with remote SSH access, systemd auto-start, and autofs SMB/NFS mounting.

## What This Does

✅ Enables SSH access to your Windows machine  
✅ Enables systemd in WSL for proper service management  
✅ Auto-starts Docker, autofs, and Tdarr Node on WSL boot  
✅ Mounts `/share` via autofs (CIFS or NFS)  
✅ Tdarr Node has full access to `/share` directory  
✅ Provides helper scripts for status checking and manual startup  

## Prerequisites

- **Windows:** Windows 10/11 with WSL 2
- **WSL Distro:** Arch Linux
- **Access:** Admin rights on Windows, sudo rights in WSL
- **Network:** Access to your NAS/file server for `/share` mount

## Quick Start

### Step 1: Windows - Enable SSH Server

1. **Copy** `setup-windows-ssh.ps1` to Windows (or access via `\\wsl$\Arch\home\me\betterstrap\tdarr\`)

2. **Run PowerShell as Administrator:**
   ```powershell
   # Allow script execution for this session
   Set-ExecutionPolicy Bypass -Scope Process -Force
   
   # Navigate to script location and run
   cd C:\path\to\script
   .\setup-windows-ssh.ps1
   ```

3. **Note the Windows IP address** displayed by the script

### Step 2: SSH into Windows from Another Machine

```bash
ssh YOUR_WINDOWS_USERNAME@WINDOWS_IP
```

### Step 3: Enter WSL and Run Setup

From the Windows SSH session:

```bash
# Enter WSL
wsl

# Navigate to setup directory
cd /home/me/betterstrap/tdarr

# Run WSL setup (requires sudo)
sudo bash ./setup-wsl-systemd.sh
```

**Important:** The script will create `/home/me/betterstrap/tdarr/autofs/shares.env` and pause for you to edit it with your NAS details. Make sure to configure:
- `SHARE_SERVER` (your NAS IP)
- `SHARE_NAME` (the SMB share name)
- `CIFS_USERNAME` and `CIFS_PASSWORD` (if using CIFS)
- Or `NFS_EXPORT` (if using NFS)

### Step 4: Restart WSL

**Critical:** WSL must be restarted for systemd to activate.

From Windows PowerShell (exit WSL first):

```powershell
# Shutdown WSL
wsl.exe --shutdown

# Start WSL again
wsl
```

### Step 5: Verify Everything Works

```bash
cd /home/me/betterstrap/tdarr

# Check status
./check-wsl-status.sh

# If anything isn't running, manually start:
./start-tdarr-wsl.sh
```

## Files Created

### Scripts (in `/home/me/betterstrap/tdarr/`)
- `setup-windows-ssh.ps1` - Windows OpenSSH server setup
- `setup-wsl-systemd.sh` - WSL systemd and Tdarr configuration
- `start-tdarr-wsl.sh` - Manual startup/recovery script
- `check-wsl-status.sh` - Quick status checker (created by setup)

### Configuration Files
- `/home/me/betterstrap/tdarr/autofs/shares.env` - Autofs mount configuration
- `/home/me/betterstrap/tdarr/tdarr.env` - Tdarr Node settings
- `/etc/wsl.conf` - WSL systemd configuration
- `/etc/auto.shares` - Autofs mount map
- `/etc/systemd/system/tdarr-node.service` - Tdarr Node systemd service

## What Starts on Boot

After setup and WSL restart:

1. **systemd** activates (PID 1)
2. **docker.service** starts automatically
3. **autofs.service** starts automatically (mounts `/share` on access)
4. **tdarr-node.service** starts automatically (starts the Tdarr Node container)

Your Tdarr Node will be running and connected to your server **every time you boot Windows!**

## Configuration

### Autofs Configuration

Edit `/home/me/betterstrap/tdarr/autofs/shares.env`:

```bash
# For CIFS/SMB
MOUNT_TYPE=cifs
SHARE_SERVER=192.168.1.210
SHARE_NAME=share
CIFS_USERNAME=me
CIFS_PASSWORD=your_password
MOUNTPOINT=/share

# For NFS
MOUNT_TYPE=nfs
NFS_EXPORT=192.168.1.210:/mnt/pool/share
MOUNTPOINT=/share
```

After editing, re-run `sudo bash ./setup-wsl-systemd.sh` to apply changes.

### Tdarr Configuration

Edit `/home/me/betterstrap/tdarr/tdarr.env`:

```bash
PUID=1000
PGID=1000
TZ=America/New_York

# Tdarr Server connection
TDARR_SERVER_IP=192.168.1.210
TDARR_SERVER_PORT=8266

# Node name (appears in Tdarr web interface)
TDARR_NODE_NAME=my-wsl-node

# Tdarr image
TDARR_IMAGE=ghcr.io/haveagitgat/tdarr_node:latest
```

After editing, restart the Tdarr container:
```bash
docker restart tdarr-node
```

## Management Commands

### Check Status
```bash
~/betterstrap/tdarr/check-wsl-status.sh
```

### Start/Restart Tdarr
```bash
~/betterstrap/tdarr/start-tdarr-wsl.sh
```

### Docker Commands
```bash
# View logs
docker logs tdarr-node -f

# Stop container
docker stop tdarr-node

# Start container
docker start tdarr-node

# Restart container
docker restart tdarr-node

# Remove container (to recreate)
docker stop tdarr-node && docker rm tdarr-node
```

### Service Management (systemd)
```bash
# Check service status
systemctl status docker autofs tdarr-node

# Restart services
sudo systemctl restart docker
sudo systemctl restart autofs
sudo systemctl restart tdarr-node

# View service logs
journalctl -u docker -f
journalctl -u autofs -f
journalctl -u tdarr-node -f
```

## Troubleshooting

### Systemd Not Active

**Problem:** `check-wsl-status.sh` says systemd is not active

**Solution:**
```powershell
# From Windows PowerShell
wsl.exe --shutdown
wsl
```

### /share Not Accessible

**Problem:** `/share` mount fails or is empty

**Solutions:**
1. Check network connectivity to NAS: `ping 192.168.1.210`
2. Verify autofs configuration: `cat /home/me/betterstrap/tdarr/autofs/shares.env`
3. Check autofs logs: `journalctl -u autofs -n 50`
4. Test CIFS mount manually:
   ```bash
   sudo mount -t cifs -o username=me,password=pass //192.168.1.210/share /mnt/test
   ```
5. Restart autofs: `sudo systemctl restart autofs`

### Docker Permission Denied

**Problem:** Docker commands require sudo

**Solution:**
```bash
# Verify you're in docker group
groups

# If not, the setup script should have added you
# Log out and back in to apply group membership
exit  # exit WSL
wsl   # re-enter WSL
```

### Tdarr Node Not Starting

**Problem:** Container fails to start

**Solutions:**
1. Check logs: `docker logs tdarr-node`
2. Verify /share is accessible: `ls /share`
3. Check Tdarr server connectivity:
   ```bash
   curl -v http://192.168.1.210:8266
   ```
4. Recreate container:
   ```bash
   docker stop tdarr-node
   docker rm tdarr-node
   ~/betterstrap/tdarr/start-tdarr-wsl.sh
   ```

### SSH Connection Refused (Windows)

**Problem:** Cannot SSH to Windows machine

**Solutions:**
1. Verify sshd is running on Windows:
   ```powershell
   Get-Service sshd
   ```
2. Check firewall rule:
   ```powershell
   Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP"
   ```
3. Test from Windows itself:
   ```powershell
   ssh localhost
   ```
4. Re-run setup script: `.\setup-windows-ssh.ps1`

## Advanced: Direct SSH to WSL

If you want to SSH directly into WSL (not just Windows then `wsl`):

1. Uncomment the WSL SSH section in `setup-windows-ssh.ps1`
2. Re-run the PowerShell script as Administrator
3. This creates a port forward: Windows port 2222 → WSL port 22

Connect with:
```bash
ssh USERNAME@WINDOWS_IP -p 2222
```

**Note:** WSL IP changes on restart, so the port proxy may need updating after WSL restarts.

## Comparison with install_node.sh

| Feature | install_node.sh | WSL Setup Scripts |
|---------|----------------|-------------------|
| Works on native Linux | ✅ | ❌ |
| Works on WSL | ⚠️ Partially | ✅ Yes |
| Auto-start on boot | ✅ (systemd) | ✅ (systemd) |
| WSL systemd setup | ❌ Manual | ✅ Automated |
| SSH access | ❌ Not included | ✅ Included |
| Autofs configuration | ❌ Manual | ✅ Automated |
| Status checking | ❌ None | ✅ Helper scripts |

**For WSL:** Use the new scripts  
**For native Arch Linux:** Use `install_node.sh`

## How Auto-Start Works

1. **WSL Boot:** Windows starts WSL with systemd as PID 1 (configured in `/etc/wsl.conf`)
2. **systemd Starts Services:**
   - `docker.service` → Docker daemon starts
   - `autofs.service` → autofs starts (ready to mount `/share`)
   - `tdarr-node.service` → Checks if `/share` accessible, then starts Tdarr container
3. **Container Runs:** Docker starts the `tdarr-node` container with `--restart unless-stopped`
4. **Connection:** Tdarr Node connects to your Tdarr server at `192.168.1.210:8266`

**No manual intervention required after initial setup!**

## Credits

These scripts are part of the betterstrap project for automated Tdarr Node deployment.

- Windows SSH: OpenSSH Server for Windows
- WSL: Windows Subsystem for Linux
- Tdarr: https://tdarr.io
- Docker: Container runtime
- Autofs: Automount daemon
