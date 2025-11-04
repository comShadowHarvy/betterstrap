#!/bin/bash

# Tdarr Node Docker Compose Installer
# This script replaces the complex install_node.sh with a simpler docker-compose approach

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==========================================="
echo "  Tdarr Node Docker Compose Installer"
echo "==========================================="
echo ""

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
  echo "❌ Error: docker-compose.yml not found in $SCRIPT_DIR"
  exit 1
fi

# Check Docker installation
if ! command -v docker &> /dev/null; then
  echo "❌ Docker is not installed. Please install Docker first:"
  echo "   sudo pacman -S docker docker-compose"
  echo "   sudo systemctl enable --now docker"
  echo "   sudo usermod -aG docker $USER"
  echo "   # Then log out and back in"
  exit 1
fi

if ! docker info &> /dev/null; then
  echo "❌ Docker is installed but not running or accessible."
  echo "   Try: sudo systemctl start docker"
  exit 1
fi

echo "✅ Docker is installed and running"

# Check if SMB share is mounted
if ! mountpoint -q /mnt/hass_share; then
  echo "❌ SMB share not mounted at /mnt/hass_share"
  echo "   Please ensure your SMB share is mounted first."
  exit 1
fi

echo "✅ SMB share mounted at /mnt/hass_share"

# Create necessary directories
echo ""
echo "📁 Creating necessary directories..."
mkdir -p /home/me/Tdarr/configs
mkdir -p /mnt/hass_share/trans

# Create/update node config if it doesn't exist or needs updating
CONFIG_FILE="/home/me/Tdarr/configs/Tdarr_Node_Config.json"
if [ ! -f "$CONFIG_FILE" ] || ! grep -q '"/share/trans"' "$CONFIG_FILE" 2>/dev/null; then
  echo "📝 Creating Tdarr node configuration..."
  cat > "$CONFIG_FILE" << 'EOF'
{
  "nodeName": "omarchy-node",
  "serverURL": "http://192.168.1.210:8266",
  "serverIP": "192.168.1.210",
  "serverPort": "8266",
  "pathTranslators": [
    {
      "server": "/share/trans",
      "node": "/tmp"
    }
  ],
  "nodeType": "mapped"
}
EOF
  echo "✅ Configuration created: $CONFIG_FILE"
else
  echo "✅ Configuration already exists: $CONFIG_FILE"
fi

# Stop any existing container
echo ""
echo "🧹 Stopping existing Tdarr node..."
docker compose down 2>/dev/null || true

# Pull latest image
echo ""
echo "🐳 Pulling Tdarr node image..."
docker compose pull

# Start the container
echo ""
echo "🚀 Starting Tdarr node..."
docker compose up -d

# Wait for container to start
echo "⏳ Waiting for container to initialize..."
sleep 5

# Check status
if docker ps --format '{{.Names}}' | grep -q '^tdarr-node$'; then
  echo ""
  echo "==========================================="
  echo "  Installation Complete!"
  echo "==========================================="
  echo ""
  echo "✅ Tdarr node started successfully!"
  echo ""
  echo "📋 Configuration:"
  echo "   Node Name: omarchy-node"
  echo "   Server: http://192.168.1.210:8266"
  echo "   Container: tdarr-node"
  echo ""
  echo "🔧 Management Commands:"
  echo "   View logs:   docker compose logs -f"
  echo "   Restart:     docker compose restart"
  echo "   Stop:        docker compose down"
  echo "   Start:       docker compose up -d"
  echo "   Recreate:    docker compose up -d --force-recreate"
  echo ""
  echo "📁 Important Paths:"
  echo "   Media:       /mnt/hass_share -> /share (in container)"
  echo "   Temp:        /mnt/hass_share/trans -> /tmp (in container)"
  echo "   Config:      /home/me/Tdarr/configs"
  echo ""
  echo "Check the Tdarr server to verify node connection."
else
  echo ""
  echo "❌ Container failed to start. Checking logs..."
  docker compose logs --tail 20
  exit 1
fi
