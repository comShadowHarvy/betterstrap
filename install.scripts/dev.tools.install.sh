#!/bin/bash

# Enhanced Development Tools Installer
# A comprehensive installer for development tools with categorization and interactive options

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

# Function to check if script is run with sudo
check_sudo() {
    if [ "$EUID" -eq 0 ]; then
        echo -e "${YELLOW}Warning: Running as root directly. It's recommended to run as a normal user with sudo.${NC}"
        return
    fi

    if ! command -v sudo &>/dev/null; then
        echo -e "${RED}Error: sudo is not installed but is required.${NC}"
        exit 1
    fi

    # Check if user has sudo privileges
    if ! sudo -v &>/dev/null; then
        echo -e "${RED}Error: Current user does not have sudo privileges.${NC}"
        exit 1
    fi
}

# Function to detect package manager and set up environment
detect_package_manager() {
    echo -e "${BLUE}Detecting package manager...${NC}"

    if command -v apt &>/dev/null; then
        PKG_MANAGER="apt"
        PKG_CHECK="dpkg -l"
        PKG_INSTALL="sudo apt install -y"
        PKG_UPDATE="sudo apt update"
        echo -e "${GREEN}Detected apt package manager (Debian/Ubuntu)${NC}"

        # Check if apt cache is updated recently (within 24 hours)
        if [ ! -f "/var/cache/apt/pkgcache.bin" ] || [ "$(find /var/cache/apt/pkgcache.bin -mtime +1)" ]; then
            echo -e "${BLUE}Updating apt package cache...${NC}"
            $PKG_UPDATE
        fi

    elif command -v dnf &>/dev/null; then
        PKG_MANAGER="dnf"
        PKG_CHECK="rpm -q"
        PKG_INSTALL="sudo dnf install -y"
        PKG_UPDATE="sudo dnf check-update || true"  # The `|| true` prevents failure on exit code 100
        echo -e "${GREEN}Detected dnf package manager (Fedora/RHEL)${NC}"

    elif command -v yum &>/dev/null; then
        PKG_MANAGER="yum"
        PKG_CHECK="rpm -q"
        PKG_INSTALL="sudo yum install -y"
        PKG_UPDATE="sudo yum check-update || true"
        echo -e "${GREEN}Detected yum package manager (RHEL/CentOS)${NC}"

    elif command -v pacman &>/dev/null; then
        PKG_MANAGER="pacman"
        PKG_CHECK="pacman -Qs"
        PKG_INSTALL="sudo pacman -S --needed --noconfirm"
        PKG_UPDATE="sudo pacman -Sy"
        echo -e "${GREEN}Detected pacman package manager (Arch Linux)${NC}"

    elif command -v zypper &>/dev/null; then
        PKG_MANAGER="zypper"
        PKG_CHECK="rpm -q"
        PKG_INSTALL="sudo zypper install -y"
        PKG_UPDATE="sudo zypper refresh"
        echo -e "${GREEN}Detected zypper package manager (openSUSE)${NC}"

    elif command -v apk &>/dev/null; then
        PKG_MANAGER="apk"
        PKG_CHECK="apk info -e"
        PKG_INSTALL="sudo apk add"
        PKG_UPDATE="sudo apk update"
        echo -e "${GREEN}Detected apk package manager (Alpine Linux)${NC}"

    else
        echo -e "${RED}Error: No supported package manager found${NC}"
        echo -e "${YELLOW}This script supports apt, dnf, yum, pacman, zypper, and apk.${NC}"
        exit 1
    fi
}

# Function to check if a package is installed
is_package_installed() {
    local package=$1

    # Special cases for certain packages
    case $package in
        "rust")
            if command -v rustc &>/dev/null; then
                return 0
            else
                return 1
            fi
            ;;
        "go")
            if command -v go &>/dev/null; then
                return 0
            else
                return 1
            fi
            ;;
        "nix")
            if command -v nix &>/dev/null; then
                return 0
            else
                return 1
            fi
            ;;
        *)
            # Default check using package manager
            $PKG_CHECK $package &>/dev/null
            return $?
            ;;
    esac
}

# Enhanced loading bar with colors and spinner
loading_bar() {
    local current=$1
    local total=$2
    local percent=$(( 100 * current / total ))
    local bar_length=40
    local filled_length=$(( bar_length * current / total ))
    local empty_length=$(( bar_length - filled_length ))
    local spinner=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
    local spin_index=$(( current % ${#spinner[@]} ))

    printf -v bar "%0.s${GREEN}█${NC}" $(seq 1 $filled_length)
    printf -v space "%0.s${BLUE}░${NC}" $(seq 1 $empty_length)

    echo -ne "${BLUE}Progress: [${bar}${space}] ${YELLOW}${percent}%%${NC} ${CYAN}${spinner[$spin_index]}${NC}\r"
}

# Function to display the header
display_header() {
    clear
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo -e "${BOLD}${CYAN}           Development Tools Installer               ${NC}"
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo

    # Display system information
    echo -e "${BOLD}System Information:${NC}"
    echo -e "${BLUE}OS:${NC} $(grep PRETTY_NAME /etc/os-release | cut -d '"' -f 2)"
    echo -e "${BLUE}Kernel:${NC} $(uname -r)"
    echo -e "${BLUE}Architecture:${NC} $(uname -m)"

    # Show available memory
    mem_total=$(free -h | awk '/^Mem:/{print $2}')
    mem_avail=$(free -h | awk '/^Mem:/{print $7}')
    echo -e "${BLUE}Memory:${NC} ${mem_avail} available / ${mem_total} total"

    # Show available disk space
    disk_avail=$(df -h . | awk 'NR==2 {print $4}')
    disk_total=$(df -h . | awk 'NR==2 {print $2}')
    echo -e "${BLUE}Disk Space:${NC} ${disk_avail} available / ${disk_total} total"

    echo
}

# Function to display a description
display_description() {
    local title=$1
    local description=$2
    local advantages=$3
    local disadvantages=$4

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
    echo -e "${BLUE}--------------------------------------------------${NC}"
    echo
}

# Function to install a tool with proper error handling
install_tool() {
    local tool=$1
    local name=$(echo "$tool" | cut -d: -f1)
    local description=$(echo "$tool" | cut -d: -f2)
    local advantages=$(echo "$tool" | cut -d: -f3)
    local disadvantages=$(echo "$tool" | cut -d: -f4)
    local category=$(echo "$tool" | cut -d: -f5)
    local pkg_name=$(echo "$tool" | cut -d: -f6 | sed 's/|/ /g')

    clear
    display_description "Installing $name" "$description" "$advantages" "$disadvantages"

    # Special case for Rust installation
    if [ "$name" = "rust" ] && ! is_package_installed "rust"; then
        echo -e "${YELLOW}Rust requires special installation...${NC}"
        if [ "$PKG_MANAGER" = "pacman" ]; then
            # Arch Linux provides a rustup package
            $PKG_INSTALL rustup
            rustup default stable
        else
            # For other distros, use rustup directly
            curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
            source "$HOME/.cargo/env"
        fi
        echo -e "\n${GREEN}Rust installed successfully.${NC}"
        return 0
    fi

    # Special case for Nix installation
    if [ "$name" = "nix" ] && ! is_package_installed "nix"; then
        echo -e "${YELLOW}Nix requires special installation...${NC}"
        curl -L https://nixos.org/nix/install | sh
        echo -e "\n${GREEN}Nix installed successfully.${NC}"
        return 0
    fi

    # Normal package installation
    if is_package_installed "$name"; then
        echo -e "${GREEN}$name is already installed.${NC}"
    else
        echo -e "${BLUE}Installing $name...${NC}"
        if $PKG_INSTALL $pkg_name; then
            echo -e "\n${GREEN}$name installed successfully.${NC}"
        else
            echo -e "\n${RED}Failed to install $name. Check logs for details.${NC}"
            return 1
        fi
    fi
    return 0
}

# Define tool categories
declare -A tool_categories
tool_categories["compilers"]="Compilers and Programming Languages"
tool_categories["build"]="Build Systems and Tools"
tool_categories["scripting"]="Scripting and Interpreted Languages"
tool_categories["version_control"]="Version Control Systems"
tool_categories["package_managers"]="Package Managers"
tool_categories["editors"]="Code Editors and IDEs"
tool_categories["debuggers"]="Debugging and Profiling Tools"
tool_categories["utilities"]="Development Utilities"

# Define tools with categories and package names
tools=(
    # Format: name:description:advantages:disadvantages:category:package_name(s)
    # Compilers and Programming Languages
    "gcc:GNU Compiler Collection for C, C++, and more:- Wide language support.\n- Strong optimization features.:- Can be slower than Clang for some tasks.:compilers:gcc"
    "clang:Clang/LLVM Compiler for C, C++, and more:- Fast and modular.\n- Good diagnostics and error messages.:- Less mature than GCC in some areas.:compilers:clang"
    "rust:Rust programming language and compiler:- Safe memory management.\n- Modern features.:- Newer, with less library support than C++.:compilers:rust"
    "go:Golang programming language and compiler:- Fast compile times.\n- Excellent concurrency support.:- Somewhat limited language features.:compilers:golang"

    # Build Systems
    "cmake:Cross-platform build system generator:- Versatile and widely supported.:- Complex syntax.:build:cmake"
    "meson:Modern build system designed for speed:- Simple to use.\n- Fast.:- Newer, with smaller community.:build:meson"
    "make:Build automation tool:- Ubiquitous and powerful.:- Can be complex for large projects.:build:make"
    "ninja:Fast, small build system:- Very fast.\n- Simple configuration.:- Less feature-rich than Make.:build:ninja"

    # Scripting Languages
    "python:Python programming language interpreter:- Versatile and widely used.\n- Extensive libraries.:- Slower execution compared to compiled languages.:scripting:python3|python3-pip"
    "node:Node.js JavaScript runtime:- Vast ecosystem.\n- Great for web development.:- Package management can be complex.:scripting:nodejs|npm"
    "ruby:Ruby programming language interpreter:- Elegant syntax.\n- Good for web applications.:- Slower than some alternatives.:scripting:ruby"

    # Version Control
    "git:Distributed version control system:- Essential for version control.\n- Strong community support.:- Requires command-line knowledge.:version_control:git"
    "mercurial:Alternative distributed version control system:- User-friendly.\n- Good performance.:- Less popular than Git.:version_control:mercurial"

    # Package Managers
    "nix:Powerful package manager for reproducible builds:- Reproducibility.\n- Multi-user environment support.:- Requires learning Nix syntax.:package_managers:nix"

    # Development Utilities
    "gdb:GNU Project Debugger:- Powerful debugging capabilities.\n- Works with multiple languages.:- Steep learning curve.:debuggers:gdb"
    "valgrind:Memory debugging, memory leak detection tool:- Excellent for memory analysis.\n- Wide language support.:- Slows execution considerably.:debuggers:valgrind"
    "strace:System call tracer:- Useful for troubleshooting.\n- Low overhead.:- Output can be overwhelming.:utilities:strace"
    "curl:Command line tool for transferring data:- Versatile.\n- Great for API testing.:- Complex syntax for advanced features.:utilities:curl"
    "jq:Command-line JSON processor:- Powerful JSON manipulation.\n- Great for API responses.:- Requires learning its syntax.:utilities:jq"
)

# Function to install tools from a category
install_category() {
    local category=$1
    local category_name=${tool_categories[$category]}
    local category_tools=()
    local total_tools=0

    # Find tools in this category
    for tool in "${tools[@]}"; do
        if [[ "$tool" == *":$category:"* ]]; then
            category_tools+=("$tool")
            ((total_tools++))
        fi
    done

    if [ $total_tools -eq 0 ]; then
        echo -e "${YELLOW}No tools found in category: $category_name${NC}"
        sleep 2
        return
    fi

    echo -e "${BLUE}Installing tools in category: ${BOLD}$category_name${NC}"
    echo -e "${YELLOW}Found $total_tools tools in this category${NC}"
    sleep 1

    local current=0
    # Install each tool in the category
    for tool in "${category_tools[@]}"; do
        if install_tool "$tool"; then
            ((current++))
            loading_bar $current $total_tools
            sleep 1
        else
            echo -e "${RED}Failed to install tool. Press any key to continue...${NC}"
            read -n 1
            ((current++))
        fi
    done

    echo -e "\n${GREEN}Completed installing tools in category: $category_name${NC}"
    echo -e "Press any key to return to the main menu..."
    read -n 1
}

# Function to display the category menu
display_category_menu() {
    clear
    display_header

    echo -e "${BOLD}${CYAN}Select a category to install:${NC}"
    echo

    # Debug: Print categories to ensure they exist
    echo -e "${BLUE}Available categories:${NC}"

    # Sort the category keys to ensure consistent ordering
    local sorted_categories=()
    for category in "${!tool_categories[@]}"; do
        sorted_categories+=("$category")
    done

    # Display each category with its index
    local i=1
    for category in "${sorted_categories[@]}"; do
        # Count tools in this category
        local count=0
        for tool in "${tools[@]}"; do
            if [[ "$tool" == *":$category:"* ]]; then
                ((count++))
            fi
        done

        echo -e "${MAGENTA}$i)${NC} ${BOLD}${tool_categories[$category]}${NC} (${YELLOW}$count tools${NC})"
        category_list[$i]=$category
        ((i++))
    done

    echo -e "${MAGENTA}a)${NC} ${BOLD}Install all tools${NC} (${YELLOW}${#tools[@]} tools${NC})"
    echo -e "${MAGENTA}q)${NC} ${BOLD}Quit${NC}"
    echo
}

# Function to install all tools
install_all() {
    local total=${#tools[@]}
    local current=0

    clear
    display_header
    echo -e "${BLUE}Installing all development tools (${YELLOW}$total tools${NC})...${NC}"
    sleep 1

    for tool in "${tools[@]}"; do
        if install_tool "$tool"; then
            ((current++))
            loading_bar $current $total
            sleep 1
        else
            echo -e "${RED}Failed to install tool. Press any key to continue...${NC}"
            read -n 1
            ((current++))
        fi
    done

    echo -e "\n${GREEN}All development tools installed.${NC}"
    echo -e "Press any key to return to the main menu..."
    read -n 1
}

# Main function
main() {
    # Check if running with sudo
    check_sudo

    # Detect package manager
    detect_package_manager

    # Create a simple, direct menu
    clear
    display_header

    echo -e "${BOLD}${CYAN}Development Tools Categories:${NC}"
    echo

    # Create a simple indexed array for categories
    categories=("compilers" "build" "scripting" "version_control" "package_managers" "editors" "debuggers" "utilities")
    category_names=("Compilers and Programming Languages" "Build Systems and Tools" "Scripting and Interpreted Languages"
                    "Version Control Systems" "Package Managers" "Code Editors and IDEs"
                    "Debugging and Profiling Tools" "Development Utilities")

    # Display the simple menu
    for i in "${!categories[@]}"; do
        # Count tools in this category
        local count=0
        for tool in "${tools[@]}"; do
            if [[ "$tool" == *":${categories[$i]}:"* ]]; then
                ((count++))
            fi
        done

        echo -e "${MAGENTA}$((i+1)))${NC} ${BOLD}${category_names[$i]}${NC} (${YELLOW}$count tools${NC})"
    done

    echo -e "${MAGENTA}a)${NC} ${BOLD}Install all tools${NC} (${YELLOW}${#tools[@]} tools${NC})"
    echo -e "${MAGENTA}q)${NC} ${BOLD}Quit${NC}"
    echo

    # Get user choice
    echo -n -e "${CYAN}Select an option (1-${#categories[@]} or a/q): ${NC}"
    read -r choice

    case $choice in
        [0-9]*)
            # Convert to zero-based index and check if valid
            local index=$((choice-1))
            if [ "$index" -ge 0 ] && [ "$index" -lt "${#categories[@]}" ]; then
                install_category "${categories[$index]}"
                # After installation, restart the script
                exec "$0"
            else
                echo -e "${RED}Invalid choice. Press any key to continue...${NC}"
                read -n 1
                # Restart the script
                exec "$0"
            fi
            ;;
        a|A)
            install_all
            # After installation, restart the script
            exec "$0"
            ;;
        q|Q)
            clear
            echo -e "${GREEN}Exiting. Thanks for using the Development Tools Installer!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Press any key to continue...${NC}"
            read -n 1
            # Restart the script
            exec "$0"
            ;;
    esac
}

# Run the main function
main
