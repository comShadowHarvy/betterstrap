#!/bin/bash

# Required dependencies
DEPS=(nmap arp-scan sipcalc)

# Colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    logger -t "network-scan" "ERROR: $1"
}

log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
    logger -t "network-scan" "INFO: $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    logger -t "network-scan" "SUCCESS: $1"
}

# Check dependencies before proceeding
check_deps() {
    local missing=()
    for dep in "${DEPS[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            missing+=("$dep")
        fi
    done
    
    if [ ${#missing[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing[*]}"
        echo "Please install missing dependencies:"
        echo "sudo apt-get install ${missing[*]}"
        exit 1
    fi
}

# Enhanced device categorization
categorize_device() {
    local mac_vendor="$1"
    local categories=(
        "IoT Device:Raspberry|Arduino|Espressif|Nordic"
        "PC:Dell|HP|Lenovo|Apple|Intel|AMD"
        "Networking:Cisco|Ubiquiti|Netgear|D-Link|TP-Link"
        "Mobile:Samsung|Apple|Huawei|Xiaomi|OnePlus"
        "Media:Sony|LG|Samsung|Roku|Amazon"
    )
    
    for category in "${categories[@]}"; do
        IFS=':' read -r cat_name cat_pattern <<< "$category"
        if [[ "$mac_vendor" =~ ($cat_pattern) ]]; then
            echo "$cat_name"
            return 0
        fi
    done
    echo "Unknown"
}

# Progress indicator
show_spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while kill -0 $pid 2>/dev/null; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Create results and log directories in the current folder (moved up)
RESULTS_DIR="$PWD/network_scan_results"
LOG_FILE="$RESULTS_DIR/scan.log"
mkdir -p "$RESULTS_DIR"
touch "$LOG_FILE"

# Global Variables
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

# Validate network range
validate_network() {
    if ! echo "$NETWORK_RANGE" | grep -qE '^([0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}$'; then
        log_error "Invalid network range: $NETWORK_RANGE"
        exit 1
    fi
}

# --- Begin Optimized ARP Scan Execution ---
# Check dependencies early
check_deps

validate_network

log_echo "${CYAN}Step 1: Discovering devices on the network using ARP scan...${NC}"
ARP_OPTS="--localnet --rate=100 --timeout=2000 --retry=2"
ARP_OPTS+=" --oui-file=/usr/share/arp-scan/ieee-oui.txt"
ARP_OPTS+=" --mac-file=/usr/share/arp-scan/mac-vendor.txt"

# Run ARP scan in background to enable proper spinner usage
sudo timeout 300 arp-scan $ARP_OPTS > "$RESULTS_DIR/network_scan.txt" 2>/dev/null &
arp_pid=$!
show_spinner "$arp_pid"
wait $arp_pid
if [ $? -ne 0 ]; then
    log_error "ARP scan failed or timed out"
    touch "$RESULTS_DIR/.scan_failed"
fi
log_echo "${GREEN}ARP scan complete! Results saved to $RESULTS_DIR/network_scan.txt${NC}"

# Count discovered devices and process results
DEVICE_COUNT=$(grep -E '^[0-9a-fA-F:]' "$RESULTS_DIR/network_scan.txt" | wc -l)
log_echo "${CYAN}Devices found in ARP scan: ${DEVICE_COUNT}${NC}"

if (( DEVICE_COUNT < 10 )); then
    log_echo "${YELLOW}Fewer than 10 devices found. Performing parallel Nmap scans...${NC}"
    NMAP_OPTS="-sn -T4 --max-retries 2 --max-rate 100"
    parallel -j 4 "nmap $NMAP_OPTS {} -oN $RESULTS_DIR/nmap_scan_{#}.txt" \
        ::: $(echo "$NETWORK_RANGE" | tr '/' ' ' | xargs sipcalc | grep 'Network' | head -n1 | awk '{print $4}') \
        2>/dev/null
    find "$RESULTS_DIR" -name "nmap_scan_*.txt" -exec grep "Nmap scan report for" {} \; | \
        awk '{print $5}' | sort -u > "$RESULTS_DIR/device_ips.txt"
else
    grep -E '^[0-9a-fA-F:]' "$RESULTS_DIR/network_scan.txt" | \
        awk '{print $1}' | sort -u > "$RESULTS_DIR/device_ips.txt"
fi

# Verify and clean IP addresses
# Ensure verified_ips.txt exists before appending
touch "$RESULTS_DIR/verified_ips.txt"
while IFS= read -r ip; do
    if [[ $ip =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] && ping -c 1 -W 1 "$ip" >/dev/null 2>&1; then
        echo "$ip" >> "$RESULTS_DIR/verified_ips.txt"
    fi
done < "$RESULTS_DIR/device_ips.txt"
mv "$RESULTS_DIR/verified_ips.txt" "$RESULTS_DIR/cleaned_device_ips.txt"

# Save scan metadata
cat > "$RESULTS_DIR/scan_metadata.json" << EOF
{
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "network_range": "$NETWORK_RANGE",
    "device_count": $DEVICE_COUNT,
    "scan_duration": $SECONDS
}
EOF

# Categorize devices by type
log_echo "${CYAN}Categorizing devices based on MAC vendors and services...${NC}"
touch "$RESULTS_DIR/device_categories.txt"
while IFS= read -r ip; do
    mac_vendor=$(grep "$ip" "$RESULTS_DIR/network_scan.txt" | awk '{$1=""; print $0}' | xargs)
    category=$(categorize_device "$mac_vendor")
    printf "%-15s %-20s %s\n" "$ip" "$category" "$mac_vendor" >> "$RESULTS_DIR/device_categories.txt"
done < "$RESULTS_DIR/device_ips.txt"
log_echo "${GREEN}Device categorization complete! Results saved to $RESULTS_DIR/device_categories.txt${NC}"

# Advanced scanning based on mode or if specific ports are detected
if $INTERACTIVE_MODE || { $AUTO_MODE && grep -q -E ":22|:80|:3389" "$RESULTS_DIR/network_scan.txt"; }; then
    log_info "Running advanced Nmap scan..."
    nmap -sV -O -oN "$RESULTS_DIR/advanced_scan.txt" -iL "$RESULTS_DIR/device_ips.txt" >/dev/null 2>&1 &
    adv_pid=$!
    show_spinner "$adv_pid"
    wait $adv_pid
    if [ $? -eq 0 ]; then
        log_success "Advanced scan complete!"
    else
        log_error "Advanced scan failed"
        touch "$RESULTS_DIR/.scan_failed"
    fi
fi

# Generate final report
{
    echo "Scan Results $(date)"
    echo "----------------"
    echo "Devices found: $DEVICE_COUNT"
    echo "----------------"
    cat "$RESULTS_DIR/device_ips.txt"
} > "$RESULTS_DIR/scan_report.txt"
log_success "Scan complete. Check $RESULTS_DIR/scan_report.txt for results"
log_echo "${CYAN}Log of all activities can be found in $LOG_FILE.${NC}"

