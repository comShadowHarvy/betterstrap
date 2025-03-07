#!/bin/bash
# ==========================================================
# Repository Download Script
# Created by: ShadowHarvy
# 
# This script reads the backup file and downloads/clones
# the repositories to the appropriate directory.
# ==========================================================

# Title Screen
clear
echo "===================================================================="
echo "  _____                 _____                      _                 "
echo " |  __ \               |  __ \                    | |                "
echo " | |__) |___ _ __   ___| |  | | _____      ___ __ | | ___   __ _  __| | ___ _ __ "
echo " |  _  // _ \ '_ \ / _ \ |  | |/ _ \ \ /\ / / '_ \| |/ _ \ / _\` |/ _\` |/ _ \ '__|"
echo " | | \ \  __/ |_) | (_) | |__| | (_) \ V  V /| | | | | (_) | (_| | (_| |  __/ |   "
echo " |_|  \_\___| .__/ \___/|_____/ \___/ \_/\_/ |_| |_|_|\___/ \__,_|\__,_|\___|_|   "
echo "            | |                                                      "
echo "            |_|                                                      "
echo "                                                                     "
echo " Created by: ShadowHarvy                                            "
echo "===================================================================="

# Loading animation with spinner
echo -n " Initializing downloader "
spinner=( '|' '/' '-' '\' )
for i in {1..20}; do
  echo -ne "\b${spinner[i%4]}"
  sleep 0.2
done
echo -e "\b READY!"

# Progress bar effect
echo ""
echo " [*] Checking repository database..."
sleep 0.7

echo -n " ["; for i in {1..25}; do echo -n "="; sleep 0.05; done; echo -n ">] "
echo "COMPLETE!"

echo ""
echo " [*] Preparing download system..."
sleep 0.8
echo " [*] Starting repository retrieval process..."
sleep 0.5
echo ""

# Define directories
HOME_DIR="$HOME"
GIT_DIR="$HOME_DIR/git"
DEV_DIR="$HOME_DIR/development"
BACKUP_DIR="$HOME_DIR/backup"
BACKUP_FILE="$BACKUP_DIR/repo_backup.txt"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found at $BACKUP_FILE"
    exit 1
fi

# Determine which directory to use for repositories
if [ -d "$GIT_DIR" ]; then
    REPO_DIR="$GIT_DIR"
    echo "Using git directory for repositories: $REPO_DIR"
else
    REPO_DIR="$DEV_DIR"
    echo "Using development directory for repositories: $REPO_DIR"
fi

# Check if repository directory exists
if [ ! -d "$REPO_DIR" ]; then
    echo "Creating repository directory: $REPO_DIR"
    mkdir -p "$REPO_DIR"
fi

# Read the backup file and clone repositories
echo "Reading backup file and cloning repositories..."
# Skip the header lines (first 4 lines)
tail -n +5 "$BACKUP_FILE" | while IFS="," read -r repo_url repo_name || [[ -n "$repo_url" ]]; do
    # Skip empty lines or comments
    if [[ -z "$repo_url" || "$repo_url" == \#* ]]; then
        continue
    fi
    
    # Clean up the repo name if it has extra whitespace
    repo_name=$(echo "$repo_name" | xargs)
    
    echo "Processing repository: $repo_url"
    
    # If repo_name is empty, extract it from the URL
    if [ -z "$repo_name" ]; then
        repo_name=$(basename "$repo_url" .git)
        echo "Extracted repository name: $repo_name"
    fi
    
    # Check if the repository already exists
    if [ -d "$REPO_DIR/$repo_name" ]; then
        echo "Repository already exists: $REPO_DIR/$repo_name"
        echo "Updating instead of cloning..."
        cd "$REPO_DIR/$repo_name" || continue
        git pull
    else
        echo "Cloning repository: $repo_url to $REPO_DIR/$repo_name"
        git clone "$repo_url" "$REPO_DIR/$repo_name"
    fi
done

echo "Repository download completed."