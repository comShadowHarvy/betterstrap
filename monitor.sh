#!/bin/bash

# Default number of lines to show (can be overridden with first argument)
LINES=${1:-20}

# Check if dmesg supports --follow option
if sudo dmesg --help 2>&1 | grep -q -- "--follow"; then
    # Function for cleaner exit
    cleanup() {
        # Kill any background processes
        if [ -n "$PID" ]; then
            kill $PID 2>/dev/null
        fi
        tput cnorm  # Restore cursor
        exit 0
    }
    trap cleanup INT TERM EXIT

    # Hide cursor for cleaner display
    tput civis

    # Clear screen and show header
    clear
    echo "Rolling dmesg output (last $LINES lines)"
    echo "Press Ctrl+C to exit"
    echo "========================="

    # Initial display
    sudo dmesg | tail -n $LINES

    # Get the timestamp of the last message or use 0 if none
    LAST_TIMESTAMP=$(sudo dmesg | tail -n 1 | grep -o '\[[0-9.]*\]' | tr -d '[]' || echo "0")

    echo "========================="
    echo "Waiting for new messages..."

    # Use --follow option with filtering to avoid duplicates
    sudo dmesg --follow | awk -v last="$LAST_TIMESTAMP" '
    {
        # If message has a timestamp in standard format
        if ($1 ~ /^\[[0-9.]+\]/) {
            ts = $1;
            gsub(/[\[\]]/, "", ts);
            
            # Only print if timestamp is newer
            if (ts > last) {
                print $0;
                fflush();
            }
        } 
        # If message has no timestamp or non-standard format, print it after initial display
        else if (last != "0") {
            print $0;
            fflush();
        }
    }' &
    
    # Store the background process ID
    PID=$!
    
    # Wait for the background process
    wait $PID
else
    # Fallback to watch command for older systems
    echo "Using watch command (dmesg --follow not available)"
    
    # Use watch command with short refresh interval
    watch -n 1 "sudo dmesg | tail -n $LINES"
fi
