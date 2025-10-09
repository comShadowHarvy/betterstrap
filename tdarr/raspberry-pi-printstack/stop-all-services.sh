#!/bin/bash
# Stop All Services Script
# Safely stops all Klipper and Tdarr services
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
    echo -e "${BLUE}[STOP]${NC} $1"
}

# Configuration
STACK_DIR="/srv/printstack"

# Check if stack directory exists
if [ ! -d "${STACK_DIR}" ]; then
    print_error "Stack directory not found at ${STACK_DIR}"
    print_error "Please run setup-printstack.sh first"
    exit 1
fi

cd "${STACK_DIR}"

print_header "Stopping All Services..."

# Stop Klipper stack
print_status "Stopping Klipper services..."
if [ -f "klipper-compose.yml" ]; then
    docker compose -f klipper-compose.yml down 2>/dev/null || {
        print_warning "Error stopping Klipper services (may already be stopped)"
    }
else
    print_warning "klipper-compose.yml not found"
fi

# Stop Tdarr stack
print_status "Stopping Tdarr services..."
if [ -f "tdarr-compose.yml" ]; then
    docker compose -f tdarr-compose.yml down 2>/dev/null || {
        print_warning "Error stopping Tdarr services (may already be stopped)"
    }
else
    print_warning "tdarr-compose.yml not found"
fi

# Stop any individual containers that might be running
print_status "Stopping any remaining containers..."
CONTAINERS=("klipper" "moonraker" "mainsail" "camera" "printer-samba" "tdarr-node")

for container in "${CONTAINERS[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        print_status "Stopping ${container}..."
        docker stop "${container}" 2>/dev/null || true
    fi
done

# Wait a moment for cleanup
sleep 2

# Check final status
print_header "Checking final status..."
STILL_RUNNING=()

for container in "${CONTAINERS[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        STILL_RUNNING+=("${container}")
    fi
done

if [ ${#STILL_RUNNING[@]} -eq 0 ]; then
    print_status "✅ All services stopped successfully!"
else
    print_warning "⚠️  Some containers are still running:"
    for container in "${STILL_RUNNING[@]}"; do
        print_warning "   - ${container}"
    done
    echo ""
    print_status "To force stop remaining containers:"
    printf "   docker stop"
    for container in "${STILL_RUNNING[@]}"; do
        printf " %s" "${container}"
    done
    echo ""
fi

echo ""
print_header "Service Status Summary:"
echo "========================"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || {
    print_warning "Could not get container status"
}

echo ""
print_status "🔧 Cleanup Options:"
echo "   Remove stopped containers: docker container prune -f"
echo "   Remove unused images:       docker image prune -f"
echo "   Remove unused volumes:      docker volume prune -f"
echo "   Remove everything unused:   docker system prune -f"
echo ""
print_status "🚀 Restart Options:"
echo "   Start printing:    ./start-klipper-stack.sh"
echo "   Start transcoding: ./start-tdarr-node.sh"