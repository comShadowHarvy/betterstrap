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
| `--no-gpu` | Disable GPU acceleration | enabled by default |
| `-h, --help` | Show help message | - |

## What the Script Does

1. **Verifies** Docker installation and share paths
2. **Detects** NVIDIA GPU and installs Container Toolkit if needed
3. **Creates** Tdarr configuration with path translators
4. **Pulls** the correct Tdarr Node Docker image
5. **Starts** the container with GPU acceleration and proper volume mappings
6. **Configures** automatic restart on boot

## Path Mapping

The script configures path translation between server and node:

- **Host**: `/share` → **Container**: `/media`
- **Host**: `/share/trans` → **Container**: `/tmp`

This allows the server to send `/share/...` paths while the node accesses them at `/media/...`.

## GPU Acceleration

The script automatically detects and enables **both NVIDIA and Intel GPUs** for maximum performance:

### Multi-GPU Support
- **NVIDIA GPUs**: NVENC (H.264/H.265) hardware encoding
- **Intel GPUs**: QuickSync (H.264/H.265/AV1) hardware encoding  
- **Dual GPU**: Can use both simultaneously for parallel encoding
- **Auto-detection**: Scans for all available GPU hardware
- **Auto-install**: Installs required drivers and toolkits
- **Non-blocking**: GPUs remain available for other applications

### Supported Hardware
- **NVIDIA**: GTX 1050+, RTX series (NVENC support)
- **Intel**: 7th gen+ processors with integrated graphics (QuickSync)
- **Hybrid systems**: Laptops with both Intel + NVIDIA GPUs

### Features
- **Parallel encoding**: Multiple streams on different GPUs
- **Load balancing**: Tdarr can distribute work across GPUs
- **Power efficiency**: Intel GPU often more power-efficient
- **Fallback support**: Gracefully handles missing drivers
- **Override**: Use `--no-gpu` to disable if needed

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