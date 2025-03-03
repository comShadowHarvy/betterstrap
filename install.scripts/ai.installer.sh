#!/bin/bash
# Enhanced Ollama Ecosystem Installer
# This script installs Ollama, multiple UI options, and sets up DeepSeek models

# Terminal colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="ollama_install_$(date +%Y%m%d_%H%M%S).log"

# Exit on error with message
fail() {
    echo -e "${RED}❌ ERROR: $1${NC}" | tee -a "$LOG_FILE"
    echo -e "${YELLOW}Check the log file for details: $LOG_FILE${NC}"
    exit 1
}

# Log and display info message
info() {
    echo -e "${BLUE}ℹ️ $1${NC}" | tee -a "$LOG_FILE"
}

# Log and display success message
success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

# Log and display warning message
warning() {
    echo -e "${YELLOW}⚠️ $1${NC}" | tee -a "$LOG_FILE"
}

# Log and display section header
section() {
    echo -e "\n${BOLD}${CYAN}=== $1 ===${NC}" | tee -a "$LOG_FILE"
}

# Display ASCII banner
display_banner() {
    echo -e "${BOLD}${BLUE}"
    echo '   ____  _ _                         _____           _        _ _           '
    echo '  / __ \| | |                       |_   _|         | |      | | |          '
    echo ' | |  | | | | __ _ _ __ ___   __ _    | |  _ __  ___| |_ __ _| | | ___ _ __ '
    echo ' | |  | | | |/ _` | '\''_ ` _ \ / _` |   | | | '\''_ \/ __| __/ _` | | |/ _ \ '\''__|'
    echo ' | |__| | | | (_| | | | | | | (_| |  _| |_| | | \__ \ || (_| | | |  __/ |   '
    echo '  \____/|_|_|\__,_|_| |_| |_|\__,_| |_____|_| |_|___/\__\__,_|_|_|\___|_|   '
    echo -e "${NC}"
    echo -e "${CYAN}A comprehensive installer for Ollama and compatible UIs${NC}\n"
}

# Initialize log file
init_log() {
    echo "=== Ollama Ecosystem Installation Log - $(date) ===" > "$LOG_FILE"
    echo "System: $(uname -a)" >> "$LOG_FILE"
}

# Check if running with sudo or as root
check_sudo() {
    section "Checking Permissions"
    
    # Check if sudo exists
    if ! command -v sudo &>/dev/null; then
        warning "sudo is not installed"
        
        # If running as root, we can proceed without sudo
        if [ "$EUID" -eq 0 ]; then
            info "Running as root, proceeding without sudo"
            # Redefine sudo to do nothing when running as root
            sudo() { "$@"; }
        else
            fail "sudo is not installed and not running as root. Please install sudo or run as root."
        fi
    else
        # Check sudo privileges
        if ! sudo -n true 2>/dev/null; then
            info "Sudo requires password. Checking credentials..."
            if ! sudo -v; then
                fail "No sudo privileges. Please ensure you have sudo access."
            fi
        fi
        success "Sudo access verified"
    fi
}

# Detect package manager and set installation commands
detect_package_manager() {
    section "Detecting Package Manager"
    
    if command -v apt &>/dev/null; then
        PKG_MANAGER="apt"
        PKG_UPDATE="sudo apt update"
        PKG_INSTALL="sudo apt install -y"
        success "Detected apt package manager (Debian/Ubuntu)"
    elif command -v dnf &>/dev/null; then
        PKG_MANAGER="dnf"
        PKG_UPDATE="sudo dnf check-update || true" # Prevent non-zero exit code
        PKG_INSTALL="sudo dnf install -y"
        success "Detected dnf package manager (Fedora)"
    elif command -v yum &>/dev/null; then
        PKG_MANAGER="yum"
        PKG_UPDATE="sudo yum check-update || true" # Prevent non-zero exit code
        PKG_INSTALL="sudo yum install -y"
        success "Detected yum package manager (CentOS/RHEL)"
    elif command -v pacman &>/dev/null; then
        PKG_MANAGER="pacman"
        PKG_UPDATE="sudo pacman -Sy"
        PKG_INSTALL="sudo pacman -S --needed --noconfirm"
        success "Detected pacman package manager (Arch Linux)"
    elif command -v apk &>/dev/null; then
        PKG_MANAGER="apk"
        PKG_UPDATE="sudo apk update"
        PKG_INSTALL="sudo apk add"
        success "Detected apk package manager (Alpine Linux)"
    else
        fail "Unsupported package manager. Cannot proceed with installation."
    fi
}

# Check if system is Arch-based
is_arch() {
    [[ -f /etc/arch-release ]] || grep -q "Arch Linux" /etc/os-release 2>/dev/null
}

# Check if AUR helper is available (for Arch-based systems)
check_aur_helper() {
    if is_arch; then
        section "Checking AUR Helper"
        
        if command -v yay &>/dev/null; then
            AUR_HELPER="yay"
            success "Found yay AUR helper"
        elif command -v paru &>/dev/null; then
            AUR_HELPER="paru"
            success "Found paru AUR helper"
        else
            warning "No AUR helper found. Pinokio installation will be skipped."
            warning "If you want to install Pinokio, please install yay or paru first."
        fi
    fi
}

# Detect container runtime (Docker or Podman)
detect_container_runtime() {
    section "Detecting Container Runtime"
    
    # Check for Podman first
    if command -v podman &>/dev/null; then
        CONTAINER_CMD="podman"
        success "Using Podman as container runtime"
        
        # Check if running rootless
        if podman info 2>/dev/null | grep -q "rootless: true"; then
            info "Running Podman in rootless mode"
        fi
        return
    fi
    
    # Check for Docker
    if command -v docker &>/dev/null; then
        # Check if Docker service is running
        if systemctl is-active --quiet docker 2>/dev/null; then
            info "Docker service is already running"
        else
            info "Starting Docker service..."
            sudo systemctl start docker || warning "Failed to start Docker service automatically"
        fi
        
        # Use sudo with Docker if not running as root and not in docker group
        if [ "$EUID" -ne 0 ] && ! groups | grep -q docker; then
            CONTAINER_CMD="sudo docker"
            warning "Using Docker with sudo. Consider adding your user to the docker group:"
            warning "sudo usermod -aG docker $USER && newgrp docker"
        else
            CONTAINER_CMD="docker"
        fi
        
        success "Using Docker as container runtime"
        return
    fi

    # Neither Docker nor Podman found, install Docker
    warning "No container runtime found. Will attempt to install Docker..."
    install_docker
    CONTAINER_CMD="docker"
}

# Install Docker if no container runtime is found
install_docker() {
    section "Installing Docker"
    
    case $PKG_MANAGER in
        apt)
            info "Setting up Docker repository..."
            $PKG_UPDATE
            $PKG_INSTALL ca-certificates curl gnupg
            sudo install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/$(. /etc/os-release; echo "$ID")/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            sudo chmod a+r /etc/apt/keyrings/docker.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$(. /etc/os-release; echo "$ID") $(. /etc/os-release; echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt update
            $PKG_INSTALL docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;
        dnf)
            info "Setting up Docker repository..."
            sudo dnf -y install dnf-plugins-core
            sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
            $PKG_INSTALL docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;
        yum)
            info "Setting up Docker repository..."
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            $PKG_INSTALL docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;
        pacman)
            $PKG_INSTALL docker docker-compose
            ;;
        apk)
            $PKG_UPDATE
            $PKG_INSTALL docker docker-compose
            ;;
    esac
    
    # Enable and start Docker service
    info "Enabling and starting Docker service..."
    sudo systemctl enable docker
    sudo systemctl start docker
    
    # Verify Docker installation
    if ! command -v docker &>/dev/null; then
        fail "Docker installation failed. Please install Docker manually."
    fi
    
    if ! systemctl is-active --quiet docker; then
        fail "Docker service failed to start. Please check Docker service status."
    fi
    
    success "Docker installed and started successfully"
}

# Install system dependencies
install_dependencies() {
    section "Installing System Dependencies"
    
    info "Updating package lists..."
    eval "$PKG_UPDATE" >> "$LOG_FILE" 2>&1 || warning "Package update failed, but continuing..."
    
    info "Installing required packages..."
    DEPS="curl wget git"
    eval "$PKG_INSTALL $DEPS" >> "$LOG_FILE" 2>&1 || fail "Failed to install dependencies"
    
    success "System dependencies installed"
}

# Install Ollama
install_ollama() {
    section "Installing Ollama"
    
    # Check if Ollama is already installed
    if command -v ollama &>/dev/null; then
        info "Ollama is already installed. Checking version..."
        CURRENT_VERSION=$(ollama --version 2>/dev/null | awk '{print $2}')
        info "Current Ollama version: $CURRENT_VERSION"
        
        read -p "Do you want to reinstall Ollama? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            success "Skipping Ollama installation"
            return
        fi
    fi
    
    info "Downloading Ollama installer..."
    if ! curl -fsSL https://ollama.com/install.sh -o /tmp/ollama_install.sh; then
        fail "Failed to download Ollama installer"
    fi
    
    info "Running Ollama installer..."
    sh /tmp/ollama_install.sh >> "$LOG_FILE" 2>&1 || fail "Ollama installation failed"
    
    # Ensure Ollama service is enabled and running
    if systemctl --version &>/dev/null; then
        info "Enabling and starting Ollama service..."
        sudo systemctl enable --now ollama.service >> "$LOG_FILE" 2>&1 || warning "Failed to enable Ollama service"
        
        # Verify service status
        if systemctl is-active --quiet ollama.service; then
            success "Ollama service is running"
        else
            warning "Ollama service is not running. Starting it manually..."
            sudo systemctl start ollama.service || fail "Failed to start Ollama service"
        fi
    else
        warning "systemd not detected. Starting Ollama manually..."
        ollama serve &>> "$LOG_FILE" &
        sleep 5
        if pgrep -f "ollama serve" > /dev/null; then
            success "Ollama is running in the background"
        else
            fail "Failed to start Ollama manually"
        fi
    fi
    
    # Clean up
    rm -f /tmp/ollama_install.sh
    
    success "Ollama installed successfully"
}

# Check and handle existing containers
check_container() {
    local container_name=$1
    
    if $CONTAINER_CMD container inspect "$container_name" &>/dev/null; then
        warning "Container '$container_name' already exists"
        read -p "Do you want to replace the existing container? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            info "Stopping and removing existing container..."
            $CONTAINER_CMD stop "$container_name" &>/dev/null || true
            $CONTAINER_CMD rm "$container_name" &>/dev/null || true
            return 0
        else
            return 1
        fi
    fi
    return 0
}

# Install Open-WebUI
install_open_webui() {
    section "Installing Open WebUI"
    
    if ! check_container "open-webui"; then
        success "Skipping Open WebUI installation"
        return
    fi
    
    info "Pulling Open WebUI image..."
    $CONTAINER_CMD pull ghcr.io/open-webui/open-webui:main >> "$LOG_FILE" 2>&1 || fail "Failed to pull Open WebUI image"
    
    info "Creating Open WebUI container..."
    $CONTAINER_CMD run -d \
        --name "open-webui" \
        --restart always \
        -p 3000:8080 \
        -v open-webui:/app/backend/data \
        ghcr.io/open-webui/open-webui:main >> "$LOG_FILE" 2>&1 || fail "Failed to create Open WebUI container"
    
    success "Open WebUI installed successfully"
}

# Install Pinokio (Only on Arch-based systems)
install_pinokio() {
    section "Installing Pinokio"
    
    if ! is_arch; then
        info "Not an Arch-based system. Skipping Pinokio installation."
        return
    fi
    
    if [ -z "$AUR_HELPER" ]; then
        warning "No AUR helper found (yay or paru). Skipping Pinokio installation."
        return
    fi
    
    # Check if Pinokio is already installed
    if command -v pinokio &>/dev/null; then
        info "Pinokio is already installed"
        read -p "Do you want to reinstall Pinokio? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            success "Skipping Pinokio installation"
            return
        fi
    fi
    
    info "Installing Pinokio from AUR..."
    $AUR_HELPER -S --noconfirm pinokio-bin >> "$LOG_FILE" 2>&1 || fail "Failed to install Pinokio"
    
    success "Pinokio installed successfully"
}

# Install LobeHub
install_lobehub() {
    section "Installing LobeHub"
    
    if ! check_container "lobehub"; then
        success "Skipping LobeHub installation"
        return
    fi
    
    info "Pulling LobeHub image..."
    $CONTAINER_CMD pull ghcr.io/lobehub/lobe-chat >> "$LOG_FILE" 2>&1 || fail "Failed to pull LobeHub image"
    
    info "Creating LobeHub container..."
    
    # For Docker, use host.docker.internal to connect to the host
    if [ "$CONTAINER_CMD" = "docker" ] || [ "$CONTAINER_CMD" = "sudo docker" ]; then
        $CONTAINER_CMD run -d \
            --name lobehub \
            --restart always \
            -p 3210:3210 \
            -e OLLAMA_API_BASE_URL=http://host.docker.internal:11434/api \
            ghcr.io/lobehub/lobe-chat >> "$LOG_FILE" 2>&1 || fail "Failed to create LobeHub container"
    else
        # For Podman, use the host IP
        HOST_IP=$(hostname -I | awk '{print $1}')
        $CONTAINER_CMD run -d \
            --name lobehub \
            --restart always \
            -p 3210:3210 \
            -e OLLAMA_API_BASE_URL=http://${HOST_IP}:11434/api \
            ghcr.io/lobehub/lobe-chat >> "$LOG_FILE" 2>&1 || fail "Failed to create LobeHub container"
    fi
    
    success "LobeHub installed successfully"
}

# Install Ollama Web UI
install_ollama_gui() {
    section "Installing Ollama Web UI"
    
    if ! check_container "ollama-gui"; then
        success "Skipping Ollama Web UI installation"
        return
    fi
    
    info "Pulling Ollama Web UI image..."
    $CONTAINER_CMD pull ollama/ollama-webui >> "$LOG_FILE" 2>&1 || fail "Failed to pull Ollama Web UI image"
    
    info "Creating Ollama Web UI container..."
    $CONTAINER_CMD run -d \
        --name ollama-gui \
        --restart always \
        -p 4000:8080 \
        -v ollama-gui:/app/backend/data \
        ollama/ollama-webui >> "$LOG_FILE" 2>&1 || fail "Failed to create Ollama Web UI container"
    
    success "Ollama Web UI installed successfully"
}

# Install Enchanted
install_enchanted() {
    section "Installing Enchanted"
    
    if ! check_container "enchanted"; then
        success "Skipping Enchanted installation"
        return
    fi
    
    info "Pulling Enchanted image..."
    $CONTAINER_CMD pull ghcr.io/enchanted-ai/enchanted >> "$LOG_FILE" 2>&1 || fail "Failed to pull Enchanted image"
    
    info "Creating Enchanted container..."
    $CONTAINER_CMD run -d \
        --name enchanted \
        --restart always \
        -p 9090:9090 \
        -v enchanted:/app/data \
        ghcr.io/enchanted-ai/enchanted >> "$LOG_FILE" 2>&1 || fail "Failed to create Enchanted container"
    
    success "Enchanted installed successfully"
}

# Choose DeepSeek model
choose_deepseek_model() {
    section "DeepSeek Model Selection"
    
    echo -e "${CYAN}Choose the DeepSeek model version you want to run:${NC}"
    echo -e "${YELLOW}1)${NC} 1.5B  - Minimal resource usage (~2.3GB)"
    echo -e "${YELLOW}2)${NC} 7B    - Balanced performance (~4.7GB)"
    echo -e "${YELLOW}3)${NC} 8B    - Intermediate (~8GB)"
    echo -e "${YELLOW}4)${NC} 14B   - Higher performance (~14GB)"
    echo -e "${YELLOW}5)${NC} 32B   - Even more power (~32GB)"
    echo -e "${YELLOW}6)${NC} 70B   - Massive (~40GB+ RAM needed)"
    echo -e "${YELLOW}7)${NC} Skip model download"
    echo ""
    
    read -p "Enter the number of your choice: " choice
    
    case $choice in
        1) MODEL="deepseek-r1:1.5b";;
        2) MODEL="deepseek-r1:7b";;
        3) MODEL="deepseek-r1:8b";;
        4) MODEL="deepseek-r1:14b";;
        5) MODEL="deepseek-r1:32b";;
        6) MODEL="deepseek-r1:70b";;
        7) MODEL="none"; info "Skipping model download";;
        *) warning "Invalid selection. Defaulting to 1.5B"; MODEL="deepseek-r1:1.5b";;
    esac
    
    # Check system RAM
    if [ "$MODEL" != "none" ]; then
        local total_ram=$(free -m | awk '/^Mem:/{print $2}')
        local model_size=${MODEL##*:}
        local recommended_ram=0
        
        case $model_size in
            "1.5b") recommended_ram=4000;; # 4GB
            "7b") recommended_ram=8000;; # 8GB
            "8b") recommended_ram=12000;; # 12GB
            "14b") recommended_ram=20000;; # 20GB
            "32b") recommended_ram=40000;; # 40GB
            "70b") recommended_ram=60000;; # 60GB
        esac
        
        if [ $total_ram -lt $recommended_ram ]; then
            warning "Your system has ${total_ram}MB RAM, but the $model_size model recommends at least ${recommended_ram}MB"
            warning "The model may run slowly or fail to load"
            read -p "Do you want to continue anyway? [y/N] " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                info "Returning to model selection..."
                choose_deepseek_model
                return
            fi
        fi
        
        success "Selected model: $MODEL"
    fi
}

# Run or download DeepSeek model
run_deepseek() {
    if [ "$MODEL" = "none" ]; then
        warning "Skipping DeepSeek model download/run"
        return
    fi
    
    section "DeepSeek Model Setup"
    
    info "Checking if model $MODEL is already downloaded..."
    if ollama list 2>/dev/null | grep -q "$MODEL"; then
        info "Model $MODEL is already downloaded"
    else
        info "Downloading $MODEL model (this may take a while)..."
        ollama pull "$MODEL" >> "$LOG_FILE" 2>&1 || fail "Failed to download $MODEL model"
        success "Model $MODEL downloaded successfully"
    fi
    
    read -p "Do you want to run the $MODEL model now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "Running $MODEL model..."
        echo -e "${YELLOW}Press Ctrl+C to exit the model when finished${NC}"
        sleep 2
        ollama run "$MODEL"
    else
        info "Skipping model execution"
        info "You can run it later with: ollama run $MODEL"
    fi
}

# System information
show_system_info() {
    local total_ram=$(free -h | awk '/^Mem:/{print $2}')
    local free_ram=$(free -h | awk '/^Mem:/{print $4}')
    local total_disk=$(df -h . | awk 'NR==2 {print $2}')
    local free_disk=$(df -h . | awk 'NR==2 {print $4}')
    local cpu_model=$(grep "model name" /proc/cpuinfo | head -1 | cut -d ':' -f2 | sed 's/^[ \t]*//')
    local cpu_cores=$(grep -c processor /proc/cpuinfo)
    
    section "System Information"
    echo -e "CPU: ${BOLD}$cpu_model${NC} (${BOLD}$cpu_cores${NC} cores)"
    echo -e "RAM: ${BOLD}$free_ram${NC} free of ${BOLD}$total_ram${NC}"
    echo -e "Disk: ${BOLD}$free_disk${NC} free of ${BOLD}$total_disk${NC}"
    echo -e "OS: ${BOLD}$(cat /etc/os-release | grep "PRETTY_NAME" | cut -d= -f2 | tr -d '"')${NC}"
    
    # Check GPU if available
    if command -v nvidia-smi &>/dev/null; then
        local gpu_model=$(nvidia-smi --query-gpu=name --format=csv,noheader)
        local gpu_memory=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader)
        echo -e "GPU: ${BOLD}$gpu_model${NC} (${BOLD}$gpu_memory${NC})"
    elif lspci | grep -i 'vga\|3d\|2d' | grep -i 'nvidia\|amd\|ati\|intel' &>/dev/null; then
        local gpu_model=$(lspci | grep -i 'vga\|3d\|2d' | grep -i 'nvidia\|amd\|ati\|intel' | head -1 | sed 's/.*: //')
        echo -e "GPU: ${BOLD}$gpu_model${NC}"
    else
        echo -e "GPU: ${BOLD}Not detected${NC}"
    fi
}

# Display service information
show_service_info() {
    section "Service Information"
    
    # Check which UIs were installed
    echo -e "${BOLD}Access your AI tools at:${NC}"
    
    if $CONTAINER_CMD container inspect "open-webui" &>/dev/null; then
        echo -e "🔗 Open-WebUI → ${CYAN}http://localhost:3000${NC}"
    fi
    
    if is_arch && command -v pinokio &>/dev/null; then
        echo -e "🔗 Pinokio → Run ${CYAN}pinokio${NC} in terminal"
    fi
    
    if $CONTAINER_CMD container inspect "ollama-gui" &>/dev/null; then
        echo -e "🔗 Ollama Web UI → ${CYAN}http://localhost:4000${NC}"
    fi
    
    if $CONTAINER_CMD container inspect "lobehub" &>/dev/null; then
        echo -e "🔗 LobeHub → ${CYAN}http://localhost:3210${NC}"
    fi
    
    if $CONTAINER_CMD container inspect "enchanted" &>/dev/null; then
        echo -e "🔗 Enchanted → ${CYAN}http://localhost:9090${NC}"
    fi
    
    if [ "$MODEL" != "none" ] && ollama list 2>/dev/null | grep -q "$MODEL"; then
        echo -e "🤖 Installed model: ${CYAN}$MODEL${NC} (run with: ${CYAN}ollama run $MODEL${NC})"
    fi
    
    echo -e "\n${BOLD}${GREEN}Installation complete! Enjoy your AI tools!${NC}"
    echo -e "Installation log saved to: ${CYAN}$LOG_FILE${NC}"
}

# Main function
main() {
    init_log
    display_banner
    
    # Show system information before installation
    show_system_info
    
    # Prompt user to continue
    echo
    read -p "Continue with installation? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        info "Installation aborted by user."
        exit 0
    fi
    
    # Main installation sequence
    check_sudo
    detect_package_manager
    check_aur_helper
    install_dependencies
    detect_container_runtime
    install_ollama
    install_open_webui
    install_pinokio
    install_lobehub
    install_ollama_gui
    install_enchanted
    choose_deepseek_model
    run_deepseek
    
    # Show final information
    show_service_info
}

# Run main function
main