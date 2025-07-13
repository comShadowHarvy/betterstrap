##!/bin/bash

# A script to install the 'asusctl' utility on Arch Linux.
# This will install 'yay' if not found, then use it to install 'asusctl'.

# --- Color Codes for Output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Step 1: Check for and install yay ---
echo -e "${GREEN}### Step 1: Checking for AUR Helper (yay) ###${NC}"
if ! command -v yay &>/dev/null; then
  echo -e "${YELLOW}yay not found. Installing it now...${NC}"
  # Install dependencies and build yay
  sudo pacman -S --needed --noconfirm git base-devel
  if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to install dependencies for yay. Aborting.${NC}"
    exit 1
  fi

  # Clone and build from a temporary directory
  git clone https://aur.archlinux.org/yay.git /tmp/yay
  (cd /tmp/yay && makepkg -si --noconfirm)
  if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to build and install yay. Aborting.${NC}"
    exit 1
  fi
  echo -e "${GREEN}yay has been successfully installed.${NC}"
else
  echo -e "${GREEN}yay is already installed. Proceeding...${NC}"
fi

echo "" # Newline for readability

# --- Step 2: Install asusctl ---
echo -e "${GREEN}### Step 2: Installing asusctl ###${NC}"
yay -S --noconfirm asusctl
if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Failed to install asusctl. Aborting.${NC}"
  exit 1
fi
echo -e "${GREEN}asusctl has been successfully installed.${NC}"

echo ""

# --- Step 3: Verify Installation ---
echo -e "${GREEN}### Step 3: Verifying asusctl installation ###${NC}"
echo -e "Attempting to list fan profiles to confirm setup..."

# Attempt to list profiles. If it works, the on-demand service is working.
if asusctl profile -L &>/dev/null; then
  echo -e "${GREEN}Success! asusctl is working correctly.${NC}"
  echo "Here are your available profiles:"
  echo -e "${YELLOW}---------------------------------${NC}"
  asusctl profile -L
  echo -e "${YELLOW}---------------------------------${NC}"
  echo -e "\nSetup is complete! You can now use 'sudo asusctl profile -P <ProfileName>' to change modes."
else
  echo -e "${RED}Verification failed. asusctl could not retrieve profiles.${NC}"
  echo -e "${YELLOW}This can sometimes happen right after installation. A system reboot is recommended.${NC}"
  echo -e "After rebooting, try running 'asusctl profile -L' manually."
  exit 1
fi

exit 0!/bin/sh
