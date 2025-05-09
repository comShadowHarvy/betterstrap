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

# Define the mount points
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

# Create the base /share directory if it doesn't exist
if [ ! -d "/share" ]; then
  echo "Creating directory: /share"
  sudo mkdir -p "/share"
else
  echo "Directory already exists: /share"
fi

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
    echo "$entry" | sudo tee -a /etc/fstab >/dev/null
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

  # Create additional specific symlinks in /share directory (for USB shares)
  if [ "$mount_point" == "/mnt/usb_share" ]; then
    custom_link_path="/share/usb1"
    if [ ! -L "$custom_link_path" ]; then
      echo "Creating symlink: $custom_link_path -> $mount_point"
      sudo ln -s "$mount_point" "$custom_link_path"
    else
      echo "Symlink already exists: $custom_link_path"
    fi
  elif [ "$mount_point" == "/mnt/usb_share_2" ]; then
    custom_link_path="/share/usb2"
    if [ ! -L "$custom_link_path" ]; then
      echo "Creating symlink: $custom_link_path -> $mount_point"
      sudo ln -s "$mount_point" "$custom_link_path"
    else
      echo "Symlink already exists: $custom_link_path"
    fi
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

# --- NEW: Map /share/trans to ~/temp ---
echo "Setting up /share/trans link..."

# Ensure ~/temp directory exists
temp_dir="$HOME/temp" # This is the target directory
if [ ! -d "$temp_dir" ]; then
  echo "Creating directory: $temp_dir"
  mkdir -p "$temp_dir" # No sudo needed for home directory
else
  echo "Directory already exists: $temp_dir"
fi

# Define the custom link name
custom_trans_link_name="/share/trans" # This is the link you will access

# Create the symbolic link /share/trans pointing to ~/temp if it doesn't exist
# Note: /share directory should have been created earlier in the script
if [ ! -L "$custom_trans_link_name" ]; then
  echo "Creating symlink: $custom_trans_link_name -> $temp_dir"
  # $temp_dir is the target, $custom_trans_link_name is the name of the link itself
  sudo ln -s "$temp_dir" "$custom_trans_link_name"
else
  echo "Symlink already exists: $custom_trans_link_name"
fi
# --- END NEW ---

echo "All tasks completed! Directories created, /etc/fstab updated, symlinks established, and shares mounted."
