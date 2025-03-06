#!/bin/bash

# Enhanced Network Discovery for Arch Linux
# This script focuses on thorough device discovery, OS detection, and service enumeration

# Set text formatting
BOLD="\033[1m"
RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
MAGENTA="\033[35m"
CYAN="\033[36m"
RESET="\033[0m"

# Script version
VERSION="2.0"

# Typewriter effect settings
TYPEWRITER_MODE=false
TYPEWRITER_SPEED=0.03  # Delay between characters in seconds
TYPEWRITER_LINE_DELAY=0.2  # Additional delay between lines

# Function to print text with a typewriter effect
typewriter_echo() {
  if [ "$TYPEWRITER_MODE" = true ]; then
    text="$*"
    for (( i=0; i<${#text}; i++ )); do
      echo -n "${text:$i:1}"
      sleep $TYPEWRITER_SPEED
    done
    echo
    sleep $TYPEWRITER_LINE_DELAY
  else
    echo -e "$*"
  fi
}

# Function to print formatted text with optional typewriter effect
echo_formatted() {
  if [ "$TYPEWRITER_MODE" = true ]; then
    # When in typewriter mode, we need to handle color codes differently
    text="$*"
    for (( i=0; i<${#text}; i++ )); do
      echo -n "${text:$i:1}"
      # Use smaller delay for escape sequences
      if [[ "${text:$i:1}" ==

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root to ensure full network scanning capabilities${RESET}"
  exit 1
fi

# Install required dependencies
install_dependencies() {
  local packages=("nmap" "net-tools" "iw" "wireless_tools" "arp-scan" "netdiscover" "ipcalc" "iputils" "nbtscan" "whois")
  local missing=()

  if [ "$TYPEWRITER_MODE" = true ]; then
    echo_formatted "\n${BOLD}${BLUE}Checking for required packages...${RESET}"
  else
    echo -e "\n${BOLD}${BLUE}Checking for required packages...${RESET}"
  fi

  for pkg in "${packages[@]}"; do
    if ! pacman -Q "$pkg" &>/dev/null; then
      missing+=("$pkg")
    fi
  done

  if [ ${#missing[@]} -ne 0 ]; then
    if [ "$TYPEWRITER_MODE" = true ]; then
      echo_formatted "${YELLOW}Installing missing packages: ${missing[*]}${RESET}"
    else
      echo -e "${YELLOW}Installing missing packages: ${missing[*]}${RESET}"
    fi

    pacman -Sy --noconfirm "${missing[@]}"
    if [ $? -ne 0 ]; then
      if [ "$TYPEWRITER_MODE" = true ]; then
        echo_formatted "${RED}Failed to install some packages. Continuing with available tools.${RESET}"
      else
        echo -e "${RED}Failed to install some packages. Continuing with available tools.${RESET}"
      fi
    else
      if [ "$TYPEWRITER_MODE" = true ]; then
        echo_formatted "${GREEN}All required packages installed successfully.${RESET}"
      else
        echo -e "${GREEN}All required packages installed successfully.${RESET}"
      fi
    fi
  else
    if [ "$TYPEWRITER_MODE" = true ]; then
      echo_formatted "${GREEN}All required packages are already installed.${RESET}"
    else
      echo -e "${GREEN}All required packages are already installed.${RESET}"
    fi
  fi
}

# Get active network interfaces
get_interfaces() {
  if [ "$TYPEWRITER_MODE" = true ]; then
    echo_formatted "\n${BOLD}${BLUE}Detecting network interfaces...${RESET}"
  else
    echo -e "\n${BOLD}${BLUE}Detecting network interfaces...${RESET}"
  fi

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
      if [ "$TYPEWRITER_MODE" = true ]; then
        echo_formatted "  ${CYAN}$iface${RESET}: UP ${YELLOW}$ip_addr${RESET} (MAC: $mac)"
      else
        echo -e "  ${CYAN}$iface${RESET}: UP ${YELLOW}$ip_addr${RESET} (MAC: $mac)"
      fi

      # Check if WiFi or Ethernet
      if [[ "$iface" =~ ^(wlan|wlp) ]]; then
        local ssid=$(iwconfig "$iface" 2>/dev/null | grep ESSID | grep -oP 'ESSID:"\K[^"]+')
        if [ -n "$ssid" ]; then
          if [ "$TYPEWRITER_MODE" = true ]; then
            echo_formatted "  ${GREEN}Connected to SSID: $ssid${RESET}"
          else
            echo -e "  ${GREEN}Connected to SSID: $ssid${RESET}"
          fi
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
    if [ "$TYPEWRITER_MODE" = true ]; then
      echo_formatted "${RED}No active network interfaces detected. Please connect to a network first.${RESET}"
    else
      echo -e "${RED}No active network interfaces detected. Please connect to a network first.${RESET}"
    fi
    exit 1
  fi
}

# Detect network scope for active interfaces
detect_network_scope() {
  NETWORK_DATA=()

  if [ "$TYPEWRITER_MODE" = true ]; then
    echo_formatted "\n${BOLD}${BLUE}Detecting network ranges...${RESET}"
  else
    echo -e "\n${BOLD}${BLUE}Detecting network ranges...${RESET}"
  fi

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

    if [ "$TYPEWRITER_MODE" = true ]; then
      echo_formatted "${GREEN}Network${RESET}: $network (Interface: $iface, Gateway: $gateway)"
    else
      echo -e "${GREEN}Network${RESET}: $network (Interface: $iface, Gateway: $gateway)"
    fi

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

# Enhanced function to perform OS detection and gather service information
perform_advanced_scans() {
  DEVICE_DETAILED_INFO=()

  echo -e "\n${BOLD}${BLUE}Performing advanced scans on discovered devices...${RESET}"
  echo -e "${YELLOW}This includes OS detection and service enumeration${RESET}"

  # Create a directory to store detailed scan results
  SCAN_DIR="$(pwd)/network_scan_$(date +%Y%m%d_%H%M%S)"
  mkdir -p "$SCAN_DIR"
  echo -e "${GREEN}Saving detailed scan results to:${RESET} $SCAN_DIR"

  # Create a master output file for summary
  MASTER_OUTPUT="$SCAN_DIR/scan_summary.txt"
  echo "Network Scan Results - $(date)" > "$MASTER_OUTPUT"
  echo "=================================" >> "$MASTER_OUTPUT"

  # Track progress
  local total_devices=${#ALL_DISCOVERED_DEVICES[@]}
  local current=0

  for ip in "${ALL_DISCOVERED_DEVICES[@]}"; do
    ((current++))
    echo -e "\n${CYAN}[$current/$total_devices] Scanning device: $ip${RESET}"

    # Create a device-specific output file
    DEVICE_OUTPUT="$SCAN_DIR/device_${ip//./_}.txt"
    echo "Detailed scan for $ip" > "$DEVICE_OUTPUT"
    echo "======================" >> "$DEVICE_OUTPUT"

    # Get hostname
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

    # Record basic device information
    echo "## Basic Information" >> "$DEVICE_OUTPUT"
    echo "IP Address: $ip" >> "$DEVICE_OUTPUT"
    echo "Hostname: $hostname" >> "$DEVICE_OUTPUT"
    echo "MAC Address: $mac" >> "$DEVICE_OUTPUT"
    echo "Vendor: $vendor" >> "$DEVICE_OUTPUT"

    # Display progress
    echo -e "${GREEN}Basic info:${RESET} Hostname: $hostname, MAC: $mac, Vendor: $vendor"

    # Determine if device is a gateway
    local is_gateway="No"
    for network_data in "${NETWORK_DATA[@]}"; do
      if [[ "$network_data" == *" $ip "* && "$network_data" == *"$ip"* ]]; then
        is_gateway="Yes"
        break
      fi
    done
    echo "Gateway Device: $is_gateway" >> "$DEVICE_OUTPUT"

    # Perform OS detection
    echo -e "${YELLOW}Performing OS detection...${RESET}"
    echo -e "\n## OS Detection" >> "$DEVICE_OUTPUT"

    # Use nmap for OS detection (may take some time)
    local os_info=$(sudo nmap -O --osscan-guess -T4 "$ip" -oN - 2>/dev/null | grep -E "OS details|OS CPE|Device|Running" | grep -v "Warning")

    if [ -n "$os_info" ]; then
      echo "$os_info" >> "$DEVICE_OUTPUT"
      local os_short=$(echo "$os_info" | head -n 1 | sed 's/OS details: //')
      echo -e "${GREEN}OS Detection:${RESET} $os_short"
    else
      echo "OS Detection: Failed or insufficient information" >> "$DEVICE_OUTPUT"
      echo -e "${YELLOW}OS Detection:${RESET} Failed or insufficient information"
    fi

    # Perform service scan
    echo -e "${YELLOW}Scanning for services...${RESET}"
    echo -e "\n## Service Scan" >> "$DEVICE_OUTPUT"

    # Use nmap to detect services with version info
    local service_scan=$(sudo nmap -sV -T4 --version-all -p 1-1000 "$ip" -oN - 2>/dev/null)
    echo "$service_scan" >> "$DEVICE_OUTPUT"

    # Extract open ports
    local open_ports=$(echo "$service_scan" | grep "open" | grep -v "filtered" | cut -d "/" -f 1 | tr '\n' ',' | sed 's/,$//')
    if [ -n "$open_ports" ]; then
      echo -e "${GREEN}Open ports:${RESET} $open_ports"
    else
      echo -e "${YELLOW}No open ports detected in range 1-1000${RESET}"
    fi

    # Extract service details for display
    local service_summary=$(echo "$service_scan" | grep "open" | grep -v "filtered" | head -n 5 | awk '{print $1 " " $3 " " $4 " " $5 " " $6}' | tr '\n' '; ')
    if [ -n "$service_summary" ]; then
      echo -e "${GREEN}Key services:${RESET} ${service_summary:0:80}..."
    fi

    # Perform vulnerability scan if specified
    if [ "$PERFORM_VULN_SCAN" = true ]; then
      echo -e "${YELLOW}Performing vulnerability scan...${RESET}"
      echo -e "\n## Vulnerability Scan" >> "$DEVICE_OUTPUT"

      # Use nmap scripts for vulnerability detection
      local vuln_scan=$(sudo nmap --script vuln -T4 -p "$(echo "$open_ports" | sed 's/,$//')" "$ip" -oN - 2>/dev/null)
      echo "$vuln_scan" >> "$DEVICE_OUTPUT"

      # Count potential vulnerabilities
      local vuln_count=$(echo "$vuln_scan" | grep -c "VULNERABLE")
      if [ "$vuln_count" -gt 0 ]; then
        echo -e "${RED}Potential vulnerabilities detected: $vuln_count${RESET}"
      else
        echo -e "${GREEN}No obvious vulnerabilities detected${RESET}"
      fi
    fi

    # Get traceroute information
    echo -e "\n## Network Path" >> "$DEVICE_OUTPUT"
    traceroute -n -T -w 2 "$ip" 2>/dev/null >> "$DEVICE_OUTPUT"

    # Get additional information based on open ports
    if [[ "$service_scan" == *"80/tcp open"* || "$service_scan" == *"443/tcp open"* ]]; then
      echo -e "\n## Web Server Information" >> "$DEVICE_OUTPUT"
      curl -s -I -m 5 "http://$ip" 2>/dev/null >> "$DEVICE_OUTPUT" || echo "Failed to connect to HTTP" >> "$DEVICE_OUTPUT"
      curl -s -I -m 5 "https://$ip" --insecure 2>/dev/null >> "$DEVICE_OUTPUT" || echo "Failed to connect to HTTPS" >> "$DEVICE_OUTPUT"
    fi

    # Try to determine device type based on all information gathered
    local device_type="Unknown"
    if [ "$is_gateway" == "Yes" ]; then
      device_type="Gateway/Router"
    elif [[ "$os_info" == *"Windows"* ]]; then
      if [[ "$service_scan" == *"3389/tcp open"* ]]; then
        device_type="Windows Server"
      else
        device_type="Windows PC"
      fi
    elif [[ "$os_info" == *"Linux"* ]]; then
      if [[ "$service_scan" == *"22/tcp open"* && ("$service_scan" == *"80/tcp open"* || "$service_scan" == *"443/tcp open"*) ]]; then
        device_type="Linux Server"
      else
        device_type="Linux Device"
      fi
    elif [[ "$os_info" == *"Apple"* || "$os_info" == *"Mac OS"* ]]; then
      device_type="Apple Device"
    elif [[ "$vendor" == *"Raspberry"* ]]; then
      device_type="Raspberry Pi"
    elif [[ "$service_scan" == *"8009/tcp open"* || "$service_scan" == *"8060/tcp open"* ]]; then
      device_type="Media Device/Smart TV"
    elif [[ "$service_scan" == *"9100/tcp open"* ]]; then
      device_type="Printer"
    elif [[ "$service_scan" == *"80/tcp open"* && "$service_scan" == *"23/tcp open"* ]]; then
      device_type="IoT Device"
    fi

    echo "Device Type: $device_type" >> "$DEVICE_OUTPUT"
    echo -e "${GREEN}Device type:${RESET} $device_type"

    # Add summary to master file
    echo "IP: $ip" >> "$MASTER_OUTPUT"
    echo "Hostname: $hostname" >> "$MASTER_OUTPUT"
    echo "MAC: $mac" >> "$MASTER_OUTPUT"
    echo "Vendor: $vendor" >> "$MASTER_OUTPUT"
    echo "Device Type: $device_type" >> "$MASTER_OUTPUT"
    echo "Open Ports: $open_ports" >> "$MASTER_OUTPUT"
    echo "OS: $os_short" >> "$MASTER_OUTPUT"
    echo "----------------------------" >> "$MASTER_OUTPUT"

    # Store structured device info for later use
    DEVICE_DETAILED_INFO+=("$ip|$hostname|$mac|$vendor|$device_type|$open_ports")

    # Small delay to prevent network overload
    sleep 1
  done

  echo -e "\n${BOLD}${GREEN}Advanced scanning complete!${RESET}"
  echo -e "${YELLOW}Detailed results saved to:${RESET} $SCAN_DIR"
}

# Function to perform lateral movement testing (if authorized)
test_lateral_movement() {
  echo -e "\n${BOLD}${BLUE}Testing for lateral movement possibilities...${RESET}"
  echo -e "${RED}WARNING: This should only be run in networks you own or have authorization to test!${RESET}"
  echo -e "Press Enter to continue or Ctrl+C to abort..."
  read -r

  # Results file
  LATERAL_RESULTS="$SCAN_DIR/lateral_movement_test.txt"
  echo "Lateral Movement Test Results - $(date)" > "$LATERAL_RESULTS"
  echo "=========================================" >> "$LATERAL_RESULTS"

  for device_info in "${DEVICE_DETAILED_INFO[@]}"; do
    IFS='|' read -r ip hostname mac vendor device_type open_ports <<< "$device_info"

    echo -e "\n${CYAN}Testing device: $ip ($hostname)${RESET}"
    echo -e "\n## Device: $ip ($hostname)" >> "$LATERAL_RESULTS"

    # Check for default credentials on web services
    if [[ "$open_ports" == *"80"* || "$open_ports" == *"8080"* || "$open_ports" == *"443"* || "$open_ports" == *"8443"* ]]; then
      echo -e "${YELLOW}Testing web interfaces for default logins...${RESET}"
      echo "Web Interface Tests:" >> "$LATERAL_RESULTS"

      # List of common admin pages to check
      local admin_pages=("/admin" "/login" "/manager" "/management" "/router" "/setup")

      for page in "${admin_pages[@]}"; do
        # Check HTTP
        local http_status=$(curl -s -o /dev/null -w "%{http_code}" -m 3 "http://$ip$page" 2>/dev/null)
        if [ "$http_status" == "200" ] || [ "$http_status" == "401" ] || [ "$http_status" == "302" ]; then
          echo "Found potential admin interface: http://$ip$page (Status: $http_status)" >> "$LATERAL_RESULTS"
          echo -e "${YELLOW}Found potential admin interface:${RESET} http://$ip$page"
        fi

        # Check HTTPS
        local https_status=$(curl -s -o /dev/null -w "%{http_code}" -m 3 "https://$ip$page" --insecure 2>/dev/null)
        if [ "$https_status" == "200" ] || [ "$https_status" == "401" ] || [ "$https_status" == "302" ]; then
          echo "Found potential admin interface: https://$ip$page (Status: $https_status)" >> "$LATERAL_RESULTS"
          echo -e "${YELLOW}Found potential admin interface:${RESET} https://$ip$page"
        fi
      done
    fi

    # Check for SMB/NetBIOS shares
    if [[ "$open_ports" == *"445"* || "$open_ports" == *"139"* ]]; then
      echo -e "${YELLOW}Checking for accessible SMB shares...${RESET}"
      echo "SMB Share Tests:" >> "$LATERAL_RESULTS"

      # Enumerate shares with null session
      local smb_shares=$(smbclient -L "$ip" -N 2>/dev/null | grep "Disk" | awk '{print $1}')
      if [ -n "$smb_shares" ]; then
        echo "Discovered SMB shares with null session:" >> "$LATERAL_RESULTS"
        echo "$smb_shares" >> "$LATERAL_RESULTS"
        echo -e "${YELLOW}Discovered SMB shares with null session:${RESET}"
        echo -e "$smb_shares"
      else
        echo "No accessible SMB shares found with null session" >> "$LATERAL_RESULTS"
      fi
    fi

    # Check for SSH with default credentials
    if [[ "$open_ports" == *"22"* ]]; then
      echo -e "${YELLOW}Testing for SSH default credentials...${RESET}"
      echo "SSH Tests:" >> "$LATERAL_RESULTS"

      # Common default credentials
      local users=("admin" "root" "user" "pi")
      local passwords=("admin" "password" "default" "raspberry")

      for user in "${users[@]}"; do
        for pass in "${passwords[@]}"; do
          # Timeout after 5 seconds
          timeout 5 sshpass -p "$pass" ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 "$user@$ip" exit 2>/dev/null
          if [ $? -eq 0 ]; then
            echo "WARNING: Successful SSH login with $user:$pass" >> "$LATERAL_RESULTS"
            echo -e "${RED}WARNING: Successful SSH login with $user:$pass${RESET}"
          fi
        done
      done
    fi

    # Check for open FTP
    if [[ "$open_ports" == *"21"* ]]; then
      echo -e "${YELLOW}Testing for anonymous FTP access...${RESET}"
      echo "FTP Tests:" >> "$LATERAL_RESULTS"

      # Try anonymous login
      local ftp_result=$(timeout 5 ftp -n "$ip" <<EOF
user anonymous anonymous
quit
EOF
2>&1)

      if [[ "$ftp_result" == *"230"* ]]; then
        echo "WARNING: Anonymous FTP access allowed" >> "$LATERAL_RESULTS"
        echo -e "${RED}WARNING: Anonymous FTP access allowed${RESET}"
      else
        echo "No anonymous FTP access" >> "$LATERAL_RESULTS"
      fi
    fi
  done

  echo -e "\n${BOLD}${GREEN}Lateral movement testing complete!${RESET}"
  echo -e "${YELLOW}Results saved to:${RESET} $LATERAL_RESULTS"
}

# Function to generate network map and reports
generate_reports() {
  echo -e "\n${BOLD}${BLUE}Generating network map and reports...${RESET}"

  # Create HTML report
  HTML_REPORT="$SCAN_DIR/network_report.html"

  # HTML header
  cat << EOF > "$HTML_REPORT"
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Network Scan Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    h1, h2 { color: #2c3e50; }
    .device { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
    .device:hover { background-color: #f5f5f5; }
    .header { background-color: #2c3e50; color: white; padding: 10px; border-radius: 5px; }
    .info { display: flex; flex-wrap: wrap; }
    .info-item { margin-right: 20px; margin-bottom: 10px; }
    .label { font-weight: bold; color: #7f8c8d; }
    .gateway { border-left: 5px solid #27ae60; }
    .warning { color: #e74c3c; font-weight: bold; }
    .open-ports { color: #e67e22; }
    table { border-collapse: collapse; width: 100%; margin: 20px 0; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
    tr:nth-child(even) { background-color: #f9f9f9; }
  </style>
</head>
<body>
  <div class="header">
    <h1>Network Scan Report</h1>
    <p>Generated on $(date)</p>
  </div>

  <h2>Network Information</h2>
EOF

  # Add network information
  echo "<table>" >> "$HTML_REPORT"
  echo "<tr><th>Network</th><th>Interface</th><th>Gateway</th><th>Local IP</th></tr>" >> "$HTML_REPORT"

  for network_data in "${NETWORK_DATA[@]}"; do
    read -r network iface gateway local_ip cidr <<< "$network_data"
    echo "<tr><td>$network</td><td>$iface</td><td>$gateway</td><td>$local_ip</td></tr>" >> "$HTML_REPORT"
  done

  echo "</table>" >> "$HTML_REPORT"

  # Add device information
  echo "<h2>Discovered Devices (${#DEVICE_DETAILED_INFO[@]})</h2>" >> "$HTML_REPORT"

  # Sort devices by IP address
  IFS=$'\n' SORTED_DEVICES=($(sort <<<"${DEVICE_DETAILED_INFO[*]}"))
  unset IFS

  for device_info in "${SORTED_DEVICES[@]}"; do
    IFS='|' read -r ip hostname mac vendor device_type open_ports <<< "$device_info"

    # Determine if this is a gateway
    local is_gateway=""
    for network_data in "${NETWORK_DATA[@]}"; do
      if [[ "$network_data" == *" $ip "* && "$network_data" == *"$ip"* ]]; then
        is_gateway=" gateway"
        break
      fi
    done

    # Start device block
    echo "<div class='device$is_gateway'>" >> "$HTML_REPORT"
    echo "<h3>$ip - $hostname</h3>" >> "$HTML_REPORT"
    echo "<div class='info'>" >> "$HTML_REPORT"

    # Add device details
    echo "<div class='info-item'><span class='label'>IP:</span> $ip</div>" >> "$HTML_REPORT"
    echo "<div class='info-item'><span class='label'>Hostname:</span> $hostname</div>" >> "$HTML_REPORT"
    echo "<div class='info-item'><span class='label'>MAC:</span> $mac</div>" >> "$HTML_REPORT"
    echo "<div class='info-item'><span class='label'>Vendor:</span> $vendor</div>" >> "$HTML_REPORT"
    echo "<div class='info-item'><span class='label'>Type:</span> $device_type</div>" >> "$HTML_REPORT"

    if [ -n "$open_ports" ]; then
      echo "<div class='info-item'><span class='label'>Open Ports:</span> <span class='open-ports'>$open_ports</span></div>" >> "$HTML_REPORT"
    else
      echo "<div class='info-item'><span class='label'>Open Ports:</span> None detected</div>" >> "$HTML_REPORT"
    fi

    # Check for warnings in lateral movement results
    if [ -f "$LATERAL_RESULTS" ]; then
      local warnings=$(grep -A 15 "Device: $ip" "$LATERAL_RESULTS" | grep "WARNING")
      if [ -n "$warnings" ]; then
        echo "<div class='info-item warning'><span class='label'>Warnings:</span> Security issues detected</div>" >> "$HTML_REPORT"
      fi
    fi

    # Close device block
    echo "</div></div>" >> "$HTML_REPORT"
  done

  # Close HTML
  cat << EOF >> "$HTML_REPORT"
  <div class="footer">
    <p>Scan performed using Enhanced Network Discovery Script v$VERSION</p>
  </div>
</body>
</html>
EOF

  echo -e "${GREEN}HTML report generated:${RESET} $HTML_REPORT"

  # Generate network map if graphviz is available
  if command -v dot &>/dev/null; then
    MAP_FILE="$SCAN_DIR/network_map.dot"

    # Create dot file header
    cat << EOF > "$MAP_FILE"
digraph network {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fillcolor=white];

  // Gateway nodes
EOF

    # Add gateway nodes
    for network_data in "${NETWORK_DATA[@]}"; do
      read -r network iface gateway local_ip cidr <<< "$network_data"
      if [ "$gateway" != "Unknown" ]; then
        echo "  \"$gateway\" [fillcolor=\"#27ae60\", fontcolor=white, label=\"Gateway\\n$gateway\"];" >> "$MAP_FILE"
      fi
    done

    # Add local device
    echo -e "\n  // Local device" >> "$MAP_FILE"
    for network_data in "${NETWORK_DATA[@]}"; do
      read -r network iface gateway local_ip cidr <<< "$network_data"
      echo "  \"$local_ip\" [fillcolor=\"#3498db\", fontcolor=white, label=\"This Device\\n$local_ip\"];" >> "$MAP_FILE"

      # Connect to gateway
      if [ "$gateway" != "Unknown" ]; then
        echo "  \"$local_ip\" -> \"$gateway\" [dir=both];" >> "$MAP_FILE"
      fi
    done

    # Add other devices
    echo -e "\n  // Other devices" >> "$MAP_FILE"
    for device_info in "${DEVICE_DETAILED_INFO[@]}"; do
      IFS='|' read -r ip hostname mac vendor device_type open_ports <<< "$device_info"

      # Skip if this is the local device or a gateway
      if [[ " ${NETWORK_DATA[@]} " =~ " $ip " ]]; then
        continue
      fi

      # Determine node color based on device type
      local color="white"
      local fontcolor="black"

      case "$device_type" in
        *"Server"*)
          color="#f1c40f"
          ;;
        *"Windows"*)
          color="#3498db"
          fontcolor="white"
          ;;
        *"Linux"*)
          color="#e67e22"
          ;;
        *"Apple"*)
          color="#7f8c8d"
          fontcolor="white"
          ;;
        *"Printer"*)
          color="#9b59b6"
          fontcolor="white"
          ;;
        *"IoT"*|*"Smart"*)
          color="#e74c3c"
          fontcolor="white"
          ;;
      esac

      local label=""
      if [ "$hostname" != "Unknown" ]; then
        label="$hostname\\n$ip"
      else
        label="$ip\\n$device_type"
      fi

      echo "  \"$ip\" [fillcolor=\"$color\", fontcolor=\"$fontcolor\", label=\"$label\"];" >> "$MAP_FILE"

      # Connect to gateway
      for network_data in "${NETWORK_DATA[@]}"; do
        read -r network iface gateway local_ip cidr <<< "$network_data"
        if [ "$gateway" != "Unknown" ]; then
          echo "  \"$ip\" -> \"$gateway\" [dir=both];" >> "$MAP_FILE"
        fi
      done
    done

    # Close dot file
    echo "}" >> "$MAP_FILE"

    # Generate PNG
    PNG_FILE="$SCAN_DIR/network_map.png"
    dot -Tpng "$MAP_FILE" -o "$PNG_FILE"

    echo -e "${GREEN}Network map generated:${RESET} $PNG_FILE"
  else
    echo -e "${YELLOW}Graphviz not installed. Network map not generated.${RESET}"
  fi
}

# Display detailed usage information
show_help() {
  echo -e "${BOLD}${MAGENTA}Enhanced Network Discovery Script v$VERSION${RESET}"
  echo -e "${CYAN}=================================================${RESET}"
  echo
  echo -e "${BOLD}${GREEN}DESCRIPTION${RESET}"
  echo -e "  A comprehensive network reconnaissance tool designed for Arch Linux systems that"
  echo -e "  discovers, identifies, and analyzes devices on your network using multiple detection"
  echo -e "  methods. The script performs OS fingerprinting, service enumeration, and optional"
  echo -e "  security testing to provide a detailed overview of your network infrastructure."
  echo
  echo -e "${BOLD}${GREEN}SYNOPSIS${RESET}"
  echo -e "  $0 [options]"
  echo
  echo -e "${BOLD}${GREEN}OPTIONS${RESET}"
  echo -e "  ${BOLD}-h, --help${RESET}"
  echo -e "      Display this detailed help information and exit."
  echo
  echo -e "  ${BOLD}-v, --vuln-scan${RESET}"
  echo -e "      Enable vulnerability scanning using Nmap's vulnerability detection scripts."
  echo -e "      This scans discovered devices for known vulnerabilities and security issues,"
  echo -e "      including outdated software, default credentials, and common misconfigurations."
  echo -e "      Note: This scan type significantly increases the total scan duration."
  echo
  echo -e "  ${BOLD}-l, --lateral-test${RESET}"
  echo -e "      Test for lateral movement possibilities within the network. This option checks for:"
  echo -e "      • Anonymous/null SMB shares access"
  echo -e "      • Default credentials on web interfaces"
  echo -e "      • Common SSH username/password combinations"
  echo -e "      • Anonymous FTP access"
  echo -e "      ${RED}WARNING: Only use this option on networks you own or have explicit permission"
  echo -e "      to test. This may trigger security systems and generate authentication logs.${RESET}"
  echo
  echo -e "  ${BOLD}-q, --quick${RESET}"
  echo -e "      Perform a faster scan with reduced detail. This option:"
  echo -e "      • Limits port scanning to most common ports"
  echo -e "      • Reduces timeout values"
  echo -e "      • Skips more intensive detection methods"
  echo -e "      • Uses more aggressive timing templates"
  echo -e "      Useful for getting a quick overview of large networks."
  echo
  echo -e "  ${BOLD}-o, --output DIR${RESET}"
  echo -e "      Specify a custom output directory for scan results instead of the default."
  echo -e "      The script will create the directory if it doesn't exist."
  echo -e "      Default: ./network_scan_YYYYMMDD_HHMMSS/"
  echo
  echo -e "${BOLD}${GREEN}SCAN PHASES${RESET}"
  echo -e "  1. ${BOLD}Dependency Check${RESET}: Verifies and installs required tools"
  echo -e "  2. ${BOLD}Network Interface Detection${RESET}: Identifies active network interfaces"
  echo -e "  3. ${BOLD}Network Range Discovery${RESET}: Determines network subnets and gateways"
  echo -e "  4. ${BOLD}Device Discovery${RESET}: Uses multiple methods to find all devices"
  echo -e "  5. ${BOLD}OS Detection${RESET}: Identifies operating systems on discovered devices"
  echo -e "  6. ${BOLD}Service Enumeration${RESET}: Identifies open ports and running services"
  echo -e "  7. ${BOLD}Vulnerability Assessment${RESET}: Optional scanning for security issues"
  echo -e "  8. ${BOLD}Lateral Movement Testing${RESET}: Optional checking for security weaknesses"
  echo -e "  9. ${BOLD}Report Generation${RESET}: Creates HTML report and network map"
  echo
  echo -e "${BOLD}${GREEN}OUTPUT FILES${RESET}"
  echo -e "  • ${BOLD}scan_summary.txt${RESET}: Overview of all discovered devices"
  echo -e "  • ${BOLD}device_X_X_X_X.txt${RESET}: Detailed information for each device"
  echo -e "  • ${BOLD}network_report.html${RESET}: Interactive HTML report of findings"
  echo -e "  • ${BOLD}network_map.png${RESET}: Visual representation of network topology"
  echo -e "  • ${BOLD}lateral_movement_test.txt${RESET}: Results of security testing (if enabled)"
  echo
  echo -e "${BOLD}${GREEN}EXAMPLES${RESET}"
  echo -e "  ${YELLOW}# Basic scan with OS detection${RESET}"
  echo -e "  sudo $0"
  echo
  echo -e "  ${YELLOW}# Quick scan of the network${RESET}"
  echo -e "  sudo $0 --quick"
  echo
  echo -e "  ${YELLOW}# Full scan with vulnerability assessment${RESET}"
  echo -e "  sudo $0 --vuln-scan"
  echo
  echo -e "  ${YELLOW}# Complete security assessment (only on authorized networks)${RESET}"
  echo -e "  sudo $0 --vuln-scan --lateral-test"
  echo
  echo -e "  ${YELLOW}# Save results to a specific location${RESET}"
  echo -e "  sudo $0 --output /home/user/network_scans"
  echo
  echo -e "  ${YELLOW}# Run with typewriter effect for dynamic output${RESET}"
  echo -e "  sudo $0 --typewriter"
  echo
  echo -e "  ${YELLOW}# Adjust typewriter speed (faster typing)${RESET}"
  echo -e "  sudo $0 --typewriter-speed 0.01"
  echo
  echo -e "${BOLD}${GREEN}REQUIRED TOOLS${RESET}"
  echo -e "  The script will automatically check for and install these dependencies:"
  echo -e "  • nmap: Network scanner, port scanner, OS detection"
  echo -e "  • net-tools: Basic network utilities (arp, ifconfig, etc.)"
  echo -e "  • iw/wireless_tools: Wireless network tools"
  echo -e "  • arp-scan: Layer 2 network scanner"
  echo -e "  • netdiscover: Active/passive network address scanner"
  echo -e "  • ipcalc: IP network calculator"
  echo -e "  • iputils: IP utilities (ping, traceroute, etc.)"
  echo -e "  • nbtscan: NetBIOS nameserver scanner"
  echo -e "  • whois: Domain/IP WHOIS lookup tool"
  echo
  echo -e "${BOLD}${GREEN}NOTES${RESET}"
  echo -e "  • This script requires root privileges to perform full network scanning."
  echo -e "  • Scan duration depends on network size and selected options."
  echo -e "  • For best results, run the script on a wired connection."
  echo -e "  • The script is designed for Arch Linux but may work on other distributions."
  echo -e "  • Network maps require graphviz to be installed."
  echo -e "  • Scanning public networks or networks without permission may be illegal."
  echo
  echo -e "${BOLD}${GREEN}SECURITY CONSIDERATIONS${RESET}"
  echo -e "  • All scanning activities are logged and may be detected by security systems."
  echo -e "  • The ${BOLD}--lateral-test${RESET} option attempts to access services and may generate logs."
  echo -e "  • Scan results may contain sensitive information about your network."
  echo -e "  • Handle the output files securely and do not share them unnecessarily."
  echo -e "  • The script does not exploit any vulnerabilities it finds."
  echo
  echo -e "${BOLD}${GREEN}AUTHOR${RESET}"
  echo -e "  Enhanced Network Discovery Script"
  echo
  echo -e "${BOLD}${RED}DISCLAIMER${RESET}"
  echo -e "  This tool is provided for legitimate network administration and security"
  echo -e "  assessment purposes only. Users are responsible for ensuring they have"
  echo -e "  appropriate authorization before scanning any network. The authors accept"
  echo -e "  no liability for misuse or damage caused by this script."
}

# Process command line options
process_options() {
  PERFORM_VULN_SCAN=false
  TEST_LATERAL=false
  QUICK_SCAN=false
  TYPEWRITER_MODE=false

  while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
      -h|--help)
        show_help
        exit 0
        ;;
      -v|--vuln-scan)
        PERFORM_VULN_SCAN=true
        shift
        ;;
      -l|--lateral-test)
        TEST_LATERAL=true
        shift
        ;;
      -q|--quick)
        QUICK_SCAN=true
        shift
        ;;
      -o|--output)
        SCAN_DIR="$2"
        shift
        shift
        ;;
      -t|--typewriter)
        TYPEWRITER_MODE=true
        # Get optional speed parameter if provided
        if [[ $# -gt 1 && $2 =~ ^[0-9]+(.[0-9]+)?$ ]]; then
          TYPEWRITER_SPEED=$2
          TYPEWRITER_LINE_DELAY=$(echo "$TYPEWRITER_SPEED * 6" | bc)
          shift
        fi
        shift
        ;;
      --typewriter-speed)
        if [[ $# -gt 1 && $2 =~ ^[0-9]+(.[0-9]+)?$ ]]; then
          TYPEWRITER_SPEED=$2
          TYPEWRITER_LINE_DELAY=$(echo "$TYPEWRITER_SPEED * 6" | bc)
          TYPEWRITER_MODE=true
          shift
        else
          echo -e "${RED}Error: --typewriter-speed requires a numeric value${RESET}"
          exit 1
        fi
        shift
        ;;
      *)
        echo -e "${RED}Unknown option: $key${RESET}"
        show_help
        exit 1
        ;;
    esac
  done
}

# Main function
main() {
  # Process command line options
  process_options "$@"

  if [ "$TYPEWRITER_MODE" = true ]; then
    echo_formatted "${BOLD}${MAGENTA}Enhanced Network Device Discovery v$VERSION${RESET}"
    echo_formatted "${CYAN}=========================================${RESET}"
  else
    echo -e "${BOLD}${MAGENTA}Enhanced Network Device Discovery v$VERSION${RESET}"
    echo -e "${CYAN}=========================================${RESET}"
  fi

  # Install dependencies
  install_dependencies

  # Get network info
  get_interfaces
  detect_network_scope

  # Discover devices
  discover_all_devices

  # Perform advanced scans
  perform_advanced_scans

  # Perform lateral movement testing if requested
  if [ "$TEST_LATERAL" = true ]; then
    test_lateral_movement
  fi

  # Generate reports
  generate_reports

  if [ "$TYPEWRITER_MODE" = true ]; then
    echo_formatted "\n${BOLD}${GREEN}Network discovery and analysis complete!${RESET}"
    echo_formatted "${YELLOW}Found ${#ALL_DISCOVERED_DEVICES[@]} devices on your network.${RESET}"
    echo_formatted "Detailed results saved to: $SCAN_DIR"
  else
    echo -e "\n${BOLD}${GREEN}Network discovery and analysis complete!${RESET}"
    echo -e "${YELLOW}Found ${#ALL_DISCOVERED_DEVICES[@]} devices on your network.${RESET}"
    echo -e "Detailed results saved to: $SCAN_DIR"
  fi
}

# Execute main function with all arguments
main "$@"
\033' ]]; then
        sleep 0.001
      else
        sleep $TYPEWRITER_SPEED
      fi
    done
    echo
    sleep $TYPEWRITER_LINE_DELAY
  else
    echo -e "$*"
  fi
}

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root to ensure full network scanning capabilities${RESET}"
  exit 1
fi

# Install required dependencies
install_dependencies() {
  local packages=("nmap" "net-tools" "iw" "wireless_tools" "arp-scan" "netdiscover" "ipcalc" "iputils" "nbtscan" "whois")
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

# Enhanced function to perform OS detection and gather service information
perform_advanced_scans() {
  DEVICE_DETAILED_INFO=()

  echo -e "\n${BOLD}${BLUE}Performing advanced scans on discovered devices...${RESET}"
  echo -e "${YELLOW}This includes OS detection and service enumeration${RESET}"

  # Create a directory to store detailed scan results
  SCAN_DIR="$(pwd)/network_scan_$(date +%Y%m%d_%H%M%S)"
  mkdir -p "$SCAN_DIR"
  echo -e "${GREEN}Saving detailed scan results to:${RESET} $SCAN_DIR"

  # Create a master output file for summary
  MASTER_OUTPUT="$SCAN_DIR/scan_summary.txt"
  echo "Network Scan Results - $(date)" > "$MASTER_OUTPUT"
  echo "=================================" >> "$MASTER_OUTPUT"

  # Track progress
  local total_devices=${#ALL_DISCOVERED_DEVICES[@]}
  local current=0

  for ip in "${ALL_DISCOVERED_DEVICES[@]}"; do
    ((current++))
    echo -e "\n${CYAN}[$current/$total_devices] Scanning device: $ip${RESET}"

    # Create a device-specific output file
    DEVICE_OUTPUT="$SCAN_DIR/device_${ip//./_}.txt"
    echo "Detailed scan for $ip" > "$DEVICE_OUTPUT"
    echo "======================" >> "$DEVICE_OUTPUT"

    # Get hostname
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

    # Record basic device information
    echo "## Basic Information" >> "$DEVICE_OUTPUT"
    echo "IP Address: $ip" >> "$DEVICE_OUTPUT"
    echo "Hostname: $hostname" >> "$DEVICE_OUTPUT"
    echo "MAC Address: $mac" >> "$DEVICE_OUTPUT"
    echo "Vendor: $vendor" >> "$DEVICE_OUTPUT"

    # Display progress
    echo -e "${GREEN}Basic info:${RESET} Hostname: $hostname, MAC: $mac, Vendor: $vendor"

    # Determine if device is a gateway
    local is_gateway="No"
    for network_data in "${NETWORK_DATA[@]}"; do
      if [[ "$network_data" == *" $ip "* && "$network_data" == *"$ip"* ]]; then
        is_gateway="Yes"
        break
      fi
    done
    echo "Gateway Device: $is_gateway" >> "$DEVICE_OUTPUT"

    # Perform OS detection
    echo -e "${YELLOW}Performing OS detection...${RESET}"
    echo -e "\n## OS Detection" >> "$DEVICE_OUTPUT"

    # Use nmap for OS detection (may take some time)
    local os_info=$(sudo nmap -O --osscan-guess -T4 "$ip" -oN - 2>/dev/null | grep -E "OS details|OS CPE|Device|Running" | grep -v "Warning")

    if [ -n "$os_info" ]; then
      echo "$os_info" >> "$DEVICE_OUTPUT"
      local os_short=$(echo "$os_info" | head -n 1 | sed 's/OS details: //')
      echo -e "${GREEN}OS Detection:${RESET} $os_short"
    else
      echo "OS Detection: Failed or insufficient information" >> "$DEVICE_OUTPUT"
      echo -e "${YELLOW}OS Detection:${RESET} Failed or insufficient information"
    fi

    # Perform service scan
    echo -e "${YELLOW}Scanning for services...${RESET}"
    echo -e "\n## Service Scan" >> "$DEVICE_OUTPUT"

    # Use nmap to detect services with version info
    local service_scan=$(sudo nmap -sV -T4 --version-all -p 1-1000 "$ip" -oN - 2>/dev/null)
    echo "$service_scan" >> "$DEVICE_OUTPUT"

    # Extract open ports
    local open_ports=$(echo "$service_scan" | grep "open" | grep -v "filtered" | cut -d "/" -f 1 | tr '\n' ',' | sed 's/,$//')
    if [ -n "$open_ports" ]; then
      echo -e "${GREEN}Open ports:${RESET} $open_ports"
    else
      echo -e "${YELLOW}No open ports detected in range 1-1000${RESET}"
    fi

    # Extract service details for display
    local service_summary=$(echo "$service_scan" | grep "open" | grep -v "filtered" | head -n 5 | awk '{print $1 " " $3 " " $4 " " $5 " " $6}' | tr '\n' '; ')
    if [ -n "$service_summary" ]; then
      echo -e "${GREEN}Key services:${RESET} ${service_summary:0:80}..."
    fi

    # Perform vulnerability scan if specified
    if [ "$PERFORM_VULN_SCAN" = true ]; then
      echo -e "${YELLOW}Performing vulnerability scan...${RESET}"
      echo -e "\n## Vulnerability Scan" >> "$DEVICE_OUTPUT"

      # Use nmap scripts for vulnerability detection
      local vuln_scan=$(sudo nmap --script vuln -T4 -p "$(echo "$open_ports" | sed 's/,$//')" "$ip" -oN - 2>/dev/null)
      echo "$vuln_scan" >> "$DEVICE_OUTPUT"

      # Count potential vulnerabilities
      local vuln_count=$(echo "$vuln_scan" | grep -c "VULNERABLE")
      if [ "$vuln_count" -gt 0 ]; then
        echo -e "${RED}Potential vulnerabilities detected: $vuln_count${RESET}"
      else
        echo -e "${GREEN}No obvious vulnerabilities detected${RESET}"
      fi
    fi

    # Get traceroute information
    echo -e "\n## Network Path" >> "$DEVICE_OUTPUT"
    traceroute -n -T -w 2 "$ip" 2>/dev/null >> "$DEVICE_OUTPUT"

    # Get additional information based on open ports
    if [[ "$service_scan" == *"80/tcp open"* || "$service_scan" == *"443/tcp open"* ]]; then
      echo -e "\n## Web Server Information" >> "$DEVICE_OUTPUT"
      curl -s -I -m 5 "http://$ip" 2>/dev/null >> "$DEVICE_OUTPUT" || echo "Failed to connect to HTTP" >> "$DEVICE_OUTPUT"
      curl -s -I -m 5 "https://$ip" --insecure 2>/dev/null >> "$DEVICE_OUTPUT" || echo "Failed to connect to HTTPS" >> "$DEVICE_OUTPUT"
    fi

    # Try to determine device type based on all information gathered
    local device_type="Unknown"
    if [ "$is_gateway" == "Yes" ]; then
      device_type="Gateway/Router"
    elif [[ "$os_info" == *"Windows"* ]]; then
      if [[ "$service_scan" == *"3389/tcp open"* ]]; then
        device_type="Windows Server"
      else
        device_type="Windows PC"
      fi
    elif [[ "$os_info" == *"Linux"* ]]; then
      if [[ "$service_scan" == *"22/tcp open"* && ("$service_scan" == *"80/tcp open"* || "$service_scan" == *"443/tcp open"*) ]]; then
        device_type="Linux Server"
      else
        device_type="Linux Device"
      fi
    elif [[ "$os_info" == *"Apple"* || "$os_info" == *"Mac OS"* ]]; then
      device_type="Apple Device"
    elif [[ "$vendor" == *"Raspberry"* ]]; then
      device_type="Raspberry Pi"
    elif [[ "$service_scan" == *"8009/tcp open"* || "$service_scan" == *"8060/tcp open"* ]]; then
      device_type="Media Device/Smart TV"
    elif [[ "$service_scan" == *"9100/tcp open"* ]]; then
      device_type="Printer"
    elif [[ "$service_scan" == *"80/tcp open"* && "$service_scan" == *"23/tcp open"* ]]; then
      device_type="IoT Device"
    fi

    echo "Device Type: $device_type" >> "$DEVICE_OUTPUT"
    echo -e "${GREEN}Device type:${RESET} $device_type"

    # Add summary to master file
    echo "IP: $ip" >> "$MASTER_OUTPUT"
    echo "Hostname: $hostname" >> "$MASTER_OUTPUT"
    echo "MAC: $mac" >> "$MASTER_OUTPUT"
    echo "Vendor: $vendor" >> "$MASTER_OUTPUT"
    echo "Device Type: $device_type" >> "$MASTER_OUTPUT"
    echo "Open Ports: $open_ports" >> "$MASTER_OUTPUT"
    echo "OS: $os_short" >> "$MASTER_OUTPUT"
    echo "----------------------------" >> "$MASTER_OUTPUT"

    # Store structured device info for later use
    DEVICE_DETAILED_INFO+=("$ip|$hostname|$mac|$vendor|$device_type|$open_ports")

    # Small delay to prevent network overload
    sleep 1
  done

  echo -e "\n${BOLD}${GREEN}Advanced scanning complete!${RESET}"
  echo -e "${YELLOW}Detailed results saved to:${RESET} $SCAN_DIR"
}

# Function to perform lateral movement testing (if authorized)
test_lateral_movement() {
  echo -e "\n${BOLD}${BLUE}Testing for lateral movement possibilities...${RESET}"
  echo -e "${RED}WARNING: This should only be run in networks you own or have authorization to test!${RESET}"
  echo -e "Press Enter to continue or Ctrl+C to abort..."
  read -r

  # Results file
  LATERAL_RESULTS="$SCAN_DIR/lateral_movement_test.txt"
  echo "Lateral Movement Test Results - $(date)" > "$LATERAL_RESULTS"
  echo "=========================================" >> "$LATERAL_RESULTS"

  for device_info in "${DEVICE_DETAILED_INFO[@]}"; do
    IFS='|' read -r ip hostname mac vendor device_type open_ports <<< "$device_info"

    echo -e "\n${CYAN}Testing device: $ip ($hostname)${RESET}"
    echo -e "\n## Device: $ip ($hostname)" >> "$LATERAL_RESULTS"

    # Check for default credentials on web services
    if [[ "$open_ports" == *"80"* || "$open_ports" == *"8080"* || "$open_ports" == *"443"* || "$open_ports" == *"8443"* ]]; then
      echo -e "${YELLOW}Testing web interfaces for default logins...${RESET}"
      echo "Web Interface Tests:" >> "$LATERAL_RESULTS"

      # List of common admin pages to check
      local admin_pages=("/admin" "/login" "/manager" "/management" "/router" "/setup")

      for page in "${admin_pages[@]}"; do
        # Check HTTP
        local http_status=$(curl -s -o /dev/null -w "%{http_code}" -m 3 "http://$ip$page" 2>/dev/null)
        if [ "$http_status" == "200" ] || [ "$http_status" == "401" ] || [ "$http_status" == "302" ]; then
          echo "Found potential admin interface: http://$ip$page (Status: $http_status)" >> "$LATERAL_RESULTS"
          echo -e "${YELLOW}Found potential admin interface:${RESET} http://$ip$page"
        fi

        # Check HTTPS
        local https_status=$(curl -s -o /dev/null -w "%{http_code}" -m 3 "https://$ip$page" --insecure 2>/dev/null)
        if [ "$https_status" == "200" ] || [ "$https_status" == "401" ] || [ "$https_status" == "302" ]; then
          echo "Found potential admin interface: https://$ip$page (Status: $https_status)" >> "$LATERAL_RESULTS"
          echo -e "${YELLOW}Found potential admin interface:${RESET} https://$ip$page"
        fi
      done
    fi

    # Check for SMB/NetBIOS shares
    if [[ "$open_ports" == *"445"* || "$open_ports" == *"139"* ]]; then
      echo -e "${YELLOW}Checking for accessible SMB shares...${RESET}"
      echo "SMB Share Tests:" >> "$LATERAL_RESULTS"

      # Enumerate shares with null session
      local smb_shares=$(smbclient -L "$ip" -N 2>/dev/null | grep "Disk" | awk '{print $1}')
      if [ -n "$smb_shares" ]; then
        echo "Discovered SMB shares with null session:" >> "$LATERAL_RESULTS"
        echo "$smb_shares" >> "$LATERAL_RESULTS"
        echo -e "${YELLOW}Discovered SMB shares with null session:${RESET}"
        echo -e "$smb_shares"
      else
        echo "No accessible SMB shares found with null session" >> "$LATERAL_RESULTS"
      fi
    fi

    # Check for SSH with default credentials
    if [[ "$open_ports" == *"22"* ]]; then
      echo -e "${YELLOW}Testing for SSH default credentials...${RESET}"
      echo "SSH Tests:" >> "$LATERAL_RESULTS"

      # Common default credentials
      local users=("admin" "root" "user" "pi")
      local passwords=("admin" "password" "default" "raspberry")

      for user in "${users[@]}"; do
        for pass in "${passwords[@]}"; do
          # Timeout after 5 seconds
          timeout 5 sshpass -p "$pass" ssh -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 "$user@$ip" exit 2>/dev/null
          if [ $? -eq 0 ]; then
            echo "WARNING: Successful SSH login with $user:$pass" >> "$LATERAL_RESULTS"
            echo -e "${RED}WARNING: Successful SSH login with $user:$pass${RESET}"
          fi
        done
      done
    fi

    # Check for open FTP
    if [[ "$open_ports" == *"21"* ]]; then
      echo -e "${YELLOW}Testing for anonymous FTP access...${RESET}"
      echo "FTP Tests:" >> "$LATERAL_RESULTS"

      # Try anonymous login
      local ftp_result=$(timeout 5 ftp -n "$ip" <<EOF
user anonymous anonymous
quit
EOF
2>&1)

      if [[ "$ftp_result" == *"230"* ]]; then
        echo "WARNING: Anonymous FTP access allowed" >> "$LATERAL_RESULTS"
        echo -e "${RED}WARNING: Anonymous FTP access allowed${RESET}"
      else
        echo "No anonymous FTP access" >> "$LATERAL_RESULTS"
      fi
    fi
  done

  echo -e "\n${BOLD}${GREEN}Lateral movement testing complete!${RESET}"
  echo -e "${YELLOW}Results saved to:${RESET} $LATERAL_RESULTS"
}

# Function to generate network map and reports
generate_reports() {
  echo -e "\n${BOLD}${BLUE}Generating network map and reports...${RESET}"

  # Create HTML report
  HTML_REPORT="$SCAN_DIR/network_report.html"

  # HTML header
  cat << EOF > "$HTML_REPORT"
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Network Scan Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    h1, h2 { color: #2c3e50; }
    .device { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
    .device:hover { background-color: #f5f5f5; }
    .header { background-color: #2c3e50; color: white; padding: 10px; border-radius: 5px; }
    .info { display: flex; flex-wrap: wrap; }
    .info-item { margin-right: 20px; margin-bottom: 10px; }
    .label { font-weight: bold; color: #7f8c8d; }
    .gateway { border-left: 5px solid #27ae60; }
    .warning { color: #e74c3c; font-weight: bold; }
    .open-ports { color: #e67e22; }
    table { border-collapse: collapse; width: 100%; margin: 20px 0; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
    tr:nth-child(even) { background-color: #f9f9f9; }
  </style>
</head>
<body>
  <div class="header">
    <h1>Network Scan Report</h1>
    <p>Generated on $(date)</p>
  </div>

  <h2>Network Information</h2>
EOF

  # Add network information
  echo "<table>" >> "$HTML_REPORT"
  echo "<tr><th>Network</th><th>Interface</th><th>Gateway</th><th>Local IP</th></tr>" >> "$HTML_REPORT"

  for network_data in "${NETWORK_DATA[@]}"; do
    read -r network iface gateway local_ip cidr <<< "$network_data"
    echo "<tr><td>$network</td><td>$iface</td><td>$gateway</td><td>$local_ip</td></tr>" >> "$HTML_REPORT"
  done

  echo "</table>" >> "$HTML_REPORT"

  # Add device information
  echo "<h2>Discovered Devices (${#DEVICE_DETAILED_INFO[@]})</h2>" >> "$HTML_REPORT"

  # Sort devices by IP address
  IFS=$'\n' SORTED_DEVICES=($(sort <<<"${DEVICE_DETAILED_INFO[*]}"))
  unset IFS

  for device_info in "${SORTED_DEVICES[@]}"; do
    IFS='|' read -r ip hostname mac vendor device_type open_ports <<< "$device_info"

    # Determine if this is a gateway
    local is_gateway=""
    for network_data in "${NETWORK_DATA[@]}"; do
      if [[ "$network_data" == *" $ip "* && "$network_data" == *"$ip"* ]]; then
        is_gateway=" gateway"
        break
      fi
    done

    # Start device block
    echo "<div class='device$is_gateway'>" >> "$HTML_REPORT"
    echo "<h3>$ip - $hostname</h3>" >> "$HTML_REPORT"
    echo "<div class='info'>" >> "$HTML_REPORT"

    # Add device details
    echo "<div class='info-item'><span class='label'>IP:</span> $ip</div>" >> "$HTML_REPORT"
    echo "<div class='info-item'><span class='label'>Hostname:</span> $hostname</div>" >> "$HTML_REPORT"
    echo "<div class='info-item'><span class='label'>MAC:</span> $mac</div>" >> "$HTML_REPORT"
    echo "<div class='info-item'><span class='label'>Vendor:</span> $vendor</div>" >> "$HTML_REPORT"
    echo "<div class='info-item'><span class='label'>Type:</span> $device_type</div>" >> "$HTML_REPORT"

    if [ -n "$open_ports" ]; then
      echo "<div class='info-item'><span class='label'>Open Ports:</span> <span class='open-ports'>$open_ports</span></div>" >> "$HTML_REPORT"
    else
      echo "<div class='info-item'><span class='label'>Open Ports:</span> None detected</div>" >> "$HTML_REPORT"
    fi

    # Check for warnings in lateral movement results
    if [ -f "$LATERAL_RESULTS" ]; then
      local warnings=$(grep -A 15 "Device: $ip" "$LATERAL_RESULTS" | grep "WARNING")
      if [ -n "$warnings" ]; then
        echo "<div class='info-item warning'><span class='label'>Warnings:</span> Security issues detected</div>" >> "$HTML_REPORT"
      fi
    fi

    # Close device block
    echo "</div></div>" >> "$HTML_REPORT"
  done

  # Close HTML
  cat << EOF >> "$HTML_REPORT"
  <div class="footer">
    <p>Scan performed using Enhanced Network Discovery Script v$VERSION</p>
  </div>
</body>
</html>
EOF

  echo -e "${GREEN}HTML report generated:${RESET} $HTML_REPORT"

  # Generate network map if graphviz is available
  if command -v dot &>/dev/null; then
    MAP_FILE="$SCAN_DIR/network_map.dot"

    # Create dot file header
    cat << EOF > "$MAP_FILE"
digraph network {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fillcolor=white];

  // Gateway nodes
EOF

    # Add gateway nodes
    for network_data in "${NETWORK_DATA[@]}"; do
      read -r network iface gateway local_ip cidr <<< "$network_data"
      if [ "$gateway" != "Unknown" ]; then
        echo "  \"$gateway\" [fillcolor=\"#27ae60\", fontcolor=white, label=\"Gateway\\n$gateway\"];" >> "$MAP_FILE"
      fi
    done

    # Add local device
    echo -e "\n  // Local device" >> "$MAP_FILE"
    for network_data in "${NETWORK_DATA[@]}"; do
      read -r network iface gateway local_ip cidr <<< "$network_data"
      echo "  \"$local_ip\" [fillcolor=\"#3498db\", fontcolor=white, label=\"This Device\\n$local_ip\"];" >> "$MAP_FILE"

      # Connect to gateway
      if [ "$gateway" != "Unknown" ]; then
        echo "  \"$local_ip\" -> \"$gateway\" [dir=both];" >> "$MAP_FILE"
      fi
    done

    # Add other devices
    echo -e "\n  // Other devices" >> "$MAP_FILE"
    for device_info in "${DEVICE_DETAILED_INFO[@]}"; do
      IFS='|' read -r ip hostname mac vendor device_type open_ports <<< "$device_info"

      # Skip if this is the local device or a gateway
      if [[ " ${NETWORK_DATA[@]} " =~ " $ip " ]]; then
        continue
      fi

      # Determine node color based on device type
      local color="white"
      local fontcolor="black"

      case "$device_type" in
        *"Server"*)
          color="#f1c40f"
          ;;
        *"Windows"*)
          color="#3498db"
          fontcolor="white"
          ;;
        *"Linux"*)
          color="#e67e22"
          ;;
        *"Apple"*)
          color="#7f8c8d"
          fontcolor="white"
          ;;
        *"Printer"*)
          color="#9b59b6"
          fontcolor="white"
          ;;
        *"IoT"*|*"Smart"*)
          color="#e74c3c"
          fontcolor="white"
          ;;
      esac

      local label=""
      if [ "$hostname" != "Unknown" ]; then
        label="$hostname\\n$ip"
      else
        label="$ip\\n$device_type"
      fi

      echo "  \"$ip\" [fillcolor=\"$color\", fontcolor=\"$fontcolor\", label=\"$label\"];" >> "$MAP_FILE"

      # Connect to gateway
      for network_data in "${NETWORK_DATA[@]}"; do
        read -r network iface gateway local_ip cidr <<< "$network_data"
        if [ "$gateway" != "Unknown" ]; then
          echo "  \"$ip\" -> \"$gateway\" [dir=both];" >> "$MAP_FILE"
        fi
      done
    done

    # Close dot file
    echo "}" >> "$MAP_FILE"

    # Generate PNG
    PNG_FILE="$SCAN_DIR/network_map.png"
    dot -Tpng "$MAP_FILE" -o "$PNG_FILE"

    echo -e "${GREEN}Network map generated:${RESET} $PNG_FILE"
  else
    echo -e "${YELLOW}Graphviz not installed. Network map not generated.${RESET}"
  fi
}

# Display detailed usage information
show_help() {
  echo -e "${BOLD}${MAGENTA}Enhanced Network Discovery Script v$VERSION${RESET}"
  echo -e "${CYAN}=================================================${RESET}"
  echo
  echo -e "${BOLD}${GREEN}DESCRIPTION${RESET}"
  echo -e "  A comprehensive network reconnaissance tool designed for Arch Linux systems that"
  echo -e "  discovers, identifies, and analyzes devices on your network using multiple detection"
  echo -e "  methods. The script performs OS fingerprinting, service enumeration, and optional"
  echo -e "  security testing to provide a detailed overview of your network infrastructure."
  echo
  echo -e "${BOLD}${GREEN}SYNOPSIS${RESET}"
  echo -e "  $0 [options]"
  echo
  echo -e "${BOLD}${GREEN}OPTIONS${RESET}"
  echo -e "  ${BOLD}-h, --help${RESET}"
  echo -e "      Display this detailed help information and exit."
  echo
  echo -e "  ${BOLD}-v, --vuln-scan${RESET}"
  echo -e "      Enable vulnerability scanning using Nmap's vulnerability detection scripts."
  echo -e "      This scans discovered devices for known vulnerabilities and security issues,"
  echo -e "      including outdated software, default credentials, and common misconfigurations."
  echo -e "      Note: This scan type significantly increases the total scan duration."
  echo
  echo -e "  ${BOLD}-l, --lateral-test${RESET}"
  echo -e "      Test for lateral movement possibilities within the network. This option checks for:"
  echo -e "      • Anonymous/null SMB shares access"
  echo -e "      • Default credentials on web interfaces"
  echo -e "      • Common SSH username/password combinations"
  echo -e "      • Anonymous FTP access"
  echo -e "      ${RED}WARNING: Only use this option on networks you own or have explicit permission"
  echo -e "      to test. This may trigger security systems and generate authentication logs.${RESET}"
  echo
  echo -e "  ${BOLD}-q, --quick${RESET}"
  echo -e "      Perform a faster scan with reduced detail. This option:"
  echo -e "      • Limits port scanning to most common ports"
  echo -e "      • Reduces timeout values"
  echo -e "      • Skips more intensive detection methods"
  echo -e "      • Uses more aggressive timing templates"
  echo -e "      Useful for getting a quick overview of large networks."
  echo
  echo -e "  ${BOLD}-o, --output DIR${RESET}"
  echo -e "      Specify a custom output directory for scan results instead of the default."
  echo -e "      The script will create the directory if it doesn't exist."
  echo -e "      Default: ./network_scan_YYYYMMDD_HHMMSS/"
  echo
  echo -e "${BOLD}${GREEN}SCAN PHASES${RESET}"
  echo -e "  1. ${BOLD}Dependency Check${RESET}: Verifies and installs required tools"
  echo -e "  2. ${BOLD}Network Interface Detection${RESET}: Identifies active network interfaces"
  echo -e "  3. ${BOLD}Network Range Discovery${RESET}: Determines network subnets and gateways"
  echo -e "  4. ${BOLD}Device Discovery${RESET}: Uses multiple methods to find all devices"
  echo -e "  5. ${BOLD}OS Detection${RESET}: Identifies operating systems on discovered devices"
  echo -e "  6. ${BOLD}Service Enumeration${RESET}: Identifies open ports and running services"
  echo -e "  7. ${BOLD}Vulnerability Assessment${RESET}: Optional scanning for security issues"
  echo -e "  8. ${BOLD}Lateral Movement Testing${RESET}: Optional checking for security weaknesses"
  echo -e "  9. ${BOLD}Report Generation${RESET}: Creates HTML report and network map"
  echo
  echo -e "${BOLD}${GREEN}OUTPUT FILES${RESET}"
  echo -e "  • ${BOLD}scan_summary.txt${RESET}: Overview of all discovered devices"
  echo -e "  • ${BOLD}device_X_X_X_X.txt${RESET}: Detailed information for each device"
  echo -e "  • ${BOLD}network_report.html${RESET}: Interactive HTML report of findings"
  echo -e "  • ${BOLD}network_map.png${RESET}: Visual representation of network topology"
  echo -e "  • ${BOLD}lateral_movement_test.txt${RESET}: Results of security testing (if enabled)"
  echo
  echo -e "${BOLD}${GREEN}EXAMPLES${RESET}"
  echo -e "  ${YELLOW}# Basic scan with OS detection${RESET}"
  echo -e "  sudo $0"
  echo
  echo -e "  ${YELLOW}# Quick scan of the network${RESET}"
  echo -e "  sudo $0 --quick"
  echo
  echo -e "  ${YELLOW}# Full scan with vulnerability assessment${RESET}"
  echo -e "  sudo $0 --vuln-scan"
  echo
  echo -e "  ${YELLOW}# Complete security assessment (only on authorized networks)${RESET}"
  echo -e "  sudo $0 --vuln-scan --lateral-test"
  echo
  echo -e "  ${YELLOW}# Save results to a specific location${RESET}"
  echo -e "  sudo $0 --output /home/user/network_scans"
  echo
  echo -e "${BOLD}${GREEN}REQUIRED TOOLS${RESET}"
  echo -e "  The script will automatically check for and install these dependencies:"
  echo -e "  • nmap: Network scanner, port scanner, OS detection"
  echo -e "  • net-tools: Basic network utilities (arp, ifconfig, etc.)"
  echo -e "  • iw/wireless_tools: Wireless network tools"
  echo -e "  • arp-scan: Layer 2 network scanner"
  echo -e "  • netdiscover: Active/passive network address scanner"
  echo -e "  • ipcalc: IP network calculator"
  echo -e "  • iputils: IP utilities (ping, traceroute, etc.)"
  echo -e "  • nbtscan: NetBIOS nameserver scanner"
  echo -e "  • whois: Domain/IP WHOIS lookup tool"
  echo
  echo -e "${BOLD}${GREEN}NOTES${RESET}"
  echo -e "  • This script requires root privileges to perform full network scanning."
  echo -e "  • Scan duration depends on network size and selected options."
  echo -e "  • For best results, run the script on a wired connection."
  echo -e "  • The script is designed for Arch Linux but may work on other distributions."
  echo -e "  • Network maps require graphviz to be installed."
  echo -e "  • Scanning public networks or networks without permission may be illegal."
  echo
  echo -e "${BOLD}${GREEN}SECURITY CONSIDERATIONS${RESET}"
  echo -e "  • All scanning activities are logged and may be detected by security systems."
  echo -e "  • The ${BOLD}--lateral-test${RESET} option attempts to access services and may generate logs."
  echo -e "  • Scan results may contain sensitive information about your network."
  echo -e "  • Handle the output files securely and do not share them unnecessarily."
  echo -e "  • The script does not exploit any vulnerabilities it finds."
  echo
  echo -e "${BOLD}${GREEN}AUTHOR${RESET}"
  echo -e "  Enhanced Network Discovery Script"
  echo
  echo -e "${BOLD}${RED}DISCLAIMER${RESET}"
  echo -e "  This tool is provided for legitimate network administration and security"
  echo -e "  assessment purposes only. Users are responsible for ensuring they have"
  echo -e "  appropriate authorization before scanning any network. The authors accept"
  echo -e "  no liability for misuse or damage caused by this script."
}

# Process command line options
process_options() {
  PERFORM_VULN_SCAN=false
  TEST_LATERAL=false
  QUICK_SCAN=false

  while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
      -h|--help)
        show_help
        exit 0
        ;;
      -v|--vuln-scan)
        PERFORM_VULN_SCAN=true
        shift
        ;;
      -l|--lateral-test)
        TEST_LATERAL=true
        shift
        ;;
      -q|--quick)
        QUICK_SCAN=true
        shift
        ;;
      -o|--output)
        SCAN_DIR="$2"
        shift
        shift
        ;;
      *)
        echo -e "${RED}Unknown option: $key${RESET}"
        show_help
        exit 1
        ;;
    esac
  done
}

# Main function
main() {
  # Process command line options
  process_options "$@"

  echo -e "${BOLD}${MAGENTA}Enhanced Network Device Discovery v$VERSION${RESET}"
  echo -e "${CYAN}=========================================${RESET}"

  # Install dependencies
  install_dependencies

  # Get network info
  get_interfaces
  detect_network_scope

  # Discover devices
  discover_all_devices

  # Perform advanced scans
  perform_advanced_scans

  # Perform lateral movement testing if requested
  if [ "$TEST_LATERAL" = true ]; then
    test_lateral_movement
  fi

  # Generate reports
  generate_reports

  echo -e "\n${BOLD}${GREEN}Network discovery and analysis complete!${RESET}"
  echo -e "${YELLOW}Found ${#ALL_DISCOVERED_DEVICES[@]} devices on your network.${RESET}"
  echo -e "Detailed results saved to: $SCAN_DIR"
}

# Execute main function with all arguments
main "$@"
