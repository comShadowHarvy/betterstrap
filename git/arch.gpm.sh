#!/bin/bash
# GitHub Credential Manager Setup Script for Pure Arch Linux
# This script is optimized specifically for vanilla Arch Linux

set -e
echo "GitHub Credential Manager Setup for Arch Linux"
echo "---------------------------------------------"

# Check if we're on Arch Linux
if ! grep -q "Arch Linux" /etc/os-release &> /dev/null; then
    echo "Warning: This script is optimized for vanilla Arch Linux."
    echo "It may still work on Arch-based distros, but is not guaranteed."
    read -p "Continue anyway? [y/N]: " continue_response
    if [[ ! "$continue_response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for sudo privileges
if ! sudo -v &> /dev/null; then
    echo "Error: This script requires sudo privileges."
    exit 1
fi

# Update system
echo "Updating package database..."
sudo pacman -Sy

# Check Git installation
if ! pacman -Q git &> /dev/null; then
    echo "Git is not installed. Installing Git..."
    sudo pacman -S --noconfirm git
fi
echo "Git is installed: $(git --version)"

# Function to install GitHub CLI
install_github_cli() {
    echo "Installing GitHub CLI..."
    
    if pacman -Q github-cli &> /dev/null; then
        echo "GitHub CLI is already installed."
    else
        sudo pacman -S --noconfirm github-cli
    fi
    
    echo "GitHub CLI installed: $(gh --version)"
}

# Function to install GitHub Credential Manager via AUR
install_gcm_aur() {
    echo "Installing GitHub Credential Manager from AUR..."
    
    # Ensure base-devel is installed (required for makepkg)
    if ! pacman -Q base-devel &> /dev/null; then
        echo "Installing base-devel package group..."
        sudo pacman -S --needed --noconfirm base-devel
    fi
    
    # Create temporary directory for AUR build
    BUILD_DIR=$(mktemp -d)
    cd "$BUILD_DIR"
    
    echo "Cloning git-credential-manager-core AUR package..."
    git clone https://aur.archlinux.org/git-credential-manager-core.git
    cd git-credential-manager-core
    
    echo "Building and installing git-credential-manager-core..."
    makepkg -si --noconfirm
    
    # Clean up
    cd "$OLDPWD"
    rm -rf "$BUILD_DIR"
    
    if command -v git-credential-manager-core &> /dev/null; then
        echo "GitHub Credential Manager installed successfully."
    else
        echo "Failed to install GitHub Credential Manager."
        exit 1
    fi
}

# Function to configure keyring for credential storage
configure_keyring() {
    echo "Setting up a secure credential store..."
    
    # Install GNOME Keyring and libsecret (preferred on Arch)
    if ! pacman -Q gnome-keyring &> /dev/null; then
        echo "Installing GNOME Keyring..."
        sudo pacman -S --noconfirm gnome-keyring libsecret
    fi
    
    # Check if libsecret is installed for Git
    if ! pacman -Q libsecret &> /dev/null; then
        echo "Installing libsecret for Git credential storage..."
        sudo pacman -S --noconfirm libsecret
    fi
    
    # Check if p11-kit is installed (required by GCM)
    if ! pacman -Q p11-kit &> /dev/null; then
        echo "Installing p11-kit..."
        sudo pacman -S --noconfirm p11-kit
    fi
    
    # Ensure the keyring daemon is running
    if command -v systemctl &> /dev/null; then
        # Enable the secret service for the current user
        systemctl --user enable --now gnome-keyring-daemon.service
    else
        echo "Note: systemd not detected. Please ensure gnome-keyring-daemon is running."
        echo "You may need to add 'gnome-keyring-daemon --start' to your login scripts."
    fi
    
    echo "Keyring setup complete."
}

# Function to configure Git credential storage
configure_git_credentials() {
    echo "Configuring Git credential storage..."
    
    # Check if GCM is installed
    if command -v git-credential-manager-core &> /dev/null; then
        # Configure GCM
        git-credential-manager-core configure
        git config --global credential.helper manager-core
        
        # Set credential.helper specifically for GitHub
        git config --global credential.https://github.com.helper manager-core
        
        echo "Git credential helper configured to use Credential Manager."
    else
        echo "GitHub Credential Manager not found, using cache credential helper."
        # Store credentials for 1 hour (3600 seconds)
        git config --global credential.helper 'cache --timeout=3600'
        
        echo "For permanent storage, consider:"
        echo "1. Re-running this script to install GitHub Credential Manager (recommended)"
        echo "2. Using Git's store helper with: git config --global credential.helper store"
        echo "   (Note: This stores credentials in plaintext in ~/.git-credentials)"
    fi
    
    echo "Git credential helper configured: $(git config --global credential.helper)"
}

# Function to authenticate with GitHub
authenticate_github() {
    echo "Authenticating with GitHub..."
    
    if command -v gh &> /dev/null; then
        echo "Please follow the prompts to log in to GitHub..."
        gh auth login
    else
        echo "GitHub CLI not installed. Manual authentication required."
        echo "Please run 'git push' to your repository and enter your credentials when prompted."
    fi
}

# Main installation process
echo "Starting installation process..."

# Step 1: Install GitHub CLI
if ! command -v gh &> /dev/null; then
    read -p "Do you want to install GitHub CLI? [y/N]: " install_gh_response
    if [[ "$install_gh_response" =~ ^[Yy]$ ]]; then
        install_github_cli
    fi
else
    echo "GitHub CLI is already installed: $(gh --version)"
fi

# Step 2: Install GitHub Credential Manager
if ! command -v git-credential-manager-core &> /dev/null; then
    read -p "Do you want to install GitHub Credential Manager from AUR? (recommended) [y/N]: " install_gcm_response
    if [[ "$install_gcm_response" =~ ^[Yy]$ ]]; then
        install_gcm_aur
        configure_keyring
    fi
else
    echo "GitHub Credential Manager is already installed."
fi

# Step 3: Configure Git credential storage
configure_git_credentials

# Step 4: Authenticate with GitHub
read -p "Do you want to authenticate with GitHub now? [y/N]: " auth_response
if [[ "$auth_response" =~ ^[Yy]$ ]]; then
    authenticate_github
fi

echo ""
echo "Setup complete! Your GitHub credentials should now be managed securely."
echo ""
echo "Notes for Arch Linux users:"
echo "- This script has set up GNOME Keyring for secure credential storage"
echo "- If using a desktop environment like GNOME, credentials will be stored securely"
echo "- If using a minimal window manager, ensure gnome-keyring-daemon is running"
echo "- You may need to add to your ~/.xinitrc or login scripts:"
echo "  eval \$(gnome-keyring-daemon --start)"
echo "  export SSH_AUTH_SOCK"
echo ""
echo "If you encounter any issues, refer to the Arch Wiki and GitHub documentation:"
echo "- https://wiki.archlinux.org/title/GNOME/Keyring"
echo "- https://docs.github.com/en/get-started/getting-started-with-git/caching-your-github-credentials-in-git"
