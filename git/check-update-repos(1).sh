#!/bin/bash
# ==========================================================
# Repository Management Script
# Created by: ShadowHarvy
# 
# This script checks for git and development directories,
# creates them if they don't exist, updates all repositories,
# and creates a backup of repository details.
# ==========================================================

# Title Screen
clear
echo "====================================================================="
echo "  _____                 _____                   _                    "
echo " |  __ \               |  __ \                 | |                   "
echo " | |__) |___ _ __   ___| |__) |___ _ __   ___  | |    ___   __ _    "
echo " |  _  // _ \ '_ \ / _ \  _  // _ \ '_ \ / _ \ | |   / _ \ / _\` |   "
echo " | | \ \  __/ |_) | (_) | | \ \  __/ |_) |  __/| |__| (_) | (_| |   "
echo " |_|  \_\___| .__/ \___/|_|  \_\___| .__/ \___||_____\___/ \__, |   "
echo "            | |                    | |                       __/ |   "
echo "            |_|                    |_|                      |___/    "
echo "                                                                     "
echo " Created by: ShadowHarvy                                            "
echo "====================================================================="

# Loading animation
echo -n " Loading system "
for i in {1..30}; do
  echo -n "."
  sleep 0.1
done
echo " DONE!"

# System initialization effect
echo ""
echo " [*] Initializing repository manager..."
sleep 0.7
echo " [*] Checking system dependencies..."
sleep 0.5
echo " [*] Establishing secure connection..."
sleep 0.8
echo " [*] Starting main program..."
sleep 0.5
echo ""

# Define directories
HOME_DIR="$HOME"
GIT_DIR="$HOME_DIR/git"
DEV_DIR="$HOME_DIR/development"
BACKUP_DIR="$HOME_DIR/backup"
BACKUP_FILE="$BACKUP_DIR/repo_backup.txt"

# Check and create directories if they don't exist
echo "Checking directories..."
if [ ! -d "$GIT_DIR" ]; then
    echo "Creating git directory: $GIT_DIR"
    mkdir -p "$GIT_DIR"
fi

if [ ! -d "$DEV_DIR" ]; then
    echo "Creating development directory: $DEV_DIR"
    mkdir -p "$DEV_DIR"
fi

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
fi

# Determine which directory to use for repositories
if [ -d "$GIT_DIR" ]; then
    REPO_DIR="$GIT_DIR"
    echo "Using git directory for repositories: $REPO_DIR"
else
    REPO_DIR="$DEV_DIR"
    echo "Using development directory for repositories: $REPO_DIR"
fi

# Initialize or clear backup file
echo "# Repository Backup File" > "$BACKUP_FILE"
echo "# Created: $(date)" >> "$BACKUP_FILE"
echo "# Format: repository_url,directory_name" >> "$BACKUP_FILE"
echo "" >> "$BACKUP_FILE"

# Function to update repositories and add them to backup file
update_repositories() {
    local dir="$1"
    echo "Checking for repositories in $dir..."
    
    # Find all git repositories in the directory
    for repo_dir in $(find "$dir" -name ".git" -type d -prune); do
        # Get the parent directory of the .git folder
        repo_dir="$(dirname "$repo_dir")"
        echo "Found repository: $repo_dir"
        
        # Change to the repository directory
        cd "$repo_dir" || continue
        
        # Get the repository URL
        repo_url=$(git config --get remote.origin.url)
        if [ -n "$repo_url" ]; then
            echo "Updating repository: $repo_dir"
            git pull
            
            # Add to backup file
            echo "$repo_url,$(basename "$repo_dir")" >> "$BACKUP_FILE"
            echo "Added to backup file: $repo_url"
        else
            echo "No remote origin found for $repo_dir, skipping..."
        fi
    done
}

# Update repositories in both directories
if [ -d "$GIT_DIR" ]; then
    update_repositories "$GIT_DIR"
fi

if [ -d "$DEV_DIR" ]; then
    update_repositories "$DEV_DIR"
fi

echo "Repository update and backup completed."
echo "Backup file created at: $BACKUP_FILE"