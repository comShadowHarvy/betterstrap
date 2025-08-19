#!/bin/bash

# Enhanced Recommended Software Installer
# A comprehensive, cross-distro installer for common desktop applications.
# Version 2.0 
#
# This script provides an interactive menu to install software categorized
# by function, supporting various package managers and formats.

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
DISTRO=""
LOG_FILE="recommended_software_install_$(date +%Y-%m-%d_%H-%M-%S).txt"

# --- Helper Functions ---

# Function to log messages to a file and console
log_message() {
    local level="$1"; shift
    local message="$*"
    local timestamp
    timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    # Write clean message to log file
    echo "$timestamp [$level] $message" >> "$LOG_FILE"
    # Write colorized message to console
    case "$level" in
        INFO) echo -e "${GREEN}[INFO]${NC} $message" ;;
        WARN) echo -e "${YELLOW}[WARN]${NC} $message" ;;
        ERROR) echo -e "${RED}[ERROR]${NC} $message" ;;
    esac
}

# Function to check for sudo privileges
check_sudo() {
    if [[ "$EUID" -eq 0 ]]; then
        log_message "ERROR" "This script should not be run as root. Run as a regular user."
        exit 1
    fi
    if ! command -v sudo &>/dev/null || ! sudo -v; then
        log_message "ERROR" "sudo is required and the current user must have sudo privileges."
        exit 1
    fi
}

# Function to detect the system's package manager and distribution
detect_system() {
    log_message "INFO" "Detecting system..."
    if [ -f /etc/os-release ]; then
        # shellcheck source=/dev/null
        . /etc/os-release
        DISTRO=$ID
    else
        log_message "ERROR" "Cannot detect Linux distribution."
        exit 1
    fi

    if command -v apt &>/dev/null; then
        PKG_MANAGER="apt"; PKG_INSTALL="sudo apt install -y"; PKG_UPDATE="sudo apt update"
    elif command -v dnf &>/dev/null; then
        PKG_MANAGER="dnf"; PKG_INSTALL="sudo dnf install -y"; PKG_UPDATE="sudo dnf check-update || true"
    elif command -v pacman &>/dev/null; then
        PKG_MANAGER="pacman"; PKG_INSTALL="sudo pacman -S --needed --noconfirm"; PKG_UPDATE="sudo pacman -Sy"
    else
        log_message "ERROR" "No supported package manager found (apt, dnf, pacman)."
        exit 1
    fi
    log_message "INFO" "Detected Distro: $DISTRO, Package Manager: $PKG_MANAGER"
}

# Function to check if a command or package is installed
is_installed() {
    local name="$1"
    local method="$2"

    case "$method" in
        flatpak) flatpak list --app | grep -q "$name" ;;
        snap) snap list | grep -q "$name" ;;
        *) command -v "$name" &>/dev/null || $PKG_INSTALL -s "$name" &>/dev/null ;; # Fallback for package check
    esac
}

# Ensures an AUR helper is available on Arch Linux
ensure_aur_helper() {
    if [[ "$PKG_MANAGER" != "pacman" ]]; then return; fi
    if is_installed yay "yay"; then AUR_HELPER="yay"; return; fi
    if is_installed paru "paru"; then AUR_HELPER="paru"; return; fi
    log_message "WARN" "No AUR helper found. Attempting to install 'yay'."
    sudo pacman -S --noconfirm --needed git base-devel
    local temp_dir; temp_dir=$(mktemp -d)
    ( cd "$temp_dir" && git clone https://aur.archlinux.org/yay.git && cd yay && makepkg -si --noconfirm )
    rm -rf "$temp_dir"
    if is_installed yay "yay"; then AUR_HELPER="yay"; else log_message "ERROR" "Failed to install AUR helper."; fi
}

# --- Installation Logic ---

install_with_pkg_manager() {
    log_message "INFO" "Installing '$1' with $PKG_MANAGER"
    if $PKG_INSTALL "$2"; then log_message "INFO" "'$1' installed successfully."; else log_message "ERROR" "Failed to install '$1'."; return 1; fi
}

install_with_flatpak() {
    is_installed flatpak "flatpak" || install_with_pkg_manager "flatpak" "flatpak"
    sudo flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
    log_message "INFO" "Installing '$1' with Flatpak."
    if sudo flatpak install -y flathub "$2"; then log_message "INFO" "'$1' installed successfully."; else log_message "ERROR" "Failed to install '$1'."; return 1; fi
}

install_with_snap() {
    is_installed snap "snap" || install_with_pkg_manager "snapd" "snapd"
    # For non-Debian systems that need the service enabled
    if ! dpkg -l &>/dev/null; then sudo systemctl enable --now snapd.socket; fi
    log_message "INFO" "Installing '$1' with Snap."
    if sudo snap install "$2"; then log_message "INFO" "'$1' installed successfully."; else log_message "ERROR" "Failed to install '$1'."; return 1; fi
}

# Primary installer function dispatcher
install_tool() {
    IFS=':' read -r name description advantages disadvantages category method source <<< "$1"

    clear; display_header
    display_description "$name" "$description" "$advantages" "$disadvantages" "$method"

    if is_installed "$name" "$method"; then
        log_message "INFO" "$name is already installed."
        sleep 2; return 0;
    fi

    local success=0
    case "$method" in
        pkg) install_with_pkg_manager "$name" "$source" || success=1 ;;
        flatpak) install_with_flatpak "$name" "$source" || success=1 ;;
        snap) install_with_snap "$name" "$source" || success=1 ;;
        *) log_message "ERROR" "Unknown installation method '$method' for $name."; success=1 ;;
    esac

    sleep 2
    return $success
}


# --- UI and Menu Functions ---

display_header() {
    clear
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo -e "${BOLD}${CYAN}      Recommended Software Installer (v2.0)          ${NC}"
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
    echo -e "${BOLD}Source:${NC} $5\n"
    echo -e "${BLUE}--------------------------------------------------${NC}\n"
}

# --- Tool Definitions ---

declare -A TOOL_CATEGORIES
TOOL_CATEGORIES=(
    ["office"]="Office & Productivity"
    ["internet"]="Internet & Communication"
    ["multimedia"]="Multimedia"
    ["graphics"]="Graphics & Design"
    ["utilities"]="System Utilities"
    ["development"]="Development Tools"
    ["security"]="Security & Privacy"
    ["games"]="Gaming"
)
ORDERED_CATEGORIES=("office" "internet" "multimedia" "graphics" "utilities" "development" "security" "games")

# Format: name:description:advantages:disadvantages:category:method:source_package_name
TOOLS=(
    "libreoffice:Free office suite compatible with MS Office.:- Comprehensive and free.\n- Works offline.:- UI can feel dated.:office:pkg:libreoffice-fresh|libreoffice"
    "onlyoffice:Modern office suite with great MS Office compatibility.:- Excellent compatibility.\n- Clean interface.:- Some features are proprietary.:flatpak:org.onlyoffice.desktopeditors"
    "firefox:Fast, private, and open-source web browser.:- Strong privacy features.\n- Highly extensible.:- Can use more memory than rivals.:internet:pkg:firefox"
    "thunderbird:Powerful, free email client from Mozilla.:- Manages multiple accounts.\n- Extensible.:- Interface can feel complex.:internet:pkg:thunderbird"
    "discord:Chat, voice, and video for communities and friends.:- Excellent for gaming.\n- High quality voice chat.:- Proprietary, resource intensive.:flatpak:com.discordapp.Discord"
    "vlc:Plays almost any video or audio file imaginable.:- Unmatched format support.\n- Free and open-source.:- Default UI is very basic.:multimedia:pkg:vlc"
    "spotify:Stream millions of songs and podcasts.:- Huge music library.\n- Great discovery features.:- Free version has ads.:snap:spotify"
    "obs-studio:Free software for video recording and live streaming.:- Professional features for free.\n- Highly configurable.:- Can have a steep learning curve.:multimedia:pkg:obs-studio"
    "gimp:Powerful free and open-source image editor.:- Photoshop-level features for free.:- UI can be intimidating for new users.:graphics:pkg:gimp"
    "krita:Professional digital painting software.:- Excellent for artists and illustrators.:- Less focused on photo manipulation.:graphics:pkg:krita"
    "inkscape:Professional vector graphics editor.:- The best FOSS alternative to Illustrator.:- Can be slow with complex files.:graphics:pkg:inkscape"
    "timeshift:System restore utility, like Windows System Restore.:- Can save a system from breaking changes.:- Requires significant disk space.:utilities:pkg:timeshift"
    "bleachbit:System cleaner and privacy guard.:- Frees up disk space.\n- Wipes free space.:- Can be dangerous if used improperly.:utilities:pkg:bleachbit"
    "htop:An interactive process viewer.:- Easy to read and use.\n- Color-coded display.:- Terminal-based only.:utilities:pkg:htop"
    "vscode:A powerful, popular, and extensible code editor.:- Massive extension ecosystem.\n- Great performance.:- Microsoft telemetry (can be disabled).:development:pkg:code"
    "docker:Platform for developing and running apps in containers.:- Consistent environments.\n- Simplifies deployment.:- Requires learning container concepts.:development:pkg:docker"
    "keepassxc:Secure, offline, and open-source password manager.:- You control your data.\n- No subscription fees.:- Syncing is a manual process.:security:pkg:keepassxc"
    "steam:The largest digital distribution platform for PC gaming.:- Huge library of games.\n- Great sales.:- Client can be resource-heavy.:games:pkg:steam-installer|steam"
    "lutris:An open gaming platform for Linux.:- Manages games from all sources.\n- Community install scripts.:- Can require manual tweaking.:games:pkg:lutris"
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
    log_message "INFO" "Installing all tools in category: $category_name"
    for tool_data in "${category_tools[@]}"; do install_tool "$tool_data"; done
    log_message "INFO" "Finished installing tools for category: $category_name"
    echo -e "\nPress any key to return to the menu..."; read -n 1 -s
}

install_all() {
    display_header
    log_message "WARN" "User initiated install of all recommended software."
    read -p "This will install all ${#TOOLS[@]} tools. Are you sure? (y/N): " -r choice
    if [[ ! "$choice" =~ ^[Yy]$ ]]; then log_message "INFO" "Installation cancelled."; return; fi
    for tool_data in "${TOOLS[@]}"; do install_tool "$tool_data"; done
    log_message "INFO" "Finished installing all recommended software."
    echo -e "\nPress any key to return to the menu..."; read -n 1 -s
}

main_menu() {
    while true; do
        display_header
        echo -e "${BOLD}${CYAN}Select a category to install:${NC}\n"
        for i in "${!ORDERED_CATEGORIES[@]}"; do
            local key="${ORDERED_CATEGORIES[$i]}"; local name="${TOOL_CATEGORIES[$key]}"
            echo -e "  ${MAGENTA}$((i + 1)))${NC} ${BOLD}$name${NC}"
        done
        echo -e "\n  ${MAGENTA}a)${NC} ${BOLD}Install All Recommended Tools${NC}"
        echo -e "  ${MAGENTA}q)${NC} ${BOLD}Quit${NC}\n"
        read -p "Enter your choice: " -r choice
        case "$choice" in
            [1-9]*)
                if (( choice > 0 && choice <= ${#ORDERED_CATEGORIES[@]} )); then
                    install_from_category "${ORDERED_CATEGORIES[$((choice-1))]}"
                else
                    log_message "WARN" "Invalid menu choice: $choice"; read -n 1 -s
                fi
                ;;
            a|A) install_all ;;
            q|Q) log_message "INFO" "Exiting."; exit 0 ;;
            *) log_message "WARN" "Invalid menu choice: $choice"; read -n 1 -s ;;
        esac
    done
}

# --- Script Entry Point ---
main() {
    init_log
    check_sudo
    detect_system
    ensure_aur_helper
    main_menu
}

# Initialize log file and run main function
init_log() {
    echo "=== Recommended Software Installer Log - $(date) ===" > "$LOG_FILE"
    log_message "INFO" "Script started. Log file: $LOG_FILE"
}

main
