#!/bin/bash
#
# 🚀 Momentum Firmware Flash Tool - UI Enhanced
# 
# Features: Interactive Menu, ASCII Art, Full Git History, Visual feedback.
#

set -uo pipefail

# --- Configuration ---
SCRIPT_VERSION="4.0.0"
REPO_URL="https://github.com/Next-Flip/Momentum-Firmware.git"
REPO_DIR="Momentum-Firmware"
DEFAULT_BRANCH="dev"

# --- Styling & Colors ---
BOLD='\033[1m'
DIM='\033[2m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# --- Visual Helpers ---

print_banner() {
    clear
    echo -e "${PURPLE}${BOLD}"
    cat << "EOF"
  __  __                                 _                     
 |  \/  |  ___   _ __ ___    ___  _ __  | |_  _   _  _ __ ___  
 | |\/| | / _ \ | '_ ` _ \  / _ \| '_ \ | __|| | | || '_ ` _ \ 
 | |  | || (_) || | | | | ||  __/| | | || |_ | |_| || | | | | |
 |_|  |_| \___/ |_| |_| |_| \___||_| |_| \__| \__,_||_| |_| |_|
                                                               
EOF
    echo -e "${CYAN}      :: Firmware Flash Tool v${SCRIPT_VERSION} ::${NC}"
    echo -e "${DIM}      Running on $(uname -s) | Branch: ${BRANCH:-$DEFAULT_BRANCH}${NC}"
    echo -e "${BLUE}===============================================================${NC}"
    echo ""
}

log()     { echo -e "  ${BLUE}ℹ${NC}  $1"; }
task()    { echo -e "  ${PURPLE}➜${NC}  ${BOLD}$1${NC}"; }
subtask() { echo -e "      ${DIM}└─ $1${NC}"; }
warn()    { echo -e "  ${YELLOW}⚠  WARNING:${NC} $1"; }
error()   { echo -e "  ${RED}✖  ERROR:${NC} $1"; exit 1; }
success() { echo -e "  ${GREEN}✔  SUCCESS:${NC} $1"; }
divider() { echo -e "${BLUE}---------------------------------------------------------------${NC}"; }

# --- Core Functions ---

check_deps() {
    command -v git >/dev/null 2>&1 || error "Git is required but not installed."
}

manage_repo() {
    local target_branch="${1:-$DEFAULT_BRANCH}"
    
    divider
    task "Checking Repository Status"
    
    if [[ ! -d "$REPO_DIR" ]]; then
        log "Repository not found. Cloning full history..."
        subtask "URL: $REPO_URL"
        subtask "Branch: $target_branch"
        
        # FULL DEPTH CLONE (No --depth 1)
        git clone --recursive --branch "$target_branch" "$REPO_URL" "$REPO_DIR" || error "Clone failed."
        success "Repository cloned."
    else
        log "Repository found. Updating..."
        cd "$REPO_DIR" || error "Cannot enter dir"
        
        # Safe update procedure
        git stash >/dev/null 2>&1
        subtask "Fetching updates..."
        git fetch origin "$target_branch" || error "Fetch failed"
        
        subtask "Checking out $target_branch..."
        git checkout "$target_branch" >/dev/null 2>&1 || error "Checkout failed"
        
        subtask "Pulling latest changes..."
        git pull origin "$target_branch" >/dev/null 2>&1 || error "Pull failed"
        
        subtask "Updating submodules..."
        git submodule update --init --recursive >/dev/null 2>&1
        
        success "Repository updated."
        cd ..
    fi
}

run_flash() {
    local build_target="${1:-flash_usb_full}"
    local clean="${2:-false}"
    
    cd "$REPO_DIR" || error "Repo directory missing."
    chmod +x fbt

    divider
    task "Starting Build Process"
    
    if [[ "$clean" == "true" ]]; then
        subtask "Cleaning build environment..."
        ./fbt clean >/dev/null
    fi

    echo -e "\n  ${YELLOW}⚡ READY TO FLASH${NC}"
    echo -e "  ${DIM}Connect your Flipper Zero via USB now.${NC}"
    
    # If not forcing, we pause for user
    if [[ "${FORCE:-false}" != "true" ]]; then
        read -p "  Press [Enter] to begin..."
    fi
    echo ""

    task "Compiling and Flashing ($build_target)..."
    # Capture output to hide noise unless error? No, users like to see build progress.
    # We will let fbt output run but indent it slightly if possible, or just run it.
    
    if ./fbt "$build_target"; then
        echo ""
        divider
        success "Flash Complete! Enjoy Momentum."
        echo ""
        exit 0
    else
        echo ""
        divider
        warn "Standard flash failed."
        
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            echo -e "  ${CYAN}hint:${NC} Linux users often need sudo for USB access."
            read -p "  Retry with sudo? [Y/n] " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                sudo ./fbt "$build_target" || error "Flash failed even with sudo."
                success "Flash Complete (via sudo)!"
                exit 0
            fi
        fi
        error "Flash failed."
    fi
}

enter_recovery() {
    divider
    echo -e "${RED}${BOLD}  🚑  DFU RECOVERY MODE${NC}"
    echo -e "  ${DIM}Use this if your device is bricked or won't boot.${NC}"
    echo ""
    echo -e "  ${BOLD}Steps:${NC}"
    echo "  1. Unplug USB."
    echo "  2. Hold [LEFT] + [BACK]."
    echo "  3. Press [RESET] once, then release [LEFT] + [BACK]."
    echo "  4. Screen should be black/orange."
    echo "  5. Plug in USB."
    echo ""
    read -p "  Press [Enter] when device is ready..."
    
    cd "$REPO_DIR" || error "Repo missing."
    ./fbt flash_usb_full
}

show_menu() {
    while true; do
        print_banner
        echo -e "  ${BOLD}Select an action:${NC}"
        echo ""
        echo -e "  ${CYAN}[1]${NC} 🔥 Flash Firmware (Standard)"
        echo -e "  ${CYAN}[2]${NC} 🧹 Clean Build & Flash"
        echo -e "  ${CYAN}[3]${NC} 🔄 Update Repository Only"
        echo -e "  ${CYAN}[4]${NC} 🚑 DFU Recovery Mode"
        echo -e "  ${CYAN}[Q]${NC} 🚪 Quit"
        echo ""
        read -p "  Option: " choice
        
        case $choice in
            1) 
                manage_repo "$DEFAULT_BRANCH"
                run_flash "flash_usb_full" "false"
                ;;
            2)
                manage_repo "$DEFAULT_BRANCH"
                run_flash "flash_usb_full" "true"
                ;;
            3)
                manage_repo "$DEFAULT_BRANCH"
                read -p "  Update done. Press Enter..."
                ;;
            4)
                manage_repo "$DEFAULT_BRANCH"
                enter_recovery
                ;;
            q|Q) 
                echo -e "  Bye!"
                exit 0 
                ;;
            *) 
                echo -e "  ${RED}Invalid option.${NC}"
                sleep 1
                ;;
        esac
    done
}

# --- Main Execution ---

check_deps

# If arguments are provided, skip menu and process them (Automation mode)
if [[ $# -gt 0 ]]; then
    BRANCH="$DEFAULT_BRANCH"
    CLEAN=false
    TARGET="flash_usb_full"
    FORCE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -b|--branch) BRANCH="$2"; shift 2 ;;
            -c|--clean) CLEAN=true; shift ;;
            -f|--force) FORCE=true; shift ;;
            -t|--target) TARGET="$2"; shift 2 ;;
            --recovery) 
                manage_repo "$BRANCH"
                enter_recovery 
                exit 0
                ;;
            *) shift ;;
        esac
    done
    
    manage_repo "$BRANCH"
    run_flash "$TARGET" "$CLEAN"
else
    # Interactive Mode
    BRANCH="$DEFAULT_BRANCH"
    show_menu
fi
