#!/bin/bash
REPO_DIR=~/git

for d in "$REPO_DIR"/*; do
    if [ -d "$d/.git" ]; then
         echo "Updating $(basename "$d")..."
         git -C "$d" pull
    fi
done
