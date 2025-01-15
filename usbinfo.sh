#!/bin/bash

# Function to show recent USB devices from dmesg
show_recent_usb_devices() {
    echo "Recent USB device activity (dmesg):"
    dmesg | grep -i usb | tail -n 50
    echo ""
}

# Function to list all connected USB devices
list_connected_usb_devices() {
    echo "Currently connected USB devices (lsusb):"
    lsusb
    echo ""
}

# Function to show detailed information about USB devices
show_detailed_usb_info() {
    echo "Detailed information about USB devices (udevadm):"
    for device in /sys/bus/usb/devices/*; do
        if [[ -d "$device" ]]; then
            device_path=$(udevadm info -q path -n "$device")
            echo "Device Path: $device_path"
            udevadm info -a -p "$device" | grep -E "looking at device|ATTRS{idVendor}|ATTRS{idProduct}|ATTR{serial}|ATTR{manufacturer}|ATTR{product}|ATTR{devpath}"
            echo ""
        fi
    done
}

# Main script execution
echo "USB Device Information"
echo "======================"
show_recent_usb_devices
list_connected_usb_devices
show_detailed_usb_info

