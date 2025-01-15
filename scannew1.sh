#!/usr/bin/env bash
################################################################################
#  script name: one_file_enumerator.sh
#  description:
#    1) Checks/installs required tools (Debian/Arch)
#    2) Gathers system info
#    3) Extended Bluetooth scanning using bluetoothctl + hcitool (if available)
#    4) Two-phase network scan:
#       - Phase 1: Quick “ping” discovery
#       - Phase 2: Detailed scanning (all ports, version, OS detection,
#         manufacturer if script is available, vulnerability checks)
#       * Includes progress bar for multiple hosts
#    5) Outputs all results into one file in a nicely presented manner
#    6) Optional -s (slow) mode for readability
################################################################################

############################
#        COLOR SETUP       #
############################
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'  # No Color

############################
#   PARSE SCRIPT OPTIONS   #
############################
SLOW_MODE=0
while getopts "s" opt; do
  case $opt in
    s) SLOW_MODE=1 ;;
    \?) echo "Invalid option: -$OPTARG"; exit 1 ;;
  esac
done

# Helper function for optional "slow" execution
slow() {
  if [ "$SLOW_MODE" -eq 1 ]; then
    sleep 2
  fi
}

############################
#        PRE-FLIGHT        #
############################
function install_package_if_missing() {
  local PKG="$1"

  if ! command -v "$PKG" &>/dev/null; then
    echo -e "${YELLOW}[*] $PKG not found. Attempting installation...${NC}"
    # Attempt to determine if Debian/Ubuntu or Arch
    if [ -f /etc/debian_version ]; then
      echo -e "${GREEN}[*] Detected Debian/Ubuntu system. Installing $PKG via apt-get.${NC}"
      apt-get update -y && apt-get install -y "$PKG"
    elif [ -f /etc/arch-release ]; then
      echo -e "${GREEN}[*] Detected Arch system. Installing $PKG via pacman.${NC}"
      pacman -Sy --noconfirm "$PKG"
    else
      echo -e "${RED}Could not detect Debian/Arch. Please install $PKG manually.${NC}"
    fi
  else
    echo -e "${GREEN}[OK] $PKG is installed.${NC}"
  fi
}

# List of packages we might need
PACKAGES=("lsb_release" "lshw" "inxi" "bluetoothctl" "hcitool" "nmap")

# Attempt to install each package if missing
for pkg in "${PACKAGES[@]}"; do
  install_package_if_missing "$pkg"
done

# Also ensure basic Bluetooth packages if they're not present
if [ -f /etc/debian_version ]; then
  apt-get install -y bluetooth bluez bluez-tools 2>/dev/null
elif [ -f /etc/arch-release ]; then
  pacman -Sy --noconfirm bluez bluez-utils 2>/dev/null
fi

# Suggest running as root for maximum functionality
if [[ $EUID -ne 0 ]]; then
  echo -e "${YELLOW}[*] It is recommended to run this script as root or via sudo for full functionality.${NC}"
fi

############################
#   SINGLE OUTPUT FILE     #
############################
FINAL_REPORT="full_scan_report.txt"
# Initialize (overwrite) the report file
echo "============================="  >  "$FINAL_REPORT"
echo " Full Scan Report"              >> "$FINAL_REPORT"
echo " Generated: $(date)"            >> "$FINAL_REPORT"
echo "============================="  >> "$FINAL_REPORT"

# Helper function to log both to console and the final report file
log() {
  echo -e "$1"
  # Strip out escape codes (colors) for the file
  # Using sed to remove ASCII escape sequences:
  echo -e "$1" | sed 's/\x1B\[[0-9;]*[A-Za-z]//g' >> "$FINAL_REPORT"
}

log "${GREEN}${BOLD}Starting Enumeration Script (Single File Logging)...${NC}"
slow

############################
#       SYSTEM INFO        #
############################
log "\n${BLUE}=======================================================${NC}"
log "${BLUE}${BOLD}[1/6] SYSTEM INFORMATION${NC}"
log "${BLUE}=======================================================${NC}"

log "${GREEN}-- OS Release --${NC}"
if command -v lsb_release &>/dev/null; then
  OSINFO=$(lsb_release -a 2>/dev/null)
  log "$OSINFO"
else
  log "lsb_release not installed."
fi

log "\n${GREEN}-- Kernel & Architecture --${NC}"
KERNELINFO=$(uname -a)
log "$KERNELINFO"

log "\n${GREEN}-- CPU/Memory Info --${NC}"
if command -v lshw &>/dev/null; then
  log "${YELLOW}(Using lshw -short)${NC}"
  HWINFO=$(lshw -short 2>/dev/null)
  log "$HWINFO"
elif command -v inxi &>/dev/null; then
  log "${YELLOW}(Using inxi -C -m)${NC}"
  HWINFO=$(inxi -C -m 2>/dev/null)
  log "$HWINFO"
else
  log "No lshw or inxi found. Skipping CPU/memory info."
fi

log "\n${GREEN}-- Disk Info --${NC}"
if command -v lsblk &>/dev/null; then
  DISKINFO=$(lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE)
  log "$DISKINFO"
else
  log "lsblk not found. Skipping."
fi
slow

############################
#     EXTENDED BLUETOOTH   #
############################
log "\n${BLUE}=======================================================${NC}"
log "${BLUE}${BOLD}[2/6] BLUETOOTH DEVICE SCAN (Extended)${NC}"
log "${BLUE}=======================================================${NC}"

BT_FOUND=0

# 1) bluetoothctl-based scan
if command -v bluetoothctl &>/dev/null; then
  log "${GREEN}[+] Using bluetoothctl for scanning...${NC}"
  # Turn on the adapter, start scanning briefly
  bluetoothctl --timeout 2 power on &>/dev/null
  bluetoothctl --timeout 2 agent on &>/dev/null
  bluetoothctl --timeout 5 scan on &>/dev/null

  DEVICES=$(bluetoothctl devices)
  if [ -n "$DEVICES" ]; then
    BT_FOUND=1
    log "${GREEN}Discovered devices (bluetoothctl):${NC}"
    log "$DEVICES"

    # More details on each device
    log "\n${GREEN}Detailed info for each discovered device:${NC}"
    while read -r dev_line; do
      dev_mac=$(echo "${dev_line}" | awk '{print $2}')
      if [ -n "${dev_mac}" ]; then
        log "${YELLOW}Device: ${dev_line}${NC}"
        INFO=$(bluetoothctl info "${dev_mac}")
        log "$INFO\n"
      fi
    done <<< "$DEVICES"
  else
    log "${RED}No devices found via bluetoothctl scan.${NC}"
  fi
else
  log "${RED}bluetoothctl not found. Skipping bluetoothctl scan.${NC}"
fi
slow

# 2) hcitool-based scan
if command -v hcitool &>/dev/null; then
  log "${GREEN}[+] Using hcitool for active scanning...${NC}"
  log "${YELLOW}Attempting 'hcitool scan' (Classic)${NC}"
  
  rm -f hcitool_scan_output.txt
  hcitool scan > hcitool_scan_output.txt 2>/dev/null &
  sleep 5
  kill $! 2>/dev/null
  
  if [ -s hcitool_scan_output.txt ]; then
    BT_FOUND=1
    SCAN_OUT=$(cat hcitool_scan_output.txt)
    log "${GREEN}Devices found (Classic):${NC}\n$SCAN_OUT"
  else
    log "${RED}No devices found via hcitool scan (Classic).${NC}"
  fi

  log "\n${YELLOW}Attempting 'hcitool lescan' (BLE)${NC}"
  rm -f hcitool_lescan_output.txt
  hcitool lescan --duplicates --passive > hcitool_lescan_output.txt 2>&1 &
  sleep 5
  kill $! 2>/dev/null
  
  if [ -s hcitool_lescan_output.txt ]; then
    BT_FOUND=1
    LESCAN_OUT=$(cat hcitool_lescan_output.txt)
    log "${GREEN}Devices found (BLE):${NC}\n$LESCAN_OUT"
  else
    log "${RED}No devices found via hcitool lescan (BLE).${NC}"
  fi
else
  log "${RED}hcitool not found or unavailable. Skipping advanced hcitool scans.${NC}"
fi

if [ "$BT_FOUND" -eq 0 ]; then
  log "${RED}[!] No Bluetooth devices found or scanning not possible with current setup.${NC}"
fi
slow

############################
#  NETWORK SCAN - PHASE 1  #
#    Quick Host Discovery  #
############################
log "\n${BLUE}=======================================================${NC}"
log "${BLUE}${BOLD}[3/6] NETWORK SCAN: PHASE 1 (Quick Discovery)${NC}"
log "${BLUE}=======================================================${NC}"

if command -v nmap &>/dev/null; then
  DEFAULT_IFACE=$(ip route show default 2>/dev/null | awk '/default/ {print $5}' | head -n1)
  if [ -n "$DEFAULT_IFACE" ]; then
    IP_ADDR=$(ip -o -f inet addr show "$DEFAULT_IFACE" | awk '{print $4}')
    log "${GREEN}[*] Detected default interface:${NC} $DEFAULT_IFACE"
    log "${GREEN}[*] Detected local subnet/IP:  ${NC} $IP_ADDR"
    slow

    log "\n${PURPLE}[+] Running quick discovery scan (ping scan) with nmap...${NC}"
    nmap -sn "$IP_ADDR" -oG quick_scan.txt
    slow

    if [ -s quick_scan.txt ]; then
      # Extract discovered hosts
      grep "Status: Up" quick_scan.txt | grep -oP '(?<=Host: )(\d{1,3}\.){3}\d{1,3}' > discovered_hosts.txt

      if [ -s discovered_hosts.txt ]; then
        log "${GREEN}[OK] Hosts discovered:${NC}"
        HOSTS=$(cat discovered_hosts.txt)
        log "$HOSTS"
      else
        log "${RED}[!] No active hosts discovered in $IP_ADDR${NC}"
      fi
    else
      log "${RED}[!] quick_scan.txt was empty or not generated properly.${NC}"
    fi
  else
    log "${RED}Could not identify a default interface. Skipping network scan.${NC}"
  fi
else
  log "${RED}nmap not found. Please install nmap to perform network scans.${NC}"
fi
slow

############################
#  NETWORK SCAN - PHASE 2  #
#    Detailed Enumeration  #
############################
log "\n${BLUE}=======================================================${NC}"
log "${BLUE}${BOLD}[4/6] NETWORK SCAN: PHASE 2 (Detailed Enumeration)${NC}"
log "${BLUE}=======================================================${NC}"

if [ -s discovered_hosts.txt ]; then
  total_hosts=$(wc -l < discovered_hosts.txt)
  host_index=1

  # Check if "mac-lookup.nse" is present. If not, remove from scripts list to avoid errors
  SCRIPTS="vuln,mac-lookup"
  if [ ! -f /usr/share/nmap/scripts/mac-lookup.nse ] && [ ! -f /usr/local/share/nmap/scripts/mac-lookup.nse ]; then
    log "${YELLOW}[!] 'mac-lookup.nse' not found. Omitting 'mac-lookup' from scripts.${NC}"
    SCRIPTS="vuln"
  fi

  while read -r host; do
    percent=$(( 100 * host_index / total_hosts ))
    log "${GREEN}[${host_index}/${total_hosts}] (${percent}%) Scanning host: $host${NC}"

    # -sV: Version detection
    # -O : OS detection
    # -p-: All ports
    # --script: $SCRIPTS (vuln, plus mac-lookup if available)
    SCAN_RESULT=$(nmap -sV -O -p- --script="$SCRIPTS" "$host" 2>&1)
    log "\n${YELLOW}--- Detailed Nmap Results for $host ---${NC}\n$SCAN_RESULT\n"

    host_index=$((host_index + 1))
    slow
  done < discovered_hosts.txt
else
  log "${RED}No discovered_hosts.txt file or it's empty. Skipping deeper scans.${NC}"
fi
slow

############################
#        WRAP-UP           #
############################
log "\n${BLUE}=======================================================${NC}"
log "${BLUE}${BOLD}[5/6] REPORT SUMMARY${NC}"
log "${BLUE}=======================================================${NC}"
log "All logs have been saved in: $FINAL_REPORT"

log "\n${BLUE}=======================================================${NC}"
log "${BLUE}${BOLD}[6/6] SCRIPT COMPLETED!${NC}"
log "${BLUE}=======================================================${NC}"
log "${GREEN}All done. Review $FINAL_REPORT for the complete scan results.${NC}"

# Final tip:
# If you'd like to keep quick_scan.txt / discovered_hosts.txt for reference, they remain in the same directory.
# The final report in 'full_scan_report.txt' includes everything in a single place.
