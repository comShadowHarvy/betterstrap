#!/bin/bash

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RESET='\033[0m'

# Function to list drives
list_drives() {
    echo -e "${BLUE}Listing all drives and identifying potential USB thumb drives:${RESET}"
    echo

    # List USB drives first
    echo -e "${GREEN}USB Drives:${RESET}"
    lsblk -d -o NAME,SIZE,MODEL,TRAN | awk '
        BEGIN { printf "%-10s %-10s %-20s %-10s\n", "NAME", "SIZE", "MODEL", "TRAN"; print "---------------------------------------------------" }
        $4 ~ /usb/ { printf "%-10s %-10s %-20s %-10s\n", $1, $2, $3, $4 }
    '

    # Store USB drives for numeric selection
    mapfile -t USB_DRIVES < <(lsblk -d -o NAME,SIZE,MODEL,TRAN | grep usb | awk '{print $1, $2, $3, $4}')

    # List all drives, highlighting USB ones
    echo -e "\n${CYAN}All Drives:${RESET}"
    lsblk -d -o NAME,SIZE,MODEL,TRAN | awk '
        BEGIN { printf "%-10s %-10s %-20s %-10s\n", "NAME", "SIZE", "MODEL", "TRAN"; print "---------------------------------------------------" }
        $1 != "NAME" { printf "%-10s %-10s %-20s %-10s\n", $1, $2, $3, $4 }
    '

    # Store all drives for numeric selection
    mapfile -t ALL_DRIVES < <(lsblk -d -o NAME,SIZE,MODEL,TRAN | grep -v NAME | awk '{print $1, $2, $3, $4}')

    echo -e "\n${GREEN}Available drives:${RESET}"
    for i in "${!ALL_DRIVES[@]}"; do
        DRIVE_INFO="${ALL_DRIVES[$i]}"
        if [[ " ${USB_DRIVES[*]} " == *"${ALL_DRIVES[$i]}"* ]]; then
            echo -e "${CYAN}$((i + 1))) $DRIVE_INFO (USB)${RESET}"
        else
            echo -e "${CYAN}$((i + 1))) $DRIVE_INFO${RESET}"
        fi
    done

    # Prompt user to select a drive
    read -p "Select a drive by number: " DRIVE_NUM
    if [[ ! $DRIVE_NUM =~ ^[0-9]+$ ]] || ((DRIVE_NUM < 1 || DRIVE_NUM > ${#ALL_DRIVES[@]})); then
        echo -e "${RED}Invalid selection. Exiting.${RESET}"
        exit 1
    fi

    DRIVE_NAME=$(echo "${ALL_DRIVES[$((DRIVE_NUM - 1))]}" | awk '{print $1}')
    echo -e "${GREEN}Selected drive: /dev/${DRIVE_NAME}${RESET}"
}

# Function to find mount point
find_mount_point() {
    MOUNT_POINT=$(lsblk -o NAME,MOUNTPOINT | grep "^$DRIVE_NAME " | awk '{print $2}')
    if [[ -z "$MOUNT_POINT" ]]; then
        echo -e "${YELLOW}Drive is not mounted. Attempting to mount...${RESET}"
        udisksctl mount -b "/dev/$DRIVE_NAME" >/dev/null 2>&1
        MOUNT_POINT=$(lsblk -o NAME,MOUNTPOINT | grep "^$DRIVE_NAME " | awk '{print $2}')
    fi

    if [[ -z "$MOUNT_POINT" ]]; then
        echo -e "${RED}Failed to find or mount the drive. Exiting.${RESET}"
        exit 1
    fi

    echo -e "${GREEN}Drive mount point: $MOUNT_POINT${RESET}"
}

# Function to confirm action
confirm_action() {
    read -p "Are you sure you want to continue with /dev/$DRIVE_NAME? (y/n): " CONFIRM
    if [[ "$CONFIRM" != "y" ]]; then
        echo -e "${RED}Operation canceled.${RESET}"
        exit 1
    fi
}

# Function to probe the drive
probe_drive() {
    echo -e "${BLUE}Running f3probe on /dev/$DRIVE_NAME...${RESET}"
    PROBE_OUTPUT=$(sudo f3probe --time-ops "/dev/$DRIVE_NAME" 2>&1)
    echo "$PROBE_OUTPUT"

    if echo "$PROBE_OUTPUT" | grep -q "is a counterfeit"; then
        LAST_SEC=$(echo "$PROBE_OUTPUT" | grep -oP 'f3fix --last-sec=\K[0-9]+')
        echo -e "${YELLOW}Drive might be counterfeit!${RESET}"
        read -p "Would you like to attempt to fix the drive with f3fix? (y/n): " FIX_DRIVE
        if [[ "$FIX_DRIVE" == "y" ]]; then
            if [ -n "$LAST_SEC" ]; then
                echo -e "${BLUE}Running f3fix on /dev/$DRIVE_NAME with --last-sec=$LAST_SEC...${RESET}"
                sudo f3fix --last-sec="$LAST_SEC" "/dev/$DRIVE_NAME"
                echo -e "${GREEN}Drive has been fixed. Please reformat it before use.${RESET}"
            else
                echo -e "${RED}Unable to determine the required --last-sec value. Please check manually.${RESET}"
            fi
        else
            echo -e "${YELLOW}Skipping fix operation.${RESET}"
        fi
    else
        echo -e "${GREEN}Drive appears to be genuine.${RESET}"
    fi
}

# Function to conduct write-read test
write_read_test() {
    read -p "Would you like to perform a write-read test on /dev/$DRIVE_NAME? (y/n): " TEST_CHOICE
    if [[ "$TEST_CHOICE" == "y" ]]; then
        find_mount_point

        echo -e "${BLUE}Running f3write on $MOUNT_POINT...${RESET}"
        sudo f3write "$MOUNT_POINT"

        echo -e "${BLUE}Running f3read on $MOUNT_POINT...${RESET}"
        sudo f3read "$MOUNT_POINT"

        echo -e "${GREEN}Write-read test completed.${RESET}"
    else
        echo -e "${YELLOW}Skipping write-read test.${RESET}"
    fi
}

# Main script execution
echo -e "${CYAN}Welcome to the F3 Helper Script!${RESET}"
list_drives
confirm_action

# Automatically probe the drive
probe_drive

# Conduct write-read test if required
write_read_test

echo -e "${GREEN}Drive tests completed. Exiting.${RESET}"
