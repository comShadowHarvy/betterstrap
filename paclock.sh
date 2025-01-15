#!/bin/bash

# Define the lock file path
LOCK_FILE="/var/lib/pacman/db.lck"

# Check if the lock file exists
if [ -e "$LOCK_FILE" ]; then
    echo "Database lock file found: $LOCK_FILE"

    # Prompt for confirmation to remove the lock file
    read -p "Do you want to remove the lock file? (y/n): " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # Remove the lock file
        sudo rm "$LOCK_FILE"
        echo "Lock file removed successfully."
    else
        echo "Operation cancelled by the user."
    fi
else
    echo "No database lock file found. No action needed."
fi
