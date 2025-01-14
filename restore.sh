#!/bin/bash

# Define backup directory
BACKUP_DIR="$HOME/back"
DATE=$(date +%Y-%m-%d)

# List available backups
echo "Available backups in $BACKUP_DIR:"
ls "$BACKUP_DIR" || { echo "No backups found in $BACKUP_DIR. Exiting."; exit 1; }

# Prompt user to select a backup
read -p "Enter the backup folder you want to restore (e.g., backup_YYYY-MM-DD): " SELECTED_BACKUP

# Check if the selected backup exists
if [ ! -d "$BACKUP_DIR/$SELECTED_BACKUP" ]; then
    echo "Backup folder not found!"
    exit 1
fi

# Check if backup is encrypted
read -p "Is the backup encrypted (e.g., .tar.gz.gpg file)? (y/n): " ENCRYPTED

if [ "$ENCRYPTED" == "y" ]; then
    read -p "Enter the backup file name (e.g., backup_YYYY-MM-DD.tar.gz.gpg): " ENCRYPTED_FILE
    if [ ! -f "$BACKUP_DIR/$ENCRYPTED_FILE" ]; then
        echo "Encrypted backup file not found!"
        exit 1
    fi
    echo "Decrypting and extracting backup..."
    gpg -d "$BACKUP_DIR/$ENCRYPTED_FILE" | tar xz -C "$BACKUP_DIR/$SELECTED_BACKUP" || { echo "Decryption failed. Exiting."; exit 1; }
    echo "Backup decrypted and extracted."
fi

# Ensure .ssh directory exists
mkdir -p ~/.ssh

# Optional: Confirm restoring components
read -p "Restore SSH keys? (y/n): " RESTORE_SSH
if [ "$RESTORE_SSH" == "y" ]; then
    echo "Restoring SSH keys..."
    cp "$BACKUP_DIR/$SELECTED_BACKUP/id" ~/.ssh/ 2>/dev/null && chmod 600 ~/.ssh/id
    cp "$BACKUP_DIR/$SELECTED_BACKUP/id.pub" ~/.ssh/ 2>/dev/null && chmod 644 ~/.ssh/id.pub
    echo "SSH keys restored."
fi

# Restore GPG keys
read -p "Restore GPG keys? (y/n): " RESTORE_GPG
if [ "$RESTORE_GPG" == "y" ]; then
    echo "Restoring GPG keys..."
    gpg --import "$BACKUP_DIR/$SELECTED_BACKUP/private-gpg-key.asc" 2>/dev/null
    gpg --import "$BACKUP_DIR/$SELECTED_BACKUP/public-gpg-key.asc" 2>/dev/null
    cp -r "$BACKUP_DIR/$SELECTED_BACKUP/gnupg-backup" ~/.gnupg 2>/dev/null && chmod -R 700 ~/.gnupg
    echo "GPG keys restored."
fi

# API keys file restore
read -p "Restore API keys file? (y/n): " RESTORE_API
if [ "$RESTORE_API" == "y" ]; then
    if [ -f "$BACKUP_DIR/$SELECTED_BACKUP/api_keys-backup" ]; then
        echo "Restoring API keys file..."
        cp "$BACKUP_DIR/$SELECTED_BACKUP/api_keys-backup" ~/.api_keys && chmod 600 ~/.api_keys
    else
        echo "API keys file not found in backup, skipping..."
    fi
fi

# Restore Zsh configuration files
read -p "Restore Zsh configuration files? (y/n): " RESTORE_ZSH
if [ "$RESTORE_ZSH" == "y" ]; then
    echo "Restoring Zsh configuration files..."
    zsh_files=(
        ".antigenrc"
        ".extrazshrc"
        ".zsh1"
        ".zshrc"
        ".aliases"
        "variables.zsh"
        "aliases.zsh"
        "tct.zsh"
        "functions.zsh"
    )
    for file in "${zsh_files[@]}"; do
        if [ -f "$BACKUP_DIR/$SELECTED_BACKUP/$file" ]; then
            cp "$BACKUP_DIR/$SELECTED_BACKUP/$file" ~/
            echo "Restored: $file"
        else
            echo "File not found in backup: $file"
        fi
    done

    # Restore .zshrc.d directory
    if [ -d "$BACKUP_DIR/$SELECTED_BACKUP/.zshrc.d" ]; then
        echo "Restoring .zshrc.d directory..."
        cp -r "$BACKUP_DIR/$SELECTED_BACKUP/.zshrc.d" ~/
    else
        echo ".zshrc.d directory not found in backup, skipping..."
    fi
fi

echo "Restore process completed."
