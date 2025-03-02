#!/usr/bin/env bash

# Data collection script
# Similar to InfoGrabber for Windows

LOGFILE="$1"

# Validate log file
if [ -z "$LOGFILE" ]; then
    echo "Usage: $0 <log_file_path>" >&2
    exit 1
fi

if ! touch "$LOGFILE" &>/dev/null; then
    echo "Cannot write to $LOGFILE. Check permissions!" >&2
    exit 1
fi

echo "Linux system info grabber" > "$LOGFILE"
echo "" >> "$LOGFILE"

echo "Interfaces" >> "$LOGFILE"
echo "##############" >> "$LOGFILE"
ifconfig -a >> "$LOGFILE" 2>/dev/null || echo "ifconfig not available" >> "$LOGFILE"
echo "" >> "$LOGFILE"

echo "Mounted FS" >> "$LOGFILE"
echo "##############" >> "$LOGFILE"
findmnt -A >> "$LOGFILE" 2>/dev/null || echo "findmnt not available" >> "$LOGFILE"
echo "" >> "$LOGFILE"

echo "Wi-Fi Information" >> "$LOGFILE"
echo "##############" >> "$LOGFILE"
iwconfig >> "$LOGFILE" 2>/dev/null || echo "iwconfig not available" >> "$LOGFILE"
nmcli dev wifi >> "$LOGFILE" 2>/dev/null || echo "nmcli not available" >> "$LOGFILE"
echo "" >> "$LOGFILE"

echo "Processes" >> "$LOGFILE"
echo "##############" >> "$LOGFILE"
ps -ax >> "$LOGFILE"
echo "" >> "$LOGFILE"

echo "Local Users" >> "$LOGFILE"
echo "##############" >> "$LOGFILE"
cat /etc/passwd | cut -d: -f1 >> "$LOGFILE"
echo "" >> "$LOGFILE"

echo "Firewall Rules" >> "$LOGFILE"
echo "##############" >> "$LOGFILE"
iptables -L -v >> "$LOGFILE" 2>/dev/null || echo "iptables not available" >> "$LOGFILE"
echo "" >> "$LOGFILE"

echo "Open Ports" >> "$LOGFILE"
echo "##############" >> "$LOGFILE"
ss -tuln >> "$LOGFILE"
echo "" >> "$LOGFILE"

echo "Installed Software" >> "$LOGFILE"
echo "##############" >> "$LOGFILE"
if command -v apt &>/dev/null; then
    apt list --installed >> "$LOGFILE" 2>/dev/null || echo "apt not available" >> "$LOGFILE"
elif command -v pacman &>/dev/null; then
    pacman -Q >> "$LOGFILE" 2>/dev/null || echo "pacman not available" >> "$LOGFILE"
elif command -v dnf &>/dev/null; then
    dnf list installed >> "$LOGFILE" 2>/dev/null || echo "dnf not available" >> "$LOGFILE"
else
    echo "No package manager found" >> "$LOGFILE"
fi
echo "" >> "$LOGFILE"

echo "Kernel Logs" >> "$LOGFILE"
echo "##############" >> "$LOGFILE"
dmesg | tail -n 50 >> "$LOGFILE"
echo "" >> "$LOGFILE"
