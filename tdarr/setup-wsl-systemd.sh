#!/bin/bash
# ============================================================================
# WSL Systemd and Tdarr Node Setup Script
# ============================================================================
# Purpose: Enable systemd, install Docker/autofs, configure Tdarr Node
# Usage: sudo bash ./setup-wsl-systemd.sh
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
AUTOFS_DIR="$SCRIPT_DIR/autofs"
TDARR_ENV="$SCRIPT_DIR/tdarr.env"
SHARES_ENV="$AUTOFS_DIR/shares.env"
STATUS_SCRIPT="$SCRIPT_DIR/check-wsl-status.sh"

# Helper functions
log_header() { echo -e "\n${CYAN}========================================${NC}"; echo -e "${CYAN}$1${NC}"; echo -e "${CYAN}========================================${NC}\n"; }
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "This script must be run with sudo"
    log_info "Usage: sudo bash $0"
    exit 1
fi

# Get the actual user (not root when using sudo)
ACTUAL_USER="${SUDO_USER:-$(logname 2>/dev/null || echo $USER)}"
ACTUAL_HOME=$(eval echo "~$ACTUAL_USER")

log_header "WSL Systemd & Tdarr Setup"
log_info "Running as: root"
log_info "Target user: $ACTUAL_USER"
log_info "User home: $ACTUAL_HOME"

# ============================================================================
# Enable systemd in WSL
# ============================================================================
log_header "Enabling systemd in WSL"

if [ ! -f /etc/wsl.conf ]; then
    log_info "Creating /etc/wsl.conf..."
    cat > /etc/wsl.conf << 'EOF'
[boot]
systemd=true

[network]
generateResolvConf=true
EOF
    log_success "/etc/wsl.conf created"
else
    if grep -q "^\[boot\]" /etc/wsl.conf && grep -q "^systemd=true" /etc/wsl.conf; then
        log_success "systemd already enabled in /etc/wsl.conf"
    else
        log_info "Updating /etc/wsl.conf to enable systemd..."
        if ! grep -q "^\[boot\]" /etc/wsl.conf; then
            echo -e "\n[boot]\nsystemd=true" >> /etc/wsl.conf
        else
            sed -i '/^\[boot\]/a systemd=true' /etc/wsl.conf
        fi
        log_success "/etc/wsl.conf updated"
    fi
fi

# Check if systemd is currently active
if [ "$(ps -p 1 -o comm=)" != "systemd" ]; then
    log_warn "systemd is not currently active (PID 1 is $(ps -p 1 -o comm=))"
    log_warn "You must restart WSL for systemd to activate"
    log_info "From Windows PowerShell, run: wsl.exe --shutdown"
    SYSTEMD_ACTIVE=false
else
    log_success "systemd is active"
    SYSTEMD_ACTIVE=true
fi

# ============================================================================
# Install Required Packages
# ============================================================================
log_header "Installing Required Packages"

log_info "Updating package database..."
pacman -Sy --noconfirm

PACKAGES="docker autofs cifs-utils nfs-utils iproute2"
log_info "Installing: $PACKAGES"
pacman -S --needed --noconfirm $PACKAGES

log_success "All packages installed"

# ============================================================================
# Configure Docker
# ============================================================================
log_header "Configuring Docker"

# Ensure docker group exists
if ! getent group docker > /dev/null; then
    log_info "Creating docker group..."
    groupadd docker
fi

# Add user to docker group
if ! groups "$ACTUAL_USER" | grep -q '\<docker\>'; then
    log_info "Adding $ACTUAL_USER to docker group..."
    usermod -aG docker "$ACTUAL_USER"
    log_success "User added to docker group (re-login required for effect)"
else
    log_success "$ACTUAL_USER already in docker group"
fi

# Enable and start docker if systemd is active
if [ "$SYSTEMD_ACTIVE" = true ]; then
    log_info "Enabling docker service..."
    systemctl enable docker
    
    if systemctl is-active --quiet docker; then
        log_success "Docker service is already running"
    else
        log_info "Starting docker service..."
        systemctl start docker
        log_success "Docker service started"
    fi
else
    log_warn "systemd not active - docker service will be enabled after WSL restart"
fi

# ============================================================================
# Configure Autofs for /share
# ============================================================================
log_header "Configuring Autofs"

# Create autofs directory
mkdir -p "$AUTOFS_DIR"
chown "$ACTUAL_USER:$ACTUAL_USER" "$AUTOFS_DIR"

# Create shares.env template if it doesn't exist
if [ ! -f "$SHARES_ENV" ]; then
    log_info "Creating autofs configuration template: $SHARES_ENV"
    cat > "$SHARES_ENV" << 'EOF'
# Autofs Configuration for /share mount
# Edit this file with your NAS/server details

# Mount type: cifs (SMB/CIFS) or nfs
MOUNT_TYPE=cifs

# === CIFS/SMB Configuration ===
# Server IP or hostname
SHARE_SERVER=192.168.1.210

# Share name on server
SHARE_NAME=share

# CIFS credentials
CIFS_USERNAME=me
CIFS_PASSWORD=Jbean343343343
CIFS_DOMAIN=

# === NFS Configuration ===
# NFS export path (format: SERVER:/export/path)
# NFS_EXPORT=192.168.1.210:/mnt/pool/share

# Mount point (should be /share for Tdarr compatibility)
MOUNTPOINT=/share
EOF
    chown "$ACTUAL_USER:$ACTUAL_USER" "$SHARES_ENV"
    log_success "Configuration template created"
    log_warn "Edit $SHARES_ENV with your actual server details before continuing"
    log_info "Press Enter to continue after editing, or Ctrl+C to abort..."
    read -r
fi

# Load configuration
log_info "Loading autofs configuration from $SHARES_ENV"
source "$SHARES_ENV"

# Create mount point
if [ ! -d "$MOUNTPOINT" ]; then
    log_info "Creating mount point: $MOUNTPOINT"
    mkdir -p "$MOUNTPOINT"
fi

# Configure autofs based on mount type
mkdir -p /etc/autofs/auto.master.d

if [ "$MOUNT_TYPE" = "cifs" ]; then
    log_info "Configuring CIFS/SMB mount..."
    
    # Create credentials file
    CREDS_FILE="/etc/auto.shares.credentials"
    cat > "$CREDS_FILE" << EOF
username=$CIFS_USERNAME
password=$CIFS_PASSWORD
${CIFS_DOMAIN:+domain=$CIFS_DOMAIN}
EOF
    chmod 600 "$CREDS_FILE"
    log_success "Credentials file created: $CREDS_FILE"
    
    # Create autofs map file
    cat > /etc/auto.shares << EOF
# Autofs map for /share (CIFS)
$MOUNTPOINT -fstype=cifs,credentials=$CREDS_FILE,uid=1000,gid=1000,iocharset=utf8,file_mode=0664,dir_mode=0775,soft,nounix,noserverino,vers=3.0 ://$SHARE_SERVER/$SHARE_NAME
EOF
    
elif [ "$MOUNT_TYPE" = "nfs" ]; then
    log_info "Configuring NFS mount..."
    
    # Create autofs map file
    cat > /etc/auto.shares << EOF
# Autofs map for /share (NFS)
$MOUNTPOINT -fstype=nfs4,soft,timeo=60,retrans=2,rw,proto=tcp,nfsvers=4.2,rsize=1048576,wsize=1048576 $NFS_EXPORT
EOF
    
else
    log_error "Invalid MOUNT_TYPE: $MOUNT_TYPE (must be 'cifs' or 'nfs')"
    exit 1
fi

log_success "Autofs map created: /etc/auto.shares"

# Create master file entry
cat > /etc/autofs/auto.master.d/shares.autofs << EOF
# Autofs master entry for /share
/- /etc/auto.shares --timeout=300
EOF

log_success "Autofs master entry created"

# Enable and start autofs if systemd is active
if [ "$SYSTEMD_ACTIVE" = true ]; then
    log_info "Enabling autofs service..."
    systemctl enable autofs
    
    log_info "Reloading autofs configuration..."
    systemctl restart autofs
    
    sleep 2
    
    # Test mount
    log_info "Testing autofs mount: ls $MOUNTPOINT"
    if timeout 10 ls "$MOUNTPOINT" > /dev/null 2>&1; then
        log_success "Autofs mount test successful!"
    else
        log_warn "Autofs mount test failed - check configuration and network connectivity"
    fi
else
    log_warn "systemd not active - autofs will be enabled after WSL restart"
fi

# ============================================================================
# Create Tdarr Environment File
# ============================================================================
log_header "Configuring Tdarr Node"

if [ ! -f "$TDARR_ENV" ]; then
    log_info "Creating Tdarr environment file: $TDARR_ENV"
    
    HOSTNAME=$(hostname)
    cat > "$TDARR_ENV" << EOF
# Tdarr Node Environment Configuration
# Edit this file to customize your Tdarr Node settings

PUID=1000
PGID=1000
UMASK_SET=002
TZ=UTC

# Tdarr Server connection
TDARR_SERVER_IP=192.168.1.210
TDARR_SERVER_PORT=8266

# Node identification
TDARR_NODE_NAME=${HOSTNAME}-wsl-node

# Tdarr image
TDARR_IMAGE=ghcr.io/haveagitgat/tdarr_node:latest
EOF
    chown "$ACTUAL_USER:$ACTUAL_USER" "$TDARR_ENV"
    log_success "Tdarr environment file created"
else
    log_success "Tdarr environment file already exists"
fi

# ============================================================================
# Create Tdarr Systemd Service
# ============================================================================
log_header "Creating Tdarr Systemd Service"

log_info "Creating /etc/systemd/system/tdarr-node.service..."

cat > /etc/systemd/system/tdarr-node.service << 'EOFSERVICE'
[Unit]
Description=Tdarr Node Container
After=docker.service autofs.service network-online.target
Wants=network-online.target
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
EnvironmentFile=/home/me/betterstrap/tdarr/tdarr.env

# Ensure /share is accessible
ExecStartPre=/bin/bash -c 'timeout 10 ls /share || (echo "ERROR: /share not accessible" && exit 1)'

# Create container if it doesn't exist, then start it
ExecStart=/bin/bash -c '\
  if ! docker inspect tdarr-node >/dev/null 2>&1; then \
    docker run -d \
      --name tdarr-node \
      --restart unless-stopped \
      --network host \
      -e PUID=${PUID} \
      -e PGID=${PGID} \
      -e UMASK_SET=${UMASK_SET} \
      -e TZ=${TZ} \
      -e serverIP=${TDARR_SERVER_IP} \
      -e serverPort=${TDARR_SERVER_PORT} \
      -e nodeName=${TDARR_NODE_NAME} \
      -v /share:/share:rw \
      -v /home/me/Tdarr/configs:/app/configs:rw \
      -v /home/me/Tdarr/logs:/app/logs:rw \
      ${TDARR_IMAGE}; \
  fi && \
  docker start tdarr-node 2>/dev/null || true'

ExecStop=/usr/bin/docker stop tdarr-node

[Install]
WantedBy=multi-user.target
EOFSERVICE

log_success "Systemd service file created"

# Create Tdarr directories
mkdir -p "$ACTUAL_HOME/Tdarr/configs" "$ACTUAL_HOME/Tdarr/logs"
chown -R "$ACTUAL_USER:$ACTUAL_USER" "$ACTUAL_HOME/Tdarr"

# Enable service if systemd is active
if [ "$SYSTEMD_ACTIVE" = true ]; then
    log_info "Enabling tdarr-node service..."
    systemctl daemon-reload
    systemctl enable tdarr-node
    log_success "Tdarr Node service enabled"
else
    log_warn "systemd not active - tdarr-node service will be enabled after WSL restart"
fi

# ============================================================================
# Create Status Check Script
# ============================================================================
log_header "Creating Helper Scripts"

log_info "Creating status check script: $STATUS_SCRIPT"

cat > "$STATUS_SCRIPT" << 'EOFSTATUS'
#!/bin/bash
# Quick status check for WSL Tdarr setup

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}WSL Tdarr Status Check${NC}"
echo -e "${CYAN}========================================${NC}\n"

# Check systemd
if [ "$(ps -p 1 -o comm=)" = "systemd" ]; then
    echo -e "${GREEN}[OK]${NC} Systemd is active"
else
    echo -e "${RED}[ERROR]${NC} Systemd is NOT active (PID 1 is $(ps -p 1 -o comm=))"
    echo -e "${YELLOW}[WARN]${NC} Run 'wsl.exe --shutdown' from Windows, then restart WSL"
    exit 1
fi

# Check services
for service in docker autofs tdarr-node; do
    if systemctl is-active --quiet $service; then
        echo -e "${GREEN}[OK]${NC} $service service is running"
    else
        echo -e "${RED}[ERROR]${NC} $service service is NOT running"
        echo -e "${YELLOW}[WARN]${NC} Try: sudo systemctl start $service"
    fi
done

# Check Docker
if docker info >/dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC} Docker daemon is accessible"
else
    echo -e "${RED}[ERROR]${NC} Docker daemon is not accessible"
fi

# Check Tdarr container
if docker ps --format '{{.Names}}' | grep -q '^tdarr-node$'; then
    echo -e "${GREEN}[OK]${NC} Tdarr Node container is running"
else
    echo -e "${YELLOW}[WARN]${NC} Tdarr Node container is not running"
    echo -e "${YELLOW}[WARN]${NC} Try: ~/betterstrap/tdarr/start-tdarr-wsl.sh"
fi

# Check /share mount
if timeout 5 ls /share >/dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC} /share is accessible"
else
    echo -e "${RED}[ERROR]${NC} /share is not accessible"
    echo -e "${YELLOW}[WARN]${NC} Check autofs configuration and network"
fi

# Show IP
WSL_IP=$(hostname -I | awk '{print $1}')
echo -e "\n${CYAN}WSL IP Address:${NC} ${YELLOW}$WSL_IP${NC}"

echo -e "\n${CYAN}========================================${NC}\n"
EOFSTATUS

chmod +x "$STATUS_SCRIPT"
chown "$ACTUAL_USER:$ACTUAL_USER" "$STATUS_SCRIPT"
log_success "Status script created"

# ============================================================================
# Get WSL IP Address
# ============================================================================
log_header "Network Information"

WSL_IP=$(hostname -I | awk '{print $1}')
if [ -n "$WSL_IP" ]; then
    log_success "WSL IP Address: $WSL_IP"
else
    log_warn "Could not determine WSL IP address"
fi

# ============================================================================
# Final Instructions
# ============================================================================
log_header "Setup Complete!"

log_success "✓ Systemd enabled in /etc/wsl.conf"
log_success "✓ Docker installed and configured"
log_success "✓ Autofs configured for /share"
log_success "✓ Tdarr Node systemd service created"
log_success "✓ Helper scripts created"

echo -e "\n${CYAN}========================================${NC}"
echo -e "${CYAN}IMPORTANT: Next Steps${NC}"
echo -e "${CYAN}========================================${NC}\n"

if [ "$SYSTEMD_ACTIVE" = false ]; then
    log_warn "Systemd is not currently active!"
    echo -e "${YELLOW}1. Exit WSL and restart it to activate systemd${NC}"
    echo -e "${YELLOW}   From Windows PowerShell, run:${NC}"
    echo -e "${GREEN}   wsl.exe --shutdown${NC}"
    echo -e "${GREEN}   wsl${NC}\n"
    echo -e "${YELLOW}2. After WSL restarts, check status:${NC}"
    echo -e "${GREEN}   $STATUS_SCRIPT${NC}\n"
else
    log_info "Systemd is active - attempting to start services now..."
    systemctl start docker autofs 2>/dev/null || true
    sleep 2
    
    echo -e "\n${YELLOW}Check status:${NC}"
    echo -e "${GREEN}   $STATUS_SCRIPT${NC}\n"
    
    echo -e "${YELLOW}Start Tdarr manually (if needed):${NC}"
    echo -e "${GREEN}   ~/betterstrap/tdarr/start-tdarr-wsl.sh${NC}\n"
fi

echo -e "${CYAN}Configuration Files:${NC}"
echo -e "  • Autofs config: ${YELLOW}$SHARES_ENV${NC}"
echo -e "  • Tdarr config: ${YELLOW}$TDARR_ENV${NC}"
echo -e "  • Status check: ${YELLOW}$STATUS_SCRIPT${NC}\n"

if [ -n "$WSL_IP" ]; then
    echo -e "${CYAN}SSH to WSL:${NC}"
    echo -e "  From Windows: ${GREEN}wsl${NC}"
    echo -e "  WSL IP: ${YELLOW}$WSL_IP${NC}\n"
fi

log_success "Setup script completed successfully!"
