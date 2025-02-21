#!/bin/bash
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
