#!/bin/bash

# Enhanced Waypipe Setup Script
# A comprehensive, cross-distro installer for Waypipe client and server.
# Version 2.0 
#
# This script installs and configures Waypipe for remote Wayland application
# forwarding over SSH.

set -eo pipefail

# --- Style and Color Configuration ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --- Global Variables ---
PKG_MANAGER=""
PKG_INSTALL=""
PKG_UPDATE=""
LOG_FILE="waypipe_setup_$(date +%Y-%m-%d_%H-%M-%S).txt"

# --- Helper Functions ---

# Function to log messages to a file and console
log_message() {
    local level="$1"; shift
    local message="$*"
    local timestamp
    timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    # Write clean message to log file
    echo "$timestamp [$level] $message" >> "$LOG_FILE"
    # Write colorized message to console
    case "$level" in
        INFO) echo -e "${BLUE}ℹ️  [INFO]${NC} $message" ;;
        SUCCESS) echo -e "${GREEN}✅ [SUCCESS]${NC} $message" ;;
        WARN) echo -e "${YELLOW}⚠️  [WARN]${NC} $message" ;;
        ERROR) echo -e "${RED}❌ [ERROR]${NC} $message" ;;
    esac
}

# Function to check for sudo privileges
check_sudo() {
    if [[ "$EUID" -eq 0 ]]; then
        log_message "ERROR" "This script should not be run as root. Run as a regular user."
        exit 1
    fi
    if ! command -v sudo &>/dev/null || ! sudo -v; then
        log_message "ERROR" "sudo is required and the current user must have sudo privileges."
        exit 1
    fi
}

# Function to detect the system's package manager
detect_package_manager() {
    log_message "INFO" "Detecting system package manager..."
    if command -v apt &>/dev/null; then
        PKG_MANAGER="apt"; PKG_INSTALL="sudo apt install -y"; PKG_UPDATE="sudo apt update"
    elif command -v dnf &>/dev/null; then
        PKG_MANAGER="dnf"; PKG_INSTALL="sudo dnf install -y"; PKG_UPDATE="sudo dnf check-update || true"
    elif command -v pacman &>/dev/null; then
        PKG_MANAGER="pacman"; PKG_INSTALL="sudo pacman -S --needed --noconfirm"; PKG_UPDATE="sudo pacman -Sy"
    elif command -v zypper &>/dev/null; then
        PKG_MANAGER="zypper"; PKG_INSTALL="sudo zypper install -y"; PKG_UPDATE="sudo zypper refresh"
    else
        log_message "ERROR" "No supported package manager found (apt, dnf, pacman, zypper)."
        exit 1
    fi
    log_message "SUCCESS" "Detected Package Manager: $PKG_MANAGER"
}

# Check if running in a Wayland session
check_wayland() {
    log_message "INFO" "Checking for Wayland environment..."
    if [[ -n "$WAYLAND_DISPLAY" ]] || [[ "$XDG_SESSION_TYPE" == "wayland" ]]; then
        log_message "SUCCESS" "Wayland session confirmed."
    else
        log_message "WARN" "Wayland session not detected. This machine may be running X11."
        read -p "Waypipe requires Wayland. Continue anyway? (y/N): " -r choice
        if [[ ! "$choice" =~ ^[Yy]$ ]]; then
            log_message "ERROR" "Installation aborted by user."
            exit 1
        fi
    fi
}

# --- Core Logic ---

# Installs Waypipe and SSH dependencies
install_dependencies() {
    log_message "INFO" "Updating package lists..."
    if ! eval "$PKG_UPDATE"; then log_message "WARN" "Package list update failed, but continuing."; fi

    log_message "INFO" "Installing Waypipe and OpenSSH..."
    local pkgs="waypipe openssh-server openssh-client"
    # Arch uses 'openssh' for both client and server
    if [[ "$PKG_MANAGER" == "pacman" ]]; then pkgs="waypipe openssh"; fi

    if $PKG_INSTALL $pkgs; then
        log_message "SUCCESS" "Waypipe and SSH dependencies installed."
    else
        log_message "ERROR" "Failed to install required packages. Aborting."
        exit 1
    fi
    log_message "INFO" "Waypipe Version: $(waypipe --version 2>&1 | head -n 1)"
}

# Configures the SSH server
configure_server() {
    log_message "INFO" "Configuring SSH server..."
    if command -v systemctl &>/dev/null; then
        if ! systemctl is-active --quiet sshd && ! systemctl is-active --quiet ssh; then
            log_message "INFO" "SSH service is not running. Enabling and starting it now."
            sudo systemctl enable --now sshd 2>/dev/null || sudo systemctl enable --now ssh 2>/dev/null
        fi
        log_message "SUCCESS" "SSH service is active."
    else
        log_message "WARN" "Non-systemd init detected. Please ensure SSH server is running."
    fi

    local sshd_config="/etc/ssh/sshd_config"
    if grep -qE "^\s*X11Forwarding\s+yes" "$sshd_config"; then
        log_message "SUCCESS" "X11Forwarding is already enabled in sshd_config."
    else
        log_message "INFO" "Enabling X11Forwarding in $sshd_config."
        echo "X11Forwarding yes" | sudo tee -a "$sshd_config" > /dev/null
        sudo systemctl restart sshd 2>/dev/null || sudo systemctl restart ssh 2>/dev/null
        log_message "INFO" "SSH service restarted to apply changes."
    fi
}

# Sets up the client's SSH config for easy access
configure_client() {
    log_message "INFO" "Configuring SSH client..."
    mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
    local ssh_config="$HOME/.ssh/config"
    touch "$ssh_config" && chmod 600 "$ssh_config"

    echo
    read -p "Enter the server's hostname or IP address: " server_host
    read -p "Enter the SSH username for the server (default: $USER): " server_user
    server_user=${server_user:-$USER}

    if grep -q "Host waypipe-$server_host" "$ssh_config"; then
        log_message "WARN" "An SSH config entry for '$server_host' already exists. Skipping."
    else
        log_message "INFO" "Adding host entry 'waypipe-$server_host' to $ssh_config"
        cat >> "$ssh_config" << EOF

# Waypipe connection for $server_host
Host waypipe-$server_host
    HostName $server_host
    User $server_user
    ForwardX11 yes
    Compression yes
EOF
        log_message "SUCCESS" "SSH config updated. Connect with: ssh waypipe-$server_host"
    fi
}

# --- Main Functions ---

# Function to perform the server-side setup
run_server_setup() {
    display_header
    log_message "INFO" "Starting Waypipe Server Setup..."
    check_wayland
    install_dependencies
    configure_server
    echo
    log_message "SUCCESS" "Server setup complete."
    echo -e "This machine is now ready to serve Wayland applications."
    sleep 3
}

# Function to perform the client-side setup
run_client_setup() {
    display_header
    log_message "INFO" "Starting Waypipe Client Setup..."
    check_wayland
    install_dependencies
    configure_client
    echo
    log_message "SUCCESS" "Client setup complete."
    echo -e "You can now connect to a configured server using: waypipe ssh <server> <command>"
    sleep 3
}

# Display final usage instructions
show_instructions() {
    local ip_addr
    ip_addr=$(hostname -I | awk '{print $1}')
    display_header
    echo -e "${BOLD}${GREEN}Waypipe Setup Finished! Here's how to use it:${NC}\n"
    echo -e "${BOLD}${CYAN}To run an application (like 'gedit') from a configured server:${NC}"
    echo -e "On your CLIENT machine, run the following command:"
    echo -e "${YELLOW}  waypipe --compress lz4 ssh waypipe-<your_server_hostname> gedit${NC}\n"
    echo -e "${BOLD}${CYAN}Breakdown:${NC}"
    echo -e "  • ${YELLOW}waypipe --compress lz4${NC}: Runs Waypipe with lz4 compression (recommended)."
    echo -e "  • ${YELLOW}ssh waypipe-<your_server_hostname>${NC}: Connects to your server via the created SSH alias."
    echo -e "  • ${YELLOW}gedit${NC}: The application to run on the server and display on the client.\n"
    echo -e "Your server's IP address appears to be: ${BOLD}$ip_addr${NC}"
    echo -e "The log for this session is located at: ${BOLD}$LOG_FILE${NC}"
    echo -e "\nPress any key to exit."
    read -n 1 -s
}

# --- UI and Script Entry ---

display_header() {
    clear
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo -e "${BOLD}${CYAN}            Waypipe Setup Script (v2.0)              ${NC}"
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo
}

main_menu() {
    display_header
    echo -e "This script installs Waypipe for forwarding Wayland applications."
    echo -e "It needs to be run on both the machine serving the app (Server) and displaying it (Client).\n"
    echo -e "  ${MAGENTA}1)${NC} Setup this machine as a ${BOLD}Server${NC}"
    echo -e "  ${MAGENTA}2)${NC} Setup this machine as a ${BOLD}Client${NC}"
    echo -e "  ${MAGENTA}3)${NC} Setup this machine as ${BOLD}Both${NC} (for local testing or symmetrical use)"
    echo -e "  ${MAGENTA}q)${NC} ${BOLD}Quit${NC}\n"
    read -p "Select an option: " -r choice

    case "$choice" in
        1) run_server_setup ;;
        2) run_client_setup ;;
        3) run_server_setup; run_client_setup ;;
        q|Q) log_message "INFO" "Exiting."; exit 0 ;;
        *) log_message "ERROR" "Invalid option."; sleep 1; main_menu ;;
    esac
}

# --- Script Entry Point ---
main() {
    check_sudo
    detect_package_manager
    main_menu
    show_instructions
}

# Initialize log file and run main function
init_log() {
    echo "=== Waypipe Setup Log - $(date) ===" > "$LOG_FILE"
    log_message "INFO" "Script started. Log file: $LOG_FILE"
}

init_log
main