#!/bin/bash

# Enhanced Recommended Software Installer
# A comprehensive installer that categorizes software and provides an interactive selection menu

set -eo pipefail

# Colors and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="software_install_$(date +%Y%m%d_%H%M%S).log"

# Logging function
log() {
    local level=$1; shift
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    # Write to log file
    echo "$timestamp [$level] $*" >> "$LOG_FILE"
    
    # Output to console with colors
    case "$level" in
        "INFO") echo -e "${GREEN}[INFO]${NC} $*" ;;
        "WARN") echo -e "${YELLOW}[WARN]${NC} $*" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $*" ;;
    esac
}

# Initialize log file
init_log() {
    echo "=== Software Installation Log - $(date) ===" > "$LOG_FILE"
    echo "System: $(uname -a)" >> "$LOG_FILE"
}

# Enhanced loading bar with Unicode blocks
loading_bar() {
    local current=$1
    local total=$2
    local percent=$((100 * current / total))
    local bar_length=30
    local filled_length=$((bar_length * current / total))
    local empty_length=$((bar_length - filled_length))
    
    printf -v bar "%0.s█" $(seq 1 $filled_length)
    printf -v space "%0.s░" $(seq 1 $empty_length)
    
    echo -ne "${BLUE}Progress: [${GREEN}${bar}${BLUE}${space}] ${YELLOW}${percent}%${NC}\r"
}

# Check for root/sudo privileges
check_sudo() {
    log "INFO" "Checking for sudo privileges..."
    
    if [ "$EUID" -eq 0 ]; then
        log "WARN" "Running as root is not recommended. Consider using a regular user with sudo privileges."
    elif ! command -v sudo &>/dev/null; then
        log "ERROR" "sudo is not installed. Please install sudo and grant your user appropriate privileges."
        exit 1
    elif ! sudo -v &>/dev/null; then
        log "ERROR" "You do not have sudo privileges. Please contact your system administrator."
        exit 1
    else
        log "INFO" "Sudo privileges confirmed."
    fi
}

# Detect package manager and distribution
detect_system() {
    log "INFO" "Detecting system..."
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        DISTRO_NAME=$NAME
        DISTRO_VERSION=$VERSION_ID
        
        case $ID in
            debian|ubuntu|linuxmint|pop|elementary|zorin)
                PKG_MANAGER="apt"
                PKG_CHECK="dpkg -l"
                PKG_INSTALL="sudo apt install -y"
                PKG_UPDATE="sudo apt update"
                INSTALL_FLATPAK="sudo apt install -y flatpak"
                INSTALL_SNAP="sudo apt install -y snapd"
                HAS_AUR=false
                ;;
            fedora)
                PKG_MANAGER="dnf"
                PKG_CHECK="rpm -q"
                PKG_INSTALL="sudo dnf install -y"
                PKG_UPDATE="sudo dnf check-update || true"
                INSTALL_FLATPAK="sudo dnf install -y flatpak"
                INSTALL_SNAP="sudo dnf install -y snapd"
                HAS_AUR=false
                ;;
            centos|rhel)
                PKG_MANAGER="dnf"
                PKG_CHECK="rpm -q"
                PKG_INSTALL="sudo dnf install -y"
                PKG_UPDATE="sudo dnf check-update || true"
                INSTALL_FLATPAK="sudo dnf install -y flatpak"
                INSTALL_SNAP="sudo dnf install -y epel-release && sudo dnf install -y snapd"
                HAS_AUR=false
                ;;
            arch|manjaro|endeavouros)
                PKG_MANAGER="pacman"
                PKG_CHECK="pacman -Qs"
                PKG_INSTALL="sudo pacman -S --needed --noconfirm"
                PKG_UPDATE="sudo pacman -Sy"
                INSTALL_FLATPAK="sudo pacman -S --needed --noconfirm flatpak"
                INSTALL_SNAP="yay -S --needed --noconfirm snapd"
                HAS_AUR=true
                
                # Check for AUR helper
                if command -v yay &>/dev/null; then
                    AUR_HELPER="yay"
                    AUR_INSTALL="yay -S --needed --noconfirm"
                    log "INFO" "Using yay as AUR helper"
                elif command -v paru &>/dev/null; then
                    AUR_HELPER="paru"
                    AUR_INSTALL="paru -S --needed --noconfirm"
                    log "INFO" "Using paru as AUR helper"
                else
                    log "WARN" "No AUR helper found. Installing yay..."
                    install_aur_helper
                fi
                ;;
            opensuse*|suse)
                PKG_MANAGER="zypper"
                PKG_CHECK="rpm -q"
                PKG_INSTALL="sudo zypper install -y"
                PKG_UPDATE="sudo zypper refresh"
                INSTALL_FLATPAK="sudo zypper install -y flatpak"
                INSTALL_SNAP="sudo zypper install -y snapd"
                HAS_AUR=false
                ;;
            *)
                log "ERROR" "Unsupported distribution: $NAME"
                exit 1
                ;;
        esac
        
        log "INFO" "Detected distribution: $DISTRO_NAME $DISTRO_VERSION"
        log "INFO" "Package manager: $PKG_MANAGER"
    else
        log "ERROR" "Could not detect distribution"
        exit 1
    fi
}

# Install AUR helper (for Arch-based distributions)
install_aur_helper() {
    log "INFO" "Installing yay AUR helper..."
    
    # Install dependencies
    $PKG_INSTALL git base-devel
    
    # Create temporary directory
    local tmp_dir=$(mktemp -d)
    cd "$tmp_dir"
    
    # Clone and build yay
    git clone https://aur.archlinux.org/yay.git
    cd yay
    makepkg -si --noconfirm
    
    # Clean up
    cd "$OLDPWD"
    rm -rf "$tmp_dir"
    
    # Verify installation
    if command -v yay &>/dev/null; then
        AUR_HELPER="yay"
        AUR_INSTALL="yay -S --needed --noconfirm"
        log "INFO" "yay installed successfully"
    else
        log "ERROR" "Failed to install yay"
        exit 1
    fi
}

# Install Flatpak
install_flatpak_support() {
    log "INFO" "Setting up Flatpak support..."
    
    if command -v flatpak &>/dev/null; then
        log "INFO" "Flatpak is already installed"
    else
        log "INFO" "Installing Flatpak..."
        $INSTALL_FLATPAK
        
        # Add Flathub repository
        sudo flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
        log "INFO" "Added Flathub repository"
    fi
}

# Install Snap
install_snap_support() {
    log "INFO" "Setting up Snap support..."
    
    if command -v snap &>/dev/null; then
        log "INFO" "Snap is already installed"
    else
        log "INFO" "Installing Snap..."
        $INSTALL_SNAP
        
        # Enable snapd service if needed
        if systemctl --version &>/dev/null; then
            sudo systemctl enable --now snapd.socket
            sudo systemctl enable --now snapd.service
        fi
        
        # Create symbolic link if it doesn't exist
        if [ ! -e /snap ] && [ -d /var/lib/snapd/snap ]; then
            sudo ln -s /var/lib/snapd/snap /snap
        fi
    fi
}

# Check if package is installed
is_package_installed() {
    local package=$1
    local package_manager=$2
    
    case $package_manager in
        "system")
            case $PKG_MANAGER in
                apt)
                    dpkg -l "$package" &>/dev/null
                    ;;
                dnf|zypper)
                    rpm -q "$package" &>/dev/null
                    ;;
                pacman)
                    pacman -Qi "$package" &>/dev/null
                    ;;
            esac
            ;;
        "flatpak")
            flatpak list --app | grep -q "$package"
            ;;
        "snap")
            snap list | grep -q "$package"
            ;;
        "aur")
            if [ "$HAS_AUR" = true ]; then
                $AUR_HELPER -Qi "$package" &>/dev/null
            else
                return 1
            fi
            ;;
    esac
}

# Display header with detected system info
display_header() {
    clear
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo -e "${BOLD}${CYAN}          Recommended Software Installer              ${NC}"
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo -e "${BLUE}Distribution:${NC} $DISTRO_NAME $DISTRO_VERSION"
    echo -e "${BLUE}Package Manager:${NC} $PKG_MANAGER"
    
    if [ "$HAS_AUR" = true ]; then
        echo -e "${BLUE}AUR Helper:${NC} $AUR_HELPER"
    fi
    
    # Add system info
    echo -e "${BLUE}Kernel:${NC} $(uname -r)"
    echo -e "${BLUE}Architecture:${NC} $(uname -m)"
    
    # Add memory and disk info
    mem_total=$(free -h | awk '/^Mem:/{print $2}')
    mem_avail=$(free -h | awk '/^Mem:/{print $7}')
    disk_avail=$(df -h . | awk 'NR==2 {print $4}')
    disk_total=$(df -h . | awk 'NR==2 {print $2}')
    echo -e "${BLUE}Memory:${NC} ${mem_avail} available / ${mem_total} total"
    echo -e "${BLUE}Disk Space:${NC} ${disk_avail} available / ${disk_total} total"
    
    echo
}

# Function to display a description
display_description() {
    local title=$1
    local description=$2
    local advantages=$3
    local disadvantages=$4
    local source=$5

    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo -e "${BOLD}${CYAN}   $title${NC}"
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo
    echo -e "${BOLD}Description:${NC}"
    echo -e "$description"
    echo
    echo -e "${BOLD}${GREEN}Advantages:${NC}"
    echo -e "$advantages"
    echo
    echo -e "${BOLD}${RED}Disadvantages:${NC}"
    echo -e "$disadvantages"
    echo
    echo -e "${BOLD}${MAGENTA}Installation Source:${NC} $source"
    echo
    echo -e "${BLUE}--------------------------------------------------${NC}"
    echo
}

# Software categories
declare -A categories
categories["office"]="Office and Productivity"
categories["internet"]="Internet and Communication"
categories["multimedia"]="Multimedia and Entertainment"
categories["graphics"]="Graphics and Design"
categories["utilities"]="System Utilities"
categories["development"]="Development Tools"
categories["security"]="Security and Privacy"
categories["games"]="Games and Entertainment"

# Package name mappings for different distributions
get_package_name() {
    local app=$1
    local distro=$DISTRO
    
    # Define package names for different distributions
    case "$app" in
        "libreoffice")
            case $distro in
                debian|ubuntu|linuxmint|pop) echo "libreoffice" ;;
                fedora|centos|rhel) echo "libreoffice" ;;
                arch|manjaro|endeavouros) echo "libreoffice-fresh" ;;
                *) echo "libreoffice" ;;
            esac
            ;;
        "firefox")
            case $distro in
                debian|ubuntu|linuxmint|pop) echo "firefox" ;;
                fedora|centos|rhel) echo "firefox" ;;
                arch|manjaro|endeavouros) echo "firefox" ;;
                *) echo "firefox" ;;
            esac
            ;;
        # Add more package name mappings as needed
        *)
            echo "$app"
            ;;
    esac
}

# Define software with categories and installation methods
declare -A software_info

# Office and Productivity
software_info["libreoffice"]="office:Free and powerful office suite, compatible with Microsoft Office formats:- Comprehensive office suite.\n- Free and open-source.:- May not have all features of Microsoft Office.\n- Interface may be different for MS Office users.:system"
software_info["onlyoffice-desktopeditors"]="office:Powerful office suite with collaborative features:- Collaborative editing.\n- Good compatibility with MS Office.:- Some advanced features require a subscription.:flatpak"
software_info["simplenote"]="office:Simple and fast note-taking app:- Fast and easy to use.\n- Cross-platform support.:- Limited advanced features.:snap"
software_info["nextcloud-desktop"]="office:Self-hosted productivity platform client:- Complete control over data.\n- Many plugins available.:- Requires server setup.:system"

# Internet and Communication
software_info["firefox"]="internet:Fast and privacy-focused web browser:- Strong privacy protections.\n- Wide range of extensions.:- Can be resource-intensive.:system"
software_info["chromium"]="internet:Open-source web browser that is the foundation of Chrome:- Fast performance.\n- Extensive extension library.:- Privacy concerns from Google integration.:system"
software_info["thunderbird"]="internet:Free and open-source email client:- Supports multiple email protocols.\n- Extensible with add-ons.:- Interface may seem dated.:system"
software_info["slack"]="internet:Collaboration hub for work, providing chat and file sharing:- Integrates with many services.\n- Good team collaboration features.:- Free version has limitations.:snap"
software_info["discord"]="internet:VoIP, instant messaging, and digital distribution platform:- Free and feature-rich.\n- Large user base.:- Can be resource-intensive.:flatpak"

# Multimedia and Entertainment
software_info["vlc"]="multimedia:Free and open-source multimedia player:- Plays almost any media file.:- Interface may seem basic.:system"
software_info["spotify"]="multimedia:Digital music service providing access to millions of songs:- Huge music library.\n- Easy to use.:- Free version has ads.:snap"
software_info["obs-studio"]="multimedia:Free and open source software for video recording and live streaming:- Professional-grade features.\n- Free and open-source.:- Can be complex to set up.:system"
software_info["kodi"]="multimedia:Free and open source media player application:- Extensive media library features.\n- Customizable with add-ons.:- May be too complex for simple needs.:system"

# Graphics and Design
software_info["gimp"]="graphics:Powerful and free image editor:- Comparable to Adobe Photoshop.\n- Free and open-source.:- Can have a steep learning curve.:system"
software_info["krita"]="graphics:Professional and open-source painting program:- Great for digital painting.\n- Free and open-source.:- Not as versatile as Photoshop for photo editing.:system"
software_info["inkscape"]="graphics:Professional vector graphics editor:- Powerful vector editing capabilities.\n- Free and open-source.:- Learning curve for beginners.:system"
software_info["blender"]="graphics:Free and open source 3D creation suite:- Comprehensive 3D modeling and animation.\n- Free and open-source.:- Complex interface and steep learning curve.:system"

# System Utilities
software_info["timeshift"]="utilities:System restore tool for Linux:- Easy system backups and restores.:- Can use a lot of disk space.:system"
software_info["bleachbit"]="utilities:Disk space cleaner and privacy manager:- Free up space and protect privacy.:- Can delete important files if not used carefully.:system"
software_info["htop"]="utilities:Interactive process viewer for Unix systems:- Easy-to-use interface.\n- Detailed system monitoring.:- No built-in logging.:system"
software_info["glances"]="utilities:Cross-platform system monitoring tool:- Detailed and comprehensive monitoring.:- Requires command-line knowledge.:system"
software_info["rclone"]="utilities:Command-line program to manage files on cloud storage:- Supports many cloud providers.\n- Powerful and flexible.:- Requires command-line knowledge.:system"

# Development Tools
software_info["visual-studio-code"]="development:Popular code editor from Microsoft:- Highly extensible.\n- Large community and support.:- Some features require extensions.:system"
software_info["git"]="development:Free and open-source distributed version control system:- Essential for version control.:- Requires learning Git commands.:system"
software_info["docker"]="development:Platform for developing, shipping, and running applications in containers:- Isolates applications.\n- Consistent environments.:- Requires learning container concepts.:system"
software_info["postman"]="development:API development environment:- Makes API testing easy.\n- Good documentation features.:- Can be resource-intensive.:snap"

# Security and Privacy
software_info["keepassxc"]="security:Cross-platform password manager:- Strong encryption.\n- Free and open-source.:- Interface can seem complex.:system"
software_info["bitwarden"]="security:Open source password management solution:- Cross-platform synchronization.\n- Free tier is feature-rich.:- Online account required for sync.:snap"
software_info["ufw"]="security:Uncomplicated Firewall:- Easy to configure.\n- Good default settings.:- Limited advanced features.:system"
software_info["cryptomator"]="security:Free cloud encryption tool:- Encrypts files before uploading to cloud.\n- Cross-platform.:- Adds additional steps to workflow.:flatpak"

# Games and Entertainment
software_info["steam"]="games:Digital distribution platform for video games:- Huge game library.\n- Regular sales.:- Resource-intensive client.:system"
software_info["lutris"]="games:Open gaming platform for Linux:- Simplifies game installation.\n- Supports various game sources.:- Some games may not work perfectly.:system"
software_info["minecraft"]="games:Popular sandbox video game:- Infinite possibilities.\n- Cross-platform multiplayer.:- Requires account purchase for full version.:flatpak"

# Function to install software based on its source
install_software_item() {
    local name=$1
    local info=${software_info[$name]}
    
    IFS=':' read -r category description advantages disadvantages source <<< "$info"
    
    display_description "Installing $name" "$description" "$advantages" "$disadvantages" "$source"
    
    # Check if already installed
    if is_package_installed "$name" "$source"; then
        log "INFO" "$name is already installed. Skipping installation."
        echo -e "${GREEN}$name is already installed. Skipping installation.${NC}"
        sleep 1
        return 0
    fi
    
    # Install based on source
    log "INFO" "Installing $name from $source source"
    echo -e "${YELLOW}Installing $name...${NC}"
    
    case $source in
        "system")
            local pkg_name=$(get_package_name "$name")
            
            if [ "$PKG_MANAGER" = "pacman" ] && ! $PKG_INSTALL "$pkg_name" &>> "$LOG_FILE"; then
                # If package is not in official repos, try AUR if available
                if [ "$HAS_AUR" = true ]; then
                    log "INFO" "Package not found in official repos, trying AUR..."
                    $AUR_INSTALL "$pkg_name" &>> "$LOG_FILE"
                else
                    log "ERROR" "Failed to install $name"
                    echo -e "${RED}Failed to install $name. See log for details.${NC}"
                    sleep 2
                    return 1
                fi
            elif ! $PKG_INSTALL "$pkg_name" &>> "$LOG_FILE"; then
                log "ERROR" "Failed to install $name"
                echo -e "${RED}Failed to install $name. See log for details.${NC}"
                sleep 2
                return 1
            fi
            ;;
        "flatpak")
            if ! command -v flatpak &>/dev/null; then
                log "INFO" "Flatpak not installed. Installing now..."
                install_flatpak_support
            fi
            flatpak install -y flathub "$name" &>> "$LOG_FILE" || {
                log "ERROR" "Failed to install $name via Flatpak"
                echo -e "${RED}Failed to install $name via Flatpak. See log for details.${NC}"
                sleep 2
                return 1
            }
            ;;
        "snap")
            if ! command -v snap &>/dev/null; then
                log "INFO" "Snap not installed. Installing now..."
                install_snap_support
            fi
            sudo snap install "$name" &>> "$LOG_FILE" || {
                log "ERROR" "Failed to install $name via Snap"
                echo -e "${RED}Failed to install $name via Snap. See log for details.${NC}"
                sleep 2
                return 1
            }
            ;;
        "aur")
            if [ "$HAS_AUR" = true ]; then
                $AUR_INSTALL "$name" &>> "$LOG_FILE" || {
                    log "ERROR" "Failed to install $name from AUR"
                    echo -e "${RED}Failed to install $name from AUR. See log for details.${NC}"
                    sleep 2
                    return 1
                }
            else
                log "WARN" "AUR not available on this distribution. Skipping $name."
                echo -e "${YELLOW}AUR not available on this distribution. Skipping $name.${NC}"
                sleep 2
                return 1
            fi
            ;;
    esac
    
    log "INFO" "Successfully installed $name"
    echo -e "${GREEN}Successfully installed $name.${NC}"
    sleep 1
    return 0
}

# Install all software in a category
install_category() {
    local category=$1
    local category_name=${categories[$category]}
    local software_list=()
    
    # Find all software in this category
    for name in "${!software_info[@]}"; do
        local info=${software_info[$name]}
        IFS=':' read -r cat _ _ _ _ <<< "$info"
        
        if [ "$cat" = "$category" ]; then
            software_list+=("$name")
        fi
    done
    
    local total=${#software_list[@]}
    if [ $total -eq 0 ]; then
        log "WARN" "No software found in category $category_name"
        echo -e "${YELLOW}No software found in category $category_name.${NC}"
        sleep 2
        return
    fi
    
    display_header
    log "INFO" "Installing all software in category: $category_name"
    echo -e "${CYAN}Installing all software in category: ${BOLD}$category_name${NC}"
    echo -e "${BLUE}Total software in this category: ${YELLOW}$total${NC}"
    sleep 1
    
    local current=0
    for name in "${software_list[@]}"; do
        clear
        install_software_item "$name"
        ((current++))
        loading_bar $current $total
    done
    
    echo -e "\n${GREEN}Completed installation of $category_name software.${NC}"
    sleep 2
}

# Display software in a category
display_category_software() {
    local category=$1
    local category_name=${categories[$category]}
    local software_list=()
    
    # Find all software in this category
    for name in "${!software_info[@]}"; do
        local info=${software_info[$name]}
        IFS=':' read -r cat description _ _ source <<< "$info"
        
        if [ "$cat" = "$category" ]; then
            software_list+=("$name")
        fi
    done
    
    local total=${#software_list[@]}
    if [ $total -eq 0 ]; then
        echo -e "${YELLOW}No software found in category $category_name.${NC}"
        return
    fi
    
    clear
    display_header
    echo -e "${BOLD}${CYAN}Software in category: $category_name${NC}"
    echo
    
    local i=1
    for name in "${software_list[@]}"; do
        local info=${software_info[$name]}
        IFS=':' read -r _ description _ _ source <<< "$info"
        
        # Truncate description if too long
        if [ ${#description} -gt 60 ]; then
            description="${description:0:57}..."
        fi
        
        # Check if installed
        if is_package_installed "$name" "$source"; then
            echo -e "${MAGENTA}$i)${NC} ${BOLD}$name${NC} [${GREEN}Installed${NC}]"
        else
            echo -e "${MAGENTA}$i)${NC} ${BOLD}$name${NC} - $description"
        fi
        
        category_items[$i]=$name
        ((i++))
    done
    
    echo -e "${MAGENTA}a)${NC} ${BOLD}Install all${NC}"
    echo -e "${MAGENTA}b)${NC} ${BOLD}Back to categories${NC}"
    echo
}

# Function for category menu
category_menu() {
    local category=$1
    declare -A category_items # Declare category_items here
    
    while true; do
        display_category_software "$category"
        echo -n -e "${CYAN}Select software to install (1-${#category_items[@]}, a for all, b for back): ${NC}"
        read -r choice
        
        case $choice in
            [0-9]*)
                if [ -n "${category_items[$choice]}" ]; then
                    clear
                    install_software_item "${category_items[$choice]}"
                    echo -e "\nPress Enter to continue..."
                    read
                else
                    echo -e "${RED}Invalid choice.${NC}"
                    sleep 1
                fi
                ;;
            a|A)
                install_category "$category"
                ;;
            b|B)
                return
                ;;
            *)
                echo -e "${RED}Invalid choice.${NC}"
                sleep 1
                ;;
        esac
    done
}

# Display main category menu
display_main_menu() {
    clear
    display_header
    
    echo -e "${BOLD}${CYAN}Select a software category:${NC}"
    echo
    
    local i=1
    for category in "${!categories[@]}"; do
        # Count software in this category
        local count=0
        for name in "${!software_info[@]}"; do
            local info=${software_info[$name]}
            IFS=':' read -r cat _ _ _ _ <<< "$info"
            
            if [ "$cat" = "$category" ]; then
                ((count++))
            fi
        done
        
        echo -e "${MAGENTA}$i)${NC} ${BOLD}${categories[$category]}${NC} (${YELLOW}$count items${NC})"
        menu_categories[$i]=$category
        ((i++))
    done
    
    echo -e "${MAGENTA}a)${NC} ${BOLD}Install all recommended software${NC}"
    echo -e "${MAGENTA}u)${NC} ${BOLD}Update system packages${NC}"
    echo -e "${MAGENTA}q)${NC} ${BOLD}Quit${NC}"
    echo
}

# Install all recommended software
install_all_recommended() {
    local total=0
    local all_software=()
    
    # Count total software
    for name in "${!software_info[@]}"; do
        all_software+=("$name")
        ((total++))
    done
    
    display_header
    log "INFO" "Installing all recommended software ($total items)"
    echo -e "${CYAN}Installing all recommended software (${YELLOW}$total items${NC})${NC}"
    sleep 1
    
    local current=0
    for name in "${all_software[@]}"; do
        clear
        install_software_item "$name"
        ((current++))
        loading_bar $current $total
    done
    
    echo -e "\n${GREEN}Completed installation of all recommended software.${NC}"
    sleep 2
}

# Update system packages
update_system() {
    display_header
    log "INFO" "Updating system packages"
    echo -e "${CYAN}Updating system packages...${NC}"
    
    if eval "$PKG_UPDATE" &>> "$LOG_FILE"; then
        log "INFO" "System packages updated successfully"
        echo -e "${GREEN}System packages updated successfully.${NC}"
    else
        log "ERROR" "Failed to update system packages"
        echo -e "${RED}Failed to update system packages. See log for details.${NC}"
    fi
    
    echo -e "\nPress Enter to continue..."
    read
}

# Main function
main() {
    init_log
    check_sudo
    detect_system

    # Main menu loop
    while true; do
        # Populate menu_categories array
        unset menu_categories
        declare -A menu_categories
        local i=1
        for category in "${!categories[@]}"; do
            menu_categories[$i]=$category
            ((i++))
        done

        display_main_menu
        echo -n -e "${CYAN}Select an option (1-${#menu_categories[@]}, a, u, or q): ${NC}"
        read -r choice

        case $choice in
            [0-9]*)
                if [ -n "${menu_categories[$choice]}" ]; then
                    category_menu "${menu_categories[$choice]}"
                else
                    echo -e "${RED}Invalid choice.${NC}"
                    sleep 1
                fi
                ;;
            a|A)
                install_all_recommended
                ;;
            u|U)
                update_system
                ;;
            q|Q)
                log "INFO" "Exiting"
                echo -e "${GREEN}Thank you for using the Recommended Software Installer!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice.${NC}"
                sleep 1
                ;;
        esac
    done
}

# Run the main function
main