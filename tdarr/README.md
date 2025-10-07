# Tdarr Node Docker Installation

This script installs and configures a Tdarr Node using Docker, replacing the previous manual installation method.

## Prerequisites

1. **Docker** must be installed and running
2. **SMB shares** must be mounted (run your `smb.sh` script first)
3. **Tdarr Server** should be running and accessible

## Quick Start

```bash
# Basic installation (uses defaults)
./install_node.sh

# Custom server IP
./install_node.sh --server-ip 192.168.1.100

# Custom version and paths
./install_node.sh --tdarr-version 2.48.01 --share-path /mnt/media
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--server-ip IP` | Tdarr server IP address | `192.168.1.210` |
| `--server-port PORT` | Tdarr server port | `8266` |
| `--node-name NAME` | Node name | `hostname-node` |
| `--tdarr-version VER` | Tdarr Node version | `2.47.01` |
| `--share-path PATH` | SMB share mount path | `/share` |
| `--trans-path PATH` | Temp/working files path | `/share/trans` |
| `-h, --help` | Show help message | - |

## What the Script Does

1. **Verifies** Docker installation and share paths
2. **Creates** Tdarr configuration with path translators
3. **Pulls** the correct Tdarr Node Docker image
4. **Starts** the container with proper volume mappings
5. **Configures** automatic restart on boot

## Path Mapping

The script configures path translation between server and node:

- **Host**: `/share` → **Container**: `/media`
- **Host**: `/share/trans` → **Container**: `/tmp`

This allows the server to send `/share/...` paths while the node accesses them at `/media/...`.

## Management Commands

After installation, use these commands:

```bash
# Check status
docker ps | grep tdarr-node

# View logs
docker logs tdarr-node -f

# Restart node
docker restart tdarr-node

# Stop node
docker stop tdarr-node

# Access container shell
docker exec -it tdarr-node /bin/bash
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs for errors
docker logs tdarr-node

# Verify share paths exist
ls -la /share/
ls -la /share/trans/
```

### Version Mismatch
```bash
# Update to match server version
docker stop tdarr-node
docker rm tdarr-node
./install_node.sh --tdarr-version X.XX.XX
```

### Can't Connect to Server
```bash
# Test connectivity
telnet 192.168.1.210 8266
# or
curl http://192.168.1.210:8266
```

## Uninstall

```bash
# Stop and remove container
docker stop tdarr-node && docker rm tdarr-node

# Remove image
docker rmi haveagitgat/tdarr_node:2.47.01

# Remove configuration
rm -rf ~/Tdarr
```

## Migration from Manual Installation

If you have an existing manual installation:

1. **Stop** the old service: `sudo systemctl stop tdarr-node`
2. **Disable** it: `sudo systemctl disable tdarr-node`
3. **Remove** the service file: `sudo rm /etc/systemd/system/tdarr-node.service`
4. **Run** this script: `./install_node.sh`

The Docker version is more reliable and easier to manage than the manual installation.