#!/bin/bash

# Enhanced Ultimate Pentest Installer
# A comprehensive, cross-distro installer for penetration testing tools.
# Version 2.0
#
# Disclaimer: These tools are for professional and educational purposes only.
#             Unauthorized use against systems you do not own is illegal.

set -eo pipefail

# --- Style and Color Configuration ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --- Global Variables ---
PKG_MANAGER=""
PKG_INSTALL=""
PKG_UPDATE=""
AUR_HELPER=""

# --- Helper Functions ---

# Function to check for sudo privileges
check_sudo() {
    if [[ "$EUID" -eq 0 ]]; then
        echo -e "${RED}Error: This script should not be run as root. Run as a regular user.${NC}"
        exit 1
    fi
    if ! command -v sudo &>/dev/null || ! sudo -v; then
        echo -e "${RED}Error: sudo is required and the current user must have sudo privileges.${NC}"
        exit 1
    fi
}

# Function to detect the system's package manager
detect_package_manager() {
    echo -e "${BLUE}Detecting package manager...${NC}"
    if command -v apt &>/dev/null; then
        PKG_MANAGER="apt"; PKG_INSTALL="sudo apt install -y"; PKG_UPDATE="sudo apt update"
        echo -e "${GREEN}Detected apt (Debian/Ubuntu).${NC}"
    elif command -v dnf &>/dev/null; then
        PKG_MANAGER="dnf"; PKG_INSTALL="sudo dnf install -y"; PKG_UPDATE="sudo dnf check-update || true"
        echo -e "${GREEN}Detected dnf (Fedora/RHEL).${NC}"
    elif command -v pacman &>/dev/null; then
        PKG_MANAGER="pacman"; PKG_INSTALL="sudo pacman -S --needed --noconfirm"; PKG_UPDATE="sudo pacman -Sy"
        echo -e "${GREEN}Detected pacman (Arch Linux).${NC}"
    else
        echo -e "${RED}Error: No supported package manager found (apt, dnf, pacman).${NC}"
        exit 1
    fi
}

# Function to check if a command is installed
is_installed() {
    command -v "$1" &>/dev/null
}

# Ensure an AUR helper (yay/paru) is installed on Arch Linux
ensure_aur_helper() {
    if [[ "$PKG_MANAGER" != "pacman" ]]; then return; fi
    if is_installed yay; then AUR_HELPER="yay"; return; fi
    if is_installed paru; then AUR_HELPER="paru"; return; fi

    echo -e "${YELLOW}No AUR helper found. Attempting to install 'yay'...${NC}"
    is_installed git || sudo pacman -S --noconfirm git base-devel
    local temp_dir
    temp_dir=$(mktemp -d)
    (
        cd "$temp_dir" || exit 1
        git clone https://aur.archlinux.org/yay.git
        cd yay || exit 1
        makepkg -si --noconfirm
    )
    rm -rf "$temp_dir"
    if is_installed yay; then
        echo -e "${GREEN}yay installed successfully.${NC}"
        AUR_HELPER="yay"
    else
        echo -e "${RED}Failed to install yay. AUR packages cannot be installed.${NC}"
        sleep 2
    fi
}

# --- Installation Logic ---

# Installs a package using the system's package manager
install_from_pkg_manager() {
    local name="$1"
    local pkgs_to_install="$2"
    echo -e "${BLUE}Installing $name via $PKG_MANAGER...${NC}"
    if $PKG_INSTALL $pkgs_to_install; then
        echo -e "\n${GREEN}$name installed successfully.${NC}"
    else
        echo -e "\n${RED}Failed to install $name via $PKG_MANAGER.${NC}"
        return 1
    fi
}

# Installs a package from the Arch User Repository
install_from_aur() {
    if [[ -z "$AUR_HELPER" ]]; then
        echo -e "${YELLOW}Cannot install '$1': No AUR helper is available.${NC}"; sleep 2; return 1;
    fi
    echo -e "${BLUE}Installing $1 via AUR helper ($AUR_HELPER)...${NC}"
    if $AUR_HELPER -S --noconfirm "$2"; then
        echo -e "\n${GREEN}$1 installed successfully.${NC}"
    else
        echo -e "\n${RED}Failed to install $1 from AUR.${NC}"; return 1;
    fi
}

# Installs a Python tool from a Git repository
install_from_git_pip() {
    local name="$1"
    local url="$2"
    is_installed pip || install_from_pkg_manager "python3-pip" "python3-pip"
    
    echo -e "${BLUE}Installing $name from Git (pip)...${NC}"
    if sudo pip install "git+$url"; then
         echo -e "\n${GREEN}$name installed successfully.${NC}"
    else
         echo -e "\n${RED}Failed to install $name from Git.${NC}"; return 1;
    fi
}

# Primary tool installer function, acts as a dispatcher
install_tool() {
    IFS=':' read -r name description advantages disadvantages category method source <<< "$1"

    clear; display_header
    display_description "Installing $name" "$description" "$advantages" "$disadvantages"

    if is_installed "$name"; then
        echo -e "${GREEN}$name is already installed.${NC}"; sleep 2; return 0;
    fi

    # Ensure build dependencies are present if needed
    if [[ "$method" == "git_"* ]]; then
        is_installed git || install_from_pkg_manager "git" "git"
    fi

    local success=0
    case "$method" in
        pkg) install_from_pkg_manager "$name" "$source" || success=1 ;;
        aur) install_from_aur "$name" "$source" || success=1 ;;
        git_pip) install_from_git_pip "$name" "$source" || success=1 ;;
        *) echo -e "${RED}Unknown installation method '$method' for $name.${NC}"; success=1 ;;
    esac

    sleep 2
    return $success
}

# --- UI and Menu Functions ---

display_header() {
    clear
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo -e "${BOLD}${CYAN}         Ultimate Pentest Installer (v2.0)           ${NC}"
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo
    echo -e "${BOLD}System Info:${NC} $(grep PRETTY_NAME /etc/os-release | cut -d'"' -f 2 2>/dev/null || uname -a)"
    echo -e "${BOLD}Package Manager:${NC} $PKG_MANAGER"
    echo
}

display_description() {
    echo -e "${BOLD}${CYAN}--- $1 ---${NC}\n"
    echo -e "${BOLD}Description:${NC}\n$2\n"
    echo -e "${BOLD}${GREEN}Advantages:${NC}\n$3\n"
    echo -e "${BOLD}${RED}Disadvantages:${NC}\n$4\n"
    echo -e "${BLUE}--------------------------------------------------${NC}\n"
}

# --- Tool Definitions ---
declare -A TOOL_CATEGORIES
TOOL_CATEGORIES=(
    ["network"]="Network Scanning & Enumeration"
    ["vuln_scan"]="Vulnerability Scanning"
    ["exploit"]="Exploitation Frameworks"
    ["web"]="Web Application Testing"
    ["password"]="Password & Credential Testing"
    ["osint"]="OSINT & Reconnaissance"
)
ORDERED_CATEGORIES=("network" "vuln_scan" "exploit" "web" "password" "osint")

# Format: name:description:advantages:disadvantages:category:method:source
TOOLS=(
    "nmap:Network discovery and security auditing.:- Comprehensive scanning.\n- Scripting engine (NSE).:- Can be complex for beginners.:network:pkg:nmap"
    "masscan:Extremely fast TCP port scanner.:- Incredible speed for large networks.:- Less feature-rich than nmap.:network:pkg:masscan"
    "nikto:Web server scanner for vulnerabilities.:- Scans for thousands of potential issues.:- Can be noisy and produce false positives.:vuln_scan:pkg:nikto"
    "metasploit-framework:The world's most used penetration testing framework.:- Massive exploit database.\n- Highly extensible.:- Heavy and can be slow to start.:exploit:pkg:metasploit-framework"
    "sqlmap:Automatic SQL injection and database takeover tool.:- Automates complex SQLi attacks.\n- Wide database support.:- Requires careful handling to avoid damage.:web:pkg:sqlmap"
    "ffuf:Fast web fuzzer written in Go.:- Extremely fast for directory/file discovery.:- Command-line only, results need parsing.:web:pkg:ffuf"
    "john:John the Ripper, a powerful password cracker.:- Supports hundreds of hash types.\n- Highly optimized.:- Can be complex to configure.:password:pkg:john"
    "hashcat:The world's fastest password cracker.:- GPU acceleration for incredible speed.:- Requires a compatible GPU and drivers.:password:pkg:hashcat"
    "hydra:A very fast network logon cracker.:- Supports numerous protocols (SSH, FTP, etc).:- Can be noisy and easily detected.:password:pkg:hydra"
    "cloud_enum:Multi-cloud asset discovery tool.:- Enumerates assets in AWS, Azure, GCP.:- Requires cloud environment knowledge.:osint:git_pip:https://github.com/initstring/cloud_enum.git"
    "subfinder:Subdomain discovery tool.:- Uses passive sources for speed and stealth.:- Quality of results depends on sources.:osint:pkg:subfinder"
    "amass:In-depth attack surface mapping and asset discovery.:- Extremely thorough.\n- Gathers massive amounts of data.:- Can be slow and complex to run.:osint:pkg:amass"
)

# --- Main Logic ---

install_from_category() {
    local category_key="$1"
    local category_name="${TOOL_CATEGORIES[$category_key]}"
    local category_tools=()
    for tool_data in "${TOOLS[@]}"; do
        if [[ "$tool_data" == *":$category_key:"* ]]; then
            category_tools+=("$tool_data")
        fi
    done
    display_header
    echo -e "${BLUE}Installing all ${#category_tools[@]} tools in category: ${BOLD}$category_name${NC}"; sleep 2
    for tool_data in "${category_tools[@]}"; do install_tool "$tool_data"; done
    echo -e "\n${GREEN}Finished installing tools for category: $category_name${NC}"
    echo -e "Press any key to return to the menu..."; read -n 1 -s
}

install_all() {
    display_header
    echo -e "${BLUE}Installing all ${#TOOLS[@]} development tools...${NC}"
    read -p "This will install all tools. Are you sure? (y/N): " -r choice
    if [[ ! "$choice" =~ ^[Yy]$ ]]; then return; fi
    for tool_data in "${TOOLS[@]}"; do install_tool "$tool_data"; done
    echo -e "\n${GREEN}All tools installed.${NC}"
    echo -e "Press any key to return to the menu..."; read -n 1 -s
}

main_menu() {
    while true; do
        display_header
        echo -e "${BOLD}${CYAN}Select a category to install:${NC}\n"
        for i in "${!ORDERED_CATEGORIES[@]}"; do
            local key="${ORDERED_CATEGORIES[$i]}"
            local name="${TOOL_CATEGORIES[$key]}"
            echo -e "  ${MAGENTA}$((i + 1)))${NC} ${BOLD}$name${NC}"
        done
        echo -e "\n  ${MAGENTA}a)${NC} ${BOLD}Install All Tools${NC}"
        echo -e "  ${MAGENTA}q)${NC} ${BOLD}Quit${NC}\n"
        read -p "Enter your choice: " -r choice
        case "$choice" in
            [1-9]*)
                if (( choice > 0 && choice <= ${#ORDERED_CATEGORIES[@]} )); then
                    install_from_category "${ORDERED_CATEGORIES[$((choice-1))]}"
                else
                    echo -e "${RED}Invalid choice. Press any key.${NC}"; read -n 1 -s
                fi
                ;;
            a|A) install_all ;;
            q|Q) echo -e "${GREEN}Exiting installer.${NC}"; exit 0 ;;
            *) echo -e "${RED}Invalid choice. Press any key.${NC}"; read -n 1 -s ;;
        esac
    done
}

# --- Script Entry Point ---
main() {
    check_sudo
    detect_package_manager
    ensure_aur_helper # Will only run on Arch Linux
    main_menu
}

main

