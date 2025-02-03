#!/bin/bash

set -e

# Function to display messages
info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

# Install Git Credential Manager
info "Installing Git Credential Manager..."
if ! command -v git-credential-manager &> /dev/null; then
    # Check if GCM is already installed
    if command -v dotnet &> /dev/null; then
        # Install GCM via dotnet if available
        dotnet tool install --global git-credential-manager
    else
        # Fallback to installing GCM from the GitHub release
        GCM_VERSION=$(curl -s https://api.github.com/repos/GitCredentialManager/git-credential-manager/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
        GCM_PACKAGE="gcm-linux_amd64.${GCM_VERSION:1}.deb"
        curl -L -o "$GCM_PACKAGE" "https://github.com/GitCredentialManager/git-credential-manager/releases/download/$GCM_VERSION/$GCM_PACKAGE"
        sudo dpkg -i "$GCM_PACKAGE"
        rm "$GCM_PACKAGE"
    fi
else
    info "Git Credential Manager version $(git-credential-manager --version) is already installed."
fi

# Backup existing git credentials configuration
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="git_credentials_backup_${BACKUP_DATE}.conf"
info "Creating backup of git credentials configuration to $BACKUP_FILE..."
git config --global --get-regexp credential > "$BACKUP_FILE" 2>/dev/null || true

# Find the location of git-credential-manager
GCM_PATH=$(command -v git-credential-manager)
if [[ -z "$GCM_PATH" ]]; then
    echo -e "\033[1;31m[ERROR]\033[0m Git Credential Manager not found after installation."
    exit 1
fi
info "Git Credential Manager found at: $GCM_PATH"

# Verify secretservice availability
if ! command -v secret-tool >/dev/null 2>&1; then
    error "secretservice backend not available. Please install libsecret-tools."
    exit 1
fi

# Configure Git to use GCM
info "Configuring Git to use Git Credential Manager..."
if ! git config --global credential.helper "$GCM_PATH"; then
    error "Failed to set credential.helper"
    exit 1
fi

if ! git config --global credential.credentialStore secretservice; then
    error "Failed to set credential.credentialStore"
    exit 1
fi

info "Configuration completed successfully."
echo "Git Credential Manager is configured to use the 'secretservice' credential store."

# Add cleanup function
cleanup() {
    info "Cleaning up temporary files..."
    rm -f "$BACKUP_FILE"
}
trap cleanup EXIT
