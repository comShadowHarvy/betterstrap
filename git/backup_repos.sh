#!/bin/bash
# ----------------------------------------------------------------------
# Script: Backup Repos Script
# Author: ShadowHarvy
# Description: Scans the ~/git directory for git repositories and saves
#              each repository's folder name and remote URL into a backup file.
# ----------------------------------------------------------------------
clear
cat << "EOF"
****************************************
*       Welcome to Backup Repos        *
*  This script scans ~/git for repositories
*   and saves their names and remote URLs
*                to a backup file       *
*            Author: ShadowHarvy         *
****************************************
EOF
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
echo ""
echo "List of backed-up repositories:"
while read repo url; do
    echo " - $repo ($url)"
done < "$BACKUP_FILE"
