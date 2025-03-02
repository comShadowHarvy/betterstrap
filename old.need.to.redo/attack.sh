#!/bin/bash

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Package manager detection and commands
declare -A PKG_CMDS

detect_package_manager() {
    if command -v apt &>/dev/null; then
        PKG_CMDS[MGR]="apt"
        PKG_CMDS[CHECK]="dpkg -l"
        PKG_CMDS[INSTALL]="sudo apt install -y"
        PKG_CMDS[UPDATE]="sudo apt update"
        PKG_CMDS[REPO_CHECK]="grep -h ^deb /etc/apt/sources.list /etc/apt/sources.list.d/*"
    elif command -v dnf &>/dev/null; then
        PKG_CMDS[MGR]="dnf"
        PKG_CMDS[CHECK]="rpm -q"
        PKG_CMDS[INSTALL]="sudo dnf install -y"
        PKG_CMDS[UPDATE]="sudo dnf check-update"
        PKG_CMDS[REPO_CHECK]="dnf repolist"
    elif command -v pacman &>/dev/null; then
        PKG_CMDS[MGR]="pacman"
        PKG_CMDS[CHECK]="pacman -Qs"
        PKG_CMDS[INSTALL]="sudo pacman -S --needed --noconfirm"
        PKG_CMDS[UPDATE]="sudo pacman -Sy"
        PKG_CMDS[REPO_CHECK]="grep ^\[.*\] /etc/pacman.conf"
    else
        log "ERROR" "No supported package manager found"
        exit 1
    fi
}

# Enhanced loading bar with Unicode blocks
loading_bar() {
    local current=$1
    local total=$2
    local percent=$((100 * current / total))
    local bar_length=20
    local filled_length=$((bar_length * current / total))
    local empty_length=$((bar_length - filled_length))
    
    local blocks=("▏" "▎" "▍" "▌" "▋" "▊" "▉" "█")
    printf -v bar "%0.s█" $(seq 1 $filled_length)
    printf -v space "%0.s░" $(seq 1 $empty_length)
    
    echo -ne "${BLUE}Progress: [${bar}${space}] ${percent}%${NC}\r"
}

# Logging function
log() {
    local level=$1; shift
    case "$level" in
        "INFO") echo -e "${GREEN}[INFO]${NC} $*" ;;
        "WARN") echo -e "${YELLOW}[WARN]${NC} $*" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $*" ;;
    esac
}

# Check if package is installed
is_package_installed() {
    local package=$1
    ${PKG_CMDS[CHECK]} "$package" >/dev/null 2>&1
}

# Check if repository is added
is_repo_added() {
    local repo=$1
    ${PKG_CMDS[REPO_CHECK]} | grep -q "$repo"
}

# Add repository based on package manager
add_repository() {
    local repo=$1
    case ${PKG_CMDS[MGR]} in
        apt)
            sudo add-apt-repository -y "$repo"
            ;;
        dnf)
            sudo dnf config-manager --add-repo "$repo"
            ;;
        pacman)
            if ! grep -q "\[$repo\]" /etc/pacman.conf; then
                echo -e "\n[$repo]" | sudo tee -a /etc/pacman.conf
            fi
            ;;
    esac
}

# Function to install a package
install_package() {
    local package=$1
    local description=$2

    if is_package_installed "$package"; then
        echo "$package is already installed."
    else
        echo "Installing $package..."
        echo "$description"
        sudo pacman -S --noconfirm "$package" || { echo "Error: Failed to install $package."; return 1; }
        echo "$package installed successfully."
    fi
}

# Display header
clear
echo "============================="
echo "   Ultimate Repo Installer"
=============================
echo

# Define steps dynamically
steps=(
    "add_repository chaotic-aur 3056513887B78AEB keyserver.ubuntu.com '[chaotic-aur]\nInclude = /etc/pacman.d/chaotic-mirrorlist' \"sudo pacman -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' && sudo pacman -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'\""
    "add_repository archstrike 5B5F5BBF9A2D15A019E20608A106C36A3170E57D keyserver.ubuntu.com '[archstrike]\nServer = https://mirror.archstrike.org/\$arch/\$repo'"
    "add_repository blackarch '' '' '' 'curl -O https://blackarch.org/strap.sh && sudo chmod +x strap.sh && sudo ./strap.sh && rm -f strap.sh'"
    "install_package fakeroot 'fakeroot provides a simulated root environment for building packages without needing root permissions.'"
    "install_package apparmor 'AppArmor provides mandatory access control, restricting program capabilities.' && sudo systemctl enable apparmor && sudo systemctl start apparmor"
    "install_package yay 'yay (Yet Another Yaourt) simplifies AUR package management.'"
    "install_package paru 'paru is a modern AUR helper focusing on speed and security.'"
    "install_package pamac-aur 'pamac provides a graphical interface for managing packages from official repositories and the AUR.'"
    "install_package aurman 'aurman offers an efficient interface for managing AUR packages.'"
)

# Run steps with dynamic progress bar
total_steps=${#steps[@]}
current_step=0

for step in "${steps[@]}"; do
    loading_bar $current_step $total_steps
    eval "$step" || { echo "Error executing step: $step"; exit 1; }
    loading_bar $((++current_step)) $total_steps
done

# Finalize
loading_bar $total_steps $total_steps
echo -e "\nAll steps completed successfully."
