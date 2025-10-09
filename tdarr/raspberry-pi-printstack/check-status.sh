#!/bin/bash
# Status Check Script
# Shows detailed status of all services and system resources
set -euo pipefail

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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
    echo -e "${BLUE}[STATUS]${NC} $1"
}

print_section() {
    echo -e "${CYAN}$1${NC}"
}

# Configuration
STACK_DIR="/srv/printstack"
PI_IP=$(hostname -I | awk '{print $1}' | tr -d ' ')
SERVER_IP="192.168.1.210"
SERVER_PORT="8266"

print_header "PrintStack Status Check"
echo "========================"
echo "Host: $(hostname)"
echo "IP: ${PI_IP}"
echo "Time: $(date)"
echo ""

# Docker Status
print_section "🐳 Docker Status:"
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        print_status "Docker is running"
        echo "   Version: $(docker --version | cut -d' ' -f3 | cut -d',' -f1)"
    else
        print_error "Docker installed but not accessible"
        echo "   Try: sudo systemctl start docker"
    fi
else
    print_error "Docker not installed"
fi
echo ""

# Container Status
print_section "📦 Container Status:"
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "   $(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No containers found")"
    
    echo ""
    print_section "💾 Container Resources:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>/dev/null || {
        print_warning "Could not get container stats"
    }
else
    print_error "Cannot check containers - Docker not available"
fi
echo ""

# Service-specific Status
KLIPPER_RUNNING=false
TDARR_RUNNING=false

if command -v docker &> /dev/null && docker info &> /dev/null; then
    if docker ps --format '{{.Names}}' | grep -q "^klipper$"; then
        KLIPPER_RUNNING=true
    fi
    
    if docker ps --format '{{.Names}}' | grep -q "^tdarr-node$"; then
        TDARR_RUNNING=true
    fi
fi

# Klipper Status
print_section "🖨️  Klipper Stack Status:"
if [ "$KLIPPER_RUNNING" = true ]; then
    print_status "Klipper stack is RUNNING"
    
    # Check individual services
    KLIPPER_SERVICES=("klipper" "moonraker" "mainsail" "camera" "printer-samba")
    for service in "${KLIPPER_SERVICES[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
            echo "   ✅ ${service}: Running"
        else
            echo "   ❌ ${service}: Not running"
        fi
    done
    
    echo ""
    echo "   🌐 Web Interfaces:"
    echo "      Mainsail:  http://${PI_IP}"
    echo "      Camera:    http://${PI_IP}:8080"
    echo "      Moonraker: http://${PI_IP}:7125"
    
    echo ""
    echo "   📁 Network Shares:"
    echo "      Config:    \\\\${PI_IP}\\Printer-Config"
    echo "      G-codes:   \\\\${PI_IP}\\Printer-GCodes"
    echo "      Timelapse: \\\\${PI_IP}\\Printer-Timelapse"
    
    # Check printer connection
    if docker logs klipper --tail 20 2>/dev/null | grep -q -i "serial.*ready\|mcu.*ready"; then
        echo "   🔌 Printer: Connected"
    elif docker logs klipper --tail 20 2>/dev/null | grep -q -i "error\|failed\|timeout"; then
        echo "   🔌 Printer: Connection issues detected"
    else
        echo "   🔌 Printer: Status unknown"
    fi
else
    print_warning "Klipper stack is STOPPED"
    echo "   Start with: ./start-klipper-stack.sh"
fi
echo ""

# Tdarr Status  
print_section "🎬 Tdarr Node Status:"
if [ "$TDARR_RUNNING" = true ]; then
    print_status "Tdarr node is RUNNING"
    echo "   📋 Configuration:"
    echo "      Node Name: $(hostname)-node"
    echo "      Server:    http://${SERVER_IP}:${SERVER_PORT}"
    # Get actual running image version
    RUNNING_VERSION=$(docker inspect tdarr-node 2>/dev/null | grep '"Image":' | cut -d':' -f3 | cut -d'"' -f1 2>/dev/null || echo "unknown")
    echo "      Version:   ${RUNNING_VERSION}"
    
    # Test server connection
    echo ""
    echo "   🔗 Server Connection:"
    if timeout 5 bash -c "</dev/tcp/$SERVER_IP/$SERVER_PORT" 2>/dev/null; then
        echo "      ✅ Can reach Tdarr server at ${SERVER_IP}:${SERVER_PORT}"
    else
        echo "      ❌ Cannot reach Tdarr server at ${SERVER_IP}:${SERVER_PORT}"
    fi
    
    # Check node status in logs
    echo ""
    echo "   📊 Node Status:"
    if docker logs tdarr-node --tail 20 2>/dev/null | grep -q -i "connected\|registered\|ready"; then
        echo "      ✅ Node appears connected to server"
    elif docker logs tdarr-node --tail 20 2>/dev/null | grep -q -i "error\|failed\|timeout"; then
        echo "      ⚠️  Node may have issues - check logs"
    else
        echo "      ⚠️  Node status unclear"
    fi
    
    echo ""
    echo "   🌐 Check node in server: http://${SERVER_IP}:8265"
else
    print_warning "Tdarr node is STOPPED"
    echo "   Start with: ./start-tdarr-node.sh"
fi
echo ""

# System Resources
print_section "💻 System Resources:"
echo "   CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "   Memory:    $(free -h | awk '/^Mem:/ {printf "%s/%s (%.1f%%)", $3, $2, ($3/$2)*100}')"
echo "   Disk:      $(df -h / | awk 'NR==2 {printf "%s/%s (%s used)", $3, $2, $5}')"

if [ -d "/srv/printstack" ]; then
    echo "   PrintStack: $(du -sh /srv/printstack 2>/dev/null | cut -f1)"
fi
echo ""

# Share Status
print_section "📁 Share Directory Status:"
if [ -d "/share" ]; then
    echo "   /share:       ✅ $(df -h /share 2>/dev/null | tail -1 | awk '{print $4" available"}' || echo "Mounted")"
    echo "   Contents:     $(ls -la /share 2>/dev/null | wc -l) items"
    
    if [ -d "/share/trans" ]; then
        echo "   /share/trans: ✅ $(ls /share/trans 2>/dev/null | wc -l) items"
    else
        echo "   /share/trans: ❌ Not found (will be created when needed)"
    fi
else
    print_error "/share directory not mounted"
    echo "   Tdarr node requires /share to be mounted"
fi
echo ""

# Camera Status
print_section "📹 Camera Status:"
if [ -c "/dev/video0" ]; then
    print_status "Camera device found at /dev/video0"
    if command -v v4l2-ctl &> /dev/null; then
        CAMERA_INFO=$(v4l2-ctl --device=/dev/video0 --info 2>/dev/null | grep "Card type" | cut -d':' -f2 | xargs)
        echo "   Device: ${CAMERA_INFO:-Unknown}"
    fi
else
    print_warning "No camera found at /dev/video0"
    echo "   Connect USB camera for timelapse/monitoring"
fi
echo ""

# Network Status
print_section "🌐 Network Status:"
echo "   IP Address: ${PI_IP}"
echo "   Hostname:   $(hostname)"

# Test key network connections
echo "   Internet:   $(ping -c1 8.8.8.8 >/dev/null 2>&1 && echo "✅ Connected" || echo "❌ No connection")"

if [ "$TDARR_RUNNING" = true ]; then
    echo "   Tdarr Server: $(timeout 3 bash -c "</dev/tcp/$SERVER_IP/$SERVER_PORT" 2>/dev/null && echo "✅ Reachable" || echo "❌ Unreachable")"
fi
echo ""

# Quick Actions
print_section "🔧 Quick Actions:"
echo "   Start printing:    ./start-klipper-stack.sh"
echo "   Start transcoding: ./start-tdarr-node.sh" 
echo "   Stop all:          ./stop-all-services.sh"
echo "   View logs:         docker logs <container-name> -f"
echo "   Full setup:        ./setup-printstack.sh"