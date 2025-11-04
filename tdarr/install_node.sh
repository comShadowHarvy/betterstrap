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
TRANS_PATH="$HOME/temp/trans"  # Path for temporary/working files
ENABLE_GPU=true  # Enable GPU acceleration for encoding
AUTO_UPDATE=false  # Enable automatic version checking
WORKER_MEMORY=4096  # Memory limit per worker in MB (default: 4GB)
MAX_WORKERS=1  # Maximum number of concurrent workers (reduced due to hardcoded 16GB per worker)
CONTAINER_MEMORY=14g  # Total container memory limit

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
    --no-gpu)
      ENABLE_GPU=false
      shift
      ;;
    --auto-update)
      AUTO_UPDATE=true
      shift
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
      echo "  --no-gpu               Disable GPU acceleration (default: enabled)"
      echo "  --auto-update          Check server version and update if needed"
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

# Function to check and install GPU support
check_gpu_support() {
  if [ "$ENABLE_GPU" != "true" ]; then
    echo "⚠️  GPU acceleration disabled"
    return 0
  fi
  
  local gpu_found=false
  local gpu_types=""
  
  # Check for NVIDIA GPU
  if lspci | grep -i nvidia >/dev/null 2>&1; then
    gpu_found=true
    gpu_types="NVIDIA"
    
    # Check if nvidia-smi works
    if ! command -v nvidia-smi >/dev/null 2>&1; then
      echo "❌ NVIDIA GPU detected but drivers not installed."
      echo "   For Arch Linux: sudo pacman -S nvidia nvidia-utils"
      ENABLE_GPU=false
      return 1
    fi
    
    # Check if NVIDIA Container Toolkit is installed
    if ! pacman -Q nvidia-container-toolkit >/dev/null 2>&1; then
      echo "🔧 Installing NVIDIA Container Toolkit..."
      sudo pacman -S nvidia-container-toolkit --noconfirm
      
      echo "🔧 Configuring Docker for NVIDIA runtime..."
      sudo nvidia-ctk runtime configure --runtime=docker
      
      echo "🔄 Restarting Docker daemon..."
      sudo systemctl restart docker
      sleep 3
    fi
  fi
  
  # Check for Intel GPU
  if lspci | grep -i "intel.*graphics" >/dev/null 2>&1; then
    gpu_found=true
    if [ -n "$gpu_types" ]; then
      gpu_types="$gpu_types + Intel"
    else
      gpu_types="Intel"
    fi
    
    # Check if Intel media driver is installed
    if ! pacman -Q intel-media-driver >/dev/null 2>&1; then
      echo "🔧 Installing Intel GPU drivers..."
      sudo pacman -S intel-media-driver libva-utils --noconfirm
    fi
  fi
  
  # Check if any GPU render devices exist
  if [ ! -d "/dev/dri" ] || [ -z "$(ls -A /dev/dri/render* 2>/dev/null)" ]; then
    echo "⚠️  No GPU render devices found at /dev/dri"
    gpu_found=false
  fi
  
  if [ "$gpu_found" = "false" ]; then
    echo "⚠️  No supported GPUs detected, disabling GPU acceleration"
    ENABLE_GPU=false
    return 0
  fi
  
  echo "✅ GPU acceleration ready ($gpu_types)"
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
echo "GPU Acceleration: $ENABLE_GPU"
echo "Auto Update: $AUTO_UPDATE"
echo ""

# Check Docker installation
check_docker

# Check GPU support
check_gpu_support

# Check server version and update TDARR_VERSION if auto-update enabled
if [ "$AUTO_UPDATE" = "true" ]; then
  echo "🔄 Auto-update enabled, checking server version..."
  if command -v curl >/dev/null 2>&1; then
    SERVER_VERSION=$(timeout 10 curl -s "http://$SERVER_IP:$SERVER_PORT/api/v2/status" 2>/dev/null | \
      grep -o '"version":"[^"]*"' | cut -d'"' -f4 || echo "")
    if [ -n "$SERVER_VERSION" ]; then
      if [ "$SERVER_VERSION" != "$TDARR_VERSION" ]; then
        echo "📋 Version mismatch detected!"
        echo "   Script default: $TDARR_VERSION"
        echo "   Server version: $SERVER_VERSION"
        echo "   Updating to match server: $SERVER_VERSION"
        TDARR_VERSION="$SERVER_VERSION"
      else
        echo "✅ Version matches server: $TDARR_VERSION"
      fi
    else
      echo "⚠️  Could not retrieve server version, using: $TDARR_VERSION"
    fi
  else
    echo "⚠️  curl not available, cannot check server version"
  fi
fi

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
    },
    {
      "server": "/share/trans",
      "node": "/tmp"
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

# Build Docker command with conditional GPU support
DOCKER_CMD="docker run -d \\
  --name $CONTAINER_NAME \\
  --restart unless-stopped"

# Add GPU support if enabled
if [ "$ENABLE_GPU" = "true" ]; then
  # Add NVIDIA GPU support
  if lspci | grep -i nvidia >/dev/null 2>&1; then
    DOCKER_CMD="$DOCKER_CMD \\
  --gpus all"
  fi
  
  # Add Intel GPU support (DRI devices for VA-API)
  if [ -d "/dev/dri" ]; then
    DOCKER_CMD="$DOCKER_CMD \\
  --device /dev/dri:/dev/dri"
  fi
  
  echo "🎥 Multi-GPU acceleration enabled"
fi

# Add remaining parameters
DOCKER_CMD="$DOCKER_CMD \\
  -v $TRANS_PATH:/tmp \\
  -v $SHARE_PATH:/media \\
  -v $HOME/Tdarr/configs:/app/configs \\
  -e serverIP=$SERVER_IP \\
  -e serverPort=$SERVER_PORT \\
  -e nodeName=$NODE_NAME \\
  -e internalNode=true \\
  -e inContainer=true"

# Add Intel GPU environment variables if Intel GPU detected
if [ "$ENABLE_GPU" = "true" ] && lspci | grep -i "intel.*graphics" >/dev/null 2>&1; then
  DOCKER_CMD="$DOCKER_CMD \\
  -e LIBVA_DRIVER_NAME=iHD"
fi

# Add worker limit (memory is hardcoded at 16GB per worker, so limit workers to 1)
DOCKER_CMD="$DOCKER_CMD \\
  -e ffmpegWorkerLimit=$MAX_WORKERS"

# Add the image name
DOCKER_CMD="$DOCKER_CMD \\
  haveagitgat/tdarr_node:$TDARR_VERSION"

# Execute the command
eval "$DOCKER_CMD"

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
echo "   GPU Acceleration: $ENABLE_GPU"
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
