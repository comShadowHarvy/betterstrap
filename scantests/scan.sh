#!/bin/bash

NETWORK="192.168.1.0/24"  # CIDR notation
DECOY_IPS=("10.10.10.10" "10.20.30.40" "192.168.0.50")
MAX_PARALLEL=5
PORTS="22,80,443,3306,8080,8443"

# Improved progress tracking
progress() {
    echo "[$(date +'%H:%M:%S')] $1"
}

# More efficient parallel scan function
parallel_scan() {
    local port=$1
    timeout 30 sudo nmap -T4 -sS -n --max-retries 2 \
        -p$port -D ${DECOY_IPS[*]} $TARGET >/dev/null 2>&1 &
    
    if [ $? -eq 124 ]; then
        progress "Scan timeout on port $port"
    fi
}

# Add network range calculation
get_ip_range() {
    nmap -sL -n "$1" | awk '/Nmap scan report/{print $NF}'
}

# Main scanning logic
progress "Starting optimized stealth scan on network $NETWORK..."

# Scan each IP in the range
for TARGET in $(get_ip_range "$NETWORK"); do
    progress "Scanning host: $TARGET"
    
    echo $PORTS | tr ',' '\n' | while read port; do
        parallel_scan $port
        
        # Control parallel processes
        while [ $(jobs -r | wc -l) -ge $MAX_PARALLEL ]; do
            sleep 0.5
        done
    done
    
    # Wait for current host scans to complete before moving to next
    wait
done

progress "Network scan completed successfully."
