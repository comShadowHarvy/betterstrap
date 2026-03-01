#!/bin/bash
# Script triggered by udev when USB device is added

LOG="$HOME/usb_notify.log"

echo "=== $(date) ===" >> "$LOG"
echo "USB Device Connected" >> "$LOG"
echo "---------------------" >> "$LOG"

# Device info from udev environment
echo "Vendor:  $ID_VENDOR" >> "$LOG"
echo "Model:   $ID_MODEL" >> "$LOG"
echo "Serial:  $ID_SERIAL" >> "$LOG"
echo "Bus:     $BUS" >> "$LOG"
echo "Device:  $DEVICE" >> "$LOG"
echo "Path:    $DEVPATH" >> "$LOG"

# Additional details
echo "" >> "$LOG"
echo "=== Detailed Info ===" >> "$LOG"
lsusb -s "$BUS:$DEVICE" 2>/dev/null >> "$LOG" || echo "lsusb info not available" >> "$LOG"

# Block device info (for storage devices)
if [ -n "$DEVNAME" ]; then
    echo "" >> "$LOG"
    echo "=== Block Device ===" >> "$LOG"
    echo "Device node: $DEVNAME" >> "$LOG"
    if [ -b "$DEVNAME" ]; then
        echo "Size: $(blockdev --getsize64 "$DEVNAME" 2>/dev/null | numfmt --to=iec- 2>/dev/null || echo 'unknown')" >> "$LOG"
    fi
fi

echo "" >> "$LOG"

# Desktop notification if available
if command -v notify-send &>/dev/null; then
    notify-send "USB Device Connected" "$ID_VENDOR $ID_MODEL"
elif command -v zenity &>/dev/null; then
    zenity --info --text="USB Device Connected\n$ID_VENDOR $ID_MODEL" &
fi

# Optional: play a sound
[ -n "$PLAY_SOUND" ] && echo -e "\a"
