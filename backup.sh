#!/bin/bash

# Define backup directory
BACKUP_DIR="$HOME/back"

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

# Function to restore a file
restore_file() {
    local file=$1
    local dest=$2
    if [ -f "$BACKUP_DIR/$SELECTED_BACKUP/$file" ]; then
        cp "$BACKUP_DIR/$SELECTED_BACKUP/$file" "$dest" && echo "Restored: $file"
    else
        echo "File not found in backup: $file"
    fi
}

# Function to restore a directory
restore_dir() {
    local dir=$1
    local dest=$2
    if [ -d "$BACKUP_DIR/$SELECTED_BACKUP/$dir" ]; then
        cp -r "$BACKUP_DIR/$SELECTED_BACKUP/$dir" "$dest" && echo "Restored: $dir"
    else
        echo "Directory not found in backup: $dir"
    fi
}

echo "Starting restore process..."

# List of dotfiles and directories to restore
dotfiles=(
    ".bashrc"
    ".zshrc"
    ".vimrc"
    ".gitconfig"
    ".profile"
    ".config"
    ".local/share"
    ".ssh"
    ".gnupg"
    ".api_keys"
    ".aliases"
    ".antigenrc"
    ".extrazshrc"
    ".zsh1"
    ".zsh_files"
    ".zshrc.d"
)

# Restore each file and directory
for item in "${dotfiles[@]}"; do
    if [ -d "$BACKUP_DIR/$SELECTED_BACKUP/$item" ]; then
        restore_dir "$item" "$HOME"
    else
        restore_file "$item" "$HOME"
    fi
done

echo "Restore process completed."
