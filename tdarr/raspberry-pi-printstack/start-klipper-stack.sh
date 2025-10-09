#!/bin/bash
# Klipper + Camera + Samba Stack Startup Script
# Ensures all images are available and starts the printing stack
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
    echo -e "${BLUE}[KLIPPER]${NC} $1"
}

# Configuration
STACK_DIR="/srv/printstack"
PI_IP=$(hostname -I | awk '{print $1}' | tr -d ' ')

# Check if we're in the right directory
if [ ! -f "${STACK_DIR}/klipper-compose.yml" ]; then
    print_error "Klipper compose file not found at ${STACK_DIR}/klipper-compose.yml"
    print_error "Please run setup-printstack.sh first"
    exit 1
fi

cd "${STACK_DIR}"

print_header "Starting Klipper Stack Setup..."

# Stop any running Tdarr containers first
print_status "Stopping any running Tdarr services..."
docker compose -f tdarr-compose.yml down 2>/dev/null || true
sleep 3

# Set proper permissions for Samba access
print_status "Setting up file permissions for network shares..."
sudo chmod -R 775 data/gcodes data/timelapse config/klipper 2>/dev/null || {
    print_warning "Could not set some permissions - you may need to run as root"
}

# Pull all required images
print_header "Pulling Docker images..."

IMAGES=(
    "mkuf/klipper:latest"
    "mkuf/moonraker:latest"
    "ghcr.io/mainsail-crew/mainsail:latest"
    "mkuf/ustreamer:latest"
    "dperson/samba:latest"
)

for image in "${IMAGES[@]}"; do
    print_status "Pulling ${image}..."
    if ! docker pull "${image}"; then
        print_error "Failed to pull ${image}"
        exit 1
    fi
done

print_status "All images pulled successfully!"

# Check for camera device
print_status "Checking for camera device..."
if [ -c "/dev/video0" ]; then
    print_status "Camera found at /dev/video0"
else
    print_warning "No camera found at /dev/video0 - camera service may fail"
    print_warning "Connect a USB camera or update the compose file for your camera device"
fi

# Start the stack
print_header "Starting Klipper services..."
if ! docker compose -f klipper-compose.yml up -d; then
    print_error "Failed to start Klipper stack"
    print_error "Checking logs..."
    docker compose -f klipper-compose.yml logs
    exit 1
fi

# Wait for services to initialize
print_status "Waiting for services to initialize..."
sleep 15

# Check service status
print_header "Checking service status..."
SERVICES=("klipper" "moonraker" "mainsail" "camera" "printer-samba")
FAILED_SERVICES=()

for service in "${SERVICES[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
        print_status "${service}: ✅ Running"
    else
        print_warning "${service}: ❌ Not running"
        FAILED_SERVICES+=("${service}")
    fi
done

# Show logs for failed services
if [ ${#FAILED_SERVICES[@]} -gt 0 ]; then
    print_warning "Some services failed to start. Showing logs:"
    for service in "${FAILED_SERVICES[@]}"; do
        echo ""
        print_warning "=== ${service} logs ==="
        docker logs "${service}" --tail 20 2>/dev/null || echo "No logs available"
    done
fi

echo ""
print_header "✅ Klipper Stack Started!"
echo ""
echo "🌐 Web Interfaces:"
echo "   Mainsail:     http://${PI_IP}"
echo "   Camera:       http://${PI_IP}:8080"
echo "   Moonraker:    http://${PI_IP}:7125"
echo ""
echo "📁 Network Shares (Guest Access):"
echo "   Config:       \\\\${PI_IP}\\Printer-Config"
echo "   G-codes:      \\\\${PI_IP}\\Printer-GCodes"
echo "   Timelapse:    \\\\${PI_IP}\\Printer-Timelapse"
echo ""
echo "📝 Next Steps:"
echo "   1. Edit ${STACK_DIR}/config/klipper/printer.cfg for your printer"
echo "   2. Find your printer's serial: ls /dev/serial/by-id/"
echo "   3. Update the [mcu] section in printer.cfg"
echo "   4. Restart if needed: docker restart klipper"
echo ""
echo "🔧 Management Commands:"
echo "   Status:   docker ps"
echo "   Logs:     docker logs klipper -f"
echo "   Stop:     docker compose -f klipper-compose.yml down"
echo "   Restart:  docker compose -f klipper-compose.yml restart"

# Check printer connection
echo ""
print_status "Checking printer connection..."
sleep 5
if docker logs klipper 2>&1 | grep -q "mcu.*: Got EOF when reading from device"; then
    print_warning "Printer not connected or serial port incorrect"
    print_warning "Update the [mcu] section in ${STACK_DIR}/config/klipper/printer.cfg"
elif docker logs klipper 2>&1 | grep -q "mcu.*: Starting serial"; then
    print_status "Printer connection looks good!"
else
    print_warning "Unable to determine printer connection status"
    print_warning "Check: docker logs klipper"
fi