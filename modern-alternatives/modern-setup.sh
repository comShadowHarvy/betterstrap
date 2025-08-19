#!/usr/bin/env bash

# Modern Setup Script with Best Practices
# This demonstrates improved shell scripting techniques

set -euo pipefail # Exit on error, undefined vars, pipe failures
IFS=$'\n\t'      # Secure Internal Field Separator

# Configuration
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_FILE="/tmp/${SCRIPT_NAME%.*}-$(date +%Y%m%d-%H%M%S).log"

# Colors and formatting
declare -A COLORS=(
    [RED]='\033[0;31m'
    [GREEN]='\033[0;32m'
    [YELLOW]='\033[1;33m'
    [BLUE]='\033[0;34m'
    [BOLD]='\033[1m'
    [RESET]='\033[0m'
)

# Logging functions
log() {
    local level="$1"; shift
    local message="$*"
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    
    echo -e "${COLORS[${level}]:-}[${level}]${COLORS[RESET]} ${message}"
    echo "${timestamp} [${level}] ${message}" >> "${LOG_FILE}"
}

info() { log "INFO" "$@"; }
warn() { log "WARN" "$@"; }
error() { log "ERROR" "$@"; }
success() { log "SUCCESS" "$@"; }

# Error handling
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        error "Script failed with exit code $exit_code"
        error "Check log file: $LOG_FILE"
    fi
    exit $exit_code
}

trap cleanup EXIT

# Utility functions
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

is_root() {
    [[ $EUID -eq 0 ]]
}

confirm() {
    local prompt="$1"
    local default="${2:-n}"
    
    if [[ "${FORCE:-}" == "true" ]]; then
        info "Force mode: auto-confirming '$prompt'"
        return 0
    fi
    
    local suffix="[y/N]"
    [[ "$default" == "y" ]] && suffix="[Y/n]"
    
    while true; do
        read -rp "$prompt $suffix: " response
        response="${response:-$default}"
        case "$response" in
            [Yy]*) return 0 ;;
            [Nn]*) return 1 ;;
            *) warn "Please answer yes or no." ;;
        esac
    done
}

# Package manager detection
detect_package_manager() {
    if command_exists apt; then
        echo "apt"
    elif command_exists pacman; then
        echo "pacman"
    elif command_exists dnf; then
        echo "dnf"
    elif command_exists brew; then
        echo "brew"
    else
        error "No supported package manager found"
        return 1
    fi
}

# Install packages based on detected package manager
install_packages() {
    local packages=("$@")
    local pkg_manager
    pkg_manager="$(detect_package_manager)"
    
    info "Installing packages with $pkg_manager: ${packages[*]}"
    
    case "$pkg_manager" in
        apt)
            sudo apt update -qq
            sudo apt install -y "${packages[@]}"
            ;;
        pacman)
            sudo pacman -Sy --needed --noconfirm "${packages[@]}"
            ;;
        dnf)
            sudo dnf install -y "${packages[@]}"
            ;;
        brew)
            brew install "${packages[@]}"
            ;;
        *)
            error "Unsupported package manager: $pkg_manager"
            return 1
            ;;
    esac
}

# Main setup functions
setup_development_environment() {
    info "Setting up development environment..."
    
    local dev_packages=(
        git
        curl
        wget
        build-essential
        python3
        python3-pip
        nodejs
        npm
    )
    
    # Adjust package names for different distributions
    local pkg_manager
    pkg_manager="$(detect_package_manager)"
    
    case "$pkg_manager" in
        pacman)
            dev_packages=(git curl wget base-devel python python-pip nodejs npm)
            ;;
        dnf)
            dev_packages=(git curl wget @development-tools python3 python3-pip nodejs npm)
            ;;
    esac
    
    install_packages "${dev_packages[@]}"
    success "Development environment setup complete"
}

setup_rust() {
    if command_exists rustup; then
        info "Rust already installed, updating..."
        rustup update
    else
        info "Installing Rust via rustup..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source "$HOME/.cargo/env"
    fi
    success "Rust setup complete"
}

setup_ai_tools() {
    info "Setting up AI/ML tools..."
    
    # Install Python packages
    pip3 install --user --upgrade \
        torch \
        transformers \
        numpy \
        pandas \
        jupyter \
        ollama
    
    # Install Ollama if not present
    if ! command_exists ollama; then
        curl -fsSL https://ollama.com/install.sh | sh
    fi
    
    success "AI tools setup complete"
}

# Configuration management
backup_configs() {
    local backup_dir="$HOME/config-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    info "Backing up configurations to $backup_dir"
    
    # List of configs to backup
    local configs=(
        "$HOME/.zshrc"
        "$HOME/.bashrc"
        "$HOME/.gitconfig"
        "$HOME/.vimrc"
        "$HOME/.config/nvim"
    )
    
    for config in "${configs[@]}"; do
        if [[ -e "$config" ]]; then
            cp -r "$config" "$backup_dir/" 2>/dev/null || true
        fi
    done
    
    success "Configurations backed up to $backup_dir"
}

# Main execution
main() {
    info "Starting modern system setup..."
    info "Log file: $LOG_FILE"
    
    # Safety checks
    if is_root; then
        error "Do not run this script as root"
        exit 1
    fi
    
    if ! command_exists sudo; then
        error "sudo is required but not found"
        exit 1
    fi
    
    # Menu system
    local -A setup_functions=(
        ["dev"]="setup_development_environment"
        ["rust"]="setup_rust" 
        ["ai"]="setup_ai_tools"
        ["backup"]="backup_configs"
    )
    
    if [[ $# -eq 0 ]]; then
        info "Available setup options:"
        for key in "${!setup_functions[@]}"; do
            echo "  $key - ${setup_functions[$key]}"
        done
        echo "  all - Run all setup functions"
        echo ""
        echo "Usage: $SCRIPT_NAME [dev|rust|ai|backup|all]"
        exit 0
    fi
    
    # Process arguments
    for arg in "$@"; do
        case "$arg" in
            all)
                for func in "${setup_functions[@]}"; do
                    if confirm "Run $func?"; then
                        $func
                    fi
                done
                ;;
            *)
                if [[ -n "${setup_functions[$arg]:-}" ]]; then
                    ${setup_functions[$arg]}
                else
                    error "Unknown option: $arg"
                    exit 1
                fi
                ;;
        esac
    done
    
    success "Setup complete! Check $LOG_FILE for details."
}

# Parse command line options
while getopts ":hf" opt; do
    case $opt in
        h)
            echo "Usage: $SCRIPT_NAME [-f] [dev|rust|ai|backup|all]"
            echo "  -f: Force mode (auto-confirm prompts)"
            echo "  -h: Show this help"
            exit 0
            ;;
        f)
            readonly FORCE=true
            ;;
        \?)
            error "Invalid option: -$OPTARG"
            exit 1
            ;;
    esac
done

shift $((OPTIND-1))

# Run main function
main "$@"
