#!/bin/bash
REPO_DIR=~/git
BACKUP_FILE="$REPO_DIR/repos_backup.txt"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found at $BACKUP_FILE"
    exit 1
fi

while read repo url; do
    if [ ! -d "$REPO_DIR/$repo" ]; then
         git clone "$url" "$REPO_DIR/$repo"
    else
         echo "Repository '$repo' already exists. Skipping."
    fi
done < "$BACKUP_FILE"
