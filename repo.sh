#!/bin/bash

# Function to display a loading bar with percentage
loading_bar() {
    local current=$1
    local total=$2
    local percent=$(( 100 * current / total ))
    local bar_length=20
    local filled_length=$(( bar_length * current / total ))
    local empty_length=$(( bar_length - filled_length ))

    printf -v bar "%0.s#" $(seq 1 $filled_length)
    printf -v space "%0.s " $(seq 1 $empty_length)

    echo -ne "Progress: [${bar}${space}] (${percent}%%)\r"
}

# Function to check if a repository is already added
is_repo_added() {
    grep -q "\[$1\]" /etc/pacman.conf
}

# Function to check if a package is installed
is_package_installed() {
    pacman -Qs "$1" > /dev/null
}

# Function to add a repository
add_repository() {
    local name="$1"
    local key="$2"
    local keyserver="$3"
    local mirror="$4"
    local additional_commands="$5"

    if is_repo_added "$name"; then
        echo "$name repository already added."
    else
        echo "Adding $name repository..."
        sudo pacman-key --recv-key "$key" --keyserver "$keyserver" || { echo "Error: Failed to add key for $name."; return 1; }
        sudo pacman-key --lsign-key "$key" || { echo "Error: Failed to sign key for $name."; return 1; }
        echo -e "$mirror" | sudo tee -a /etc/pacman.conf
        eval "$additional_commands"
        echo "$name repository added."
    fi
}

# Function to install a package
install_package() {
    local package="$1"
    local description="$2"

    if is_package_installed "$package"; then
        echo "$package is already installed."
    else
        echo "$description"
        sudo pacman -S --noconfirm "$package" || { echo "Error: Failed to install $package."; return 1; }
        echo "$package installed successfully."
    fi
}

# Display header
clear
echo "============================="
echo "   Ultimate Repo Installer"
echo "============================="
echo

# Total steps for progress bar
total_steps=8
current_step=0

# Add Chaotic AUR repository
loading_bar $current_step $total_steps
add_repository "chaotic-aur" \
    "3056513887B78AEB" \
    "keyserver.ubuntu.com" \
    "[chaotic-aur]\nInclude = /etc/pacman.d/chaotic-mirrorlist" \
    "sudo pacman -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' &&
     sudo pacman -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'"
loading_bar $((++current_step)) $total_steps

# Add ArchStrike repository
loading_bar $current_step $total_steps
add_repository "archstrike" \
    "5B5F5BBF9A2D15A019E20608A106C36A3170E57D" \
    "keyserver.ubuntu.com" \
    "[archstrike]\nServer = https://mirror.archstrike.org/\$arch/\$repo" \
    ""
loading_bar $((++current_step)) $total_steps

# Add BlackArch repository
loading_bar $current_step $total_steps
if is_repo_added "blackarch"; then
    echo "BlackArch repository already added."
else
    echo "Adding BlackArch repository..."
    curl -O https://blackarch.org/strap.sh || { echo "Error: Failed to download BlackArch strap.sh."; exit 1; }
    sudo chmod +x strap.sh
    sudo ./strap.sh || { echo "Error: Failed to execute strap.sh."; exit 1; }
    rm -f strap.sh
    echo "BlackArch repository added."
fi
loading_bar $((++current_step)) $total_steps

# Update package database
loading_bar $current_step $total_steps
echo "Updating package database..."
sudo pacman -Syyu || { echo "Error: Failed to update package database."; exit 1; }
loading_bar $((++current_step)) $total_steps

# Install fakeroot
loading_bar $current_step $total_steps
install_package "fakeroot" "fakeroot provides a simulated root environment for building packages without actual root permissions."
loading_bar $((++current_step)) $total_steps

# Install AppArmor
loading_bar $current_step $total_steps
install_package "apparmor" "AppArmor is a Linux security module for mandatory access control." &&
sudo systemctl enable apparmor &&
sudo systemctl start apparmor
loading_bar $((++current_step)) $total_steps

# Install yay
loading_bar $current_step $total_steps
install_package "yay" "yay (Yet Another Yaourt) is a popular AUR helper."
loading_bar $((++current_step)) $total_steps

# Install paru
loading_bar $current_step $total_steps
install_package "paru" "paru is a modern AUR helper written in Rust."
loading_bar $((++current_step)) $total_steps

# Finalize
loading_bar $total_steps $total_steps
echo -ne '\nAll steps completed.\n'
