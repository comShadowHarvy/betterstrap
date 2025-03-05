#!/bin/bash

# Bluetooth Scanner for Arch Linux
# This script scans for nearby Bluetooth devices and provides detailed information

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root to ensure full Bluetooth functionality"
  exit 1
fi

# Automatically install all required packages
install_dependencies() {
  local packages=("bluez" "bluez-utils" "hwids" "bluez-hid2hci" "bluez-plugins" "bluez-tools")
  local missing=()

  echo "Checking for required packages..."
  for pkg in "${packages[@]}"; do
    if ! pacman -Q "$pkg" &>/dev/null; then
      missing+=("$pkg")
    fi
  done

  if [ ${#missing[@]} -ne 0 ]; then
    echo "Installing missing packages: ${missing[*]}"
    pacman -Sy --noconfirm "${missing[@]}"
    if [ $? -ne 0 ]; then
      echo "Failed to install some packages. Please check your internet connection and try again."
      exit 1
    fi
    echo "All required packages installed successfully."
  else
    echo "All required packages are already installed."
  fi
  
  # Enable bluetooth service to start on boot
  if ! systemctl is-enabled --quiet bluetooth; then
    echo "Enabling Bluetooth service to start on boot..."
    systemctl enable bluetooth
  fi
}

# Start Bluetooth service and ensure it's running
start_bluetooth_service() {
  echo "Checking Bluetooth service status..."
  if ! systemctl is-active --quiet bluetooth; then
    echo "Starting Bluetooth service..."
    systemctl start bluetooth
    sleep 3
    
    if ! systemctl is-active --quiet bluetooth; then
      echo "Failed to start Bluetooth service. Please check your hardware."
      exit 1
    fi
    echo "Bluetooth service started successfully."
  else
    echo "Bluetooth service is already running."
  fi

  # Check if Bluetooth adapter is present
  if ! hciconfig | grep -q "hci"; then
    echo "No Bluetooth adapter found. Please check your hardware."
    exit 1
  fi

  # Power on the Bluetooth adapter if needed
  if hciconfig | grep -q "DOWN"; then
    echo "Powering on Bluetooth adapter..."
    hciconfig hci0 up
    sleep 1
  fi
}

# Scan for devices
scan_devices() {
  local scan_time=10
  echo "Starting Bluetooth scan (this will take $scan_time seconds)..."
  
  # Start scanning in the background using bluetoothctl
  echo -e "scan on\nexit" | bluetoothctl > /dev/null &
  
  # Give the scan time to find devices
  sleep $scan_time
  
  # Stop the scan
  echo -e "scan off\nexit" | bluetoothctl > /dev/null
  
  # Get the list of discovered devices
  DEVICES=$(echo -e "devices\nexit" | bluetoothctl | grep "Device" | cut -d ' ' -f 2)
  
  if [ -z "$DEVICES" ]; then
    echo "No Bluetooth devices found."
    exit 0
  fi
  
  echo "Found $(echo "$DEVICES" | wc -l) device(s)"
  echo "───────────────────────────────────────────────────"
}

# Get detailed information about each device
get_device_info() {
  for mac in $DEVICES; do
    echo "Device: $mac"
    
    # Get device name
    NAME=$(echo -e "info $mac\nexit" | bluetoothctl | grep "Name:" | cut -d ":" -f 2- | xargs)
    if [ -n "$NAME" ]; then
      echo "Name: $NAME"
    else
      echo "Name: Unknown"
    fi
    
    # Get device class
    CLASS=$(echo -e "info $mac\nexit" | bluetoothctl | grep "Class:" | cut -d ":" -f 2- | xargs)
    if [ -n "$CLASS" ]; then
      echo "Class: $CLASS"
      # Decode class if possible
      decode_class "$CLASS"
    fi
    
    # Get RSSI (Signal Strength)
    RSSI=$(hcitool rssi "$mac" 2>/dev/null | grep -o -E "[-0-9]+" | xargs)
    if [ -n "$RSSI" ]; then
      echo "Signal Strength (RSSI): ${RSSI}dBm"
    fi
    
    # Get services
    echo "Services:"
    if ! echo -e "info $mac\nexit" | bluetoothctl | grep "UUID" | grep -q "Service"; then
      echo "  No service information available"
    else
      echo -e "info $mac\nexit" | bluetoothctl | grep "UUID" | grep "Service" | while read -r line; do
        echo "  $line" | cut -d ":" -f 2- | xargs
      done
    fi
    
    # Get connection status
    if echo -e "info $mac\nexit" | bluetoothctl | grep -q "Connected: yes"; then
      echo "Status: Connected"
    else
      echo "Status: Not Connected"
    fi
    
    # Try to get vendor information from MAC address
    VENDOR=$(get_vendor_from_mac "$mac")
    if [ -n "$VENDOR" ]; then
      echo "Vendor: $VENDOR"
    fi
    
    # Try to get additional information with l2ping
    l2ping -c 1 "$mac" &>/dev/null
    if [ $? -eq 0 ]; then
      echo "L2CAP Ping: Successful"
    fi
    
    echo "───────────────────────────────────────────────────"
  done
}

# Function to decode Bluetooth class codes
decode_class() {
  local class_code="$1"
  
  # Convert to hexadecimal if not already
  if [[ ! "$class_code" =~ ^0x ]]; then
    class_code="0x$class_code"
  fi
  
  # Convert to decimal for bit manipulation
  local decimal=$(printf "%d" "$class_code")
  
  # Major device classes
  local major_class=$((($decimal >> 8) & 0x1F))
  
  case $major_class in
    0) echo "  Type: Miscellaneous" ;;
    1) echo "  Type: Computer" ;;
    2) echo "  Type: Phone" ;;
    3) echo "  Type: LAN/Network Access Point" ;;
    4) echo "  Type: Audio/Video" ;;
    5) echo "  Type: Peripheral" ;;
    6) echo "  Type: Imaging" ;;
    7) echo "  Type: Wearable" ;;
    8) echo "  Type: Toy" ;;
    9) echo "  Type: Health" ;;
    31) echo "  Type: Uncategorized" ;;
    *) echo "  Type: Unknown ($major_class)" ;;
  esac
  
  # Minor device class - this could be expanded based on the major class
  if [ $major_class -eq 1 ]; then  # Computer
    local minor_class=$((($decimal >> 2) & 0x3F))
    case $minor_class in
      1) echo "  Subtype: Desktop" ;;
      2) echo "  Subtype: Server" ;;
      3) echo "  Subtype: Laptop" ;;
      4) echo "  Subtype: Handheld PC/PDA" ;;
      5) echo "  Subtype: Palm sized PC/PDA" ;;
      6) echo "  Subtype: Wearable computer" ;;
      7) echo "  Subtype: Tablet" ;;
      *) echo "  Subtype: Unknown computer type" ;;
    esac
  elif [ $major_class -eq 2 ]; then  # Phone
    local minor_class=$((($decimal >> 2) & 0x3F))
    case $minor_class in
      1) echo "  Subtype: Cellular" ;;
      2) echo "  Subtype: Cordless" ;;
      3) echo "  Subtype: Smartphone" ;;
      4) echo "  Subtype: Wired modem or voice gateway" ;;
      5) echo "  Subtype: Common ISDN Access" ;;
      *) echo "  Subtype: Unknown phone type" ;;
    esac
  elif [ $major_class -eq 4 ]; then  # Audio/Video
    local minor_class=$((($decimal >> 2) & 0x3F))
    case $minor_class in
      1) echo "  Subtype: Wearable Headset Device" ;;
      2) echo "  Subtype: Hands-free Device" ;;
      4) echo "  Subtype: Microphone" ;;
      5) echo "  Subtype: Loudspeaker" ;;
      6) echo "  Subtype: Headphones" ;;
      7) echo "  Subtype: Portable Audio" ;;
      8) echo "  Subtype: Car Audio" ;;
      9) echo "  Subtype: Set-top Box" ;;
      10) echo "  Subtype: HiFi Audio Device" ;;
      11) echo "  Subtype: VCR" ;;
      12) echo "  Subtype: Video Camera" ;;
      13) echo "  Subtype: Camcorder" ;;
      14) echo "  Subtype: Video Monitor" ;;
      15) echo "  Subtype: Video Display and Loudspeaker" ;;
      16) echo "  Subtype: Video Conferencing" ;;
      18) echo "  Subtype: Gaming/Toy" ;;
      *) echo "  Subtype: Unknown audio/video type" ;;
    esac
  fi
  
  # Service classes
  local service_class=$((($decimal >> 13) & 0x7FF))
  
  if (( service_class & 0x001 )); then echo "  Service: Limited Discoverable Mode"; fi
  if (( service_class & 0x008 )); then echo "  Service: Positioning"; fi
  if (( service_class & 0x010 )); then echo "  Service: Networking"; fi
  if (( service_class & 0x020 )); then echo "  Service: Rendering"; fi
  if (( service_class & 0x040 )); then echo "  Service: Capturing"; fi
  if (( service_class & 0x080 )); then echo "  Service: Object Transfer"; fi
  if (( service_class & 0x100 )); then echo "  Service: Audio"; fi
  if (( service_class & 0x200 )); then echo "  Service: Telephony"; fi
  if (( service_class & 0x400 )); then echo "  Service: Information"; fi
}

# Try to get vendor from MAC address (first 3 bytes)
get_vendor_from_mac() {
  local mac="$1"
  local oui=$(echo "$mac" | tr -d ':' | cut -c 1-6 | tr '[:lower:]' '[:upper:]')
  
  # Check if we have the OUI database
  if [ ! -f "/usr/share/hwdata/oui.txt" ] && [ ! -f "/var/lib/ieee-data/oui.txt" ]; then
    if ! pacman -Q hwids &>/dev/null; then
      echo "Unknown (hwids package not installed)"
      return
    fi
  fi
  
  # Look up the vendor in the OUI database
  if [ -f "/usr/share/hwdata/oui.txt" ]; then
    local vendor=$(grep -i "$oui" "/usr/share/hwdata/oui.txt" | cut -d $'\t' -f 3- | head -n 1)
  elif [ -f "/var/lib/ieee-data/oui.txt" ]; then
    local vendor=$(grep -i "$oui" "/var/lib/ieee-data/oui.txt" | cut -d $'\t' -f 3- | head -n 1)
  else
    echo "Unknown (OUI database not found)"
    return
  fi
  
  if [ -n "$vendor" ]; then
    echo "$vendor"
  else
    echo "Unknown vendor"
  fi
}

# Main execution
echo "Bluetooth Device Scanner for Arch Linux"
echo "───────────────────────────────────────────────────"

# Run the functions
install_dependencies
start_bluetooth_service
scan_devices
get_device_info

echo "Scan complete."