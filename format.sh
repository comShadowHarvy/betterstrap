#!/usr/bin/env bash

# Created: $(date)
# Description: 

# Exit on error, undefined vars, and pipe failures
#!/bin/bash

# Exit on error
set -e

# Check if script is run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root. Try 'sudo $0'" >&2
    exit 1
fi

# Clear the screen
clear

# Function to list available drives
list_drives() {
    echo "Available drives:"
    echo "-----------------"
    
    # Get list of drives, excluding loop devices and ram disks
    lsblk -dpno NAME,SIZE,MODEL | grep -v "loop\|ram" | nl -w2 -s") "
    
    echo "-----------------"
}

# Function to list available filesystem types
list_filesystems() {
    echo "Available filesystem types:"
    echo "--------------------------"
    echo "1) fat32    - FAT32 filesystem (recommended for drives < 32GB, compatible with most OS)"
    echo "2) ntfs     - NTFS filesystem (Windows compatible, supports files > 4GB)"
    echo "3) ext4     - Linux filesystem (best for Linux-only use)"
    echo "4) exfat    - Extended FAT (compatible with most OS, supports files > 4GB)"
    echo "5) btrfs    - B-tree filesystem (modern Linux filesystem with advanced features)"
    echo "6) xfs      - High-performance journaling filesystem for Linux"
    echo "--------------------------"
}

# Display warning
echo "WARNING: This script will FORMAT a drive, DESTROYING ALL DATA on it."
echo "Make sure you have backed up any important data before proceeding."
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# List available drives
list_drives

# Get user selection for drive
echo ""
echo "Enter the number of the drive you want to format:"
read drive_number

# Validate drive selection
drive_count=$(lsblk -dpno NAME | grep -v "loop\|ram" | wc -l)
if ! [[ "$drive_number" =~ ^[0-9]+$ ]] || [ "$drive_number" -lt 1 ] || [ "$drive_number" -gt "$drive_count" ]; then
    echo "Invalid selection. Exiting."
    exit 1
fi

# Get the selected drive
selected_drive=$(lsblk -dpno NAME | grep -v "loop\|ram" | sed -n "${drive_number}p")
drive_info=$(lsblk -dno SIZE,MODEL "$selected_drive" | tr -s ' ')

echo ""
echo "You selected: $selected_drive ($drive_info)"
echo ""

# List available filesystem types
list_filesystems

# Get user selection for filesystem
echo ""
echo "Enter the number of the filesystem type (default: 1 for fat32):"
read fs_number

# Set default to fat32 if no input
if [ -z "$fs_number" ]; then
    fs_number=1
fi

# Validate filesystem selection
if ! [[ "$fs_number" =~ ^[0-9]+$ ]] || [ "$fs_number" -lt 1 ] || [ "$fs_number" -gt 6 ]; then
    echo "Invalid selection. Using default (fat32)."
    fs_number=1
fi

# Map selection to filesystem type and format command
case $fs_number in
    1)
        fs_type="fat32"
        format_cmd="mkfs.vfat -F 32"
        ;;
    2)
        fs_type="ntfs"
        format_cmd="mkfs.ntfs -f"
        ;;
    3)
        fs_type="ext4"
        format_cmd="mkfs.ext4 -F"
        ;;
    4)
        fs_type="exfat"
        format_cmd="mkfs.exfat"
        ;;
    5)
        fs_type="btrfs"
        format_cmd="mkfs.btrfs -f"
        ;;
    6)
        fs_type="xfs"
        format_cmd="mkfs.xfs -f"
        ;;
esac

# Ask for label
echo ""
echo "Enter a label for the drive (optional, press Enter to skip):"
read drive_label

# Prepare label option if provided
label_option=""
if [ ! -z "$drive_label" ]; then
    case $fs_type in
        fat32)
            label_option="-n \"$drive_label\""
            ;;
        ntfs)
            label_option="-L \"$drive_label\""
            ;;
        ext4)
            label_option="-L \"$drive_label\""
            ;;
        exfat)
            label_option="-n \"$drive_label\""
            ;;
        btrfs)
            label_option="-L \"$drive_label\""
            ;;
        xfs)
            label_option="-L \"$drive_label\""
            ;;
    esac
fi

# Final confirmation
echo ""
echo "You are about to format $selected_drive ($drive_info) with $fs_type filesystem."
if [ ! -z "$drive_label" ]; then
    echo "Drive label will be: $drive_label"
fi
echo ""
echo "WARNING: This will DESTROY ALL DATA on $selected_drive!"
echo "Type 'YES' (all caps) to confirm and proceed with formatting:"
read confirmation

if [ "$confirmation" != "YES" ]; then
    echo "Formatting cancelled. Exiting."
    exit 0
fi

# Unmount the drive if it's mounted
echo "Unmounting $selected_drive if mounted..."
umount "$selected_drive"* 2>/dev/null || true

# Format the drive
echo "Formatting $selected_drive as $fs_type..."
eval "$format_cmd $label_option $selected_drive"

echo ""
echo "Formatting complete!"
echo "Drive $selected_drive has been formatted as $fs_type."
if [ ! -z "$drive_label" ]; then
    echo "Drive label set to: $drive_label"
fi
