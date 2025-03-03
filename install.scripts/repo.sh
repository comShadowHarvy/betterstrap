#!/bin/bash
# Enhanced Arch Linux Rice Setup Script

# Error handling function
handle_error() {
    echo "Error: $1"
    exit 1
}

# Function to check if repository already exists in pacman.conf
repo_exists() {
    grep -q "\[$1\]" /etc/pacman.conf
}

# Update the system
echo "==> Updating system packages..."
sudo pacman -Syu --noconfirm || handle_error "Failed to update system"

# ----------------------
# CHAOTIC AUR REPOSITORY
# ----------------------
echo "==> Setting up Chaotic AUR repository..."
if ! repo_exists "chaotic-aur"; then
    # Import and sign key
    sudo pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com || handle_error "Failed to receive Chaotic AUR key"
    sudo pacman-key --lsign-key 3056513887B78AEB || handle_error "Failed to sign Chaotic AUR key"
    
    # Install keyring and mirrorlist
    sudo pacman -U --noconfirm 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst' || handle_error "Failed to install Chaotic AUR packages"
    
    # Add to pacman.conf
    echo -e "\n[chaotic-aur]\nInclude = /etc/pacman.d/chaotic-mirrorlist\n" | sudo tee -a /etc/pacman.conf > /dev/null
    echo "Chaotic AUR repository added successfully"
else
    echo "Chaotic AUR repository already configured"
fi

# ----------------------
# BLACKARCH REPOSITORY
# ----------------------
echo "==> Setting up BlackArch repository..."
if ! repo_exists "blackarch"; then
    # Download and verify strap.sh (using SHA256 instead of SHA1)
    curl -O https://blackarch.org/strap.sh || handle_error "Failed to download BlackArch strap.sh"
    echo "5ea40d49ecd14c2e024deecf90605426db97ea0c539f704f3c3220a1d1a66e16 strap.sh" | sha256sum -c || handle_error "BlackArch script verification failed"
    
    # Make executable and install
    chmod +x strap.sh
    sudo ./strap.sh || handle_error "BlackArch bootstrap failed"
    
    # Clean up
    rm strap.sh
    echo "BlackArch repository added successfully"
else
    echo "BlackArch repository already configured"
fi

# ----------------------
# ARCHSTRIKE REPOSITORY
# ----------------------
echo "==> Setting up ArchStrike repository..."
if ! repo_exists "archstrike"; then
    # Initialize pacman keyring if needed
    sudo pacman-key --init || handle_error "Failed to initialize pacman keyring"
    
    # Import and sign ArchStrike key
    echo "Importing ArchStrike key..."
    dirmngr < /dev/null
    if ! sudo pacman-key -r 9D5F1C051D146843CDA4858BDE64825E7CBC0D51; then
        echo "Key server might be unreachable, trying direct download..."
        curl -O https://archstrike.org/keyfile.asc || handle_error "Failed to download ArchStrike keyfile"
        sudo pacman-key --add keyfile.asc || handle_error "Failed to add ArchStrike key"
        rm keyfile.asc
    fi
    
    sudo pacman-key --lsign-key 9D5F1C051D146843CDA4858BDE64825E7CBC0D51 || handle_error "Failed to sign ArchStrike key"
    
    # Add ArchStrike repository to pacman.conf
    echo -e "\n[archstrike]\nInclude = /etc/pacman.d/archstrike-mirrorlist\n" | sudo tee -a /etc/pacman.conf > /dev/null
    
    # Refresh package databases
    sudo pacman -Syy || handle_error "Failed to refresh package databases"
    
    # Install ArchStrike keyring and mirrorlist
    sudo pacman -S --noconfirm archstrike-keyring archstrike-mirrorlist || handle_error "Failed to install ArchStrike keyring and mirrorlist"
    echo "ArchStrike repository added successfully"
else
    echo "ArchStrike repository already configured"
fi

# ----------------------
# ENABLE MULTILIB
# ----------------------
echo "==> Enabling multilib repository..."
if grep -q "^\s*#\s*\[multilib\]" /etc/pacman.conf; then
    sudo sed -i '/\[multilib\]/,/Include/s/^#//' /etc/pacman.conf
    echo "Multilib repository enabled"
else
    if grep -q "^\s*\[multilib\]" /etc/pacman.conf; then
        echo "Multilib repository already enabled"
    else
        echo "Multilib section not found in /etc/pacman.conf."
        echo "Consider adding it manually if needed."
    fi
fi

# ----------------------
# FINAL SYSTEM UPDATE
# ----------------------
echo "==> Refreshing package databases and upgrading system..."
sudo pacman -Syyu --noconfirm || handle_error "Final system update failed"

echo "==> All repositories have been configured successfully!"
echo "==> You can now proceed with installing your ricing packages."