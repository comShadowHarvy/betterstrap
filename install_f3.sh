#!/bin/bash

set -e  # Exit on error

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
    elif command -v yum &>/dev/null; then
        PKG_MANAGER="yum"
        PKG_UPDATE="sudo yum check-update"
        PKG_INSTALL="sudo yum install -y"
    elif command -v pacman &>/dev/null; then
        PKG_MANAGER="pacman"
        PKG_UPDATE="sudo pacman -Sy"
        PKG_INSTALL="sudo pacman -S --needed --noconfirm"
    elif command -v apk &>/dev/null; then
        PKG_MANAGER="apk"
        PKG_UPDATE="sudo apk update"
        PKG_INSTALL="sudo apk add"
    else
        echo "❌ Unsupported package manager"
        exit 1
    fi
}

# Function to install required libraries
install_libraries() {
    detect_package_manager
    echo "🔄 Installing required libraries..."
    $PKG_UPDATE
    case $PKG_MANAGER in
        apt)
            $PKG_INSTALL libudev1 libudev-dev libparted-dev
            ;;
        dnf)
            $PKG_INSTALL systemd-libs systemd-devel parted-devel
            ;;
        yum)
            $PKG_INSTALL systemd-libs systemd-devel parted-devel
            ;;
        pacman)
            $PKG_INSTALL libsystemd systemd parted
            ;;
        apk)
            $PKG_INSTALL libudev libudev-dev parted
            ;;
    esac
    echo "✅ Libraries installed successfully."
}

# Main script execution
install_libraries
