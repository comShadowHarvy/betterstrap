#!/bin/bash
set -e

# Configuration
SERVER_IP="192.168.1.210"
SERVER_PORT="8266"
SERVER_URL="http://${SERVER_IP}:${SERVER_PORT}"
NODE_NAME="${HOSTNAME}-node"
TDARR_VERSION="2.47.01"  # Set to match your server version
CONTAINER_NAME="tdarr-node"
SHARE_PATH="/share"  # Path to your SMB share mount
TRANS_PATH="/share/trans"  # Path for temporary/working files

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --server-ip)
      SERVER_IP="$2"
      SERVER_URL="http://${SERVER_IP}:${SERVER_PORT}"
      shift 2
      ;;
    --server-port)
      SERVER_PORT="$2"
      SERVER_URL="http://${SERVER_IP}:${SERVER_PORT}"
      shift 2
      ;;
    --node-name)
      NODE_NAME="$2"
      shift 2
      ;;
    --tdarr-version)
      TDARR_VERSION="$2"
      shift 2
      ;;
    --share-path)
      SHARE_PATH="$2"
      shift 2
      ;;
    --trans-path)
      TRANS_PATH="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo "Options:"
      echo "  --server-ip IP         Server IP address (default: 192.168.1.210)"
      echo "  --server-port PORT     Server port (default: 8266)"
      echo "  --node-name NAME       Node name (default: hostname-node)"
      echo "  --tdarr-version VER    Tdarr Node version (default: 2.47.01)"
      echo "  --share-path PATH      Path to SMB share mount (default: /share)"
      echo "  --trans-path PATH      Path for temp/working files (default: /share/trans)"
      echo "  -h, --help             Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use -h or --help for usage information"
      exit 1
      ;;
  esac
done

# Function to check if Docker is installed and running
check_docker() {
  if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   sudo pacman -S docker"
    echo "   sudo systemctl enable --now docker"
    echo "   sudo usermod -aG docker $USER"
    echo "   # Then log out and back in, or run: newgrp docker"
    exit 1
  fi
  
  if ! docker info &> /dev/null; then
    echo "❌ Docker is installed but not running or accessible."
    echo "   Try: sudo systemctl start docker"
    echo "   Or add your user to docker group: sudo usermod -aG docker $USER"
    exit 1
  fi
  
  echo "✅ Docker is installed and running"
}

# Function to stop and remove existing container
cleanup_existing_container() {
  if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "🧹 Stopping and removing existing container..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
  fi
}

echo "==========================================="
echo "  Tdarr Node Docker Installation Script"
echo "==========================================="
echo "Server URL: $SERVER_URL"
echo "Node Name: $NODE_NAME"
echo "Tdarr Version: $TDARR_VERSION"
echo "Share Path: $SHARE_PATH"
echo "Temp Path: $TRANS_PATH"
echo ""

# Check Docker installation
check_docker

# Verify share paths exist
echo "📁 Checking share paths..."
if [ ! -d "$SHARE_PATH" ]; then
  echo "❌ Share path $SHARE_PATH does not exist!"
  echo "   Please ensure your SMB shares are mounted first."
  echo "   Run your smb.sh script or mount the shares manually."
  exit 1
fi

if [ ! -d "$TRANS_PATH" ]; then
  echo "❌ Trans path $TRANS_PATH does not exist!"
  echo "   Please ensure your SMB shares are mounted first."
  exit 1
fi

echo "✅ Share paths verified"

# Create config directory
echo "📝 Creating Tdarr configuration..."
mkdir -p "$HOME/Tdarr/configs"

# Create the node configuration file with path translator
cat > "$HOME/Tdarr/configs/Tdarr_Node_Config.json" << EOF
{
  "nodeName": "$NODE_NAME",
  "serverURL": "$SERVER_URL",
  "nodeType": "mapped",
  "priority": 0,
  "handbrakePath": "",
  "ffmpegPath": "",
  "mkvpropeditPath": "",
  "pathTranslators": [
    {
      "server": "$SHARE_PATH",
      "node": "/media"
    }
  ],
  "maxLogSizeMB": 10,
  "pollInterval": 2000,
  "startPaused": false
}
EOF

echo "✅ Configuration created: $HOME/Tdarr/configs/Tdarr_Node_Config.json"

# Test server connection
echo "🔗 Testing connection to Tdarr server at $SERVER_URL..."
if timeout 10 bash -c "</dev/tcp/$SERVER_IP/$SERVER_PORT" 2>/dev/null; then
  echo "✅ Successfully connected to Tdarr server at $SERVER_IP:$SERVER_PORT"
else
  echo "⚠️  Warning: Could not connect to Tdarr server at $SERVER_IP:$SERVER_PORT"
  echo "   Please ensure the server is running and accessible."
  echo "   You can still proceed with the installation."
fi

# Clean up any existing container
cleanup_existing_container

# Pull the Docker image
echo "🐳 Pulling Tdarr Node Docker image..."
docker pull "haveagitgat/tdarr_node:$TDARR_VERSION"

# Start the container
echo "🚀 Starting Tdarr Node container..."
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  -v "$TRANS_PATH:/tmp" \
  -v "$SHARE_PATH:/media" \
  -v "$HOME/Tdarr/configs:/app/configs" \
  -e serverIP="$SERVER_IP" \
  -e serverPort="$SERVER_PORT" \
  -e nodeName="$NODE_NAME" \
  -e internalNode=true \
  -e inContainer=true \
  "haveagitgat/tdarr_node:$TDARR_VERSION"

# Wait a moment for container to start
echo "⏳ Waiting for container to initialize..."
sleep 10

# Check container status
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "✅ Container is running successfully!"
else
  echo "❌ Container failed to start. Checking logs..."
  docker logs "$CONTAINER_NAME" --tail 20
  exit 1
fi

# Show recent logs
echo ""
echo "📋 Recent container logs:"
echo "========================"
docker logs "$CONTAINER_NAME" --tail 15

echo ""
echo "==========================================="
echo "  Installation Complete!"
echo "==========================================="
echo ""
echo "📋 Configuration Summary:"
echo "   Node Name: $NODE_NAME"
echo "   Server URL: $SERVER_URL"
echo "   Tdarr Version: $TDARR_VERSION"
echo "   Container Name: $CONTAINER_NAME"
echo "   Config File: $HOME/Tdarr/configs/Tdarr_Node_Config.json"
echo "   Share Path: $SHARE_PATH → /media (in container)"
echo "   Temp Path: $TRANS_PATH → /tmp (in container)"
echo ""
echo "🔧 Management Commands:"
echo "   Status:   docker ps | grep $CONTAINER_NAME"
echo "   Logs:     docker logs $CONTAINER_NAME -f"
echo "   Stop:     docker stop $CONTAINER_NAME"
echo "   Start:    docker start $CONTAINER_NAME"
echo "   Restart:  docker restart $CONTAINER_NAME"
echo "   Shell:    docker exec -it $CONTAINER_NAME /bin/bash"
echo ""
echo "🗑️  Uninstall Commands:"
echo "   docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME"
echo "   docker rmi haveagitgat/tdarr_node:$TDARR_VERSION"
echo "   rm -rf $HOME/Tdarr"
echo ""
echo "✅ Your Tdarr Node should now be connecting to the server at $SERVER_URL"
echo "   Check the server's web interface to verify the node connection."
echo "   If there are issues, check: docker logs $CONTAINER_NAME"
