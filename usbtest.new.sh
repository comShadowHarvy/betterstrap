#!/bin/bash

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RESET='\033[0m'

# Function to check if F3 tools are installed
check_f3_installed() {
    echo -e "${BLUE}Checking if F3 tools are installed...${RESET}"
    
    if command -v f3probe >/dev/null 2>&1 && command -v f3write >/dev/null 2>&1 && command -v f3read >/dev/null 2>&1; then
        echo -e "${GREEN}F3 tools are already installed.${RESET}"
        return 0
    else
        echo -e "${YELLOW}F3 tools are not installed or not in PATH.${RESET}"
        return 1
    fi
}

# Function to download and install F3
install_f3() {
    echo -e "${BLUE}Installing F3 tools...${RESET}"
    
    # Create temporary directory
    TMP_DIR=$(mktemp -d)
    cd "$TMP_DIR" || { echo -e "${RED}Failed to create temporary directory.${RESET}"; exit 1; }
    
    # Check for required tools
    for cmd in wget unzip make gcc; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            echo -e "${RED}Required tool '$cmd' is not installed. Please install it first.${RESET}"
            exit 1
        fi
    done
    
    # Get latest release URL
    echo -e "${CYAN}Fetching latest F3 release from GitHub...${RESET}"
    LATEST_RELEASE_URL=$(wget -qO- https://github.com/AltraMayor/f3/tags | grep -oP 'href="/AltraMayor/f3/archive/refs/tags/v[0-9]+\.[0-9]+\.zip"' | head -1 | cut -d '"' -f 2)
    
    if [[ -z "$LATEST_RELEASE_URL" ]]; then
        echo -e "${RED}Failed to find latest release. Attempting to download v8.0 directly...${RESET}"
        DOWNLOAD_URL="https://github.com/AltraMayor/f3/archive/refs/tags/v8.0.zip"
        VERSION="8.0"
    else
        DOWNLOAD_URL="https://github.com$LATEST_RELEASE_URL"
        VERSION=$(echo "$LATEST_RELEASE_URL" | grep -oP 'v\K[0-9]+\.[0-9]+')
    fi
    
    echo -e "${CYAN}Downloading F3 version $VERSION...${RESET}"
    wget "$DOWNLOAD_URL" -O f3.zip || { echo -e "${RED}Download failed.${RESET}"; exit 1; }
    
    echo -e "${CYAN}Extracting F3...${RESET}"
    unzip f3.zip || { echo -e "${RED}Extraction failed.${RESET}"; exit 1; }
    
    # Enter the directory (name might vary based on version)
    F3_DIR=$(find . -maxdepth 1 -type d -name "f3-*" | head -1)
    cd "$F3_DIR" || { echo -e "${RED}Failed to enter F3 directory.${RESET}"; exit 1; }
    
    echo -e "${CYAN}Compiling F3...${RESET}"
    make || { echo -e "${RED}Compilation failed.${RESET}"; exit 1; }
    
    echo -e "${CYAN}Installing F3...${RESET}"
    sudo make install || { echo -e "${RED}Installation failed. Trying without sudo...${RESET}"; make install || { echo -e "${RED}Installation failed.${RESET}"; exit 1; }; }
    
    echo -e "${GREEN}F3 version $VERSION has been successfully installed.${RESET}"
    
    # Clean up
    cd "$OLDPWD" || exit
    rm -rf "$TMP_DIR"
}

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

# Check if F3 is installed, install if not
if ! check_f3_installed; then
    read -p "Would you like to install F3 now? (y/n): " INSTALL_CHOICE
    if [[ "$INSTALL_CHOICE" == "y" ]]; then
        install_f3
        # Verify installation was successful
        if ! check_f3_installed; then
            echo -e "${RED}F3 installation appears to have failed. Please install manually.${RESET}"
            exit 1
        fi
    else
        echo -e "${RED}F3 tools are required for this script. Exiting.${RESET}"
        exit 1
    fi
fi

# Continue with drive testing
list_drives
confirm_action

# Automatically probe the drive
probe_drive

# Conduct write-read test if required
write_read_test

echo -e "${GREEN}Drive tests completed. Exiting.${RESET}"