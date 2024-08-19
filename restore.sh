#!/bin/bash

# Define backup directory
BACKUP_DIR="$HOME/back"
DATE=$(date +%Y-%m-%d)

# List available backups
echo "Available backups:"
ls "$BACKUP_DIR"
read -p "Enter the backup folder you want to restore (e.g., backup_YYYY-MM-DD): " SELECTED_BACKUP

# Check if the selected backup exists
if [ ! -d "$BACKUP_DIR/$SELECTED_BACKUP" ]; then
    echo "Backup folder not found!"
    exit 1
fi

# Ensure the .ssh directory exists
mkdir -p ~/.ssh

# SSH restore
echo "Restoring SSH keys..."
cp "$BACKUP_DIR/$SELECTED_BACKUP/id" ~/.ssh/
cp "$BACKUP_DIR/$SELECTED_BACKUP/id.pub" ~/.ssh/
chmod 600 ~/.ssh/id
chmod 644 ~/.ssh/id.pub

# GPG keys restore
echo "Restoring GPG keys..."
gpg --import "$BACKUP_DIR/$SELECTED_BACKUP/private-gpg-key.asc"
gpg --import "$BACKUP_DIR/$SELECTED_BACKUP/public-gpg-key.asc"

# GPG configuration restore
echo "Restoring GPG configuration..."
cp -r "$BACKUP_DIR/$SELECTED_BACKUP/gnupg-backup" ~/.gnupg
chmod -R 700 ~/.gnupg

# API keys file restore
if [ -f "$BACKUP_DIR/$SELECTED_BACKUP/api_keys-backup" ]; then
    echo "Restoring API keys file..."
    cp "$BACKUP_DIR/$SELECTED_BACKUP/api_keys-backup" ~/.api_keys
    chmod 600 ~/.api_keys
else
    echo "API keys file not found in backup, skipping..."
fi

# Optional decryption (if the backup was encrypted)
read -p "Is the backup encrypted (did you create a .tar.gz.gpg file)? (y/n): " ENCRYPTED

if [ "$ENCRYPTED" == "y" ]; then
    read -p "Enter the backup .tar.gz.gpg file name (e.g., backup_YYYY-MM-DD.tar.gz.gpg): " ENCRYPTED_FILE
    gpg -d "$BACKUP_DIR/$ENCRYPTED_FILE" | tar xz -C "$HOME"
    echo "Backup decrypted and restored."
fi

# Restore additional zsh configuration files
echo "Restoring additional zsh configuration files..."
cp "$BACKUP_DIR/$SELECTED_BACKUP/.antigenrc" ~/
cp "$BACKUP_DIR/$SELECTED_BACKUP/.extrazshrc" ~/
cp "$BACKUP_DIR/$SELECTED_BACKUP/.zsh1" ~/
cp "$BACKUP_DIR/$SELECTED_BACKUP/.zshrc" ~/
cp "$BACKUP_DIR/$SELECTED_BACKUP/.aliases" ~/
cp "$BACKUP_DIR/$SELECTED_BACKUP/variables.zsh" ~/.zsh_files/
cp "$BACKUP_DIR/$SELECTED_BACKUP/aliases.zsh" ~/.zsh_files/
cp "$BACKUP_DIR/$SELECTED_BACKUP/tct.zsh" ~/.zsh_files/
cp "$BACKUP_DIR/$SELECTED_BACKUP/functions.zsh" ~/.zsh_files/

# Restore .zshrc.d directory
if [ -d "$BACKUP_DIR/$SELECTED_BACKUP/.zshrc.d" ]; then
    echo "Restoring .zshrc.d directory..."
    cp -r "$BACKUP_DIR/$SELECTED_BACKUP/.zshrc.d" ~/
else
    echo ".zshrc.d directory not found in backup, skipping..."
fi

echo "Restore completed."
