#!/bin/bash
#
# 🚀 Momentum Firmware Flash Tool - Professional Edition
# 
# Features: Full Git History, Recovery Mode, Auto-Update, Safe Flashing.
#

set -uo pipefail

# Configuration
SCRIPT_VERSION="3.1.0"
REPO_URL="https://github.com/Next-Flip/Momentum-Firmware.git"
REPO_DIR="Momentum-Firmware"
BRANCH="dev"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# --- Helper Functions ---

log() { echo -e "${BLUE}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

show_help() {
    cat << EOF
Momentum Flash Tool v$SCRIPT_VERSION (Full Depth)

Usage: ./flash.momentum.sh [options]

Options:
  -b, --branch <name>   Set branch (default: dev)
  -c, --clean           Clean build environment before compiling
  -f, --force           Skip confirmation prompts
  -t, --target <name>   Specify build target (default: flash_usb_full)
  --recovery            Enter DFU/Recovery helper mode
  -h, --help            Show this help

EOF
}

# --- DFU / Recovery Mode ---
# Helps users fix a bricked Flipper
enter_recovery_mode() {
    echo -e "${RED}=== RECOVERY MODE ===${NC}"
    echo "This mode is used to recover a Flipper Zero that won't boot."
    echo ""
    echo -e "${CYAN}Instructions to enter DFU mode:${NC}"
    echo "1. Disconnect Flipper from USB."
    echo "2. Hold [LEFT] + [BACK] buttons simultaneously."
    echo "3. While holding, press and release [RESET]."
    echo "4. Release [LEFT] + [BACK]. The screen should remain dark/orange."
    echo "5. Connect to USB."
    echo ""
    read -p "Press Enter when you have connected the device in DFU mode..."
    
    log "Attempting to flash in DFU mode..."
    # We use 'flash_usb_full' which handles DFU if detected by fbt
    ./fbt flash_usb_full
    
    if [[ $? -eq 0 ]]; then
        success "Recovery Flash Complete!"
        exit 0
    else
        err "Recovery failed. Ensure the device is recognized by your OS (check lsusb/System Report)."
    fi
}

# --- Main Logic ---

# Default State
CLEAN_BUILD=false
FORCE=false
BUILD_TARGET="flash_usb_full"
RECOVERY_MODE=false

# Parse Args
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--branch) BRANCH="$2"; shift 2 ;;
        -c|--clean) CLEAN_BUILD=true; shift ;;
        -f|--force) FORCE=true; shift ;;
        -t|--target) BUILD_TARGET="$2"; shift 2 ;;
        --recovery) RECOVERY_MODE=true; shift ;;
        -h|--help) show_help; exit 0 ;;
        *) err "Unknown option: $1" ;;
    esac
done

# 1. Dependency Check
command -v git >/dev/null 2>&1 || err "Git is not installed."

# 2. Repository Management (Full Depth)
if [[ ! -d "$REPO_DIR" ]]; then
    log "Cloning Momentum Firmware (Full History)..."
    log "This may take a moment as we are downloading the complete repository."
    # Removed --depth 1 to ensure full history
    git clone --recursive --branch "$BRANCH" "$REPO_URL" "$REPO_DIR" || err "Git clone failed"
else
    log "Updating Momentum Firmware..."
    cd "$REPO_DIR" || err "Could not enter directory"
    
    # Stash local changes to prevent conflicts during update
    git stash >/dev/null 2>&1
    
    # Standard git pull for full history management
    git fetch origin "$BRANCH" || err "Git fetch failed"
    git checkout "$BRANCH" || err "Git checkout failed"
    git pull origin "$BRANCH" || err "Git pull failed"
    
    # Update submodules (recursive, no depth limit)
    git submodule update --init --recursive || warn "Submodule update had issues"
    
    cd ..
fi

# 3. Enter Repo
cd "$REPO_DIR" || err "Missing repo directory"
chmod +x fbt

# 4. Handle Recovery Mode Request
if [[ "$RECOVERY_MODE" == "true" ]]; then
    enter_recovery_mode
fi

# 5. Build & Flash
if [[ "$CLEAN_BUILD" == "true" ]]; then
    log "Cleaning build environment..."
    ./fbt clean
fi

log "Starting Build & Flash process for target: $BUILD_TARGET"

if [[ "$FORCE" != "true" ]]; then
    read -p "⚠️  Connect Flipper via USB now. Press Enter to start..."
fi

# Try to flash
if ./fbt "$BUILD_TARGET"; then
    success "Flash Complete!"
    exit 0
else
    EXIT_CODE=$?
    echo ""
    warn "Standard flash failed (Exit Code: $EXIT_CODE)."
    
    # Linux Permission Logic
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        warn "Permission denied? Trying sudo..."
        if sudo ./fbt "$BUILD_TARGET"; then
             success "Flash Complete (via sudo)!"
             exit 0
        fi
    fi
    
    err "Flash process failed."
fi
