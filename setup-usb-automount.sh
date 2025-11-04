#!/bin/bash
# USB Automounting Setup Script for Arch Linux + Hyprland
# This script configures automatic USB device mounting with notifications

set -e

echo "=== USB Automounting Setup ==="
echo

# Install required packages
echo "Installing required packages..."
sudo pacman -S --needed udisks2 udiskie exfatprogs dosfstools f2fs-tools polkit-gnome mako libnotify

echo
echo "Creating udiskie configuration..."
mkdir -p ~/.config/udiskie

cat > ~/.config/udiskie/config.yml << 'EOF'
program_options:
  automount: true
  notify: true
  tray: false

# Optional per-filesystem mount options (tune as desired):
# mount_options:
#   ntfs3: [windows_names, big_writes]
#   vfat:  [shortname=mixed, utf8=1]
#   exfat: []
#   f2fs:  []
#   ext4:  []
#   btrfs: []
#   xfs:   []
EOF

echo "Created ~/.config/udiskie/config.yml"

# Create symlink
echo
echo "Creating ~/usb symlink to /run/media/$USER..."
ln -sfn /run/media/$USER ~/usb
echo "Symlink created: ~/usb -> /run/media/$USER"

# Add to Hyprland autostart
echo
echo "Configuring Hyprland autostart..."
AUTOSTART_FILE="$HOME/.config/hypr/autostart.conf"

# Check if autostart entries already exist
if grep -q "udiskie" "$AUTOSTART_FILE" 2>/dev/null; then
    echo "USB automount entries already exist in $AUTOSTART_FILE"
else
    cat >> "$AUTOSTART_FILE" << 'EOF'

# USB automounting and related services
exec-once = /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1
exec-once = mako
exec-once = udiskie
EOF
    echo "Added autostart entries to $AUTOSTART_FILE"
fi

# Start services now (if not already running)
echo
echo "Starting services..."

if ! pgrep -x polkit-gnome-authentication-agent-1 > /dev/null; then
    /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &
    echo "Started polkit-gnome"
else
    echo "polkit-gnome already running"
fi

if ! pgrep -x mako > /dev/null; then
    mako &
    echo "Started mako"
else
    echo "mako already running"
fi

if ! pgrep -x udiskie > /dev/null; then
    udiskie &
    echo "Started udiskie"
else
    echo "udiskie already running"
fi

echo
echo "=== Setup Complete! ==="
echo
echo "Summary:"
echo "  • USB devices will automount to: /run/media/$USER/<device-label>"
echo "  • Accessible via: ~/usb/<device-label>"
echo "  • Notifications enabled for mount/unmount events"
echo "  • Filesystem support: NTFS (ntfs3), exFAT, FAT32, ext4, F2FS, and more"
echo
echo "Test it: Plug in a USB device and check ~/usb/"
echo "Verify NTFS driver: findmnt -t ntfs3"
echo
echo "Services will start automatically on next login."
