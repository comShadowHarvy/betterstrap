#!/bin/bash

# Define backup directory
BACKUP_DIR="$HOME/back"

# List available backups
echo "Available backups in $BACKUP_DIR:"
ls "$BACKUP_DIR" || { echo "No backups found in $BACKUP_DIR. Exiting."; exit 1; }

# Prompt user to select a backup
read -p "Enter the backup to restore (folder name or .tar.gz file): " SELECTED_BACKUP

# Check if the selected backup exists
if [ -d "$BACKUP_DIR/$SELECTED_BACKUP" ]; then
    RESTORE_PATH="$BACKUP_DIR/$SELECTED_BACKUP"
    echo "Restoring from folder: $RESTORE_PATH"
elif [ -f "$BACKUP_DIR/$SELECTED_BACKUP" ]; then
    if [[ "$SELECTED_BACKUP" == *.tar.gz ]]; then
        echo "Extracting and restoring from archive: $SELECTED_BACKUP"
        RESTORE_PATH=$(mktemp -d)
        tar -xzf "$BACKUP_DIR/$SELECTED_BACKUP" -C "$RESTORE_PATH" || { echo "Extraction failed. Exiting."; exit 1; }
    else
        echo "Invalid backup format. Only folders or .tar.gz files are supported."
        exit 1
    fi
else
    echo "Backup not found!"
    exit 1
fi

# Ensure .ssh directory exists
mkdir -p ~/.ssh

# Restore SSH keys
read -p "Restore SSH keys? (y/n): " RESTORE_SSH
if [ "$RESTORE_SSH" == "y" ]; then
    echo "Restoring SSH keys..."
    cp "$RESTORE_PATH/id" ~/.ssh/ 2>/dev/null && chmod 600 ~/.ssh/id
    cp "$RESTORE_PATH/id.pub" ~/.ssh/ 2>/dev/null && chmod 644 ~/.ssh/id.pub
    echo "SSH keys restored."
fi

# Restore GPG keys
read -p "Restore GPG keys? (y/n): " RESTORE_GPG
if [ "$RESTORE_GPG" == "y" ]; then
    echo "Restoring GPG keys..."
    gpg --import "$RESTORE_PATH/private-gpg-key.asc" 2>/dev/null
    gpg --import "$RESTORE_PATH/public-gpg-key.asc" 2>/dev/null
    cp -r "$RESTORE_PATH/gnupg-backup" ~/.gnupg 2>/dev/null && chmod -R 700 ~/.gnupg
    echo "GPG keys restored."
fi

# Restore API keys
read -p "Restore API keys file? (y/n): " RESTORE_API
if [ "$RESTORE_API" == "y" ]; then
    if [ -f "$RESTORE_PATH/api_keys-backup" ]; then
        echo "Restoring API keys file..."
        cp "$RESTORE_PATH/api_keys-backup" ~/.api_keys && chmod 600 ~/.api_keys
    else
        echo "API keys file not found in backup, skipping..."
    fi
fi

# Restore Zsh configuration files
read -p "Restore Zsh configuration files? (y/n): " RESTORE_ZSH
if [ "$RESTORE_ZSH" == "y" ]; then
    echo "Restoring Zsh configuration files..."
    cp "$RESTORE_PATH/"{.antigenrc,.extrazshrc,.zsh1,.zshrc,.aliases} ~ 2>/dev/null || echo "Some Zsh config files not found, skipping..."
    cp -r "$RESTORE_PATH/zsh_files" ~/.zsh_files 2>/dev/null || echo "Zsh files not found, skipping..."
    cp -r "$RESTORE_PATH/.zshrc.d" ~/ 2>/dev/null || echo ".zshrc.d directory not found, skipping..."
fi

# Restore keyrings
read -p "Restore keychains? (y/n): " RESTORE_KEYCHAINS
if [ "$RESTORE_KEYCHAINS" == "y" ]; then
    echo "Restoring keychains..."
    cp -r "$RESTORE_PATH/keyrings" ~/.local/share/keyrings 2>/dev/null && chmod -R 700 ~/.local/share/keyrings
    echo "Keychains restored."
fi

# Restore .config directory
read -p "Restore .config directory? (y/n): " RESTORE_CONFIG
if [ "$RESTORE_CONFIG" == "y" ]; then
    echo "Restoring .config directory..."
    cp -r "$RESTORE_PATH/config-backup" ~/.config 2>/dev/null
    echo ".config directory restored."
fi

# Restore Git credential manager
read -p "Restore Git credential manager? (y/n): " RESTORE_GIT
if [ "$RESTORE_GIT" == "y" ]; then
    echo "Restoring Git credential manager configuration..."
    if [ -f "$RESTORE_PATH/git-credential-helper" ]; then
        cp "$RESTORE_PATH/git-credential-helper" "$(git config --get credential.helper)" 2>/dev/null
        echo "Git credential manager restored."
    else
        echo "Git credential manager configuration not found in backup."
    fi
fi

# Cleanup temporary files if archive was extracted
if [ -n "$TEMP_DIR" ]; then
    echo "Cleaning up temporary extraction files..."
    rm -rf "$TEMP_DIR"
fi

echo "Restore process completed successfully."
