#!/bin/bash

# Define the SMB share entries
entries=(
  "//192.168.1.210/media/ /mnt/hass_media cifs username=me,password=Jbean343343343,uid=1000,gid=1000 0 0"
  "//192.168.1.210/config/ /mnt/hass_config cifs username=me,password=Jbean343343343,uid=1000,gid=1000 0 0"
  "//192.168.1.210/share/ /mnt/hass_share cifs username=me,password=Jbean343343343,uid=1000,gid=1000 0 0"
  "//192.168.1.47/USB-Share /mnt/usb_share cifs guest,uid=1000,gid=1000 0 0"
  "//192.168.1.47/USB-Share-2 /mnt/usb_share_2 cifs guest,uid=1000,gid=1000 0 0"
  "//192.168.1.47/ROM-Share /mnt/rom_share cifs guest,uid=1000,gid=1000 0 0"
)

# Define the mount points and corresponding home directory links
mount_points=(
  "/mnt/hass_media"
  "/mnt/hass_config"
  "/mnt/hass_share"
  "/mnt/usb_share"
  "/mnt/usb_share_2"
  "/mnt/rom_share"
)

# Backup the current /etc/fstab file with a timestamp
timestamp=$(date "+%Y%m%d%H%M%S")
backup_file="/etc/fstab.bak.$timestamp"
sudo cp /etc/fstab "$backup_file"
echo "Backup of /etc/fstab created at $backup_file"

# Loop through each entry, create directories, update /etc/fstab, create symlinks, and mount
for i in "${!entries[@]}"; do
  entry="${entries[$i]}"
  mount_point="${mount_points[$i]}"
  home_link="$HOME/$(basename "$mount_point")"

  # Create the mount point directory if it doesn't exist
  if [ ! -d "$mount_point" ]; then
    echo "Creating directory: $mount_point"
    sudo mkdir -p "$mount_point"
  else
    echo "Directory already exists: $mount_point"
  fi

  # Add the entry to /etc/fstab if it doesn't exist
  if ! grep -Fq "$entry" /etc/fstab; then
    echo "Adding entry to /etc/fstab: $entry"
    echo "$entry" | sudo tee -a /etc/fstab > /dev/null
  else
    echo "Entry already exists in /etc/fstab: $entry"
  fi

  # Create a symbolic link in the home directory if it doesn't exist
  if [ ! -L "$home_link" ]; then
    echo "Creating symlink: $home_link -> $mount_point"
    ln -s "$mount_point" "$home_link"
  else
    echo "Symlink already exists: $home_link"
  fi

  # Mount the directory
  echo "Mounting $mount_point"
  if sudo mount "$mount_point"; then
    echo "Successfully mounted $mount_point"
  else
    echo "Failed to mount $mount_point"
    echo "Please check the /etc/fstab entry or network connectivity."
  fi
done

echo "All tasks completed! Directories created, /etc/fstab updated, symlinks established, and shares mounted."
