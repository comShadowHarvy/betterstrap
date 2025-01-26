#!/bin/bash

# Define the group to check
GROUP="dialout"
USER=$(whoami)

# Check if the group exists
if ! getent group "$GROUP" > /dev/null 2>&1; then
    echo "Group '$GROUP' does not exist. Creating it..."
    sudo groupadd "$GROUP"
    echo "Group '$GROUP' created."
else
    echo "Group '$GROUP' already exists."
fi

# Check if the current user is in the group
if groups "$USER" | grep -q "\b$GROUP\b"; then
    echo "User '$USER' is already in the group '$GROUP'."
else
    echo "Adding user '$USER' to the group '$GROUP'..."
    sudo usermod -aG "$GROUP" "$USER"
    echo "User '$USER' added to the group '$GROUP'."
    echo "You need to log out and back in for the changes to take effect."
fi
