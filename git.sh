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

# Install dependencies for Arch Linux
install_arch_dependencies() {
    log_info "Installing dependencies for Arch Linux..."
    
    # Update package lists
    log_info "Updating package database..."
    sudo pacman -Syu --noconfirm
    
    # Install Git
    if ! check_version "git" "2.19.0" "git --version | awk '{print \$3}'"; then
        log_info "Installing Git >= 2.19.0..."
        sudo pacman -S --noconfirm git
    fi
    
    # Install Git LFS
    if ! command_exists git-lfs; then
        log_info "Installing Git LFS..."
        sudo pacman -S --noconfirm git-lfs
        git lfs install
    fi
    
    # Install C compiler for treesitter
    log_info "Installing C compiler..."
    sudo pacman -S --noconfirm gcc
    
    # Install other required dependencies
    log_info "Installing build dependencies..."
    sudo pacman -S --noconfirm base-devel cmake curl unzip ninja
    
    # Install dependencies for fzf-lua (optional)
    log_info "Installing optional dependencies..."
    sudo pacman -S --noconfirm ripgrep fd fzf
    
    # Install lazygit (optional)
    if ! command_exists lazygit; then
        log_info "Installing lazygit..."
        sudo pacman -S --noconfirm lazygit
    fi
    
    log_success "Dependencies installed successfully!"
}

# Install Nerd Font
install_nerd_font() {
    log_info "Installing Nerd Font (v3.0 or greater)..."
    
    FONT_DIR="$HOME/.local/share/fonts"
    mkdir -p "$FONT_DIR"
    
    log_info "Downloading JetBrainsMono Nerd Font..."
    curl -fLo "$FONT_DIR/JetBrains Mono Regular Nerd Font Complete.ttf" \
        https://github.com/ryanoasis/nerd-fonts/raw/master/patched-fonts/JetBrainsMono/Ligatures/Regular/JetBrainsMonoNerdFont-Regular.ttf
    
    log_info "Updating font cache..."
    fc-cache -f -v
    
    log_success "Nerd Font installed successfully!"
}

# Build and install Neovim from source
install_neovim_from_source() {
    log_info "Building Neovim >= 0.9.0 with LuaJIT from source..."
    
    # Install build dependencies
    sudo pacman -S --noconfirm base-devel cmake unzip ninja curl gettext

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
    
    log_success "Neovim installed successfully from source!"
}

# Install Neovim from Arch repos
install_neovim_from_repo() {
    log_info "Installing Neovim from Arch repositories..."
    sudo pacman -S --noconfirm neovim
    log_success "Neovim installed successfully from repository!"
}

# Configure Git authentication
configure_git_auth() {
    log_info "Setting up Git authentication..."
    
    echo "Choose your preferred Git authentication method:"
    echo "1) HTTPS with credential manager"
    echo "2) SSH keys"
    echo "3) GitHub CLI"
    echo "4) Skip Git authentication setup"
    
    read -p "Enter your choice (1-4): " auth_choice
    
    case $auth_choice in
        1)
            log_info "Setting up HTTPS with credential manager..."
            sudo pacman -S --noconfirm libsecret
            git config --global credential.helper /usr/lib/git-core/git-credential-libsecret
            git config --global credential.helper store
            
            echo ""
            echo "HTTPS credential manager is now configured."
            echo "The first time you pull or push to a GitHub repository,"
            echo "you'll be asked for your username and password/token."
            echo "Your credentials will be stored securely after that."
            ;;
        2)
            log_info "Setting up SSH keys for GitHub..."
            
            # Check if SSH key already exists
            if [[ ! -f ~/.ssh/id_ed25519 ]]; then
                read -p "Enter your GitHub email address: " github_email
                ssh-keygen -t ed25519 -C "$github_email"
                
                # Start ssh-agent
                eval "$(ssh-agent -s)"
                
                # Add key to ssh-agent
                ssh-add ~/.ssh/id_ed25519
                
                echo ""
                echo "Your SSH public key is:"
                cat ~/.ssh/id_ed25519.pub
                echo ""
                echo "Please add this key to your GitHub account at:"
                echo "https://github.com/settings/keys"
            else
                log_info "SSH key already exists at ~/.ssh/id_ed25519"
                echo ""
                echo "Your existing SSH public key is:"
                cat ~/.ssh/id_ed25519.pub
            fi
            
            # Configure Git to use SSH
            git config --global url."git@github.com:".insteadOf "https://github.com/"
            ;;
        3)
            log_info "Setting up GitHub CLI..."
            sudo pacman -S --noconfirm github-cli
            gh auth login
            ;;
        4)
            log_info "Skipping Git authentication setup..."
            ;;
        *)
            log_warning "Invalid choice. Skipping Git authentication setup."
            ;;
    esac
    
    log_success "Git authentication setup completed!"
}

# Main function
main() {
    log_info "Starting Neovim environment setup for Arch Linux..."
    
    # Install dependencies
    install_arch_dependencies
    
    # Configure Git authentication
    configure_git_auth
    
    # Install Nerd Font (optional)
    read -p "Do you want to install a Nerd Font? (y/n): " install_font
    if [[ $install_font == "y" || $install_font == "Y" ]]; then
        install_nerd_font
    fi
    
    # Install Neovim
    log_info "Checking Neovim version..."
    if ! check_version "nvim" "0.9.0" "nvim --version | head -n 1 | awk '{print \$2}'"; then
        echo "Neovim not found or version too old. How would you like to install it?"
        echo "1) Install from Arch repositories"
        echo "2) Build from source (ensures LuaJIT support)"
        read -p "Enter your choice (1-2): " nvim_choice
        
        case $nvim_choice in
            1)
                install_neovim_from_repo
                ;;
            2)
                install_neovim_from_source
                ;;
            *)
                log_warning "Invalid choice. Installing from repository..."
                install_neovim_from_repo
                ;;
        esac
    else
        log_success "Neovim already installed with required version."
    fi
    
    log_success "Neovim environment setup completed successfully!"
    log_info "You now have all the required and optional dependencies installed for your Neovim setup."
}

# Run the main function
main
