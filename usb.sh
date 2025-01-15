#!/bin/bash

# Script to continuously monitor and display new USB updates

filter_string="usb"  # Filter string for USB events

# Store the last message timestamp for comparison
last_timestamp=""

while true; do
    # Get all new messages since the last timestamp
    new_usb_messages=$(dmesg | grep -i "$filter_string" | awk -v last_ts="$last_timestamp" '$1 > last_ts { print }')

    # Check if any new messages were found
    if [ -n "$new_usb_messages" ]; then
        echo "$new_usb_messages"

        # Update the last timestamp
        last_timestamp=$(echo "$new_usb_messages" | tail -n 1 | awk '{print $1}')
    fi

    # Sleep for a short duration before checking again (adjust as needed)
    sleep 1
done

