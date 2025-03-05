#!/bin/bash
# Waypipe Setup Script - for remote Wayland application forwarding
# This script sets up Waypipe on both server and client machines

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="waypipe_setup_$(date +%Y%m%d_%H%M%S).log"
touch "$LOG_FILE"

# Function to log messages
log() {
    echo "$1" | tee -a "$LOG_FILE"
}

# Function to display success message
success() {
    log "${GREEN}✅ $1${NC}"
}

# Function to display info message
info() {
    log "${BLUE}ℹ️ $1${NC}"
}

# Function to display warning message
warning() {
    log "${YELLOW}⚠️ $1${NC}"
}

# Function to display error message
error() {
    log "${RED}❌ $1${NC}"
    if [ "$2" = "exit" ]; then
        exit 1
    fi
}

# Display banner
display_banner() {
    echo -e "${BOLD}${BLUE}"
    echo "╔═══════════════════════════════════════════════════╗"
    echo "║                 Waypipe Setup                     ║"
    echo "║     Remote Wayland Applications over SSH          ║"
    echo "╚═══════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${CYAN}A comprehensive setup script for Waypipe server and client${NC}\n"
}

# Check for sudo access
check_sudo() {
    info "Checking sudo access..."
    if ! command -v sudo &>/dev/null; then
        error "sudo is not installed. Please install sudo first." "exit"
    fi
    if ! sudo -v &>/dev/null; then
        error "No sudo privileges. Please ensure you have sudo access." "exit"
    fi
    success "Sudo access confirmed"
}

# Function to detect package manager
detect_package_manager() {
    info "Detecting package manager..."
    if command -v apt &>/dev/null; then
        PKG_MANAGER="apt"
        PKG_UPDATE="sudo apt update"
        PKG_INSTALL="sudo apt install -y"
        WAYPIPE_PKG="waypipe"
        success "Detected apt package manager (Debian/Ubuntu)"
    elif command -v dnf &>/dev/null; then
        PKG_MANAGER="dnf"
        PKG_UPDATE="sudo dnf check-update || true" # Prevent non-zero exit code
        PKG_INSTALL="sudo dnf install -y"
        WAYPIPE_PKG="waypipe"
        success "Detected dnf package manager (Fedora)"
    elif command -v pacman &>/dev/null; then
        PKG_MANAGER="pacman"
        PKG_UPDATE="sudo pacman -Sy"
        PKG_INSTALL="sudo pacman -S --needed --noconfirm"
        WAYPIPE_PKG="waypipe"
        success "Detected pacman package manager (Arch Linux)"
    elif command -v zypper &>/dev/null; then
        PKG_MANAGER="zypper"
        PKG_UPDATE="sudo zypper refresh"
        PKG_INSTALL="sudo zypper install -y"
        WAYPIPE_PKG="waypipe"
        success "Detected zypper package manager (openSUSE)"
    else
        error "Unsupported package manager. Cannot proceed with installation." "exit"
    fi
}

# Check for Wayland environment
check_wayland() {
    info "Checking for Wayland environment..."
    
    if [ -n "$WAYLAND_DISPLAY" ]; then
        success "Wayland session detected: $WAYLAND_DISPLAY"
    elif [ "$XDG_SESSION_TYPE" = "wayland" ]; then
        success "Wayland session detected via XDG_SESSION_TYPE"
    else
        warning "Wayland session not detected. This machine may be using X11."
        warning "Waypipe requires Wayland to work properly."
        
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Installation aborted." "exit"
        fi
    fi
}

# Install waypipe and dependencies
install_waypipe() {
    info "Updating package lists..."
    eval "$PKG_UPDATE" || warning "Package update failed, but continuing..."
    
    info "Installing Waypipe and dependencies..."
    case $PKG_MANAGER in
        apt)
            $PKG_INSTALL waypipe ssh openssh-server || error "Failed to install packages" "exit"
            ;;
        dnf)
            $PKG_INSTALL waypipe openssh-server || error "Failed to install packages" "exit"
            ;;
        pacman)
            $PKG_INSTALL waypipe openssh || error "Failed to install packages" "exit"
            ;;
        zypper)
            $PKG_INSTALL waypipe openssh || error "Failed to install packages" "exit"
            ;;
    esac
    
    # Verify waypipe installation
    if ! command -v waypipe &>/dev/null; then
        error "Waypipe installation failed or not in PATH." "exit"
    fi
    
    success "Waypipe installed successfully: $(waypipe --version 2>&1 | head -n 1)"
}

# Configure SSH for Waypipe on server
configure_ssh_server() {
    info "Configuring SSH server for Waypipe..."
    
    # Ensure SSH server is running
    if command -v systemctl &>/dev/null; then
        if ! systemctl is-active --quiet sshd.service && ! systemctl is-active --quiet ssh.service; then
            info "Starting SSH server..."
            if systemctl list-unit-files | grep -q "sshd.service"; then
                sudo systemctl enable --now sshd.service || warning "Failed to enable SSH server"
            elif systemctl list-unit-files | grep -q "ssh.service"; then
                sudo systemctl enable --now ssh.service || warning "Failed to enable SSH server"
            else
                warning "SSH service not found. Please ensure SSH server is installed and running."
            fi
        else
            success "SSH server is already running"
        fi
    else
        warning "systemd not detected. Please ensure SSH server is running manually."
    fi
    
    # Check if SSH server config allows X11Forwarding (needed for some setups)
    SSH_CONFIG="/etc/ssh/sshd_config"
    if [ -f "$SSH_CONFIG" ]; then
        if ! grep -q "^X11Forwarding yes" "$SSH_CONFIG"; then
            info "Enabling X11Forwarding in SSH server config..."
            echo -e "\n# Added by Waypipe setup\nX11Forwarding yes" | sudo tee -a "$SSH_CONFIG" > /dev/null
            
            # Restart SSH server to apply changes
            if command -v systemctl &>/dev/null; then
                if systemctl list-unit-files | grep -q "sshd.service"; then
                    sudo systemctl restart sshd.service || warning "Failed to restart SSH server"
                elif systemctl list-unit-files | grep -q "ssh.service"; then
                    sudo systemctl restart ssh.service || warning "Failed to restart SSH server"
                fi
            else
                warning "Please restart your SSH server manually to apply changes"
            fi
        else
            success "X11Forwarding already enabled in SSH server config"
        fi
    else
        warning "SSH server config not found at $SSH_CONFIG"
    fi
    
    success "SSH server configured for Waypipe"
}

# Setup client SSH config for easy connections
setup_client_ssh_config() {
    info "Setting up SSH client config for Waypipe..."
    
    # Create .ssh directory if it doesn't exist
    if [ ! -d "$HOME/.ssh" ]; then
        mkdir -p "$HOME/.ssh"
        chmod 700 "$HOME/.ssh"
    fi
    
    # Create or update SSH config
    SSH_CONFIG="$HOME/.ssh/config"
    
    # Ask for server details
    read -p "Enter the hostname or IP of your server: " server_host
    read -p "Enter the SSH username for the server (default: $USER): " server_user
    server_user=${server_user:-$USER}
    read -p "Enter the SSH port for the server (default: 22): " server_port
    server_port=${server_port:-22}
    
    # Create a host entry
    echo -e "\nCreating SSH config entry for server '$server_host'..."
    
    cat >> "$SSH_CONFIG" << EOF

# Added by Waypipe setup
Host waypipe-server
    HostName $server_host
    User $server_user
    Port $server_port
    # Compression can improve performance for Waypipe
    Compression yes
    # Forward X11 connections (might be needed for some setups)
    ForwardX11 yes
    # Keep connection alive
    ServerAliveInterval 30
    ServerAliveCountMax 3
EOF
    
    chmod 600 "$SSH_CONFIG"
    success "SSH client config created at $SSH_CONFIG"
    info "You can now connect using: ssh waypipe-server"
}

# Create scripts for easier use
create_helper_scripts() {
    info "Creating helper scripts for Waypipe..."
    
    # Create directory for scripts
    SCRIPT_DIR="$HOME/.local/bin"
    mkdir -p "$SCRIPT_DIR"
    
    # Create server-side launcher script
    SERVER_SCRIPT="$SCRIPT_DIR/waypipe-server-run"
    cat > "$SERVER_SCRIPT" << 'EOF'
#!/bin/bash
# Waypipe server-side launcher script

# Check if an application was specified
if [ $# -eq 0 ]; then
    echo "Usage: $(basename "$0") <application> [arguments]"
    echo "Example: $(basename "$0") firefox"
    exit 1
fi

# Ensure XDG_RUNTIME_DIR is set
if [ -z "$XDG_RUNTIME_DIR" ]; then
    export XDG_RUNTIME_DIR="/run/user/$(id -u)"
fi

# Set appropriate Wayland socket
if [ -n "$WAYLAND_DISPLAY" ]; then
    # Use existing WAYLAND_DISPLAY
    echo "Using Wayland display: $WAYLAND_DISPLAY"
else
    # Try to find a Wayland socket
    for socket in "$XDG_RUNTIME_DIR"/wayland-*; do
        if [ -S "$socket" ]; then
            export WAYLAND_DISPLAY="$(basename "$socket")"
            echo "Setting Wayland display: $WAYLAND_DISPLAY"
            break
        fi
    done
    
    # Default to wayland-0 if not found
    if [ -z "$WAYLAND_DISPLAY" ]; then
        export WAYLAND_DISPLAY="wayland-0"
        echo "Defaulting to Wayland display: $WAYLAND_DISPLAY"
    fi
fi

# Launch the application
echo "Launching: $@"
"$@"
EOF
    
    chmod +x "$SERVER_SCRIPT"
    
    # Create client-side launcher script
    CLIENT_SCRIPT="$SCRIPT_DIR/waypipe-run"
    cat > "$CLIENT_SCRIPT" << 'EOF'
#!/bin/bash
# Waypipe client-side launcher script

# Check if server and application were specified
if [ $# -lt 2 ]; then
    echo "Usage: $(basename "$0") <server> <application> [arguments]"
    echo "Example: $(basename "$0") waypipe-server firefox"
    exit 1
fi

SERVER="$1"
shift

# Ensure XDG_RUNTIME_DIR is set locally
if [ -z "$XDG_RUNTIME_DIR" ]; then
    export XDG_RUNTIME_DIR="/run/user/$(id -u)"
fi

# Set up Wayland socket locally
if [ -z "$WAYLAND_DISPLAY" ]; then
    for socket in "$XDG_RUNTIME_DIR"/wayland-*; do
        if [ -S "$socket" ]; then
            export WAYLAND_DISPLAY="$(basename "$socket")"
            echo "Local Wayland display: $WAYLAND_DISPLAY"
            break
        fi
    done
    
    # Default to wayland-0 if not found
    if [ -z "$WAYLAND_DISPLAY" ]; then
        export WAYLAND_DISPLAY="wayland-0"
        echo "Defaulting to local Wayland display: $WAYLAND_DISPLAY"
    fi
fi

# Run waypipe with SSH to launch the application
echo "Connecting to $SERVER and launching: $@"
waypipe --compress lz4 ssh "$SERVER" "$@"
EOF
    
    chmod +x "$CLIENT_SCRIPT"
    
    # Add scripts to PATH if not already
    if [[ ":$PATH:" != *":$SCRIPT_DIR:"* ]]; then
        echo -e "\n# Added by Waypipe setup\nexport PATH=\"\$PATH:$SCRIPT_DIR\"" >> "$HOME/.bashrc"
        echo -e "\n# Added by Waypipe setup\nexport PATH=\"\$PATH:$SCRIPT_DIR\"" >> "$HOME/.zshrc" 2>/dev/null || true
        
        # Update current PATH
        export PATH="$PATH:$SCRIPT_DIR"
        info "Added $SCRIPT_DIR to PATH. Please restart your shell or source your profile."
    fi
    
    success "Helper scripts created in $SCRIPT_DIR:"
    success "- waypipe-run: Client-side launcher"
    success "- waypipe-server-run: Server-side launcher"
}

# Show usage instructions
show_instructions() {
    echo -e "\n${BOLD}${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${GREEN}             Waypipe Setup Complete!                         ${NC}"
    echo -e "${BOLD}${GREEN}════════════════════════════════════════════════════════════${NC}\n"
    
    echo -e "${BOLD}${BLUE}📋 USAGE INSTRUCTIONS${NC}"
    echo -e "${BLUE}--------------------------------------------------------------${NC}"
    
    echo -e "${BOLD}${CYAN}🔗 SERVER-SIDE SETUP${NC}"
    echo -e "Your server has been configured to work with Waypipe."
    echo -e "1. Ensure the SSH server is running: ${BOLD}sudo systemctl status ssh${NC}"
    echo -e "2. The server's IP address is: ${BOLD}$(hostname -I | awk '{print $1}')${NC}"
    echo -e "3. The installed Waypipe version is: ${BOLD}$(waypipe --version 2>&1 | head -n 1)${NC}\n"
    
    echo -e "${BOLD}${CYAN}🔗 CLIENT-SIDE USAGE${NC}"
    echo -e "To run applications from your server while already connected via SSH:"
    echo -e "1. First, SSH to your server: ${BOLD}ssh waypipe-server${NC}"
    echo -e "2. Then run the application with: ${BOLD}waypipe-server-run firefox${NC} (or any application)"
    echo -e "\nTo run applications from your client machine directly:"
    echo -e "Use the helper script: ${BOLD}waypipe-run waypipe-server firefox${NC}\n"
    
    echo -e "${BOLD}${CYAN}📊 EXAMPLE COMMANDS${NC}"
    echo -e "• Run Firefox: ${BOLD}waypipe-run waypipe-server firefox${NC}"
    echo -e "• Run GIMP: ${BOLD}waypipe-run waypipe-server gimp${NC}"
    echo -e "• Run VS Code: ${BOLD}waypipe-run waypipe-server code${NC}"
    echo -e "• Run a terminal: ${BOLD}waypipe-run waypipe-server gnome-terminal${NC}"
    echo -e "• Run a specific command with args: ${BOLD}waypipe-run waypipe-server xterm -fa 'Monospace' -fs 14${NC}\n"
    
    echo -e "${BOLD}${CYAN}⚠️ TROUBLESHOOTING${NC}"
    echo -e "• If you get \"Can't open display\" or similar errors, ensure Wayland is running"
    echo -e "• Check if WAYLAND_DISPLAY is set: ${BOLD}echo \$WAYLAND_DISPLAY${NC}"
    echo -e "• Check if XDG_RUNTIME_DIR is set: ${BOLD}echo \$XDG_RUNTIME_DIR${NC}"
    echo -e "• Verify the server has the application installed"
    echo -e "• Add compression for better performance: ${BOLD}waypipe --compress lz4 ssh ...${NC}"
    echo -e "• Debug with: ${BOLD}waypipe --debug ssh ...${NC}"
    
    echo -e "\n${BLUE}--------------------------------------------------------------${NC}"
    echo -e "${GREEN}Setup complete! Log file saved to: ${BOLD}$LOG_FILE${NC}\n"
}

# Main function - Server setup
setup_server() {
    info "Setting up Waypipe on server..."
    
    check_sudo
    detect_package_manager
    check_wayland
    install_waypipe
    configure_ssh_server
    create_helper_scripts
    
    success "Server setup completed successfully!"
}

# Main function - Client setup
setup_client() {
    info "Setting up Waypipe on client..."
    
    check_sudo
    detect_package_manager
    check_wayland
    install_waypipe
    setup_client_ssh_config
    create_helper_scripts
    
    success "Client setup completed successfully!"
}

# Main execution
display_banner

echo -e "This script will install and configure Waypipe for remote application forwarding over SSH."
echo -e "Waypipe must be installed on both the server and client machines.\n"

echo -e "Please select the setup type:"
echo -e "1) Server setup (the machine that will run the applications)"
echo -e "2) Client setup (the machine that will display the applications)"
echo -e "3) Both server and client setup (for a single machine that will act as both)"
echo -e "q) Quit"
echo

read -p "Select an option [1-3/q]: " option

case $option in
    1)
        setup_server
        ;;
    2)
        setup_client
        ;;
    3)
        setup_server
        setup_client
        ;;
    q|Q)
        info "Exiting setup."
        exit 0
        ;;
    *)
        error "Invalid option. Exiting." "exit"
        ;;
esac

show_instructions
