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
    local name=$1
    local key=$2
    local keyserver=$3
    local repo_line=$4
    local extra_commands=$5

    if is_repo_added "$name"; then
        echo "$name repository already added."
    else
        echo "Adding $name repository..."

        if [[ "$name" == "archstrike" ]]; then
            echo "Attempting to fetch ArchStrike key..."
            if ! curl -s https://archstrike.org/keyfile.asc | sudo pacman-key --add -; then
                echo "Failed to fetch ArchStrike key. Adding repository with SigLevel set to Never."
                echo -e "[archstrike]\nSigLevel = Never\nServer = https://mirror.archstrike.org/\$arch/\$repo" | sudo tee -a /etc/pacman.conf
            else
                sudo pacman-key --lsign-key "$key" || {
                    echo "Failed to locally sign ArchStrike key. Adding repository with SigLevel set to Never."
                    echo -e "[archstrike]\nSigLevel = Never\nServer = https://mirror.archstrike.org/\$arch/\$repo" | sudo tee -a /etc/pacman.conf
                }
            fi
        else
            if [[ -n "$key" ]]; then
                sudo pacman-key --recv-key "$key" --keyserver "$keyserver" ||
                sudo pacman-key --recv-key "$key" --keyserver "hkps://keys.openpgp.org" ||
                {
                    echo "Error: Failed to fetch the GPG key for $name from multiple keyservers.";
                    return 1;
                }
                sudo pacman-key --lsign-key "$key" || { echo "Error: Failed to locally sign the key for $name."; return 1; }
            fi

            echo -e "$repo_line" | sudo tee -a /etc/pacman.conf
        fi

        eval "$extra_commands"
        echo "$name repository added."
    fi
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
