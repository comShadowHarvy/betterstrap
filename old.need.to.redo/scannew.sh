#!/usr/bin/env bash
################################################################################
#  script name: super_enumerator.sh
#  description:
#    1) Checks/installs needed tools on Debian/Arch
#    2) Gathers system info
#    3) Bluetooth scanning
#    4) Network: discover hosts (ping)
#    5) Fancy OS detection on each discovered host:
#       - prints full OS detection output
#       - picks a color-coded guess
#    6) Optional deeper scans (Levels 1..4)
#    7) Logs everything to a single report, plus optional debug logs
################################################################################

############################
#         COLORS
############################
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'  # No Color

############################
#       USAGE & ARGS
############################
usage() {
  echo -e "${BOLD}Usage:${NC} $0 [options]"
  echo
  echo "Options:"
  echo "  -s               Slow mode (adds sleep between steps)"
  echo "  -p <N>           Parallel scans (N jobs) for deeper scanning. Default=1"
  echo "  -l <1..4>        Level of deeper scanning (default=4):"
  echo "                     1 = Only host discovery + OS detection"
  echo "                     2 = + basic port scan (top 100)"
  echo "                     3 = + intermediate (top 1000, version detection)"
  echo "                     4 = + full (all TCP ports, scripts)"
  echo "  -i <iface>       Specify interface(s) for host discovery (repeatable)"
  echo "  -r <CIDR>        Specify subnet/range for discovery (e.g. 192.168.0.0/24)"
  echo "  -d               Debug mode: logs raw OS output to debug_os.txt as well"
  echo "  -h               Show this help message"
  echo
  echo "Examples:"
  echo "  $0 -l 1"
  echo "  $0 -l 4 -p 4"
  echo "  $0 -r 192.168.1.0/24 -s -d"
  exit 1
}

SLOW_MODE=0
PARALLEL_JOBS=1
LEVEL=4
DEBUG_MODE=0
TARGET_INTERFACES=()
TARGET_SUBNET=""

while getopts "sp:l:i:r:dh" opt; do
  case $opt in
    s) SLOW_MODE=1 ;;
    p) PARALLEL_JOBS="$OPTARG" ;;
    l) LEVEL="$OPTARG" ;;
    i) TARGET_INTERFACES+=("$OPTARG") ;;
    r) TARGET_SUBNET="$OPTARG" ;;
    d) DEBUG_MODE=1 ;;
    h) usage ;;
    \?) usage ;;
  esac
done

############################
#       SLOW HELPER
############################
pause_if_slow() {
  if [ "$SLOW_MODE" -eq 1 ]; then
    sleep 2
  fi
}

############################
#  CHECK & INSTALL PKGS
############################
function check_and_install() {
  local PKG="$1"
  if command -v "$PKG" &>/dev/null; then
    echo -e "${GREEN}[OK] $PKG is already installed.${NC}"
    return
  fi
  echo -e "${YELLOW}[*] $PKG not found. Attempting installation...${NC}"
  if [ -f /etc/debian_version ]; then
    echo -e "${GREEN}[*] Debian/Ubuntu system. Installing $PKG via apt-get.${NC}"
    apt-get update -y && apt-get install -y "$PKG"
  elif [ -f /etc/arch-release ]; then
    echo -e "${GREEN}[*] Arch system. Installing $PKG via pacman.${NC}"
    pacman -Sy --noconfirm "$PKG"
  else
    echo -e "${RED}[!] Unknown distro. Please install $PKG manually.${NC}"
  fi
}

PACKAGES=("lsb_release" "lshw" "inxi" "bluetoothctl" "hcitool" "nmap")
for pkg in "${PACKAGES[@]}"; do
  check_and_install "$pkg"
done

# Basic Bluetooth packages
if [ -f /etc/debian_version ]; then
  apt-get install -y bluetooth bluez bluez-tools 2>/dev/null
elif [ -f /etc/arch-release ]; then
  pacman -Sy --noconfirm bluez bluez-utils 2>/dev/null
fi

# Suggest root
if [[ $EUID -ne 0 ]]; then
  echo -e "${YELLOW}[*] Recommended to run as root or sudo for full functionality.${NC}"
fi

############################
#   SETUP OUTPUT LOG
############################
FINAL_REPORT="full_scan_report.txt"
echo "============================="  >  "$FINAL_REPORT"
echo " Full Scan Report"              >> "$FINAL_REPORT"
echo " Generated: $(date)"            >> "$FINAL_REPORT"
echo "============================="  >> "$FINAL_REPORT"

# Helper log function
log() {
  echo -e "$1"
  echo -e "$1" | sed 's/\x1B\[[0-9;]*[A-Za-z]//g' >> "$FINAL_REPORT"
}

############################
#   FANCY HEAD/FOOT
############################
fancy_header() {
  log "${MAGENTA}=============================================================${NC}"
  log "${BOLD}$1${NC}"
  log "${MAGENTA}=============================================================${NC}"
}

fancy_footer() {
  log "${MAGENTA}=============================================================${NC}"
  log "${BOLD}$1${NC}"
  log "${MAGENTA}=============================================================${NC}"
}

############################
#        MAIN STEPS
############################

fancy_header "Starting Super Enumerator (Level=$LEVEL, Parallel=$PARALLEL_JOBS)"

############################
# 1) SYSTEM INFORMATION
############################
log "\n${BLUE}${BOLD}[STEP 1] SYSTEM INFO${NC}"
pause_if_slow

# OS Release
log "${GREEN}-- OS Release --${NC}"
if command -v lsb_release &>/dev/null; then
  OSINFO=$(lsb_release -a 2>/dev/null)
  log "$OSINFO"
fi

# Kernel & Architecture
log "\n${GREEN}-- Kernel & Architecture --${NC}"
KERNELINFO=$(uname -a)
log "$KERNELINFO"

# CPU/Memory
log "\n${GREEN}-- CPU/Memory Info --${NC}"
if command -v lshw &>/dev/null; then
  log "${YELLOW}(Using lshw -short)${NC}"
  HWINFO=$(lshw -short 2>/dev/null | egrep -i 'processor|memory')
  log "$HWINFO"
elif command -v inxi &>/dev/null; then
  log "${YELLOW}(Using inxi -C -m)${NC}"
  HWINFO=$(inxi -C -m 2>/dev/null)
  log "$HWINFO"
fi

# Disk Info
log "\n${GREEN}-- Disk Info --${NC}"
if command -v lsblk &>/dev/null; then
  DISKINFO=$(lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE)
  log "$DISKINFO"
fi

############################
# 2) BLUETOOTH SCAN
############################
log "\n${BLUE}${BOLD}[STEP 2] BLUETOOTH DEVICE SCAN${NC}"
pause_if_slow

BT_FOUND=0

if command -v bluetoothctl &>/dev/null; then
  log "${GREEN}[+] bluetoothctl scanning...${NC}"
  bluetoothctl --timeout 2 power on &>/dev/null
  bluetoothctl --timeout 2 agent on &>/dev/null
  bluetoothctl --timeout 6 scan on &>/dev/null
  DEVICES=$(bluetoothctl devices)
  if [ -n "$DEVICES" ]; then
    BT_FOUND=1
    log "${GREEN}Discovered devices:${NC}"
    log "$DEVICES"

    log "\n${GREEN}Detailed info:${NC}"
    while read -r dev_line; do
      dev_mac=$(echo "$dev_line" | awk '{print $2}')
      if [ -n "$dev_mac" ]; then
        INFO=$(bluetoothctl info "$dev_mac")
        log "${YELLOW}Device: $dev_line${NC}"
        log "$INFO\n"
      fi
    done <<< "$DEVICES"
  else
    log "${RED}No devices found via bluetoothctl.${NC}"
  fi
fi

if command -v hcitool &>/dev/null; then
  log "${GREEN}[+] hcitool scanning...${NC}"
  rm -f hcitool_scan_output.txt
  hcitool scan > hcitool_scan_output.txt 2>/dev/null &
  sleep 5
  kill $! 2>/dev/null
  if [ -s hcitool_scan_output.txt ]; then
    BT_FOUND=1
    SCAN_OUT=$(cat hcitool_scan_output.txt)
    log "${GREEN}Devices found (Classic):${NC}\n$SCAN_OUT"
  else
    log "${RED}No devices found via 'hcitool scan'.${NC}"
  fi

  rm -f hcitool_lescan_output.txt
  hcitool lescan --duplicates --passive > hcitool_lescan_output.txt 2>&1 &
  sleep 5
  kill $! 2>/dev/null
  if [ -s hcitool_lescan_output.txt ]; then
    BT_FOUND=1
    LESCAN_OUT=$(cat hcitool_lescan_output.txt)
    log "${GREEN}Devices found (BLE):${NC}\n$LESCAN_OUT"
  else
    log "${RED}No BLE devices found via 'hcitool lescan'.${NC}"
  fi
fi

if [ "$BT_FOUND" -eq 0 ]; then
  log "${YELLOW}[!] No Bluetooth devices found or scanning not possible right now.${NC}"
fi

############################
# 3) NETWORK DISCOVERY
############################
log "\n${BLUE}${BOLD}[STEP 3] HOST DISCOVERY (PING)${NC}"
pause_if_slow

rm -f quick_scan.txt discovered_hosts.txt

if ! command -v nmap &>/dev/null; then
  log "${RED}nmap not found; skipping network scans.${NC}"
else
  # Identify subnets
  if [ -n "$TARGET_SUBNET" ]; then
    log "${GREEN}[+] Using user subnet: $TARGET_SUBNET${NC}"
    echo "$TARGET_SUBNET" > /tmp/enumerator_subnets.txt
  else
    if [ "${#TARGET_INTERFACES[@]}" -gt 0 ]; then
      log "${GREEN}[+] Using user-specified interfaces: ${TARGET_INTERFACES[*]}${NC}"
      :> /tmp/enumerator_subnets.txt
      for iface in "${TARGET_INTERFACES[@]}"; do
        ip -o -f inet addr show "$iface" 2>/dev/null | awk '{print $4}' >> /tmp/enumerator_subnets.txt
      done
    else
      DEFAULT_IFACE=$(ip route show default 2>/dev/null | awk '/default/ {print $5}' | head -n1)
      if [ -n "$DEFAULT_IFACE" ]; then
        log "${GREEN}[+] Detected default interface: $DEFAULT_IFACE${NC}"
        ip -o -f inet addr show "$DEFAULT_IFACE" | awk '{print $4}' > /tmp/enumerator_subnets.txt
      else
        log "${RED}No default interface found. Skipping host discovery.${NC}"
      fi
    fi
  fi

  if [ -s /tmp/enumerator_subnets.txt ]; then
    while read -r SUBNET; do
      log "${MAGENTA}[*] Pinging subnet: $SUBNET${NC}"
      nmap -sn -n "$SUBNET" -oG - >> quick_scan.txt
      pause_if_slow
    done < /tmp/enumerator_subnets.txt

    if [ -s quick_scan.txt ]; then
      grep "Status: Up" quick_scan.txt | grep -oP '(?<=Host: )(\d{1,3}\.){3}\d{1,3}' >> discovered_hosts.txt
      sort -u discovered_hosts.txt -o discovered_hosts.txt
      if [ -s discovered_hosts.txt ]; then
        log "${GREEN}[OK] Discovered hosts:${NC}"
        cat discovered_hosts.txt | while read -r h; do
          log "  -> $h"
        done
      else
        log "${RED}[!] No active hosts discovered.${NC}"
      fi
    else
      log "${RED}[!] No data in 'quick_scan.txt'.${NC}"
    fi
  else
    log "${RED}[!] No subnets found to scan. Nothing done.${NC}"
  fi
fi

############################
# 4) FANCY OS DETECTION
############################
log "\n${BLUE}${BOLD}[STEP 4] OS DETECTION (FULL + COLOR GUESS)${NC}"
pause_if_slow

if [ -s discovered_hosts.txt ]; then
  total_os_hosts=$(wc -l < discovered_hosts.txt)
  os_count=1

  # Function to run nmap OS detection
  function fancy_os_detect() {
    local host="$1"
    local os_out

    os_out=$(nmap -n -Pn -O --osscan-limit --max-retries=2 "$host" 2>&1)

    # Print raw output first
    log "${YELLOW}${BOLD}--- RAW OS DETECTION for $host ---${NC}"
    log "$os_out"

    # If debug, store to debug_os.txt
    if [ "$DEBUG_MODE" -eq 1 ]; then
      echo "$os_out" >> debug_os.txt
      echo -e "\n----\n" >> debug_os.txt
    fi

    # Parse lines
    local running_line
    running_line=$(echo "$os_out" | grep -m1 '^Running: ' | sed 's/^Running: //')
    local guess_line
    guess_line=$(echo "$os_out" | grep -m1 '^Aggressive OS guesses: ' | sed 's/^Aggressive OS guesses: //')
    local details_line
    details_line=$(echo "$os_out" | grep -m1 '^OS details: ' | sed 's/^OS details: //')

    local likely_os=""
    if [ -n "$running_line" ]; then
      likely_os="$running_line"
    elif [ -n "$guess_line" ]; then
      likely_os="$guess_line"
    elif [ -n "$details_line" ]; then
      likely_os="$details_line"
    else
      likely_os="No OS guess found."
    fi

    # Color-coded guess
    local color="$YELLOW"
    if [[ "$likely_os" =~ [Ww]indows ]]; then
      color="$BLUE"
      likely_os="Likely Windows: $likely_os"
    elif [[ "$likely_os" =~ [Ll]inux ]]; then
      color="$GREEN"
      likely_os="Likely Linux: $likely_os"
    elif [[ "$likely_os" =~ [Mm]ac\ [Oo][Ss] ]] || [[ "$likely_os" =~ [Oo][Ss]\ [Xx] ]] || [[ "$likely_os" =~ [Mm]ac[Oo][Ss] ]]; then
      color="$CYAN"
      likely_os="Likely macOS: $likely_os"
    elif [[ "$likely_os" =~ [Ff]ree[Bb][Ss][Dd] ]] || [[ "$likely_os" =~ [Oo]pen[Bb][Ss][Dd] ]]; then
      color="$RED"
      likely_os="Likely BSD: $likely_os"
    else
      likely_os="Unknown or niche OS: $likely_os"
    fi

    log "\n${BOLD}${color}--- OS GUESS for $host ---${NC}"
    log "${color}$likely_os${NC}"
  }

  while read -r host; do
    percent_os=$((100 * os_count / total_os_hosts))
    log "${GREEN}[$os_count/$total_os_hosts] $percent_os% - OS detection on: $host${NC}"
    fancy_os_detect "$host"
    os_count=$((os_count + 1))
    pause_if_slow
  done < discovered_hosts.txt
else
  log "${RED}No discovered hosts. Skipping OS detection.${NC}"
fi

############################
# 5) DEEPER SCANS (LEVELS)
############################
log "\n${BLUE}${BOLD}[STEP 5] DEEPER SCANS (Levels=$LEVEL)${NC}"
pause_if_slow

if [ "$LEVEL" -eq 1 ]; then
  log "${GREEN}Level=1 => Only discovery & OS detection done.${NC}"
else
  if [ -s discovered_hosts.txt ]; then
    total_hosts=$(wc -l < discovered_hosts.txt)
    log "${GREEN}[$total_hosts hosts] => Deeper scanning at level $LEVEL...${NC}"
    pause_if_slow

    function get_nmap_cmd_for_level() {
      local lvl="$1"
      case "$lvl" in
        2)
          # top 100, skip DNS
          echo "nmap -n -T4 --top-ports 100 -sS --max-retries=1"
          ;;
        3)
          # top 1000, version detection
          echo "nmap -n -T4 --top-ports 1000 -sV --max-retries=2"
          ;;
        4)
          # all ports + scripts
          # not using -O here since we already did OS detection
          echo "nmap -n -sV -p- --script=vuln,default --max-retries=3"
          ;;
      esac
    }

    DEEPER_CMD="$(get_nmap_cmd_for_level "$LEVEL")"

    function run_deeper_scan() {
      local host="$1"
      local scan_out
      scan_out=$($DEEPER_CMD "$host" 2>&1)
      # Log to final report
      echo -e "\n--- Deeper Scan Results for $host ---\n$scan_out\n" \
        | sed 's/\x1B\[[0-9;]*[A-Za-z]//g' >> "$FINAL_REPORT"
      # Also print short form to console
      echo -e "${MAGENTA}[Deeper Scan:$host]${NC}\n$scan_out\n"
    }

    if [ "$PARALLEL_JOBS" -gt 1 ]; then
      log "${MAGENTA}[*] Parallel scans: $PARALLEL_JOBS jobs${NC}"
      cat discovered_hosts.txt | xargs -I{} -n1 -P "$PARALLEL_JOBS" bash -c "run_deeper_scan {}"
    else
      idx=1
      while read -r host; do
        pct=$((100 * idx / total_hosts))
        log "${GREEN}[$idx/$total_hosts] $pct% => Deeper scan: $host${NC}"
        run_deeper_scan "$host"
        idx=$((idx + 1))
        pause_if_slow
      done < discovered_hosts.txt
    fi
  else
    log "${RED}No discovered_hosts.txt => no deeper scans.${NC}"
  fi
fi

############################
# 6) WRAP-UP
############################
fancy_footer "Cleanup & Summary"

rm -f /tmp/enumerator_subnets.txt 2>/dev/null
rm -f hcitool_scan_output.txt hcitool_lescan_output.txt 2>/dev/null
rm -f quick_scan.txt 2>/dev/null
# If you want to remove discovered_hosts.txt => uncomment:
# rm -f discovered_hosts.txt

log "${GREEN}All done! Full results in $FINAL_REPORT${NC}"
if [ "$DEBUG_MODE" -eq 1 ]; then
  log "${YELLOW}Debug OS logs in debug_os.txt${NC}"
fi
fancy_footer "Script Completed Successfully!"
