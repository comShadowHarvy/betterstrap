#!/usr/bin/env bash

#!/usr/bin/env bash

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        OS=$DISTRIB_ID
        VER=$DISTRIB_RELEASE
    elif [ -f /etc/debian_version ]; then
        OS=Debian
        VER=$(cat /etc/debian_version)
    elif [ -f /etc/redhat-release ]; then
        OS=RedHat
        VER=$(cat /etc/redhat-release | cut -d ' ' -f 3)
    elif [[ "$(uname)" == "Darwin" ]]; then
        OS="macOS"
        VER=$(sw_vers -productVersion)
    else
        OS="Unknown"
        VER="Unknown"
    fi
    log_info "Detected OS: $OS $VER"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check version of a program
check_version() {
    local program=$1
    local min_version=$2
    local version_cmd=$3
    local version

    if ! command_exists "$program"; then
        return 1
    fi

    version=$($version_cmd)
    
    # Simple version comparison (works for most x.y.z formats)
    if [ "$(echo -e "$version\n$min_version" | sort -V | head -n1)" = "$min_version" ]; then
        log_success "$program version $version is newer than required version $min_version"
        return 0
    else
        log_warning "$program version $version is older than required version $min_version"
        return 1
    fi
}

# Install dependencies for Debian/Ubuntu
install_debian() {
    log_info "Installing dependencies for Debian/Ubuntu..."
    
    # Update package lists
    sudo apt update
    
    # Install build dependencies
    sudo apt install -y build-essential
    
    # Install Git
    if ! check_version "git" "2.19.0" "git --version | awk '{print \$3}'"; then
        log_info "Installing Git >= 2.19.0..."
        sudo add-apt-repository -y ppa:git-core/ppa
        sudo apt update
        sudo apt install -y git
    fi
    
    # Install other required dependencies
    sudo apt install -y curl cmake gettext libtool-bin unzip ninja-build
    
    # Install C compiler for treesitter
    sudo apt install -y gcc g++
    
    # Install dependencies for fzf-lua (optional)
    log_info "Installing optional dependencies..."
    sudo apt install -y ripgrep fd-find
    
    # Install lazygit (optional)
    if ! command_exists lazygit; then
        LAZYGIT_VERSION=$(curl -s "https://api.github.com/repos/jesseduffield/lazygit/releases/latest" | grep -Po '"tag_name": "v\K[^"]*')
        curl -Lo lazygit.tar.gz "https://github.com/jesseduffield/lazygit/releases/latest/download/lazygit_${LAZYGIT_VERSION}_Linux_x86_64.tar.gz"
        tar xf lazygit.tar.gz lazygit
        sudo install lazygit /usr/local/bin
        rm lazygit lazygit.tar.gz
    fi
    
    # Install fzf (optional)
    if ! check_version "fzf" "0.25.1" "fzf --version | awk '{print \$1}'"; then
        log_info "Installing fzf >= 0.25.1..."
        git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
        ~/.fzf/install --all
    fi
    
    log_success "Dependencies installed successfully!"
}

# Install dependencies for Fedora/RHEL/CentOS
install_fedora() {
    log_info "Installing dependencies for Fedora/RHEL/CentOS..."
    
    # Install build dependencies
    sudo dnf install -y make automake gcc gcc-c++ kernel-devel cmake
    
    # Install Git
    if ! check_version "git" "2.19.0" "git --version | awk '{print \$3}'"; then
        log_info "Installing Git >= 2.19.0..."
        sudo dnf install -y git
    fi
    
    # Install other required dependencies
    sudo dnf install -y curl gettext unzip ninja-build libtool
    
    # Install C compiler for treesitter
    sudo dnf install -y gcc gcc-c++
    
    # Install dependencies for fzf-lua (optional)
    log_info "Installing optional dependencies..."
    sudo dnf install -y ripgrep fd-find
    
    # Install lazygit (optional)
    if ! command_exists lazygit; then
        LAZYGIT_VERSION=$(curl -s "https://api.github.com/repos/jesseduffield/lazygit/releases/latest" | grep -Po '"tag_name": "v\K[^"]*')
        curl -Lo lazygit.tar.gz "https://github.com/jesseduffield/lazygit/releases/latest/download/lazygit_${LAZYGIT_VERSION}_Linux_x86_64.tar.gz"
        tar xf lazygit.tar.gz lazygit
        sudo install lazygit /usr/local/bin
        rm lazygit lazygit.tar.gz
    fi
    
    # Install fzf (optional)
    if ! check_version "fzf" "0.25.1" "fzf --version | awk '{print \$1}'"; then
        log_info "Installing fzf >= 0.25.1..."
        git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
        ~/.fzf/install --all
    fi
    
    log_success "Dependencies installed successfully!"
}

# Install dependencies for Arch Linux
install_arch() {
    log_info "Installing dependencies for Arch Linux..."
    
    # Update package lists
    sudo pacman -Syu --noconfirm
    
    # Install Git
    if ! check_version "git" "2.19.0" "git --version | awk '{print \$3}'"; then
        log_info "Installing Git >= 2.19.0..."
        sudo pacman -S --noconfirm git
    fi
    
    # Install other required dependencies
    sudo pacman -S --noconfirm base-devel cmake curl unzip ninja
    
    # Install C compiler for treesitter
    sudo pacman -S --noconfirm gcc
    
    # Install dependencies for fzf-lua (optional)
    log_info "Installing optional dependencies..."
    sudo pacman -S --noconfirm ripgrep fd fzf
    
    # Install lazygit (optional)
    if ! command_exists lazygit; then
        sudo pacman -S --noconfirm lazygit
    fi
    
    log_success "Dependencies installed successfully!"
}

# Install dependencies for macOS
install_macos() {
    log_info "Installing dependencies for macOS..."
    
    # Check if Homebrew is installed
    if ! command_exists brew; then
        log_info "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install Git
    if ! check_version "git" "2.19.0" "git --version | awk '{print \$3}'"; then
        log_info "Installing Git >= 2.19.0..."
        brew install git
    fi
    
    # Install other required dependencies
    brew install cmake curl unzip ninja gettext
    brew link --force gettext
    
    # Install C compiler for treesitter
    log_info "Checking for Xcode Command Line Tools (C compiler)..."
    if ! command_exists clang; then
        log_info "Installing Xcode Command Line Tools..."
        xcode-select --install
    fi
    
    # Install dependencies for fzf-lua (optional)
    log_info "Installing optional dependencies..."
    brew install ripgrep fd
    
    # Install lazygit (optional)
    if ! command_exists lazygit; then
        brew install lazygit
    fi
    
    # Install fzf (optional)
    if ! check_version "fzf" "0.25.1" "fzf --version | awk '{print \$1}'"; then
        log_info "Installing fzf >= 0.25.1..."
        brew install fzf
        $(brew --prefix)/opt/fzf/install
    fi
    
    log_success "Dependencies installed successfully!"
}

# Install Nerd Font
install_nerd_font() {
    log_info "Installing Nerd Font (v3.0 or greater)..."
    
    FONT_DIR=""
    
    if [[ "$OS" == "macOS" ]]; then
        FONT_DIR="$HOME/Library/Fonts"
    else
        FONT_DIR="$HOME/.local/share/fonts"
        mkdir -p "$FONT_DIR"
    fi
    
    log_info "Downloading JetBrainsMono Nerd Font..."
    curl -fLo "$FONT_DIR/JetBrains Mono Regular Nerd Font Complete.ttf" \
        https://github.com/ryanoasis/nerd-fonts/raw/master/patched-fonts/JetBrainsMono/Ligatures/Regular/JetBrainsMonoNerdFont-Regular.ttf
    
    if [[ "$OS" != "macOS" ]]; then
        log_info "Updating font cache..."
        fc-cache -f -v
    fi
    
    log_success "Nerd Font installed successfully!"
}

# Build and install Neovim from source
install_neovim() {
    log_info "Building Neovim >= 0.9.0 with LuaJIT..."
    
    # Clone Neovim repository
    git clone https://github.com/neovim/neovim /tmp/neovim
    cd /tmp/neovim
    
    # Checkout the latest stable release
    git checkout stable
    
    # Build and install
    make CMAKE_BUILD_TYPE=RelWithDebInfo
    sudo make install
    
    # Verify installation
    nvim --version
    
    log_success "Neovim installed successfully!"
}

# Main function
main() {
    log_info "Starting Neovim environment setup..."
    
    # Detect OS
    detect_os
    
    # Install dependencies based on OS
    case $OS in
        *Ubuntu*|*Debian*)
            install_debian
            ;;
        *Fedora*|*CentOS*|*Red Hat*)
            install_fedora
            ;;
        *Arch*)
            install_arch
            ;;
        *macOS*)
            install_macos
            ;;
        *)
            log_error "Unsupported OS: $OS"
            exit 1
            ;;
    esac
    
    # Install Nerd Font (optional)
    read -p "Do you want to install a Nerd Font? (y/n): " install_font
    if [[ $install_font == "y" || $install_font == "Y" ]]; then
        install_nerd_font
    fi
    
    # Install Neovim
    log_info "Checking Neovim version..."
    if ! check_version "nvim" "0.9.0" "nvim --version | head -n 1 | awk '{print \$2}'"; then
        read -p "Do you want to build and install Neovim from source? (y/n): " install_nvim
        if [[ $install_nvim == "y" || $install_nvim == "Y" ]]; then
            install_neovim
        else
            log_warning "Skipping Neovim installation. Make sure to install Neovim >= 0.9.0 with LuaJIT support manually."
        fi
    fi
    
    log_success "Neovim environment setup completed successfully!"
    log_info "You now have all the required and optional dependencies installed for your Neovim setup."
}

# Run the main function
main
