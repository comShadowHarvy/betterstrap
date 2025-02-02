#!/bin/bash

set -e  # Exit on error

# Check for sudo access
check_sudo() {
    if ! command -v sudo &>/dev/null; then
        echo "❌ sudo is not installed. Please install sudo first."
        exit 1
    fi
    if ! sudo -v &>/dev/null; then
        echo "❌ No sudo privileges. Please ensure you have sudo access."
        exit 1
    fi
}

# Function to detect package manager
detect_package_manager() {
    if command -v apt &>/dev/null; then
        PKG_MANAGER="apt"
        PKG_UPDATE="sudo apt update"
        PKG_INSTALL="sudo apt install -y"
    elif command -v dnf &>/dev/null; then
        PKG_MANAGER="dnf"
        PKG_UPDATE="sudo dnf check-update"
        PKG_INSTALL="sudo dnf install -y"
    elif command -v pacman &>/dev/null; then
        PKG_MANAGER="pacman"
        PKG_UPDATE="sudo pacman -Sy"
        PKG_INSTALL="sudo pacman -S --needed --noconfirm"
    else
        echo "❌ Unsupported package manager"
        exit 1
    fi
}

# Function to detect if the system is Arch-based
is_arch() {
    [[ -f /etc/arch-release ]]
}

# Function to detect and set the container runtime (Docker or Podman)
detect_container_runtime() {
    if command -v podman &>/dev/null; then
        CONTAINER_CMD="podman"
        echo "✅ Using Podman"
        return
    fi
    
    if command -v docker &>/dev/null; then
        CONTAINER_CMD="docker"
        if ! systemctl is-active --quiet docker; then
            echo "🔄 Starting Docker service..."
            sudo systemctl start docker
        fi
        echo "✅ Using Docker"
        return
    fi

    echo "🔄 No container runtime found. Installing Docker..."
    install_docker
    CONTAINER_CMD="docker"
}

# Function to install Docker if neither Docker nor Podman is found
install_docker() {
    detect_package_manager
    
    case $PKG_MANAGER in
        apt)
            $PKG_UPDATE
            $PKG_INSTALL docker.io docker-compose
            ;;
        dnf)
            $PKG_INSTALL docker docker-compose
            ;;
        pacman)
            $PKG_INSTALL docker docker-compose
            ;;
    esac
    
    sudo systemctl enable docker
    sudo systemctl start docker
}

# Install dependencies
install_dependencies() {
    detect_package_manager
    check_sudo
    echo "🔄 Installing system dependencies..."
    $PKG_UPDATE
    
    # Common dependencies across distributions
    DEPS="curl wget git"
    $PKG_INSTALL $DEPS
}

# Install Ollama
install_ollama() {
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    sudo systemctl enable --now ollama.service

    if systemctl is-active --quiet ollama.service; then
        echo "✅ Ollama service is running."
    else
        echo "❌ Failed to start Ollama service. Check logs."
        exit 1
    fi
}

# Install Open-WebUI
install_open_webui() {
    echo "Installing Open-WebUI..."
    $CONTAINER_CMD run -d --name open-webui \
        -p 3000:3000 \
        -v open-webui-data:/app/backend/data \
        --restart unless-stopped \
        ghcr.io/open-webui/open-webui:main
    echo "✅ Open-WebUI should be accessible at http://localhost:3000"
}

# Install Pinokio (Only on Arch-based systems using yay)
install_pinokio() {
    if is_arch; then
        echo "Installing Pinokio from AUR..."
        if command -v yay &>/dev/null; then
            yay -S --noconfirm pinokio-bin
        else
            echo "❌ yay not found. Please install yay first."
            exit 1
        fi
    else
        echo "Skipping Pinokio installation. Not an Arch-based system."
    fi
}

# Install LobeHub
install_lobehub() {
    echo "Installing LobeHub..."
    $CONTAINER_CMD run -d --name lobehub \
        -p 3210:3210 \
        -v lobehub-data:/data \
        --restart unless-stopped \
        lobehub/lobe-chat:latest
    echo "✅ LobeHub should be accessible at http://localhost:3210"
}

# Install Ollama GUI
install_ollama_gui() {
    echo "Installing Ollama GUI..."
    $CONTAINER_CMD run -d --name ollama-gui \
        -p 4000:80 \
        -v ollama-gui-data:/usr/share/nginx/html \
        --restart unless-stopped \
        ghcr.io/ollama-webui/ollama-webui:latest
    echo "✅ Ollama GUI should be accessible at http://localhost:4000"
}

# Install Enchanted
install_enchanted() {
    echo "Installing Enchanted..."
    $CONTAINER_CMD run -d --name enchanted \
        -p 9090:9090 \
        -v enchanted-data:/data \
        --restart unless-stopped \
        ghcr.io/ericlathrop/enchanted:latest
    echo "✅ Enchanted should be accessible at http://localhost:9090"
}

# Prompt user to choose DeepSeek model version
choose_deepseek_model() {
    echo "Choose the DeepSeek model version you want to run:"
    echo "1) 1.5B  - Minimal resource usage (~2.3GB)"
    echo "2) 7B    - Balanced performance (~4.7GB)"
    echo "3) 8B    - Intermediate (~8GB)"
    echo "4) 14B   - Higher performance (~14GB)"
    echo "5) 32B   - Even more power (~32GB)"
    echo "6) 70B   - Massive (~40GB+ RAM needed)"
    echo ""
    read -p "Enter the number of your choice: " choice

    case $choice in
        1) MODEL="deepseek-r1:1.5b";;
        2) MODEL="deepseek-r1:7b";;
        3) MODEL="deepseek-r1:8b";;
        4) MODEL="deepseek-r1:14b";;
        5) MODEL="deepseek-r1:32b";;
        6) MODEL="deepseek-r1:70b";;
        *) echo "Invalid selection. Defaulting to 1.5B"; MODEL="deepseek-r1:1.5b";;
    esac
    echo "Selected model: $MODEL"
}

# Run DeepSeek model in Ollama
run_deepseek() {
    echo "Running $MODEL model..."
    ollama run "$MODEL"
}

# Execution flow
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

echo "🎉 All installations completed! 🚀"

echo "💡 Access your AI tools at:"
echo "🔗 Open-WebUI → http://localhost:3000"
echo "🔗 Pinokio (if installed) → Run `pinokio`"
echo "🔗 LobeHub → http://localhost:3210"
echo "🔗 Ollama GUI → http://localhost:4000"
echo "🔗 Enchanted → http://localhost:9090"
echo "🔗 Running DeepSeek model: $MODEL"
