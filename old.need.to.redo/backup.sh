
#!/bin/bash

# Define backup directory
BACKUP_DIR="$HOME/back"
DATE=$(date +%Y-%m-%d)
BACKUP_NAME="backup_$DATE"
FULL_BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Create backup directory
mkdir -p "$FULL_BACKUP_PATH"

# SSH backup
echo "Backing up SSH keys..."
cp ~/.ssh/id ~/.ssh/id.pub "$FULL_BACKUP_PATH" 2>/dev/null || echo "SSH keys not found, skipping..."

# GPG keys backup
echo "Backing up GPG keys..."
GPG_KEY_ID="6E84E35B67DC0349"  # Replace with your actual GPG key ID
gpg --armor --export $GPG_KEY_ID > "$FULL_BACKUP_PATH/public-gpg-key.asc"
gpg --armor --export-secret-keys $GPG_KEY_ID > "$FULL_BACKUP_PATH/private-gpg-key.asc"

# GPG configuration backup
echo "Backing up GPG configuration..."
cp -r ~/.gnupg "$FULL_BACKUP_PATH/gnupg-backup" 2>/dev/null || echo "GPG configuration not found, skipping..."

# API keys file backup
echo "Backing up API keys file..."
cp ~/.api_keys "$FULL_BACKUP_PATH/api_keys-backup" 2>/dev/null || echo "API keys file not found, skipping..."

# Zsh configuration files backup
echo "Backing up Zsh configuration files..."
cp ~/.antigenrc ~/.extrazshrc ~/.zsh1 ~/.zshrc ~/.aliases ~/.zimrc "$FULL_BACKUP_PATH" 2>/dev/null || echo "Some Zsh config files not found, skipping..."

# Zsh additional files
echo "Backing up additional Zsh files..."
mkdir -p "$FULL_BACKUP_PATH/zsh_files"
cp ~/.zsh_files/* "$FULL_BACKUP_PATH/zsh_files" 2>/dev/null || echo "Zsh files not found, skipping..."

# Backup .zshrc.d directory
echo "Backing up .zshrc.d directory..."
cp -r ~/.zshrc.d "$FULL_BACKUP_PATH" 2>/dev/null || echo ".zshrc.d directory not found, skipping..."

# Backup keyrings
echo "Backing up keyrings..."
cp -r ~/.local/share/keyrings "$FULL_BACKUP_PATH/keyrings" 2>/dev/null || echo "Keyrings not found, skipping..."

# Backup .config directory
echo "Backing up .config directory..."
cp -r ~/.config "$FULL_BACKUP_PATH/config-backup" 2>/dev/null || echo ".config directory not found, skipping..."

# Backup Git credential manager
echo "Backing up Git credential manager..."
GIT_CRED=$(git config --get credential.helper)
if [ -n "$GIT_CRED" ]; then
    echo "$GIT_CRED" > "$FULL_BACKUP_PATH/git-credential-helper"
else
    echo "Git credential manager not configured, skipping..."
fi

# Prompt for compression
read -p "Would you like to compress the backup? (y/n): " COMPRESS
if [ "$COMPRESS" == "y" ]; then
    tar -czf "$FULL_BACKUP_PATH.tar.gz" -C "$FULL_BACKUP_PATH" . && rm -rf "$FULL_BACKUP_PATH"
    echo "Backup compressed to $FULL_BACKUP_PATH.tar.gz"
else
    echo "Backup saved as a folder: $FULL_BACKUP_PATH"
fi

echo "Backup process completed."

# Validate paths before backing up
validate_path() {
    local path="$1"
    if [ -e "$path" ]; then
        echo "Backing up $path..."
        tar_args+=("$path")
    else
        echo "$path not found, skipping..."
    fi
}

# Start of the backup process
tar_args=()

# Validate and add paths to the tar arguments
validate_path "$HOME/.ssh"
validate_path "$HOME/.gnupg"
validate_path "$HOME/.api_keys"
validate_path "$HOME/.zshrc"
validate_path "$HOME/.zshrc.d"
validate_path "$HOME/.config"
validate_path "$HOME/.local/share/keyrings"
validate_path "$HOME/.git-credentials"

# Compress the validated paths into a tar.gz file and split into 60MB blocks
if [ ! -z "$tar_args" ]; then
    compressed_file="/home/me/back/backup_$(date +%Y-%m-%d).tar.gz"
    split_size=60m

    tar -czf - "${tar_args[@]}" 2>/home/me/back/error.log | split -b $split_size - "$compressed_file."
    if [ $? -eq 0 ]; then
        echo "Backup split into 60MB blocks as $compressed_file.*"
    else
        echo "Error occurred during tar or split. Check /home/me/back/error.log for details."
    fi
else
    echo "No valid paths to backup. Exiting."
fi
