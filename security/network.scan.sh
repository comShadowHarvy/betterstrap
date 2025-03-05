#!/bin/bash

# Enhanced Network Discovery for Arch Linux
# This script focuses on thorough device discovery using multiple methods

# Set text formatting
BOLD="\033[1m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
MAGENTA="\033[35m"
CYAN="\033[36m"
RESET="\033[0m"

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root to ensure full network scanning capabilities${RESET}"
  exit 1
fi

# Install required dependencies
install_dependencies() {
  local packages=("nmap" "net-tools" "iw" "wireless_tools" "arp-scan" "netdiscover" "ipcalc" "iputils")
  local missing=()

  echo -e "\n${BOLD}${BLUE}Checking for required packages...${RESET}"
  for pkg in "${packages[@]}"; do
    if ! pacman -Q "$pkg" &>/dev/null; then
      missing+=("$pkg")
    fi
  done

  if [ ${#missing[@]} -ne 0 ]; then
    echo -e "${YELLOW}Installing missing packages: ${missing[*]}${RESET}"
    pacman -Sy --noconfirm "${missing[@]}"
    if [ $? -ne 0 ]; then
      echo -e "${RED}Failed to install some packages. Continuing with available tools.${RESET}"
    else
      echo -e "${GREEN}All required packages installed successfully.${RESET}"
    fi
  else
    echo -e "${GREEN}All required packages are already installed.${RESET}"
  fi
}

# Get active network interfaces
get_interfaces() {
  echo -e "\n${BOLD}${BLUE}Detecting network interfaces...${RESET}"

  # Initialize interface variables
  ETH_ACTIVE_INTERFACES=""
  WIFI_ACTIVE_INTERFACES=""

  # Get all interfaces
  INTERFACES=$(ip -o link show | awk -F': ' '{print $2}' | grep -v "lo\|docker\|veth\|br-")

  # Find active interfaces
  for iface in $INTERFACES; do
    local state=$(ip -o link show "$iface" | awk '{print $9}')
    local ip_addr=$(ip -o -4 addr show "$iface" 2>/dev/null | awk '{print $4}' | head -n 1)
    local mac=$(ip link show "$iface" | grep -oP 'link/ether \K[^ ]+')

    if [ "$state" == "UP" ] && [ -n "$ip_addr" ]; then
      echo -e "  ${CYAN}$iface${RESET}: UP ${YELLOW}$ip_addr${RESET} (MAC: $mac)"

      # Check if WiFi or Ethernet
      if [[ "$iface" =~ ^(wlan|wlp) ]]; then
        local ssid=$(iwconfig "$iface" 2>/dev/null | grep ESSID | grep -oP 'ESSID:"\K[^"]+')
        if [ -n "$ssid" ]; then
          echo -e "  ${GREEN}Connected to SSID: $ssid${RESET}"
        fi
        WIFI_ACTIVE_INTERFACES+=" $iface"
      else
        ETH_ACTIVE_INTERFACES+=" $iface"
      fi
    fi
  done

  # Trim leading spaces
  ETH_ACTIVE_INTERFACES=$(echo "$ETH_ACTIVE_INTERFACES" | xargs)
  WIFI_ACTIVE_INTERFACES=$(echo "$WIFI_ACTIVE_INTERFACES" | xargs)

  # Check if we have any active interfaces
  if [ -z "$ETH_ACTIVE_INTERFACES" ] && [ -z "$WIFI_ACTIVE_INTERFACES" ]; then
    echo -e "${RED}No active network interfaces detected. Please connect to a network first.${RESET}"
    exit 1
  fi
}

# Detect network scope for active interfaces
detect_network_scope() {
  NETWORK_DATA=()

  echo -e "\n${BOLD}${BLUE}Detecting network ranges...${RESET}"

  # Process all active interfaces
  for iface in $ETH_ACTIVE_INTERFACES $WIFI_ACTIVE_INTERFACES; do
    # Get interface details
    local ip_cidr=$(ip -o -4 addr show "$iface" 2>/dev/null | awk '{print $4}' | head -n 1)
    if [ -z "$ip_cidr" ]; then continue; fi

    # Split IP and CIDR
    local ip=${ip_cidr%/*}
    local cidr=${ip_cidr#*/}

    # Calculate network range
    local network=$(ipcalc -n "$ip_cidr" | grep -oP 'Network:\s+\K[^ ]+')

    # Get default gateway
    local gateway=$(ip route show dev "$iface" | grep default | awk '{print $3}')
    if [ -z "$gateway" ]; then gateway="Unknown"; fi

    echo -e "${GREEN}Network${RESET}: $network (Interface: $iface, Gateway: $gateway)"

    # Store network data
    NETWORK_DATA+=("$network $iface $gateway $ip $cidr")
  done
}

# Aggressively scan for all devices using multiple methods
discover_all_devices() {
  ALL_DISCOVERED_DEVICES=()

  echo -e "\n${BOLD}${BLUE}Discovering all network devices...${RESET}"
  echo -e "${YELLOW}This will use multiple scanning methods to find all devices${RESET}"

  for network_data in "${NETWORK_DATA[@]}"; do
    read -r network iface gateway local_ip cidr <<< "$network_data"

    echo -e "\n${BOLD}${GREEN}Scanning network: $network via $iface${RESET}"

    # Create a temporary file to store discovered IPs
    TEMP_IP_FILE=$(mktemp)

    # Get the subnet base address without CIDR
    SUBNET=${network%/*}

    # Get broadcast address
    BROADCAST=$(ipcalc -b "$network" | grep -oP 'Broadcast:\s+\K[^ ]+')

    echo -e "${YELLOW}Method 1: ARP Scan${RESET}"
    sudo arp-scan --interface="$iface" --localnet | grep -v "DUP\|Interface\|packets\|Starting\|Ending" | awk '{print $1}' >> "$TEMP_IP_FILE"

    echo -e "${YELLOW}Method 2: Netdiscover (passive)${RESET}"
    timeout 10 sudo netdiscover -i "$iface" -P -r "$network" | grep -v "Currently scanning" | awk '{print $1}' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' >> "$TEMP_IP_FILE"

    echo -e "${YELLOW}Method 3: Nmap ping scan${RESET}"
    sudo nmap -sn -T4 "$network" -e "$iface" | grep "Nmap scan report" | awk '{print $NF}' | sed 's/(//g' | sed 's/)//g' >> "$TEMP_IP_FILE"

    echo -e "${YELLOW}Method 4: Host/port scan - checking common ports${RESET}"
    # Check for devices with common ports open
    for port in 22 80 443 445 139 135 21 23 53 3389; do
      sudo nmap -sS -T4 --open -p $port "$network" -e "$iface" | grep "Nmap scan report" | awk '{print $NF}' | sed 's/(//g' | sed 's/)//g' >> "$TEMP_IP_FILE"
    done

    echo -e "${YELLOW}Method 5: Checking ARP cache${RESET}"
    arp -a | grep -v "incomplete" | awk '{print $2}' | sed 's/(//g' | sed 's/)//g' >> "$TEMP_IP_FILE"

    # Sort and remove duplicates
    sort -u "$TEMP_IP_FILE" > "${TEMP_IP_FILE}.sorted"

    # Count discovered devices
    DEVICE_COUNT=$(wc -l < "${TEMP_IP_FILE}.sorted")
    echo -e "${GREEN}Total devices discovered: $DEVICE_COUNT${RESET}"

    # Process each discovered device
    while read -r ip; do
      if [[ -n "$ip" && "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        # Check if this is our local IP and mark it if so
        if [ "$ip" == "$local_ip" ]; then
          echo -e "${CYAN}$ip${RESET} (${MAGENTA}This device${RESET})"
        elif [ "$ip" == "$gateway" ]; then
          echo -e "${CYAN}$ip${RESET} (${MAGENTA}Gateway${RESET})"
        else
          echo -e "${CYAN}$ip${RESET}"
        fi

        # Add to global list
        if [[ ! " ${ALL_DISCOVERED_DEVICES[@]} " =~ " $ip " ]]; then
          ALL_DISCOVERED_DEVICES+=("$ip")
        fi
      fi
    done < "${TEMP_IP_FILE}.sorted"

    # Clean up
    rm -f "$TEMP_IP_FILE" "${TEMP_IP_FILE}.sorted"
  done

  # Final count
  echo -e "\n${BOLD}${GREEN}Discovery complete. Found ${#ALL_DISCOVERED_DEVICES[@]} unique devices${RESET}"
}

# Identify devices by checking basic services
identify_devices() {
  echo -e "\n${BOLD}${BLUE}Identifying discovered devices...${RESET}"

  DEVICE_INFO=()

  for ip in "${ALL_DISCOVERED_DEVICES[@]}"; do
    echo -e "\n${CYAN}Device: $ip${RESET}"

    # Try to get hostname
    local hostname=$(host "$ip" 2>/dev/null | grep "domain name pointer" | awk '{print $NF}' | sed 's/\.$//')
    if [ -z "$hostname" ]; then
      # Try nbtscan if available
      if command -v nbtscan &>/dev/null; then
        hostname=$(nbtscan -q "$ip" 2>/dev/null | grep -v "^$" | awk '{print $2}')
      fi

      if [ -z "$hostname" ]; then
        hostname="Unknown"
      fi
    fi

    # Get MAC address
    local mac=$(arp -n | grep "$ip" | awk '{print $3}')
    if [ -z "$mac" ] || [ "$mac" == "(incomplete)" ]; then
      # Try to get MAC with ping and arp
      ping -c 1 -W 1 "$ip" > /dev/null 2>&1
      mac=$(arp -n | grep "$ip" | awk '{print $3}')
      if [ -z "$mac" ] || [ "$mac" == "(incomplete)" ]; then
        mac="Unknown"
      fi
    fi

    # Get vendor from MAC
    local vendor="Unknown"
    if [ "$mac" != "Unknown" ]; then
      local oui=$(echo "$mac" | tr -d ':' | cut -c 1-6 | tr '[:lower:]' '[:upper:]')

      if [ -f "/usr/share/hwdata/oui.txt" ]; then
        vendor=$(grep -i "$oui" "/usr/share/hwdata/oui.txt" | cut -d $'\t' -f 3- | head -n 1)
      elif [ -f "/var/lib/ieee-data/oui.txt" ]; then
        vendor=$(grep -i "$oui" "/var/lib/ieee-data/oui.txt" | cut -d $'\t' -f 3- | head -n 1)
      fi

      if [ -z "$vendor" ]; then
        vendor="Unknown vendor"
      fi
    fi

    # Check common ports to identify device type
    local device_type="Unknown"
    local open_ports=""

    # Quick port check for common services
    if nc -zw1 "$ip" 80 2>/dev/null || nc -zw1 "$ip" 443 2>/dev/null; then
      if nc -zw1 "$ip" 8080 2>/dev/null || nc -zw1 "$ip" 8443 2>/dev/null; then
        device_type="Web Server/Proxy"
      else
        device_type="Web Server/Router"
      fi
      open_ports="Web (80/443)"
    elif nc -zw1 "$ip" 22 2>/dev/null; then
      device_type="Computer/Server"
      open_ports="SSH (22)"
    elif nc -zw1 "$ip" 445 2>/dev/null || nc -zw1 "$ip" 139 2>/dev/null; then
      device_type="File Server/Computer"
      open_ports="SMB (445/139)"
    elif nc -zw1 "$ip" 53 2>/dev/null; then
      device_type="DNS Server"
      open_ports="DNS (53)"
    elif nc -zw1 "$ip" 21 2>/dev/null; then
      device_type="FTP Server"
      open_ports="FTP (21)"
    elif nc -zw1 "$ip" 23 2>/dev/null; then
      device_type="Telnet Device"
      open_ports="Telnet (23)"
    elif nc -zw1 "$ip" 3389 2>/dev/null; then
      device_type="Windows/RDP Server"
      open_ports="RDP (3389)"
    elif nc -zw1 "$ip" 5000 2>/dev/null || nc -zw1 "$ip" 5001 2>/dev/null; then
      device_type="IoT Device"
      open_ports="IoT (5000/5001)"
    elif nc -zw1 "$ip" 8009 2>/dev/null || nc -zw1 "$ip" 8060 2>/dev/null; then
      device_type="Smart TV/Streaming Device"
      open_ports="Media (8009/8060)"
    elif nc -zw1 "$ip" 9100 2>/dev/null; then
      device_type="Printer"
      open_ports="Printer (9100)"
    fi

    # Check if it's a gateway
    for network_data in "${NETWORK_DATA[@]}"; do
      if [[ "$network_data" == *" $ip "* ]]; then
        device_type="Gateway/Router"
        break
      fi
    done

    # Print device information
    echo -e "${GREEN}Hostname:${RESET} $hostname"
    echo -e "${GREEN}MAC Address:${RESET} $mac"
    echo -e "${GREEN}Vendor:${RESET} $vendor"
    echo -e "${GREEN}Type:${RESET} $device_type"
    echo -e "${GREEN}Ports:${RESET} $open_ports"

    # Store device info
    DEVICE_INFO+=("$ip $hostname $mac $vendor $device_type")
  done
}

# Main function
main() {
  echo -e "${BOLD}${MAGENTA}Enhanced Network Device Discovery${RESET}"
  echo -e "${CYAN}======================================${RESET}"

  # Install dependencies
  install_dependencies

  # Get network info
  get_interfaces
  detect_network_scope

  # Discover and identify devices
  discover_all_devices
  identify_devices

  echo -e "\n${BOLD}${GREEN}Network discovery complete!${RESET}"
  echo -e "${YELLOW}Found ${#ALL_DISCOVERED_DEVICES[@]} devices on your network.${RESET}"
}

# Execute main function
main
