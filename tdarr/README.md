# Tdarr Node Automated Setup with Autofs

A comprehensive, cross-distribution setup script for Tdarr transcoding nodes with automatic SMB share mounting via autofs.

## Overview

This script provides a complete, automated installation of a Tdarr transcoding node that:

- Detects your Linux distribution and installs appropriate packages
- Configures autofs for automatic, on-demand SMB share mounting
- Installs and configures Docker or Podman
- Creates a Docker Compose configuration for easy management
- Installs lazydocker for TUI-based container management
- Handles special cases like SELinux, OSTree, and read-only filesystems

## Supported Distributions

- Arch Linux / Manjaro
- Debian / Ubuntu
- Fedora
- SteamOS
- Bazzite (OSTree)

## Prerequisites

- Network connectivity to SMB servers (192.168.1.210 and 192.168.1.47)
- Sudo/root access for package installation
- Internet connection for downloading packages

## Quick Start

```bash
# Run the setup script (interactive, will prompt to start)
./setup-tdarr.sh

# Start immediately after setup
./setup-tdarr.sh --start-now

# Setup without starting (for testing)
./setup-tdarr.sh --no-start
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--start-now` | Start Tdarr container immediately after setup |
| `--no-start` | Complete setup but don't start the container |
| `--help` | Show help message and exit |

## What the Script Does

The setup script performs the following operations:

### 1. System Detection
- Identifies Linux distribution and package manager
- Detects SELinux enforcement status
- Checks for OSTree (immutable) filesystems
- Identifies read-only filesystems (SteamOS)

### 2. Package Installation
- Installs autofs for automatic share mounting
- Installs cifs-utils for SMB/CIFS support
- Installs Docker (preferred) or Podman
- Installs docker-compose or podman-compose
- Installs lazydocker for container management

### 3. Autofs Configuration
- Creates secure SMB credential storage
- Configures autofs master file
- Sets up mount maps for all shares
- Enables and starts autofs service
- Validates all mount points

### 4. Container Setup
- Generates Docker Compose configuration
- Creates lazydocker wrapper script
- Optionally pulls and starts Tdarr container
- Verifies container connectivity

## Autofs Shares

The script configures automatic mounting for six SMB shares:

### Authenticated Shares (192.168.1.210)
- `hass_share` - Main media share
- `hass_media` - Media files
- `hass_config` - Configuration files

### Guest Shares (192.168.1.47)
- `usb_share` - USB Share 1
- `usb_share_2` - USB Share 2
- `rom_share` - ROM files

All shares are mounted at: `~/tdarr/mounts/`

## Container Configuration

### Volume Mappings
- `~/tdarr/mounts/hass_share` maps to `/share` (in container)
- `~/tdarr/mounts/hass_share/trans` maps to `/tmp` (in container)
- `~/Tdarr/configs` maps to `/app/configs` (in container)

### Default Settings
- **Server**: 192.168.1.210:8266
- **Image**: haveagitgat/tdarr_node:2.49.01
- **Node Name**: `<hostname>-node`
- **Network Mode**: host
- **Restart Policy**: unless-stopped

## Management Commands

### Using Docker Compose

```bash
cd ~/tdarr

# Start container
docker compose up -d

# Stop container
docker compose down

# View logs
docker compose logs -f

# Restart container
docker compose restart

# Check status
docker compose ps
```

### Using Lazydocker TUI

```bash
# Launch interactive container management
~/tdarr/ld.sh
```

### Direct Docker Commands

```bash
# Check status
docker ps --filter "name=tdarr-node"

# View logs
docker logs tdarr-node -f

# Restart
docker restart tdarr-node

# Stop
docker stop tdarr-node

# Shell access
docker exec -it tdarr-node /bin/bash
```

### Autofs Management

```bash
# Check mount status
mount | grep tdarr

# List mounted shares
ls ~/tdarr/mounts/

# Verify specific mount
mountpoint ~/tdarr/mounts/hass_share

# Restart autofs
sudo systemctl restart autofs

# Check autofs logs
journalctl -u autofs -f
```

## File Locations

### Configuration Files
- Setup script: `~/betterstrap/tdarr/setup-tdarr.sh`
- Docker Compose: `~/tdarr/docker-compose.yml`
- Lazydocker wrapper: `~/tdarr/ld.sh`
- Autofs master: `/etc/autofs/auto.master.d/tdarr.autofs`
- Autofs map: `/etc/auto.tdarr`
- SMB credentials: `/etc/auto.smb.210` (root-only)

### Directories
- Mount points: `~/tdarr/mounts/`
- Node configs: `~/Tdarr/configs/`
- Setup log: `~/tdarr/setup-tdarr.log`

## Troubleshooting

### Mounts Not Working

```bash
# Restart autofs service
sudo systemctl restart autofs

# Check autofs status
systemctl status autofs

# Manually trigger mount
ls ~/tdarr/mounts/hass_share

# Check mount logs
journalctl -u autofs -n 50
```

### Container Won't Start

```bash
# Check logs
docker logs tdarr-node --tail 50

# Verify mounts are accessible
ls ~/tdarr/mounts/hass_share

# Test Docker
docker info

# Validate compose file
docker compose -f ~/tdarr/docker-compose.yml config
```

### Network/Server Connection Issues

```bash
# Test server connectivity
ping 192.168.1.210

# Check if server port is open
nc -zv 192.168.1.210 8266

# Check SMB connectivity
smbclient -L //192.168.1.210 -U me
```

### Permission Issues

If using Docker and seeing permission errors:

```bash
# Verify you're in docker group
groups

# If not, log out and back in, or:
newgrp docker

# Re-run docker commands
```

### SELinux Issues (Fedora/Bazzite)

```bash
# Check for denials
sudo ausearch -m avc -ts recent

# Enable SMB access for containers
sudo setsebool -P virt_use_samba 1

# Check container logs for SELinux errors
docker logs tdarr-node | grep -i selinux
```

## Replication to Other Computers

To set up Tdarr on additional computers:

1. Copy the betterstrap directory to the new machine:
   ```bash
   # Using git
   git clone <your-repo> ~/betterstrap
   
   # Or using rsync
   rsync -av user@source:~/betterstrap ~/
   ```

2. Run the setup script:
   ```bash
   ~/betterstrap/tdarr/setup-tdarr.sh --start-now
   ```

3. The node will appear in the Tdarr server as `<hostname>-node`

### Customization

Before running on a new machine, you may want to edit `setup-tdarr.sh` to change:
- Server IP/port (lines 24-25)
- SMB credentials (lines 57-58)
- Tdarr version (line 23)

## Uninstallation

```bash
# Stop and remove container
cd ~/tdarr
docker compose down

# Remove autofs configuration
sudo rm /etc/autofs/auto.master.d/tdarr.autofs
sudo rm /etc/auto.tdarr
sudo rm /etc/auto.smb.210
sudo systemctl restart autofs

# Remove directories
rm -rf ~/tdarr ~/Tdarr

# Optional: Remove Docker (if not used elsewhere)
# Arch: sudo pacman -Rns docker docker-compose
# Debian: sudo apt remove docker-ce docker-ce-cli
```

## Features and Benefits

### Autofs Advantages
- **On-demand mounting**: Shares mount only when accessed
- **Automatic unmounting**: Unmounts after 120 seconds of inactivity
- **Resource efficient**: No permanent connections to servers
- **Resilient**: Automatically retries failed mounts
- **Transparent**: Applications see normal directories

### Multi-Distribution Support
- Arch Linux family (Arch, Manjaro, SteamOS)
- Debian family (Debian, Ubuntu)
- Red Hat family (Fedora, Bazzite)
- Handles OSTree immutable systems
- Manages SELinux contexts automatically

### Container Benefits
- Consistent environment across machines
- Easy version management
- Isolated from system changes
- Simple backup and restore
- Resource limiting capabilities

## Web Interface

After setup, check your Tdarr server web interface:

- URL: `http://192.168.1.210:8265`
- Look for your node in the "Nodes" tab
- Node name will be: `<hostname>-node`

## Support

For issues or questions:

1. Check the setup log: `~/tdarr/setup-tdarr.log`
2. Review Docker logs: `docker logs tdarr-node`
3. Verify autofs: `systemctl status autofs`
4. Test mounts: `ls ~/tdarr/mounts/hass_share`

## License

This setup script is part of the betterstrap project.
