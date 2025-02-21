#!/bin/bash
# ----------------------------------------------------------------------
# Script: Backup Repos Script
# Author: ShadowHarvy
# Description: Scans the ~/git directory for git repositories and saves
#              each repository's folder name and remote URL into a backup file.
# ----------------------------------------------------------------------
clear
echo "****************************************"
echo "*         Backup Repos Script          *"
echo "*   Scans ~/git for git repos and saves  *"
echo "*   their names and remote URLs to a file*"
echo "*                                      *"
echo "*            ShadowHarvy               *"
echo "****************************************"
sleep 5

REPO_DIR=~/git
BACKUP_FILE="$REPO_DIR/repos_backup.txt"
> "$BACKUP_FILE"

for d in "$REPO_DIR"/*; do
    if [ -d "$d/.git" ]; then
         repo=$(basename "$d")
         url=$(git -C "$d" config --get remote.origin.url)
         echo "$repo $url" >> "$BACKUP_FILE"
    fi
done

echo "Backup created at $BACKUP_FILE"
