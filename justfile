# Betterstrap Modern Task Runner
# Replaces all the old install scripts with a cleaner, more maintainable approach
# Install Just: cargo install just
# Usage: just <command>

# Set shell options for all recipes
set shell := ["zsh", "-c"]

# Default recipe to display available commands
default:
    @echo "🚀 Betterstrap Modern Task Runner"
    @echo "================================="
    @just --list

# === SYSTEM SETUP ===

# Setup Arch Linux repositories and pacman configuration
setup-repos:
    #!/usr/bin/env zsh
    set -euo pipefail
    echo "🔧 Setting up Arch Linux repositories..."
    
    # Check if we're on Arch Linux
    if [[ ! -f /etc/arch-release ]]; then
        echo "❌ This command is only for Arch Linux systems"
        exit 1
    fi
    
    # Update keyring first
    sudo pacman -Sy --needed --noconfirm archlinux-keyring
    
    # Enable multilib if not already enabled
    if ! grep -q "^\[multilib\]" /etc/pacman.conf; then
        echo "📦 Enabling multilib repository..."
        sudo sed -i '/^#\[multilib\]/,/^#Include/ s/^#//' /etc/pacman.conf
    fi
    
    # Configure pacman for better experience
    echo "⚙️  Configuring pacman..."
    sudo sed -i 's/#Color/Color/' /etc/pacman.conf
    sudo sed -i 's/#ParallelDownloads = 5/ParallelDownloads = 10/' /etc/pacman.conf
    sudo sed -i 's/#VerbosePkgLists/VerbosePkgLists/' /etc/pacman.conf
    
    # Add ILoveCandy for better progress bars
    if ! grep -q "ILoveCandy" /etc/pacman.conf; then
        sudo sed -i '/^Color/a ILoveCandy' /etc/pacman.conf
    fi
    
    # Refresh databases
    sudo pacman -Syy
    
    echo "✅ Repository setup complete!"

# Install recommended software with modern approach
install-recommended:
    #!/usr/bin/env zsh
    set -euo pipefail
    echo "📦 Installing recommended software..."
    
    # Detect package manager
    if command -v pacman >/dev/null 2>&1; then
        PKG_INSTALL="sudo pacman -S --needed --noconfirm"
        PKG_UPDATE="sudo pacman -Sy"
    elif command -v apt >/dev/null 2>&1; then
        PKG_INSTALL="sudo apt install -y"
        PKG_UPDATE="sudo apt update"
    else
        echo "❌ Unsupported package manager"
        exit 1
    fi
    
    $PKG_UPDATE
    
    # Essential tools
    echo "🔧 Installing essential tools..."
    $PKG_INSTALL git curl wget htop neofetch
    
    # Development tools
    echo "💻 Installing development tools..."
    $PKG_INSTALL code firefox thunderbird
    
    # Multimedia
    echo "🎵 Installing multimedia tools..."
    $PKG_INSTALL vlc gimp
    
    # Office
    echo "📄 Installing office tools..."
    if command -v pacman >/dev/null 2>&1; then
        $PKG_INSTALL libreoffice-fresh
    else
        $PKG_INSTALL libreoffice
    fi
    
    # System utilities
    echo "🛠️  Installing system utilities..."
    $PKG_INSTALL timeshift bleachbit
    
    echo "✅ Recommended software installed!"

# Setup development environment
setup-dev:
    #!/usr/bin/env zsh
    set -euo pipefail
    echo "💻 Setting up development environment..."
    
    # Detect package manager and install packages
    if command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --needed --noconfirm \
            base-devel git curl wget python python-pip \
            nodejs npm go rust gcc clang cmake make \
            gdb valgrind strace jq docker
    elif command -v apt >/dev/null 2>&1; then
        sudo apt update
        sudo apt install -y \
            build-essential git curl wget python3 python3-pip \
            nodejs npm golang-go rustc gcc clang cmake make \
            gdb valgrind strace jq docker.io
    else
        echo "❌ Unsupported package manager"
        exit 1
    fi
    
    # Install Rust properly if not already installed
    if ! command -v rustup >/dev/null 2>&1; then
        echo "🦀 Installing Rust via rustup..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source ~/.cargo/env
    fi
    
    # Setup Docker
    if command -v docker >/dev/null 2>&1; then
        echo "🐳 Configuring Docker..."
        sudo systemctl enable --now docker
        sudo usermod -aG docker $USER
        echo "⚠️  You may need to log out and back in for Docker group changes to take effect"
    fi
    
    echo "✅ Development environment ready!"

# Setup AI/ML environment 
setup-ai:
    #!/usr/bin/env zsh
    set -euo pipefail
    echo "🤖 Setting up AI/ML environment..."
    
    # Install Python AI packages
    echo "📚 Installing Python AI libraries..."
    pip install --user --upgrade \
        torch torchvision torchaudio \
        transformers \
        numpy pandas matplotlib seaborn \
        jupyter jupyterlab \
        scikit-learn \
        ollama
    
    # Install Ollama
    if ! command -v ollama >/dev/null 2>&1; then
        echo "🦙 Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
        
        # Start ollama service
        if command -v systemctl >/dev/null 2>&1; then
            sudo systemctl enable --now ollama
        fi
    fi
    
    # Install popular model
    read -q "REPLY?📥 Install phi3:mini model? (y/n): "
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📥 Pulling phi3:mini model..."
        ollama pull phi3:mini
    fi
    
    echo "✅ AI/ML environment ready!"
    echo "🚀 Run 'ollama run phi3:mini' to start chatting!"

# Setup security tools (with warning)
setup-security:
    #!/usr/bin/env zsh
    set -euo pipefail
    echo "🔒 Setting up security tools..."
    echo "⚠️  These tools are for authorized testing only!"
    echo "⚠️  Misuse of these tools may be illegal!"
    
    read -q "REPLY?Continue with security tools installation? (y/n): "
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cancelled."
        exit 0
    fi
    
    # Install security tools based on package manager
    if command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --needed --noconfirm \
            nmap masscan \
            wireshark-qt \
            john hashcat hydra \
            sqlmap \
            nikto \
            metasploit
    elif command -v apt >/dev/null 2>&1; then
        sudo apt update
        sudo apt install -y \
            nmap masscan \
            wireshark \
            john hashcat hydra \
            sqlmap \
            nikto
    fi
    
    # Install additional tools via pip
    echo "🐍 Installing Python security tools..."
    pip install --user \
        scapy \
        requests \
        beautifulsoup4
    
    echo "✅ Security tools installed!"
    echo "⚠️  Remember: Only use these tools on systems you own or have explicit permission to test!"

# Setup plymouth boot animation (Arch only)
setup-plymouth:
    #!/usr/bin/env zsh
    set -euo pipefail
    
    if [[ ! -f /etc/arch-release ]]; then
        echo "❌ Plymouth setup is only supported on Arch Linux"
        exit 1
    fi
    
    echo "🎨 Setting up Plymouth boot animation..."
    
    # Install Plymouth
    sudo pacman -S --needed --noconfirm plymouth
    
    # Set theme
    THEME=${1:-spinfinity}
    echo "🎭 Setting Plymouth theme to: $THEME"
    sudo plymouth-set-default-theme "$THEME"
    
    # Configure mkinitcpio
    echo "⚙️  Configuring mkinitcpio..."
    if ! grep -q "plymouth" /etc/mkinitcpio.conf; then
        sudo sed -i '/^HOOKS=/s/\(udev\)/plymouth \1/' /etc/mkinitcpio.conf
    fi
    
    # Regenerate initramfs
    sudo mkinitcpio -P
    
    # Configure GRUB
    echo "⚙️  Configuring GRUB..."
    if ! grep -q "splash" /etc/default/grub; then
        sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="\([^"]*\)"/GRUB_CMDLINE_LINUX_DEFAULT="\1 splash quiet"/' /etc/default/grub
    fi
    
    sudo grub-mkconfig -o /boot/grub/grub.cfg
    
    echo "✅ Plymouth setup complete!"
    echo "🔄 Reboot to see the boot animation"

# Install waypipe for remote Wayland apps
install-waypipe:
    #!/usr/bin/env zsh
    set -euo pipefail
    echo "📡 Installing Waypipe for remote Wayland applications..."
    
    if command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --needed --noconfirm waypipe
    elif command -v apt >/dev/null 2>&1; then
        sudo apt install -y waypipe
    else
        echo "❌ Unsupported package manager"
        exit 1
    fi
    
    echo "✅ Waypipe installed!"
    echo "💡 Usage: waypipe ssh user@host app_name"

# === SYSTEM MAINTENANCE ===

# Update entire system
update-system:
    #!/usr/bin/env zsh
    set -euo pipefail
    echo "🔄 Updating entire system..."
    
    # Update system packages
    if command -v pacman >/dev/null 2>&1; then
        echo "📦 Updating Arch packages..."
        sudo pacman -Syu --noconfirm
        
        # Clean package cache
        sudo pacman -Sc --noconfirm
        
        # Remove orphaned packages
        orphans=$(pacman -Qtdq 2>/dev/null || true)
        if [[ -n "$orphans" ]]; then
            echo "🗑️  Removing orphaned packages..."
            sudo pacman -Rns $orphans --noconfirm
        fi
    elif command -v apt >/dev/null 2>&1; then
        echo "📦 Updating Debian/Ubuntu packages..."
        sudo apt update && sudo apt upgrade -y
        sudo apt autoremove -y
        sudo apt autoclean
    fi
    
    # Update Rust if installed
    if command -v rustup >/dev/null 2>&1; then
        echo "🦀 Updating Rust..."
        rustup update
    fi
    
    # Update Python packages
    if command -v pip >/dev/null 2>&1; then
        echo "🐍 Updating Python packages..."
        pip install --user --upgrade pip
        pip list --user --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip install --user -U 2>/dev/null || true
    fi
    
    # Update npm packages
    if command -v npm >/dev/null 2>&1; then
        echo "📦 Updating npm packages..."
        npm update -g
    fi
    
    # Update Ollama models
    if command -v ollama >/dev/null 2>&1; then
        echo "🦙 Updating Ollama models..."
        ollama list | awk 'NR>1 {print $1}' | head -10 | xargs -I {} ollama pull {} 2>/dev/null || true
    fi
    
    echo "✅ System update complete!"

# Clean up system
cleanup-system:
    #!/usr/bin/env zsh
    set -euo pipefail
    echo "🧹 Cleaning up system..."
    
    # Package manager cleanup
    if command -v pacman >/dev/null 2>&1; then
        echo "🗑️  Cleaning pacman cache..."
        sudo pacman -Sc --noconfirm
        
        # Remove orphaned packages
        orphans=$(pacman -Qtdq 2>/dev/null || true)
        if [[ -n "$orphans" ]]; then
            echo "🗑️  Removing orphaned packages: $orphans"
            sudo pacman -Rns $orphans --noconfirm
        fi
    elif command -v apt >/dev/null 2>&1; then
        echo "🗑️  Cleaning apt cache..."
        sudo apt autoremove -y
        sudo apt autoclean
    fi
    
    # Docker cleanup
    if command -v docker >/dev/null 2>&1; then
        echo "🐳 Cleaning Docker..."
        docker system prune -f
    fi
    
    # Clean temporary files
    echo "🧽 Cleaning temporary files..."
    sudo rm -rf /tmp/* 2>/dev/null || true
    rm -rf ~/.cache/pip/* 2>/dev/null || true
    rm -rf ~/.npm/_cacache 2>/dev/null || true
    
    # Clean old logs
    if command -v journalctl >/dev/null 2>&1; then
        echo "📋 Cleaning old logs..."
        sudo journalctl --vacuum-time=7d
    fi
    
    echo "✅ System cleanup complete!"

# === BACKUPS AND UTILITIES ===

# Backup important configurations
backup-configs:
    #!/usr/bin/env zsh
    set -euo pipefail
    backup_dir="$HOME/config-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    echo "💾 Backing up configurations to $backup_dir"
    
    # System configs
    [[ -f ~/.zshrc ]] && cp ~/.zshrc "$backup_dir/"
    [[ -f ~/.bashrc ]] && cp ~/.bashrc "$backup_dir/"
    [[ -f ~/.gitconfig ]] && cp ~/.gitconfig "$backup_dir/"
    [[ -f ~/.vimrc ]] && cp ~/.vimrc "$backup_dir/"
    
    # SSH config
    [[ -f ~/.ssh/config ]] && cp ~/.ssh/config "$backup_dir/ssh_config"
    
    # App configs
    [[ -d ~/.config/nvim ]] && cp -r ~/.config/nvim "$backup_dir/"
    [[ -d ~/.config/code-oss ]] && cp -r ~/.config/code-oss "$backup_dir/" 2>/dev/null || true
    [[ -d ~/.config/VSCodium ]] && cp -r ~/.config/VSCodium "$backup_dir/" 2>/dev/null || true
    
    # Package lists
    if command -v pacman >/dev/null 2>&1; then
        pacman -Qqe > "$backup_dir/pacman-explicit.txt"
        pacman -Qqm > "$backup_dir/pacman-aur.txt"
    elif command -v apt >/dev/null 2>&1; then
        dpkg --get-selections > "$backup_dir/dpkg-selections.txt"
    fi
    
    echo "✅ Backup complete: $backup_dir"

# Show system information
system-info:
    #!/usr/bin/env zsh
    set -euo pipefail
    echo "🖥️  System Information"
    echo "===================="
    
    # OS info
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        echo "OS: $PRETTY_NAME"
    fi
    
    # Hardware info
    echo "Kernel: $(uname -r)"
    echo "CPU: $(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)"
    echo "RAM: $(free -h | awk '/^Mem:/{print $2 " total, " $7 " available"}')"
    
    # Disk usage
    echo "Disk Usage:"
    df -h / | awk 'NR==2 {print "  Root: " $3 " used / " $2 " total (" $5 " full)"}'
    
    # Package counts
    if command -v pacman >/dev/null 2>&1; then
        echo "Packages: $(pacman -Q | wc -l) installed"
    elif command -v apt >/dev/null 2>&1; then
        echo "Packages: $(dpkg --get-selections | wc -l) installed"
    fi
    
    # Uptime
    echo "Uptime: $(uptime -p)"

# === AI SPECIFIC COMMANDS ===

# List available Ollama models
ai-models:
    #!/usr/bin/env zsh
    if ! command -v ollama >/dev/null 2>&1; then
        echo "❌ Ollama not installed. Run: just setup-ai"
        exit 1
    fi
    
    echo "🦙 Available Ollama Models:"
    ollama list

# Pull a specific AI model
ai-pull model:
    #!/usr/bin/env zsh
    if ! command -v ollama >/dev/null 2>&1; then
        echo "❌ Ollama not installed. Run: just setup-ai"
        exit 1
    fi
    
    echo "📥 Pulling model: {{model}}"
    ollama pull "{{model}}"

# Run an AI model
ai-run model:
    #!/usr/bin/env zsh
    if ! command -v ollama >/dev/null 2>&1; then
        echo "❌ Ollama not installed. Run: just setup-ai"
        exit 1
    fi
    
    echo "🤖 Running model: {{model}}"
    ollama run "{{model}}"

# === COMPOSITE COMMANDS ===

# Complete system setup (everything)
setup-complete:
    echo "🚀 Running complete system setup..."
    just setup-repos
    just install-recommended  
    just setup-dev
    echo "✨ Complete setup finished!"
    echo "💡 Optional: Run 'just setup-ai' for AI tools"
    echo "💡 Optional: Run 'just setup-security' for security tools"

# Daily maintenance routine
daily-maintenance:
    echo "🔄 Running daily maintenance..."
    just update-system
    just cleanup-system
    echo "✅ Daily maintenance complete!"

# === HELP AND UTILITIES ===

# Show detailed help for all commands
help:
    @echo "📖 Betterstrap Task Runner - Detailed Help"
    @echo "==========================================="
    @echo ""
    @echo "🔧 SYSTEM SETUP:"
    @echo "  setup-repos         - Configure Arch Linux repositories and pacman"
    @echo "  install-recommended - Install essential desktop software"  
    @echo "  setup-dev          - Install development tools and languages"
    @echo "  setup-ai           - Install AI/ML tools and Ollama"
    @echo "  setup-security     - Install security/penetration testing tools"
    @echo "  setup-plymouth     - Configure Plymouth boot animation (Arch only)"
    @echo "  install-waypipe    - Install Waypipe for remote Wayland apps"
    @echo ""
    @echo "🔄 MAINTENANCE:"
    @echo "  update-system      - Update all packages and tools"
    @echo "  cleanup-system     - Clean caches and remove unused packages"
    @echo "  backup-configs     - Backup important configuration files"
    @echo "  system-info        - Display system information"
    @echo ""
    @echo "🤖 AI COMMANDS:"
    @echo "  ai-models          - List installed Ollama models"
    @echo "  ai-pull <model>    - Download a specific model"
    @echo "  ai-run <model>     - Run an interactive chat with a model"
    @echo ""
    @echo "🚀 COMPOSITE COMMANDS:"
    @echo "  setup-complete     - Run complete system setup"
    @echo "  daily-maintenance  - Run daily update and cleanup"
    @echo ""
    @echo "💡 Examples:"
    @echo "  just setup-complete     # Full system setup"
    @echo "  just ai-pull phi3:mini  # Download phi3:mini model"
    @echo "  just ai-run phi3:mini   # Chat with phi3:mini"
    @echo "  just daily-maintenance  # Update and clean system"
