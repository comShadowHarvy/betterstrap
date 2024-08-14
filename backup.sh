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

# API keys backup
echo "Backing up API keys..."
cp -r ~/.apikeys "$BACKUP_DIR/apikeys-backup"

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
