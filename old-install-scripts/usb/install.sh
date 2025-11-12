#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "USB Device Notification System Installer"
echo "=========================================="
echo ""

# Check if running on Arch Linux
if [[ ! -f /etc/arch-release ]]; then
  echo "Warning: This script is designed for Arch Linux."
  read -p "Continue anyway? (y/N): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Get current username
CURRENT_USER="${SUDO_USER:-$USER}"
if [[ "$CURRENT_USER" == "root" ]]; then
  echo "Error: Please run this script as your regular user (with sudo when needed)."
  echo "Do not run as root directly."
  exit 1
fi

echo "Installing for user: $CURRENT_USER"
echo ""

# Install required packages
echo "Installing required packages..."
sudo pacman -S --needed --noconfirm udisks2 libnotify util-linux coreutils

# Check if mako is installed
if ! command -v mako &> /dev/null; then
  echo ""
  echo "Warning: mako notification daemon not found."
  read -p "Install mako? (Y/n): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    sudo pacman -S --needed --noconfirm mako
    echo "Note: You'll need to start mako in your Wayland compositor config."
  fi
fi

# Copy scripts to /usr/local/bin
echo ""
echo "Installing notification scripts..."
sudo cp "$SCRIPT_DIR/notify-device-added.sh" /usr/local/bin/notify-device-added.sh
sudo cp "$SCRIPT_DIR/notify-usb-device.sh" /usr/local/bin/notify-usb-device.sh
sudo chown root:root /usr/local/bin/notify-device-added.sh /usr/local/bin/notify-usb-device.sh
sudo chmod 755 /usr/local/bin/notify-device-added.sh /usr/local/bin/notify-usb-device.sh

# Create udev rules with correct username
echo "Installing udev rules..."
sudo cp "$SCRIPT_DIR/99-device-notify.rules" /etc/udev/rules.d/99-device-notify.rules.tmp
sudo sed -i "s/{{USERNAME}}/$CURRENT_USER/g" /etc/udev/rules.d/99-device-notify.rules.tmp
sudo mv /etc/udev/rules.d/99-device-notify.rules.tmp /etc/udev/rules.d/99-device-notify.rules
sudo chown root:root /etc/udev/rules.d/99-device-notify.rules
sudo chmod 644 /etc/udev/rules.d/99-device-notify.rules

# Reload udev rules
echo "Reloading udev rules..."
sudo udevadm control --reload-rules

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "The following notifications will be shown:"
echo "  • Block devices (USB drives, HDDs, SSDs) with detailed info"
echo "  • All USB devices (keyboards, mice, hubs, etc.)"
echo ""
echo "Test by plugging in a USB device!"
echo ""
echo "To test manually with an existing partition:"
echo "  lsblk -pf"
echo "  XDG_RUNTIME_DIR=/run/user/\$(id -u) DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/\$(id -u)/bus /usr/local/bin/notify-device-added.sh /dev/sdX1"
echo ""
echo "To restrict to USB storage only, edit /etc/udev/rules.d/99-device-notify.rules"
echo "and follow the instructions in the comments."
echo ""
