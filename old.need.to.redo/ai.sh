#!/bin/bash

# Better error handling and improved flow
set -e  # Exit on error

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="ollama_install_$(date +%Y%m%d_%H%M%S).log"
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
    log "${BLUE}🔄 $1${NC}"
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
        error "Unsupported package manager" "exit"
    fi
}

# Function to detect if the system is Arch-based
is_arch() {
    [[ -f /etc/arch-release ]]
}

# Function to detect and set the container runtime (Docker or Podman)
detect_container_runtime() {
    info "Detecting container runtime..."
    if command -v podman &>/dev/null; then
        CONTAINER_CMD="podman"
        success "Using Podman as container runtime"
        return
    fi
    
    if command -v docker &>/dev/null; then
        # Use sudo if not running as root and not in docker group
        if [ "$EUID" -ne 0 ] && ! groups | grep -q docker; then
            CONTAINER_CMD="sudo docker"
        else
            CONTAINER_CMD="docker"
        fi
        
        if ! systemctl is-active --quiet docker; then
            info "Starting Docker service..."
            if ! sudo systemctl start docker; then
                warning "Failed to start Docker service automatically. You may need to start it manually."
            fi
        fi
        
        success "Using Docker as container runtime"
        return
    fi

    warning "No container runtime found. Installing Docker..."
    install_docker
    CONTAINER_CMD="docker"
}

# Function to install Docker if neither Docker nor Podman is found
install_docker() {
    detect_package_manager
    
    case $PKG_MANAGER in
        apt)
            info "Installing Docker using apt..."
            $PKG_UPDATE
            if ! $PKG_INSTALL docker.io docker-compose; then
                error "Failed to install Docker" "exit"
            fi
            ;;
        dnf)
            info "Installing Docker using dnf..."
            if ! $PKG_INSTALL docker docker-compose; then
                error "Failed to install Docker" "exit"
            fi
            ;;
        yum)
            info "Installing Docker using yum..."
            $PKG_UPDATE
            if ! $PKG_INSTALL docker docker-compose; then
                error "Failed to install Docker" "exit"
            fi
            ;;
        pacman)
            info "Installing Docker using pacman..."
            if ! $PKG_INSTALL docker docker-compose; then
                error "Failed to install Docker" "exit"
            fi
            ;;
        apk)
            info "Installing Docker using apk..."
            $PKG_UPDATE
            if ! $PKG_INSTALL docker docker-compose; then
                error "Failed to install Docker" "exit"
            fi
            ;;
    esac
    
    info "Enabling and starting Docker service..."
    sudo systemctl enable docker
    if ! sudo systemctl start docker; then
        error "Failed to start Docker service" "exit"
    fi
    success "Docker installed and started successfully"
}

# Install dependencies
install_dependencies() {
    detect_package_manager
    check_sudo
    info "Installing system dependencies..."
    if ! $PKG_UPDATE; then
        warning "Package update failed, but continuing..."
    fi
    
    DEPS="curl wget git"
    if ! $PKG_INSTALL $DEPS; then
        error "Failed to install dependencies" "exit"
    fi
    success "System dependencies installed"
}

# Install Ollama
install_ollama() {
    info "Installing Ollama..."
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
    
    if ! curl -fsSL https://ollama.com/install.sh | sh; then
        error "Ollama installation failed" "exit"
    fi
    
    if systemctl --version &>/dev/null; then
        info "Enabling and starting Ollama service..."
        if ! sudo systemctl enable --now ollama.service; then
            warning "Failed to enable Ollama service"
        fi
        
        if systemctl is-active --quiet ollama.service; then
            success "Ollama service is running"
        else
            warning "Ollama service is not running. Starting it manually..."
            if ! sudo systemctl start ollama.service; then
                error "Failed to start Ollama service" "exit"
            fi
        fi
    else
        warning "systemd not detected. Starting Ollama manually..."
        ollama serve &> /dev/null &
        sleep 5
        if pgrep -f "ollama serve" > /dev/null; then
            success "Ollama is running in the background"
        else
            error "Failed to start Ollama manually" "exit"
        fi
    fi
    
    # Wait for Ollama API to be ready
    info "Waiting for Ollama API to be ready..."
    for i in {1..10}; do
        if curl -s http://localhost:11434/api/version &>/dev/null; then
            success "Ollama API is ready"
            break
        elif [ $i -eq 10 ]; then
            warning "Ollama API might not be ready yet. Continuing anyway..."
        else
            info "Waiting for Ollama API (attempt $i/10)..."
            sleep 2
        fi
    done
}

# Prompt user to choose DeepSeek model version
choose_deepseek_model() {
    info "Selecting DeepSeek model..."
    echo "Choose the DeepSeek model version you want to download:"
    echo "1) 1.5B  - Minimal resource usage (~2.3GB)"
    echo "2) 7B    - Balanced performance (~4.7GB)"
    echo "3) 8B    - Intermediate (~8GB)"
    echo "4) 14B   - Higher performance (~14GB)"
    echo "5) 32B   - Even more power (~32GB)"
    echo "6) 70B   - Massive (~40GB+ RAM needed)"
    echo "7) Skip model download"
    echo ""
    read -p "Enter the number of your choice: " choice

    case $choice in
        1) MODEL="deepseek-r1:1.5b";;
        2) MODEL="deepseek-r1:7b";;
        3) MODEL="deepseek-r1:8b";;
        4) MODEL="deepseek-r1:14b";;
        5) MODEL="deepseek-r1:32b";;
        6) MODEL="deepseek-r1:70b";;
        7) MODEL="none"; info "Skipping model download"; return;;
        *) warning "Invalid selection. Defaulting to 1.5B"; MODEL="deepseek-r1:1.5b";;
    esac
    
    # Check for already downloaded model
    if [ "$MODEL" != "none" ]; then
        info "Checking if model $MODEL is already downloaded..."
        if ollama list 2>/dev/null | grep -q "$MODEL"; then
            success "Model $MODEL is already downloaded"
        else
            download_deepseek
        fi
    fi
}

# Download DeepSeek model in Ollama
download_deepseek() {
    if [ "$MODEL" = "none" ]; then
        return
    fi
    
    info "Downloading $MODEL model (this may take a while)..."
    echo "This operation can take several minutes to complete depending on your internet speed and system performance."
    
    if ! ollama pull "$MODEL"; then
        error "Failed to download $MODEL model. You can try again later with: ollama pull $MODEL"
        return 1
    fi
    success "Model $MODEL downloaded successfully"
}

# Run DeepSeek model in Ollama
run_deepseek() {
    if [ "$MODEL" = "none" ]; then
        info "No model selected to run"
        return
    fi
    
    # Verify model exists
    if ! ollama list 2>/dev/null | grep -q "$MODEL"; then
        warning "Model $MODEL is not downloaded. Cannot run."
        return
    fi
    
    read -p "Do you want to run the $MODEL model now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "Running $MODEL model..."
        echo "Press Ctrl+C to exit the model when finished"
        sleep 2
        ollama run "$MODEL"
    else
        info "Skipping model execution"
        info "You can run it later with: ollama run $MODEL"
    fi
}

# Function to check and handle existing containers
check_container() {
    local container_name=$1
    
    if $CONTAINER_CMD container inspect "$container_name" &>/dev/null; then
        info "Container '$container_name' already exists"
        read -p "Do you want to replace the existing container? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            info "Stopping and removing existing container..."
            $CONTAINER_CMD stop "$container_name" &>/dev/null || warning "Failed to stop container '$container_name'"
            $CONTAINER_CMD rm "$container_name" &>/dev/null || warning "Failed to remove container '$container_name'"
            return 0
        else
            return 1
        fi
    fi
    return 0
}

# Install Open-WebUI
install_open_webui() {
    info "Installing Open WebUI..."
    
    if ! check_container "open-webui"; then
        success "Skipping Open WebUI installation"
        return
    fi
    
    info "Pulling Open WebUI image..."
    if ! $CONTAINER_CMD pull ghcr.io/open-webui/open-webui:main; then
        error "Failed to pull Open WebUI image"
        return
    fi
    
    info "Creating Open WebUI container..."
    if ! $CONTAINER_CMD run -d \
        --name "open-webui" \
        --restart always \
        -p 3000:8080 \
        -v open-webui:/app/backend/data \
        ghcr.io/open-webui/open-webui:main; then
        error "Failed to create Open WebUI container"
        return
    fi
    
    success "Open WebUI installed successfully at http://localhost:3000"
}

# Install Pinokio (Only on Arch-based systems using yay)
install_pinokio() {
    if is_arch; then
        info "Installing Pinokio from AUR..."
        if command -v yay &>/dev/null; then
            if ! yay -S --noconfirm pinokio-bin; then
                error "Failed to install Pinokio"
                return
            fi
            success "Pinokio installed successfully"
        else
            warning "yay not found. Pinokio installation skipped. You can install it manually with yay -S pinokio-bin."
        fi
    else
        info "Skipping Pinokio installation. Not an Arch-based system."
    fi
}

# Install LobeHub
install_lobehub() {
    info "Installing LobeHub..."
    
    if ! check_container "lobehub"; then
        success "Skipping LobeHub installation"
        return
    fi
    
    info "Pulling LobeHub image..."
    if ! $CONTAINER_CMD pull ghcr.io/lobehub/lobe-chat; then
        error "Failed to pull LobeHub image"
        return
    fi
    
    info "Creating LobeHub container..."
    # Determine the correct host address for Docker/Podman
    if [[ "$CONTAINER_CMD" == *"podman"* ]]; then
        # For Podman, use the host IP
        HOST_IP=$(hostname -I | awk '{print $1}')
        if ! $CONTAINER_CMD run -d \
            --name lobehub \
            --restart always \
            -p 3210:3210 \
            -e OLLAMA_API_BASE_URL=http://${HOST_IP}:11434/api \
            ghcr.io/lobehub/lobe-chat; then
            error "Failed to create LobeHub container"
            return
        fi
    else
        # For Docker, use host.docker.internal
        if ! $CONTAINER_CMD run -d \
            --name lobehub \
            --restart always \
            -p 3210:3210 \
            -e OLLAMA_API_BASE_URL=http://host.docker.internal:11434/api \
            ghcr.io/lobehub/lobe-chat; then
            error "Failed to create LobeHub container"
            return
        fi
    fi
    
    success "LobeHub installed successfully at http://localhost:3210"
}

# Install Ollama GUI
install_ollama_gui() {
    info "Installing Ollama Web UI..."
    
    if ! check_container "ollama-gui"; then
        success "Skipping Ollama Web UI installation"
        return
    fi
    
    info "Pulling Ollama Web UI image..."
    if ! $CONTAINER_CMD pull ollama/ollama-webui; then
        error "Failed to pull Ollama Web UI image"
        return
    fi
    
    info "Creating Ollama Web UI container..."
    if ! $CONTAINER_CMD run -d \
        --name ollama-gui \
        --restart always \
        -p 4000:8080 \
        -v ollama-gui:/app/backend/data \
        ollama/ollama-webui; then
        error "Failed to create Ollama Web UI container"
        return
    fi
    
    success "Ollama Web UI installed successfully at http://localhost:4000"
}

# Install Enchanted
install_enchanted() {
    info "Installing Enchanted..."
    
    if ! check_container "enchanted"; then
        success "Skipping Enchanted installation"
        return
    fi
    
    info "Pulling Enchanted image..."
    if ! $CONTAINER_CMD pull ghcr.io/enchanted-ai/enchanted; then
        error "Failed to pull Enchanted image"
        return
    fi
    
    info "Creating Enchanted container..."
    if ! $CONTAINER_CMD run -d \
        --name enchanted \
        --restart always \
        -p 9090:9090 \
        -v enchanted:/app/data \
        ghcr.io/enchanted-ai/enchanted; then
        error "Failed to create Enchanted container"
        return
    fi
    
    success "Enchanted installed successfully at http://localhost:9090"
}

# Display service information
show_service_info() {
    info "Installation Summary"
    
    echo -e "\n${GREEN}🎉 Installation completed!${NC}"
    echo -e "${BLUE}💡 Access your AI tools at:${NC}"
    
    # Check which UIs were installed
    if $CONTAINER_CMD container inspect "open-webui" &>/dev/null; then
        echo -e "🔗 Open-WebUI → ${GREEN}http://localhost:3000${NC}"
    fi
    
    if is_arch && command -v pinokio &>/dev/null; then
        echo -e "🔗 Pinokio → Run ${GREEN}pinokio${NC} in terminal"
    fi
    
    if $CONTAINER_CMD container inspect "ollama-gui" &>/dev/null; then
        echo -e "🔗 Ollama Web UI → ${GREEN}http://localhost:4000${NC}"
    fi
    
    if $CONTAINER_CMD container inspect "lobehub" &>/dev/null; then
        echo -e "🔗 LobeHub → ${GREEN}http://localhost:3210${NC}"
    fi
    
    if $CONTAINER_CMD container inspect "enchanted" &>/dev/null; then
        echo -e "🔗 Enchanted → ${GREEN}http://localhost:9090${NC}"
    fi
    
    if [ "$MODEL" != "none" ] && ollama list 2>/dev/null | grep -q "$MODEL"; then
        echo -e "🤖 Installed model: ${GREEN}$MODEL${NC} (run with: ${GREEN}ollama run $MODEL${NC})"
    fi
    
    echo -e "\nInstallation log saved to: ${BLUE}$LOG_FILE${NC}"
}

# Main execution flow
info "Starting installation process..."
install_dependencies
detect_container_runtime
install_ollama
choose_deepseek_model
# The order has been changed to download and install the model before the UI components
install_open_webui || warning "OpenWebUI installation failed, continuing with other components"
install_pinokio || warning "Pinokio installation failed, continuing with other components"
install_lobehub || warning "LobeHub installation failed, continuing with other components"
install_ollama_gui || warning "Ollama GUI installation failed, continuing with other components"
install_enchanted || warning "Enchanted installation failed, continuing with other components"
run_deepseek
show_service_info