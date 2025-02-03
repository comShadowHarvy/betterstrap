#!/bin/bash

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to detect package manager
detect_package_manager() {
    if command -v apt &>/dev/null; then
        PKG_MANAGER="apt"
        PKG_CHECK="dpkg -l"
        PKG_INSTALL="sudo apt install -y"
    elif command -v dnf &>/dev/null; then
        PKG_MANAGER="dnf"
        PKG_CHECK="rpm -q"
        PKG_INSTALL="sudo dnf install -y"
    elif command -v pacman &>/dev/null; then
        PKG_MANAGER="pacman"
        PKG_CHECK="pacman -Qs"
        PKG_INSTALL="sudo pacman -S --needed --noconfirm"
    else
        echo -e "${RED}Error: No supported package manager found${NC}"
        exit 1
    fi
}

# Enhanced loading bar with colors and spinner
loading_bar() {
    local current=$1
    local total=$2
    local percent=$(( 100 * current / total ))
    local bar_length=30
    local filled_length=$(( bar_length * current / total ))
    local empty_length=$(( bar_length - filled_length ))
    local spinner=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
    local spin_index=$(( current % ${#spinner[@]} ))

    printf -v bar "%0.s#" $(seq 1 $filled_length)
    printf -v space "%0.s " $(seq 1 $empty_length)

    echo -ne "Progress: [${bar}${space}] (${percent}%%) ${spinner[$spin_index]}\r"
}

# Function to check if a package is installed
is_package_installed() {
    $PKG_CHECK $1 > /dev/null
}

# Function to display the header
display_header() {
    clear
    echo "============================="
    echo "  Development Tools Installer"
    echo "============================="
    echo
}

# Function to display a description
display_description() {
    local title=$1
    local description=$2
    local advantages=$3
    local disadvantages=$4

    tput cup 4 0
    echo "============================="
    echo "   $title"
    echo "============================="
    echo
    echo "Description:"
    echo "$description"
    echo
    echo "Advantages:"
    echo -e "$advantages"
    echo
    echo "Disadvantages:"
    echo -e "$disadvantages"
    echo
    echo "----------------------------------"
    echo
}

total_steps=10
current_step=0

display_header

# List of development tools to install
tools=(
    "gcc:GNU Compiler Collection for C, C++, and more:- Wide language support.\n- Strong optimization features.:- Can be slower than Clang for some tasks."
    "clang:Clang/LLVM Compiler for C, C++, and more:- Fast and modular.\n- Good diagnostics and error messages.:- Less mature than GCC in some areas."
    "rust:Rust programming language and compiler:- Safe memory management.\n- Modern features.:- Newer, with less library support than C++."
    "go:Golang programming language and compiler:- Fast compile times.\n- Excellent concurrency support.:- Somewhat limited language features."
    "cmake:Cross-platform build system generator:- Versatile and widely supported.:- Complex syntax."
    "meson:Modern build system designed for speed:- Simple to use.\n- Fast.:- Newer, with smaller community."
    "make:Build automation tool:- Ubiquitous and powerful.:- Can be complex for large projects."
    "python:Python programming language interpreter:- Versatile and widely used.\n- Extensive libraries.:- Slower execution compared to compiled languages."
    "git:Distributed version control system:- Essential for version control.\n- Strong community support.:- Requires command-line knowledge."
    "nix:Powerful package manager for reproducible builds:- Reproducibility.\n- Multi-user environment support.:- Requires learning Nix syntax."
)

# Function to install a tool
install_tool() {
    local tool=$1
    local name=$(echo $tool | cut -d: -f1)
    local description=$(echo $tool | cut -d: -f2)
    local advantages=$(echo $tool | cut -d: -f3)
    local disadvantages=$(echo $tool | cut -d: -f4)

    clear
    display_description "Installing $name" "$description" "$advantages" "$disadvantages"
    sleep 7
    if is_package_installed "$name"; then
        echo "$name is already installed."
    else
        $PKG_INSTALL $name
        echo -ne "\n$name installed.\n"
    fi
    loading_bar $((++current_step)) $total_steps
}

# Detect package manager
detect_package_manager

# Install each tool
for tool in "${tools[@]}"; do
    install_tool "$tool"
done

loading_bar $total_steps $total_steps
echo -ne '\nAll development tools installed.\n'
