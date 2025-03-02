#!/bin/bash
# If repository folder does not exist, clone it; otherwise, update it
if [ ! -d "Momentum-Firmware" ]; then
    echo "Cloning repository..."
    git clone --recursive --jobs 8 https://github.com/Next-Flip/Momentum-Firmware.git || { echo "Clone failed"; exit 1; }
else
    echo "Repository already exists. Pulling updates..."
fi

cd Momentum-Firmware || { echo "Failed to change directory"; exit 1; }

# Update repository if .git exists
if [ -d ".git" ]; then
    git pull || { echo "Git pull failed."; exit 1; }
fi

# Run the flash command
echo "Flashing device as normal user..."
./fbt flash_usb_full
if [ $? -ne 0 ]; then
    echo "Flash command failed. Retrying as root..."
    sudo ./fbt flash_usb_full
fi
