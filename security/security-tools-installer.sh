#!/bin/bash
# Security Tools Installer
# Author: ShadowHarvy
# Description: A script to install security and penetration testing tools
# for Parrot OS and Kali Linux using the install.sh utility script.

# ANSI color codes
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Clear the screen
clear

# Display title screen
echo -e "${GREEN}"
echo "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
echo "┃                                                        ┃"
echo "┃             SECURITY TOOLS INSTALLER                   ┃"
echo "┃                                                        ┃"
echo "┃         For Parrot OS and Kali Linux                  ┃"
echo "┃                                                        ┃"
echo "┃               By: ShadowHarvy                         ┃"
echo "┃                                                        ┃"
echo "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
echo -e "${NC}"

# Check if install.sh exists
if [ ! -f "./install.sh" ]; then
    echo -e "${RED}Error: install.sh script not found in the current directory.${NC}"
    echo "Please ensure the install.sh script is in the same directory as this script."
    exit 1
fi

# Check if install.sh is executable
if [ ! -x "./install.sh" ]; then
    echo -e "${YELLOW}Making install.sh executable...${NC}"
    chmod +x ./install.sh
fi

# Function to install a package
install_package() {
    echo -e "${CYAN}Installing $1...${NC}"
    ./install.sh "$1"
    echo -e "${GREEN}Finished installing $1${NC}"
    echo ""
}

# Display disclaimer
echo -e "${YELLOW}DISCLAIMER: These tools should only be used for legitimate security testing"
echo -e "with proper authorization. Unauthorized use against systems you don't own"
echo -e "or have permission to test is illegal and unethical.${NC}"
echo ""
echo -e "Press Enter to continue or Ctrl+C to exit..."
read

# Tool categories
declare -A categories
categories=(
    ["1"]="Reconnaissance Tools"
    ["2"]="Vulnerability Scanners"
    ["3"]="Exploitation Tools"
    ["4"]="Wireless Testing"
    ["5"]="Web Application Testing"
    ["6"]="Password Tools"
    ["7"]="Forensics Tools"
    ["8"]="Reporting Tools"
    ["9"]="All Tools"
)

# Tools by category
declare -A tools
tools=(
    ["1"]="nmap masscan dnsenum whois dnsrecon theHarvester recon-ng spiderfoot"
    ["2"]="nikto openvas nessus lynis wpscan sqlmap"
    ["3"]="metasploit-framework exploitdb sqlmap hydra netcat"
    ["4"]="aircrack-ng kismet wifite reaver bully"
    ["5"]="burpsuite zaproxy sqlmap owasp-zap dirbuster gobuster"
    ["6"]="john hashcat hydra crunch cewl"
    ["7"]="autopsy volatility foremost testdisk binwalk"
    ["8"]="faraday dradis maltego"
)

# Main menu
while true; do
    clear
    echo -e "${GREEN}=== SECURITY TOOLS INSTALLER ===${NC}"
    echo ""
    echo "Select a category to install:"
    echo ""
    
    for key in "${!categories[@]}"; do
        echo -e "${CYAN}$key.${NC} ${categories[$key]}"
    done
    
    echo -e "${RED}0.${NC} Exit"
    echo ""
    echo -n "Enter your choice [0-9]: "
    read choice
    
    if [ "$choice" == "0" ]; then
        echo -e "${GREEN}Thank you for using the Security Tools Installer!${NC}"
        exit 0
    elif [ "$choice" == "9" ]; then
        echo -e "${YELLOW}Installing all tools. This may take a while...${NC}"
        for i in {1..8}; do
            for tool in ${tools[$i]}; do
                install_package "$tool"
            done
        done
    elif [[ "$choice" =~ ^[1-8]$ ]]; then
        echo -e "${YELLOW}Installing ${categories[$choice]}...${NC}"
        
        # Display tools in this category
        echo -e "${CYAN}Tools to be installed:${NC}"
        for tool in ${tools[$choice]}; do
            echo "  - $tool"
        done
        echo ""
        echo -n "Proceed with installation? (y/n): "
        read confirm
        
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            for tool in ${tools[$choice]}; do
                install_package "$tool"
            done
        fi
    else
        echo -e "${RED}Invalid choice. Please try again.${NC}"
        sleep 2
    fi
    
    # After installation, prompt to continue or exit
    if [[ "$choice" =~ ^[1-9]$ ]]; then
        echo -e "${GREEN}Installation complete!${NC}"
        echo -n "Return to main menu? (y/n): "
        read return_choice
        if [[ ! "$return_choice" =~ ^[Yy]$ ]]; then
            echo -e "${GREEN}Thank you for using the Security Tools Installer!${NC}"
            exit 0
        fi
    fi
done
