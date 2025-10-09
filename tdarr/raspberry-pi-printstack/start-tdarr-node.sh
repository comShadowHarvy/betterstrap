#!/bin/bash
# Tdarr Node Startup Script
# Ensures images are available, tests server connection, and starts transcoding node
set -euo pipefail

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[TDARR]${NC} $1"
}

# Configuration - adjust these for your setup
STACK_DIR="/srv/printstack"
SERVER_IP="192.168.1.210"
SERVER_PORT="8266"
SERVER_URL="http://${SERVER_IP}:${SERVER_PORT}"
NODE_NAME="${HOSTNAME}-node"
PI_IP=$(hostname -I | awk '{print $1}' | tr -d ' ')

# Auto-detect server version or use latest
TDAR_VERSION="latest"
SERVER_VERSION="unknown"

# Check if we're in the right directory
if [ ! -f "${STACK_DIR}/tdarr-compose.yml" ]; then
    print_error "Tdarr compose file not found at ${STACK_DIR}/tdarr-compose.yml"
    print_error "Please run setup-printstack.sh first"
    exit 1
fi

cd "${STACK_DIR}"

print_header "Starting Tdarr Node Setup..."

# Stop any running Klipper services first
print_status "Stopping any running Klipper services..."
docker compose -f klipper-compose.yml down 2>/dev/null || true
sleep 3

# Check Docker installation
print_status "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    print_error "Please install Docker first: sudo pacman -S docker"
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running or not accessible"
    print_error "Try: sudo systemctl start docker"
    print_error "Or: sudo usermod -aG docker $USER (then log out/in)"
    exit 1
fi

print_status "Docker is ready"

# Check GPU support
print_status "Checking GPU acceleration support..."
gpu_found=false
gpu_types=""

# Check for NVIDIA GPU
if lspci | grep -i nvidia >/dev/null 2>&1; then
    gpu_found=true
    gpu_types="NVIDIA"
    
    if command -v nvidia-smi >/dev/null 2>&1; then
        print_status "NVIDIA GPU detected and drivers available"
    else
        print_warning "NVIDIA GPU detected but drivers not installed"
        print_warning "Consider installing: sudo pacman -S nvidia nvidia-utils"
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
    print_status "Intel GPU detected"
fi

# Check for render devices
if [ ! -d "/dev/dri" ] || [ -z "$(ls -A /dev/dri/render* 2>/dev/null)" ]; then
    print_warning "No GPU render devices found at /dev/dri"
    gpu_found=false
fi

if [ "$gpu_found" = "false" ]; then
    print_warning "No supported GPUs detected - using CPU-only transcoding"
else
    print_status "GPU acceleration ready ($gpu_types)"
fi

# Verify share paths
print_header "Checking required directories..."

if [ ! -d "/share" ]; then
    print_error "/share directory does not exist!"
    print_error "Please ensure your SMB shares are mounted first"
    print_error "This is required for Tdarr to access media files"
    exit 1
fi
print_status "/share directory found"

if [ ! -d "/share/trans" ]; then
    print_status "Creating /share/trans directory for temporary files..."
    mkdir -p "/share/trans"
fi
print_status "/share/trans directory ready"

# Test server connection and detect version
print_header "Testing Tdarr server connection and detecting version..."
print_status "Attempting to connect to $SERVER_URL..."

if timeout 10 bash -c "</dev/tcp/$SERVER_IP/$SERVER_PORT" 2>/dev/null; then
    print_status "✅ Successfully connected to Tdarr server at $SERVER_IP:$SERVER_PORT"
    
    # Try to get server version from API
    print_status "Detecting server version..."
    if command -v curl >/dev/null 2>&1; then
        SERVER_VERSION=$(timeout 5 curl -s "http://${SERVER_IP}:8265/api/v2/status" 2>/dev/null | grep -o '"version":"[^"]*' | cut -d'"' -f4 2>/dev/null || echo "unknown")
        if [ "$SERVER_VERSION" != "unknown" ] && [ -n "$SERVER_VERSION" ]; then
            print_status "Server version detected: $SERVER_VERSION"
            TDAR_VERSION="$SERVER_VERSION"
        else
            print_status "Could not detect server version, using latest"
        fi
    else
        print_warning "curl not available, using latest version"
    fi
else
    print_warning "⚠️  Could not connect to Tdarr server at $SERVER_IP:$SERVER_PORT"
    print_warning "Please ensure:"
    print_warning "  1. Tdarr server is running on $SERVER_IP"
    print_warning "  2. Port $SERVER_PORT is accessible"
    print_warning "  3. No firewall is blocking the connection"
    print_warning ""
    print_warning "You can still proceed with latest version, but the node won't work until the server is available."
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Installation cancelled"
        exit 1
    fi
fi

# Pull Docker image with detected/latest version
print_header "Pulling Tdarr Node Docker image..."
print_status "Pulling haveagitgat/tdarr_node:${TDAR_VERSION}..."

if ! docker pull "haveagitgat/tdarr_node:${TDAR_VERSION}"; then
    print_error "Failed to pull Tdarr Node image with version ${TDAR_VERSION}"
    if [ "$TDAR_VERSION" != "latest" ]; then
        print_warning "Falling back to latest version..."
        TDAR_VERSION="latest"
        if ! docker pull "haveagitgat/tdarr_node:latest"; then
            print_error "Failed to pull latest image as well"
            print_error "Check your internet connection and Docker registry access"
            exit 1
        fi
    else
        print_error "Check your internet connection and Docker registry access"
        exit 1
    fi
fi

print_status "Image pulled successfully: haveagitgat/tdarr_node:${TDAR_VERSION}"

# Update Docker Compose to use detected version
print_status "Updating Docker Compose configuration..."
if [ -f "${STACK_DIR}/tdarr-compose.yml" ]; then
    sed -i "s|image: haveagitgat/tdarr_node:.*|image: haveagitgat/tdarr_node:${TDAR_VERSION}|" "${STACK_DIR}/tdarr-compose.yml"
    print_status "Docker Compose updated to use version: ${TDAR_VERSION}"
else
    print_error "Docker Compose file not found - please run setup script first"
    exit 1
fi

# Update node configuration with current hostname and server
print_status "Updating Tdarr node configuration..."
if [ -f "${STACK_DIR}/config/tdarr/Tdarr_Node_Config.json" ]; then
    sed -i "s/\"nodeName\": \".*-node\"/\"nodeName\": \"${NODE_NAME}\"/" "${STACK_DIR}/config/tdarr/Tdarr_Node_Config.json"
    sed -i "s|\"serverURL\": \"http://.*:8266\"|\"serverURL\": \"${SERVER_URL}\"|" "${STACK_DIR}/config/tdarr/Tdarr_Node_Config.json"
    print_status "Configuration updated for current hostname and server"
else
    print_warning "Node configuration file not found - it will be created by the container"
fi

# Start the Tdarr node
print_header "Starting Tdarr Node container..."
if ! docker compose -f tdarr-compose.yml up -d; then
    print_error "Failed to start Tdarr node"
    print_error "Checking logs..."
    docker compose -f tdarr-compose.yml logs
    exit 1
fi

# Wait for container to initialize
print_status "Waiting for container to initialize..."
sleep 15

# Check container status
if docker ps --format '{{.Names}}' | grep -q "^tdarr-node$"; then
    print_status "✅ Tdarr Node container started successfully!"
else
    print_error "❌ Container failed to start"
    print_error "Checking recent logs..."
    docker logs tdarr-node --tail 20 2>/dev/null || echo "No logs available"
    exit 1
fi

# Show container logs
print_header "Recent container logs:"
echo "========================"
docker logs tdarr-node --tail 15

echo ""
print_header "✅ Tdarr Node Setup Complete!"
echo ""
echo "📋 Configuration Summary:"
echo "   Node Name: $NODE_NAME"
echo "   Server URL: $SERVER_URL"
echo "   Container: tdarr-node"
echo "   Tdarr Version: $TDAR_VERSION ($([ "$SERVER_VERSION" != "unknown" ] && echo "matched server" || echo "latest available"))"
echo "   GPU Acceleration: $([[ $gpu_found == true ]] && echo "Enabled ($gpu_types)" || echo "Disabled")"
echo ""
echo "📁 Directory Mappings:"
echo "   /share → /media (in container)"
echo "   /share/trans → /tmp (in container)"
echo ""
echo "🔧 Management Commands:"
echo "   Status:   docker ps | grep tdarr-node"
echo "   Logs:     docker logs tdarr-node -f"
echo "   Stop:     docker stop tdarr-node"
echo "   Restart:  docker restart tdarr-node"
echo "   Shell:    docker exec -it tdarr-node /bin/bash"
echo ""
echo "🗑️  Stop and Remove:"
echo "   docker compose -f tdarr-compose.yml down"
echo ""
echo "🌐 Check Status:"
echo "   Your Tdarr node should appear in the server web interface at:"
echo "   http://${SERVER_IP}:8265"
echo ""
echo "   Look for node: '${NODE_NAME}' in the Tdarr server's Nodes tab"

# Final connection test
print_status "Performing final connection test..."
sleep 5
if docker logs tdarr-node 2>&1 | grep -q -i "connected\|registered\|ready"; then
    print_status "✅ Node appears to have connected successfully!"
elif docker logs tdarr-node 2>&1 | grep -q -i "error\|failed\|connection"; then
    print_warning "⚠️  Node may have connection issues - check logs above"
else
    print_warning "⚠️  Connection status unclear - monitor logs with: docker logs tdarr-node -f"
fi