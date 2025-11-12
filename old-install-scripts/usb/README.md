# USB Device Notification System

Automatic desktop notifications for USB and block devices on Arch Linux.

## Features

### Block Device Notifications (USB drives, external HDDs/SSDs)
Shows comprehensive information when storage devices are connected:
- Device model and vendor
- Filesystem type (ext4, NTFS, FAT32, exFAT, etc.)
- Device label and size
- Mount point (if auto-mounted)
- UUID and serial number
- Bus type (USB, SATA, NVMe)
- Read-only status
- Removable status
- Rotational (HDD vs SSD)

### USB Device Notifications (All USB devices)
Shows information for keyboards, mice, hubs, and other USB devices:
- Model name
- VID:PID
- Serial number
- USB version
- Link speed

## Installation

### Quick Install

```bash
cd ~/betterstrap/old-install-scripts/usb
./install.sh
```

The installer will:
1. Install required packages (udisks2, libnotify, util-linux, coreutils)
2. Optionally install mako if not present
3. Copy scripts to `/usr/local/bin/`
4. Install udev rules to `/etc/udev/rules.d/`
5. Automatically configure for your username
6. Reload udev rules

### Manual Installation

```bash
# Install packages
sudo pacman -S --needed udisks2 libnotify util-linux coreutils mako

# Copy scripts
sudo cp notify-device-added.sh /usr/local/bin/
sudo cp notify-usb-device.sh /usr/local/bin/
sudo chmod 755 /usr/local/bin/notify-device-added.sh /usr/local/bin/notify-usb-device.sh

# Install udev rules (replace USERNAME with your username)
sudo cp 99-device-notify.rules /etc/udev/rules.d/
sudo sed -i 's/{{USERNAME}}/your_username/g' /etc/udev/rules.d/99-device-notify.rules

# Reload udev
sudo udevadm control --reload-rules
```

## Requirements

- **Arch Linux** (may work on other distros with modifications)
- **Notification daemon**: mako, dunst, or similar
- **Wayland or X11** desktop environment
- **udisks2**: For device information
- **util-linux**: Provides lsblk
- **libnotify**: Provides notify-send

## Usage

Once installed, notifications appear automatically when you:
- Plug in a USB storage device
- Connect any USB device (keyboard, mouse, etc.)
- Connect external HDDs/SSDs

### Testing

Test with an existing partition:
```bash
# List partitions
lsblk -pf

# Test notification (replace /dev/sdX1 with actual partition)
XDG_RUNTIME_DIR=/run/user/$(id -u) \
DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus \
/usr/local/bin/notify-device-added.sh /dev/sdX1
```

## Customization

### USB Storage Only

To receive notifications only for USB storage devices (not internal drives):

1. Edit `/etc/udev/rules.d/99-device-notify.rules`
2. Comment out the first two `ACTION=="add"` lines for block devices
3. Uncomment the USB-filtered versions at the bottom
4. Reload: `sudo udevadm control --reload-rules`

### Disable Non-Storage USB Devices

To disable notifications for keyboards, mice, etc.:

1. Edit `/etc/udev/rules.d/99-device-notify.rules`
2. Comment out the line with `SUBSYSTEM=="usb"`
3. Reload: `sudo udevadm control --reload-rules`

### Adjust Mount Detection Delay

If mount points aren't showing in notifications:

1. Edit `/usr/local/bin/notify-device-added.sh`
2. Change `sleep 0.8` to a higher value (e.g., `sleep 1.2`)

## Files

```
~/betterstrap/old-install-scripts/usb/
├── install.sh                    # Installation script
├── notify-device-added.sh        # Block device notification script
├── notify-usb-device.sh          # USB device notification script
├── 99-device-notify.rules        # udev rules template
└── README.md                     # This file
```

After installation:
```
/usr/local/bin/notify-device-added.sh
/usr/local/bin/notify-usb-device.sh
/etc/udev/rules.d/99-device-notify.rules
```

## Troubleshooting

### No notifications appear

1. **Check if mako is running:**
   ```bash
   ps aux | grep mako
   ```
   If not running, start it (usually in your compositor config).

2. **Test notification daemon:**
   ```bash
   notify-send "Test" "This is a test"
   ```

3. **Check udev logs:**
   ```bash
   sudo journalctl -b -u systemd-udevd
   sudo journalctl -b | grep notify-device-added.sh
   ```

4. **Monitor udev events:**
   ```bash
   sudo udevadm monitor --udev --kernel --property
   ```
   Then plug in a device to see if events are detected.

### Notifications for internal drives

If you're getting notifications for internal drives and only want USB:
- Follow the "USB Storage Only" customization above

### Wrong username in udev rules

If notifications don't work after transferring to a new system:
```bash
# Re-run the installer
cd ~/betterstrap/old-install-scripts/usb
./install.sh
```

Or manually edit `/etc/udev/rules.d/99-device-notify.rules` and replace the username.

## Uninstallation

```bash
sudo rm /usr/local/bin/notify-device-added.sh
sudo rm /usr/local/bin/notify-usb-device.sh
sudo rm /etc/udev/rules.d/99-device-notify.rules
sudo udevadm control --reload-rules
```

## License

MIT License - Free to use and modify.
