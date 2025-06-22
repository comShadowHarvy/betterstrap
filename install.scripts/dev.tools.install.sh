#!/bin/bash

# Enhanced Development Tools Installer
# A comprehensive installer for development tools with categorization and interactive options
# Version 2.0 (Updated by Gemini)

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
PKG_CHECK=""
PKG_INSTALL=""
PKG_UPDATE=""

# --- Helper Functions ---

# Function to check for sudo privileges
check_sudo() {
    if [[ "$EUID" -eq 0 ]]; then
        echo -e "${YELLOW}Warning: It's recommended to run this script as a regular user, not as root.${NC}"
        sleep 2
        return
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
        PKG_MANAGER="apt" PKG_CHECK="dpkg -l" PKG_INSTALL="sudo apt install -y" PKG_UPDATE="sudo apt update"
        echo -e "${GREEN}Detected apt (Debian/Ubuntu).${NC}"
    elif command -v dnf &>/dev/null; then
        PKG_MANAGER="dnf" PKG_CHECK="rpm -q" PKG_INSTALL="sudo dnf install -y" PKG_UPDATE="sudo dnf check-update || true"
        echo -e "${GREEN}Detected dnf (Fedora/RHEL).${NC}"
    elif command -v yum &>/dev/null; then
        PKG_MANAGER="yum" PKG_CHECK="rpm -q" PKG_INSTALL="sudo yum install -y" PKG_UPDATE="sudo yum check-update || true"
        echo -e "${GREEN}Detected yum (CentOS/RHEL).${NC}"
    elif command -v pacman &>/dev/null; then
        PKG_MANAGER="pacman" PKG_CHECK="pacman -Qs" PKG_INSTALL="sudo pacman -S --needed --noconfirm" PKG_UPDATE="sudo pacman -Sy"
        echo -e "${GREEN}Detected pacman (Arch Linux).${NC}"
    elif command -v zypper &>/dev/null; then
        PKG_MANAGER="zypper" PKG_CHECK="rpm -q" PKG_INSTALL="sudo zypper install -y" PKG_UPDATE="sudo zypper refresh"
        echo -e "${GREEN}Detected zypper (openSUSE).${NC}"
    elif command -v apk &>/dev/null; then
        PKG_MANAGER="apk" PKG_CHECK="apk info -e" PKG_INSTALL="sudo apk add" PKG_UPDATE="sudo apk update"
        echo -e "${GREEN}Detected apk (Alpine Linux).${NC}"
    else
        echo -e "${RED}Error: No supported package manager found (apt, dnf, yum, pacman, zypper, apk).${NC}"
        exit 1
    fi
}

# Function to update package manager cache if needed
update_package_cache() {
    echo -e "${BLUE}Checking package manager cache...${NC}"
    # For apt, check if cache is older than 24 hours
    if [[ "$PKG_MANAGER" == "apt" ]] && { [[ ! -f "/var/cache/apt/pkgcache.bin" ]] || [[ $(find /var/cache/apt/pkgcache.bin -mtime +1) ]]; }; then
        echo -e "${CYAN}Updating apt package cache...${NC}"
        $PKG_UPDATE
    elif [[ "$PKG_MANAGER" != "apt" ]]; then
        # For other package managers, a check-update or refresh is generally good practice.
        echo -e "${CYAN}Running package manager update check...${NC}"
        $PKG_UPDATE
    else
        echo -e "${GREEN}Apt cache is up to date.${NC}"
    fi
}

# Function to check if a command or package is installed
is_installed() {
    local name="$1"
    # Check for command existence first for special cases
    if command -v "$name" &>/dev/null; then
        return 0
    fi
    # Fallback to package manager check
    if $PKG_CHECK "$name" &>/dev/null; then
        return 0
    fi
    return 1
}

# Safer function to install remote scripts (e.g., rustup, nix installer)
install_remote_script() {
    local name="$1"
    local url="$2"
    local run_command="$3"
    local temp_script

    temp_script=$(mktemp)
    echo -e "${CYAN}Downloading installer for $name from $url...${NC}"
    if ! curl -fsSL "$url" -o "$temp_script"; then
        echo -e "${RED}Error downloading $name installer.${NC}"
        rm -f "$temp_script"
        return 1
    fi

    echo -e "${YELLOW}SECURITY: Installer for $name downloaded."
    echo -e "You can review it with: ${BOLD}cat $temp_script${NC}"
    read -p "Do you want to run the installer for $name? (y/N): " -r choice
    if [[ "$choice" =~ ^[Yy]$ ]]; then
        bash -c "$run_command" "$temp_script"
    else
        echo -e "${YELLOW}Skipping installation of $name.${NC}"
    fi
    rm -f "$temp_script"
}

# Function to install a single tool
install_tool() {
    # Parse tool details
    IFS=':' read -r name description advantages disadvantages category pkg_names <<< "$1"
    local pkgs_to_install="${pkg_names//|/ }" # Replace pipe with space

    clear
    display_description "Installing $name" "$description" "$advantages" "$disadvantages"

    if is_installed "$name"; then
        echo -e "${GREEN}$name is already installed.${NC}"
        sleep 2
        return 0
    fi

    # Handle special installation cases
    case "$name" in
        rust)
            echo -e "${YELLOW}Rust requires a special installation via rustup.${NC}"
            install_remote_script "Rust" "https://sh.rustup.rs" "bash %s -s -- -y"
            # Attempt to source the environment for the current session
            if [[ -f "$HOME/.cargo/env" ]]; then source "$HOME/.cargo/env"; fi
            ;;
        nix)
            echo -e "${YELLOW}Nix requires a special installation.${NC}"
            install_remote_script "Nix" "https://nixos.org/nix/install" "bash %s"
            ;;
        *)
            # Normal package installation
            echo -e "${BLUE}Installing $name via $PKG_MANAGER...${NC}"
            if $PKG_INSTALL $pkgs_to_install; then
                echo -e "\n${GREEN}$name installed successfully.${NC}"
            else
                echo -e "\n${RED}Failed to install $name. Check logs for details.${NC}"
                return 1
            fi
            ;;
    esac
    sleep 2
    return 0
}

# --- UI and Menu Functions ---

display_header() {
    clear
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo -e "${BOLD}${CYAN}           Development Tools Installer (v2.0)        ${NC}"
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo
    echo -e "${BOLD}System Info:${NC} $(grep PRETTY_NAME /etc/os-release | cut -d'"' -f 2 2>/dev/null || uname -a)"
    echo -e "${BOLD}Package Manager:${NC} $PKG_MANAGER"
    echo
}

display_description() {
    clear
    display_header
    echo -e "${BOLD}${CYAN}--- $1 ---${NC}\n"
    echo -e "${BOLD}Description:${NC}\n$2\n"
    echo -e "${BOLD}${GREEN}Advantages:${NC}\n$3\n"
    echo -e "${BOLD}${RED}Disadvantages:${NC}\n$4\n"
    echo -e "${BLUE}--------------------------------------------------${NC}\n"
}

# --- Tool Definitions ---

# Define tool categories
declare -A TOOL_CATEGORIES
TOOL_CATEGORIES=(
    ["compilers"]="Compilers & Languages"
    ["build"]="Build Systems & Tools"
    ["scripting"]="Scripting Languages"
    ["version_control"]="Version Control"
    ["package_managers"]="Package Managers"
    ["utilities"]="Dev Utilities"
)
# Define an ordered list of category keys
ORDERED_CATEGORIES=("compilers" "build" "scripting" "version_control" "package_managers" "utilities")

# Define tools
# Format: name:description:advantages:disadvantages:category:package_name(s)
TOOLS=(
    "gcc:GNU Compiler Collection for C/C++.:- Wide language support.\n- Strong optimization.:- Slower than Clang for some tasks.:compilers:gcc"
    "clang:Clang/LLVM Compiler for C/C++.:- Fast and modular.\n- Good diagnostics.:- Less mature than GCC in some areas.:compilers:clang"
    "rust:Rust programming language.:- Memory safety without garbage collection.\n- Modern features.:- Steeper learning curve than Go.:compilers:rust"
    "go:Go programming language.:- Fast compile times.\n- Excellent concurrency.:- Simpler feature set.:compilers:golang|go"
    "cmake:Cross-platform build system.:- Versatile and widely supported.:- Complex syntax.:build:cmake"
    "meson:Modern and fast build system.:- Simple to use.\n- Fast.:- Newer, smaller community.:build:meson"
    "make:The classic build automation tool.:- Ubiquitous and powerful.:- Can be complex for large projects.:build:make|build-essential"
    "ninja:Fast, small build system.:- Extremely fast.\n- Simple.:- Less feature-rich than Make.:build:ninja-build|ninja"
    "python:Python interpreter and pip.:- Versatile and huge library ecosystem.:- Slower than compiled languages.:scripting:python3|python3-pip"
    "node:Node.js JavaScript runtime.:- Vast ecosystem (npm).\n- Great for web dev.:- Can have complex dependency chains.:scripting:nodejs|npm"
    "ruby:Ruby interpreter.:- Elegant syntax.\n- Excellent for web apps (Rails).:- Slower than many alternatives.:scripting:ruby"
    "git:Distributed version control.:- The industry standard.\n- Powerful and flexible.:- Can be complex to learn.:version_control:git"
    "nix:Powerful, reproducible package manager.:- Perfectly reproducible builds.\n- Atomic upgrades.:- Steep learning curve.:package_managers:nix"
    "gdb:The GNU Project Debugger.:- Powerful for C/C++ and others.:- Can be difficult to learn.:utilities:gdb"
    "valgrind:Memory debugging & leak detection.:- Invaluable for memory analysis.:- Slows execution considerably.:utilities:valgrind"
    "strace:System call tracer.:- Great for low-level troubleshooting.:- Output can be overwhelming.:utilities:strace"
    "curl:Tool for transferring data with URLs.:- Extremely versatile for APIs.:- Can have complex syntax.:utilities:curl"
    "jq:Command-line JSON processor.:- Powerful for JSON manipulation.:- Requires learning its syntax.:utilities:jq"
)

# --- Main Logic ---

# Function to install all tools in a given category
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
    echo -e "${BLUE}Installing all ${#category_tools[@]} tools in category: ${BOLD}$category_name${NC}"
    sleep 2

    for tool_data in "${category_tools[@]}"; do
        install_tool "$tool_data"
    done
    
    echo -e "\n${GREEN}Finished installing tools for category: $category_name${NC}"
    echo -e "Press any key to return to the menu..."
    read -n 1 -s
}

# Function to install all tools from all categories
install_all() {
    display_header
    echo -e "${BLUE}Installing all ${#TOOLS[@]} development tools...${NC}"
    read -p "This will install all tools. Are you sure? (y/N): " -r choice
    if [[ ! "$choice" =~ ^[Yy]$ ]]; then
        return
    fi

    for tool_data in "${TOOLS[@]}"; do
        install_tool "$tool_data"
    done

    echo -e "\n${GREEN}All development tools installed.${NC}"
    echo -e "Press any key to return to the menu..."
    read -n 1 -s
}


# Primary menu loop
main_menu() {
    while true; do
        display_header
        echo -e "${BOLD}${CYAN}Select a category to install:${NC}\n"
        
        # Display menu options from ordered categories
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
            a|A)
                install_all
                ;;
            q|Q)
                echo -e "${GREEN}Exiting installer.${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice. Press any key.${NC}"; read -n 1 -s
                ;;
        esac
    done
}


# --- Script Entry Point ---
main() {
    check_sudo
    detect_package_manager
    update_package_cache
    main_menu
}

main
