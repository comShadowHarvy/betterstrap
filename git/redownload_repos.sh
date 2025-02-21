#!/bin/bash
# ----------------------------------------------------------------------
# Script: Redownload Repos Script
# Author: ShadowHarvy
# Description: Reads the backup file from ~/git and clones any missing
#              repositories back into the folder.
# ----------------------------------------------------------------------
clear
cat << "EOF"
******************************************
*      Welcome to Redownload Repos       *
*   This script reads the backup file and  *
*    clones any missing git repositories   *
*             from ~/git                   *
*            Author: ShadowHarvy           *
******************************************
EOF
sleep 5

REPO_DIR=~/git
BACKUP_FILE="$REPO_DIR/repos_backup.txt"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found at $BACKUP_FILE"
    exit 1
fi

while read repo url; do
    if [ ! -d "$REPO_DIR/$repo" ]; then
         echo "Cloning $repo from $url..."
         git clone "$url" "$REPO_DIR/$repo"
         echo "Downloaded $repo."
    else
         echo "Repository '$repo' already exists. Skipping."
    fi
done < "$BACKUP_FILE"
