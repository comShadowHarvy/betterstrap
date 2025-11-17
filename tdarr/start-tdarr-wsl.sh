#!/bin/bash
# ============================================================================
# Start Tdarr Node in WSL
# ============================================================================
# Purpose: Ensure Docker, autofs, and Tdarr Node are running
# Usage: bash ./start-tdarr-wsl.sh  (or sudo if docker requires it)
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TDARR_ENV="$SCRIPT_DIR/tdarr.env"

# Helper functions
log_header() { echo -e "\n${CYAN}========================================${NC}"; echo -e "${CYAN}$1${NC}"; echo -e "${CYAN}========================================${NC}\n"; }
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

log_header "Tdarr Node Startup Script"

# Check if systemd is active
SYSTEMD_ACTIVE=false
if [ "$(ps -p 1 -o comm=)" = "systemd" ]; then
    log_success "Systemd is active"
    SYSTEMD_ACTIVE=true
else
    log_warn "Systemd is NOT active (PID 1 is $(ps -p 1 -o comm=))"
    log_warn "Some features may not work correctly"
    log_info "To enable systemd: run setup-wsl-systemd.sh and restart WSL"
fi

# ============================================================================
# Start Docker
# ============================================================================
log_header "Starting Docker"

if command -v systemctl >/dev/null 2>&1 && [ "$SYSTEMD_ACTIVE" = true ]; then
    log_info "Using systemd to manage Docker..."
    
    if systemctl is-active --quiet docker; then
        log_success "Docker service is already running"
    else
        log_info "Starting Docker service..."
        sudo systemctl start docker
        sleep 3
        
        if systemctl is-active --quiet docker; then
            log_success "Docker service started"
        else
            log_error "Failed to start Docker service"
            exit 1
        fi
    fi
else
    log_warn "systemd not available, attempting manual Docker start..."
    
    if docker info >/dev/null 2>&1; then
        log_success "Docker daemon is already running"
    else
        log_info "Starting dockerd manually..."
        sudo nohup dockerd >/var/log/dockerd.log 2>&1 &
        
        # Wait for Docker to be ready
        for i in {1..30}; do
            if docker info >/dev/null 2>&1; then
                log_success "Docker daemon started"
                break
            fi
            sleep 1
        done
        
        if ! docker info >/dev/null 2>&1; then
            log_error "Failed to start Docker daemon"
            log_info "Check /var/log/dockerd.log for errors"
            exit 1
        fi
    fi
fi

# Verify Docker is accessible
if ! docker info >/dev/null 2>&1; then
    log_error "Docker daemon is not accessible"
    log_info "Try running with sudo or check docker group membership"
    exit 1
fi

log_success "Docker is ready"

# ============================================================================
# Start Autofs
# ============================================================================
log_header "Starting Autofs"

if command -v systemctl >/dev/null 2>&1 && [ "$SYSTEMD_ACTIVE" = true ]; then
    log_info "Using systemd to manage autofs..."
    
    if systemctl is-active --quiet autofs; then
        log_success "Autofs service is already running"
    else
        log_info "Starting autofs service..."
        sudo systemctl start autofs
        sleep 2
        
        if systemctl is-active --quiet autofs; then
            log_success "Autofs service started"
        else
            log_warn "Failed to start autofs service"
        fi
    fi
else
    log_warn "systemd not available - autofs requires systemd"
    log_warn "Autofs will not be available until systemd is enabled"
fi

# Test /share accessibility
log_info "Testing /share accessibility..."
if timeout 10 ls /share >/dev/null 2>&1; then
    log_success "/share is accessible"
else
    log_error "/share is NOT accessible"
    log_warn "Tdarr Node may not function correctly without /share"
    log_info "Check autofs configuration and network connectivity"
fi

# ============================================================================
# Start/Create Tdarr Node Container
# ============================================================================
log_header "Starting Tdarr Node Container"

# Load Tdarr environment
if [ -f "$TDARR_ENV" ]; then
    log_info "Loading Tdarr configuration from $TDARR_ENV"
    source "$TDARR_ENV"
else
    log_warn "Tdarr environment file not found: $TDARR_ENV"
    log_warn "Using default values..."
    PUID=1000
    PGID=1000
    UMASK_SET=002
    TZ=UTC
    TDARR_SERVER_IP=192.168.1.210
    TDARR_SERVER_PORT=8266
    TDARR_NODE_NAME="$(hostname)-wsl-node"
    TDARR_IMAGE="ghcr.io/haveagitgat/tdarr_node:latest"
fi

# Check if container exists
if docker inspect tdarr-node >/dev/null 2>&1; then
    log_info "Tdarr Node container exists"
    
    # Check if it's running
    if docker ps --format '{{.Names}}' | grep -q '^tdarr-node$'; then
        log_success "Tdarr Node container is already running"
    else
        log_info "Starting Tdarr Node container..."
        docker start tdarr-node
        sleep 3
        
        if docker ps --format '{{.Names}}' | grep -q '^tdarr-node$'; then
            log_success "Tdarr Node container started"
        else
            log_error "Failed to start Tdarr Node container"
            log_info "Check container logs: docker logs tdarr-node"
            exit 1
        fi
    fi
else
    log_info "Tdarr Node container does not exist, creating it..."
    
    # Ensure Tdarr directories exist
    mkdir -p "$HOME/Tdarr/configs" "$HOME/Tdarr/logs"
    
    # Create and start container
    docker run -d \
        --name tdarr-node \
        --restart unless-stopped \
        --network host \
        -e PUID="$PUID" \
        -e PGID="$PGID" \
        -e UMASK_SET="$UMASK_SET" \
        -e TZ="$TZ" \
        -e serverIP="$TDARR_SERVER_IP" \
        -e serverPort="$TDARR_SERVER_PORT" \
        -e nodeName="$TDARR_NODE_NAME" \
        -v /share:/share:rw \
        -v "$HOME/Tdarr/configs:/app/configs:rw" \
        -v "$HOME/Tdarr/logs:/app/logs:rw" \
        "$TDARR_IMAGE"
    
    sleep 5
    
    if docker ps --format '{{.Names}}' | grep -q '^tdarr-node$'; then
        log_success "Tdarr Node container created and started"
    else
        log_error "Failed to create/start Tdarr Node container"
        log_info "Check container logs: docker logs tdarr-node"
        exit 1
    fi
fi

# ============================================================================
# Status Display
# ============================================================================
log_header "Service Status"

# Show service status if systemd is available
if command -v systemctl >/dev/null 2>&1 && [ "$SYSTEMD_ACTIVE" = true ]; then
    for service in docker autofs tdarr-node; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            log_success "$service service is running"
        else
            log_warn "$service service is not running"
        fi
    done
fi

# Show Docker containers
log_info "Docker containers:"
docker ps --filter "name=tdarr-node" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Show /share status
if mountpoint -q /share 2>/dev/null; then
    log_success "/share is mounted"
elif [ -d /share ] && timeout 5 ls /share >/dev/null 2>&1; then
    log_success "/share is accessible (autofs)"
else
    log_warn "/share is not accessible"
fi

# Get WSL IP
WSL_IP=$(hostname -I | awk '{print $1}')
if [ -n "$WSL_IP" ]; then
    log_info "WSL IP Address: $WSL_IP"
fi

# ============================================================================
# Show Recent Logs
# ============================================================================
log_header "Recent Tdarr Node Logs"

log_info "Last 20 lines from Tdarr Node:"
echo -e "${CYAN}----------------------------------------${NC}"
docker logs tdarr-node --tail 20 2>&1 || log_warn "Could not fetch logs"
echo -e "${CYAN}----------------------------------------${NC}"

# ============================================================================
# Final Status
# ============================================================================
log_header "Startup Complete!"

if docker ps --format '{{.Names}}' | grep -q '^tdarr-node$'; then
    log_success "✓ Tdarr Node is running"
    log_info "Server: http://$TDARR_SERVER_IP:$TDARR_SERVER_PORT"
    log_info "Node Name: $TDARR_NODE_NAME"
    echo -e "\n${CYAN}Management Commands:${NC}"
    echo -e "  View logs:      ${GREEN}docker logs tdarr-node -f${NC}"
    echo -e "  Stop container: ${GREEN}docker stop tdarr-node${NC}"
    echo -e "  Restart:        ${GREEN}docker restart tdarr-node${NC}"
    echo -e "  Check status:   ${GREEN}$SCRIPT_DIR/check-wsl-status.sh${NC}"
else
    log_error "✗ Tdarr Node is not running"
    echo -e "\n${YELLOW}Troubleshooting:${NC}"
    echo -e "  Check logs:     ${GREEN}docker logs tdarr-node${NC}"
    echo -e "  Check /share:   ${GREEN}ls -la /share${NC}"
    echo -e "  Check services: ${GREEN}$SCRIPT_DIR/check-wsl-status.sh${NC}"
    exit 1
fi

echo ""
