#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Create results and log directories in the current folder
RESULTS_DIR="$PWD/network_scan_results"
LOG_FILE="$RESULTS_DIR/scan.log"
mkdir -p "$RESULTS_DIR"
touch "$LOG_FILE"

# Variables
AUTO_MODE=false
INTERACTIVE_MODE=false
DEBUG_MODE=false

# Function to log and echo with optional debug delay
log_echo() {
    echo -e "$1" | tee -a "$LOG_FILE"
    if [ "$DEBUG_MODE" = true ]; then
        sleep 1  # Slows down for debug mode
    fi
}

# Progress bar function using pv
progress_bar() {
    while read -r line; do
        echo "$line"
        sleep 0.05  # Simulates progress (adjust based on scan speed)
    done | pv -p -t -e -b -N "$1" > /dev/null
}

# Parse command-line options
while getopts "aid" opt; do
    case $opt in
        a) AUTO_MODE=true ;;
        i) INTERACTIVE_MODE=true ;;
        d) DEBUG_MODE=true ;;
        *) echo "Usage: $0 [-a] for auto mode, [-i] for interactive mode, or [-d] for debug mode"; exit 1 ;;
    esac
done

# Debug mode configuration
if $DEBUG_MODE; then
    log_echo "${CYAN}Running in debug mode... Detailed logging enabled.${NC}"
fi

# Auto mode configuration
if $AUTO_MODE; then
    log_echo "${CYAN}Running in auto mode...${NC}"
    INTERACTIVE_MODE=false
fi

# Interactive mode configuration
if $INTERACTIVE_MODE; then
    log_echo "${CYAN}Running in interactive mode...${NC}"
fi

# Detect active network interface and range
ACTIVE_INTERFACE=$(ip -o -4 addr show | grep -v '127.0.0.1' | awk '{print $2}' | head -n 1)
NETWORK_RANGE=$(ip -o -4 addr show | grep -v '127.0.0.1' | awk '{print $4}' | head -n 1)

if $INTERACTIVE_MODE; then
    log_echo "${CYAN}Detected active network interface: ${ACTIVE_INTERFACE}${NC}"
    log_echo "${CYAN}Detected network range: ${NETWORK_RANGE}${NC}"
    read -p "Press Enter to confirm or input a different network range (e.g., 192.168.1.0/24): " USER_INPUT
    [ -n "$USER_INPUT" ] && NETWORK_RANGE="$USER_INPUT"
fi

log_echo "${CYAN}Using network range: ${NETWORK_RANGE}${NC}"

# Perform ARP scan
log_echo "${CYAN}Step 1: Discovering devices on the network using ARP scan...${NC}"
(sudo arp-scan --localnet --oui-file=/usr/share/arp-scan/ieee-oui.txt --mac-file=/usr/share/arp-scan/mac-vendor.txt > "$RESULTS_DIR/network_scan.txt") 2>/dev/null &
progress_bar "ARP Scan"
log_echo "${GREEN}ARP scan complete! Results saved to $RESULTS_DIR/network_scan.txt${NC}"

# Count the number of devices found
DEVICE_COUNT=$(grep -E '^[0-9a-fA-F:]' "$RESULTS_DIR/network_scan.txt" | wc -l)
log_echo "${CYAN}Devices found in ARP scan: ${DEVICE_COUNT}${NC}"

# If fewer than 10 devices found, perform a quick Nmap scan
if (( DEVICE_COUNT < 10 )); then
    log_echo "${YELLOW}Fewer than 10 devices found. Performing a quick Nmap scan to expand the list...${NC}"
    (nmap -sn "$NETWORK_RANGE" -oN "$RESULTS_DIR/quick_nmap_scan.txt") &
    progress_bar "Quick Nmap Scan"
    log_echo "${GREEN}Quick Nmap scan complete! Results saved to $RESULTS_DIR/quick_nmap_scan.txt${NC}"

    # Parse Nmap results to list IPs
    grep "Nmap scan report for" "$RESULTS_DIR/quick_nmap_scan.txt" | awk '{print $5}' > "$RESULTS_DIR/device_ips.txt"
else
    # Parse ARP scan results to list IPs
    grep -E '^[0-9a-fA-F:]' "$RESULTS_DIR/network_scan.txt" | awk '{print $1}' > "$RESULTS_DIR/device_ips.txt"
fi

# Clean device list to ensure only valid IP addresses are included
grep -E '^([0-9]{1,3}\.){3}[0-9]{1,3}$' "$RESULTS_DIR/device_ips.txt" > "$RESULTS_DIR/cleaned_device_ips.txt"
mv "$RESULTS_DIR/cleaned_device_ips.txt" "$RESULTS_DIR/device_ips.txt"

# Categorize devices by type (e.g., IoT, servers, PCs)
log_echo "${CYAN}Categorizing devices based on MAC vendors and services...${NC}"
touch "$RESULTS_DIR/device_categories.txt"
while read -r ip; do
    mac_vendor=$(grep "$ip" "$RESULTS_DIR/network_scan.txt" | awk '{print $2, $3}')
    category="Unknown"
    if [[ "$mac_vendor" =~ "Raspberry" || "$mac_vendor" =~ "Arduino" ]]; then
        category="IoT Device"
    elif [[ "$mac_vendor" =~ "Dell" || "$mac_vendor" =~ "HP" ]]; then
        category="PC"
    elif [[ "$mac_vendor" =~ "Cisco" || "$mac_vendor" =~ "Ubiquiti" ]]; then
        category="Networking Equipment"
    fi
    echo "$ip - $category" >> "$RESULTS_DIR/device_categories.txt"
done < "$RESULTS_DIR/device_ips.txt"

log_echo "${GREEN}Device categorization complete! Results saved to $RESULTS_DIR/device_categories.txt${NC}"

# Advanced scanning (optional in interactive mode or based on logic in auto mode)
if $INTERACTIVE_MODE || { $AUTO_MODE && grep -q -E ":22|:80|:3389" "$RESULTS_DIR/network_scan.txt"; }; then
    log_echo "${CYAN}Running advanced Nmap scan with service and OS detection...${NC}"
    (nmap -sV -O -oN "$RESULTS_DIR/advanced_scan.txt" -iL "$RESULTS_DIR/device_ips.txt") &
    progress_bar "Advanced Nmap Scan"
    log_echo "${GREEN}Advanced scan complete! Results saved to $RESULTS_DIR/advanced_scan.txt${NC}"
fi

# Final output
log_echo "${GREEN}Scan complete! Results saved in ${RESULTS_DIR}.${NC}"
log_echo "${CYAN}Log of all activities can be found in $LOG_FILE.${NC}"

