#!/bin/bash
# Remount /mnt/usb as read-write if it is read-only
if mount | grep -q "/mnt/usb type exfat (ro"; then
    mount -o remount,rw /mnt/usb && echo "/mnt/usb remounted as rw"
fi

# Remount /mnt/usb2 as read-write if it is read-only
if mount | grep -q "/mnt/usb2 type exfat (ro"; then
    mount -o remount,rw /mnt/usb2 && echo "/mnt/usb2 remounted as rw"
fi
