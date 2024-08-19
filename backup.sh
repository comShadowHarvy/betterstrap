#!/bin/bash

# Define backup directory
BACKUP_DIR="$HOME/back"
DATE=$(date +%Y-%m-%d)
BACKUP_DIR="$BACKUP_DIR/backup_$DATE"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# SSH backup
echo "Backing up SSH keys..."
cp ~/.ssh/id ~/.ssh/id.pub "$BACKUP_DIR"

# GPG keys backup
echo "Backing up GPG keys..."
GPG_KEY_ID="6E84E35B67DC0349"  # Replace with your actual GPG key ID
gpg --armor --export $GPG_KEY_ID > "$BACKUP_DIR/public-gpg-key.asc"
gpg --armor --export-secret-keys $GPG_KEY_ID > "$BACKUP_DIR/private-gpg-key.asc"

# GPG configuration backup
echo "Backing up GPG configuration..."
cp -r ~/.gnupg "$BACKUP_DIR/gnupg-backup"

# API keys file backup
echo "Backing up API keys file..."
if [ -f "$HOME/.api_keys" ]; then
    cp ~/.api_keys "$BACKUP_DIR/api_keys-backup"
else
    echo "API keys file not found, skipping..."
fi

# Zsh configuration files backup
echo "Backing up Zsh configuration files..."
cp ~/.antigenrc "$BACKUP_DIR"
cp ~/.extrazshrc "$BACKUP_DIR"
cp ~/.zsh1 "$BACKUP_DIR"
cp ~/.zshrc "$BACKUP_DIR"
cp ~/.aliases "$BACKUP_DIR"
cp ~/.zsh_files/variables.zsh "$BACKUP_DIR"
cp ~/.zsh_files/aliases.zsh "$BACKUP_DIR"
cp ~/.zsh_files/tct.zsh "$BACKUP_DIR"
cp ~/.zsh_files/functions.zsh "$BACKUP_DIR"

# Backup .zshrc.d directory
if [ -d ~/.zshrc.d ]; then
    echo "Backing up .zshrc.d directory..."
    cp -r ~/.zshrc.d "$BACKUP_DIR"
else
    echo ".zshrc.d directory not found, skipping..."
fi

# Optional encryption
read -p "Would you like to encrypt the backup? (y/n): " ENCRYPT

if [ "$ENCRYPT" == "y" ]; then
    echo "Encrypting backup..."
    tar -czf - "$BACKUP_DIR" | gpg --cipher-algo AES256 -c -o "$BACKUP_DIR.tar.gz.gpg"
    rm -rf "$BACKUP_DIR"
    echo "Backup encrypted and saved as $BACKUP_DIR.tar.gz.gpg"
else
    echo "Backup saved in $BACKUP_DIR"
fi

echo "Backup completed."
