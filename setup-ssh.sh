#!/bin/bash
# =============================================================================
# SSH Setup Script
# 
# Enables SSH server and displays connection information
# Supports: Arch Linux, Debian, Ubuntu, Fedora, SteamOS, and Bazzite
# =============================================================================

set -Eeo pipefail

# Terminal colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly MAGENTA='\033[0;35m'
readonly NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${MAGENTA}  $*${NC}"
    echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

log() {
    local level="$1"
    shift
    local message="$*"
    
    case "$level" in
        "INFO")  color="$GREEN" ;;
        "WARN")  color="$YELLOW" ;;
        "ERROR") color="$RED" ;;
        "SUCCESS") color="$CYAN" ;;
        *)       color="$NC" ;;
    esac
    
    echo -e "${color}[$level]${NC} $message"
}

# Detect distribution
detect_distribution() {
    if [ ! -f /etc/os-release ]; then
        log "ERROR" "Cannot detect distribution: /etc/os-release not found"
        exit 1
    fi
    
    source /etc/os-release
    
    case "$ID" in
        arch|manjaro)
            DISTRO="arch"
            PKG_MANAGER="pacman"
            SSH_SERVICE="sshd"
            ;;
        steamos)
            DISTRO="steamos"
            PKG_MANAGER="pacman"
            SSH_SERVICE="sshd"
            IS_READONLY_FS=true
            ;;
        debian|ubuntu)
            DISTRO="debian"
            PKG_MANAGER="apt"
            SSH_SERVICE="ssh"
            ;;
        fedora)
            DISTRO="fedora"
            PKG_MANAGER="dnf"
            SSH_SERVICE="sshd"
            ;;
        bazzite*)
            DISTRO="bazzite"
            PKG_MANAGER="rpm-ostree"
            SSH_SERVICE="sshd"
            IS_OSTREE=true
            ;;
        *)
            if [[ "$ID_LIKE" == *"arch"* ]]; then
                DISTRO="arch"
                PKG_MANAGER="pacman"
                SSH_SERVICE="sshd"
            elif [[ "$ID_LIKE" == *"debian"* ]] || [[ "$ID_LIKE" == *"ubuntu"* ]]; then
                DISTRO="debian"
                PKG_MANAGER="apt"
                SSH_SERVICE="ssh"
            elif [[ "$ID_LIKE" == *"fedora"* ]]; then
                DISTRO="fedora"
                PKG_MANAGER="dnf"
                SSH_SERVICE="sshd"
            else
                log "ERROR" "Unsupported distribution: $ID"
                exit 1
            fi
            ;;
    esac
    
    log "INFO" "Distribution: $DISTRO ($ID $VERSION_ID)"
}

# Install OpenSSH server
install_openssh() {
    log "INFO" "Checking OpenSSH server installation..."
    
    case "$DISTRO" in
        arch|steamos)
            if ! pacman -Q openssh &>/dev/null; then
                log "INFO" "Installing OpenSSH server..."
                
                if [ "$IS_READONLY_FS" = true ]; then
                    log "WARN" "Read-only filesystem detected (SteamOS)"
                    log "WARN" "Disabling read-only mode temporarily..."
                    sudo steamos-readonly disable
                fi
                
                sudo pacman -Sy --needed --noconfirm openssh
                
                if [ "$IS_READONLY_FS" = true ]; then
                    sudo steamos-readonly enable
                fi
            else
                log "INFO" "OpenSSH server already installed"
            fi
            ;;
        debian)
            if ! dpkg -l openssh-server &>/dev/null; then
                log "INFO" "Installing OpenSSH server..."
                sudo apt-get update
                sudo apt-get install -y openssh-server
            else
                log "INFO" "OpenSSH server already installed"
            fi
            ;;
        fedora)
            if ! rpm -q openssh-server &>/dev/null; then
                log "INFO" "Installing OpenSSH server..."
                sudo dnf install -y openssh-server
            else
                log "INFO" "OpenSSH server already installed"
            fi
            ;;
        bazzite)
            if [ "$IS_OSTREE" = true ]; then
                if ! rpm -q openssh-server &>/dev/null; then
                    log "INFO" "Installing OpenSSH server with rpm-ostree..."
                    sudo rpm-ostree install -y openssh-server
                    log "WARN" "A reboot is required to complete installation"
                    log "WARN" "After reboot, re-run this script to complete setup"
                    exit 0
                else
                    log "INFO" "OpenSSH server already installed"
                fi
            fi
            ;;
    esac
    
    log "SUCCESS" "OpenSSH server installed"
}

# Enable and start SSH service
enable_ssh_service() {
    log "INFO" "Enabling SSH service..."
    
    if systemctl is-enabled "$SSH_SERVICE" &>/dev/null; then
        log "INFO" "SSH service already enabled"
    else
        sudo systemctl enable "$SSH_SERVICE"
        log "SUCCESS" "SSH service enabled"
    fi
    
    if systemctl is-active "$SSH_SERVICE" &>/dev/null; then
        log "INFO" "SSH service already running"
    else
        sudo systemctl start "$SSH_SERVICE"
        log "SUCCESS" "SSH service started"
    fi
    
    # Verify service is running
    if systemctl is-active "$SSH_SERVICE" &>/dev/null; then
        log "SUCCESS" "SSH service is running"
    else
        log "ERROR" "Failed to start SSH service"
        sudo systemctl status "$SSH_SERVICE"
        exit 1
    fi
}

# Get network information
get_network_info() {
    print_header "SSH Connection Information"
    
    # Get username
    USERNAME="$USER"
    
    # Get all IP addresses (excluding loopback)
    echo -e "${CYAN}Available IP Addresses:${NC}"
    echo ""
    
    # Use ip command to get addresses
    if command -v ip &>/dev/null; then
        while IFS= read -r line; do
            if [[ $line =~ inet\ ([0-9.]+) ]]; then
                local ip="${BASH_REMATCH[1]}"
                if [[ ! $ip =~ ^127\. ]]; then
                    local iface=$(echo "$line" | grep -oP '(?<=inet ).*(?=/)')
                    local iface_name=$(ip -o link show | grep -B1 "$iface" | head -1 | awk '{print $2}' | sed 's/://')
                    echo -e "  ${GREEN}$ip${NC}  (${iface_name:-unknown})"
                fi
            fi
        done < <(ip -4 addr show | grep -v "scope host")
    elif command -v hostname &>/dev/null; then
        hostname -I | tr ' ' '\n' | while read -r ip; do
            if [[ ! $ip =~ ^127\. ]] && [[ -n $ip ]]; then
                echo -e "  ${GREEN}$ip${NC}"
            fi
        done
    fi
    
    echo ""
    echo -e "${CYAN}SSH Connection Command:${NC}"
    
    # Get primary IP (first non-localhost)
    PRIMARY_IP=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v "^127\." | head -1)
    
    if [ -n "$PRIMARY_IP" ]; then
        echo -e "  ${YELLOW}ssh $USERNAME@$PRIMARY_IP${NC}"
    else
        echo -e "  ${YELLOW}ssh $USERNAME@<IP_ADDRESS>${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}SSH Port:${NC}"
    SSH_PORT=$(sudo ss -tlnp | grep sshd | grep -oP ':\K\d+' | head -1)
    if [ -n "$SSH_PORT" ]; then
        echo -e "  ${GREEN}$SSH_PORT${NC} (default)"
    else
        echo -e "  ${GREEN}22${NC} (default)"
    fi
    
    echo ""
    echo -e "${CYAN}Hostname:${NC}"
    echo -e "  ${GREEN}$(hostname)${NC}"
    
    echo ""
}

# Check firewall
check_firewall() {
    log "INFO" "Checking firewall configuration..."
    
    # Check if firewalld is running
    if systemctl is-active firewalld &>/dev/null; then
        log "INFO" "Firewalld is active"
        if ! sudo firewall-cmd --list-services | grep -q ssh; then
            log "WARN" "SSH not allowed in firewall, adding..."
            sudo firewall-cmd --permanent --add-service=ssh
            sudo firewall-cmd --reload
            log "SUCCESS" "SSH added to firewall"
        else
            log "INFO" "SSH already allowed in firewall"
        fi
    # Check if ufw is running
    elif command -v ufw &>/dev/null && sudo ufw status | grep -q "Status: active"; then
        log "INFO" "UFW is active"
        if ! sudo ufw status | grep -q "22/tcp.*ALLOW"; then
            log "WARN" "SSH not allowed in firewall, adding..."
            sudo ufw allow ssh
            log "SUCCESS" "SSH added to firewall"
        else
            log "INFO" "SSH already allowed in firewall"
        fi
    else
        log "INFO" "No active firewall detected"
    fi
}

# Main execution
main() {
    print_header "SSH Setup Script"
    
    # Check if running as root (should not be)
    if [ "$EUID" -eq 0 ]; then
        log "ERROR" "This script should not be run as root"
        log "ERROR" "Run as a normal user - sudo will be used when needed"
        exit 1
    fi
    
    detect_distribution
    install_openssh
    enable_ssh_service
    check_firewall
    get_network_info
    
    print_header "Setup Complete!"
    echo -e "${GREEN}✓${NC} SSH server is running and ready for connections"
    echo ""
}

main "$@"
