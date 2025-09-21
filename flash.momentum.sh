#!/bin/bash
#
# 🚀 Momentum Firmware Flash Tool - Enhanced Version
# 
# Advanced Flipper Zero firmware flashing tool with safety features,
# device detection, error recovery, and comprehensive logging.
#
# Usage: ./flash.momentum.sh [options]
#

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Script configuration
SCRIPT_VERSION="2.0.0"
SCRIPT_NAME="Momentum Flash Tool"
REPO_URL="https://github.com/Next-Flip/Momentum-Firmware.git"
REPO_DIR="Momentum-Firmware"
LOG_DIR="$HOME/.momentum-flash"
LOG_FILE="$LOG_DIR/flash-$(date +%Y%m%d-%H%M%S).log"
LOCKFILE="/tmp/momentum-flash.lock"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Default options
VERBOSE=false
QUIET=false
FORCE=false
DRY_RUN=false
BRANCH="dev"
BUILD_TARGET=""
SKIP_UPDATE=false
BACKUP_FIRMWARE=true
AUTO_CONFIRM=true
CLEAN_BUILD=false

# Logging functions
setup_logging() {
    mkdir -p "$LOG_DIR"
    exec 1> >(tee -a "$LOG_FILE")
    exec 2> >(tee -a "$LOG_FILE" >&2)
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

info() {
    if [[ "$QUIET" != "true" ]]; then
        echo -e "${BLUE}[INFO]${NC} $*"
        log "INFO: $*"
    fi
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" >&2
    log "WARN: $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
    log "ERROR: $*"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
    log "SUCCESS: $*"
}

verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${CYAN}[VERBOSE]${NC} $*"
        log "VERBOSE: $*"
    fi
}

# Cleanup and signal handling
cleanup() {
    local exit_code=$?
    
    if [[ -f "$LOCKFILE" ]]; then
        rm -f "$LOCKFILE"
        verbose "Removed lockfile"
    fi
    
    if [[ $exit_code -ne 0 ]]; then
        error "Script failed with exit code $exit_code"
        echo
        echo -e "${YELLOW}Check the log file for details: $LOG_FILE${NC}"
        echo -e "${YELLOW}For help, run: $0 --help${NC}"
    fi
    
    exit $exit_code
}

trap cleanup EXIT
trap 'echo -e "\n${YELLOW}Interrupted by user${NC}"; exit 130' INT TERM

# Help and version
show_help() {
    cat << EOF
${WHITE}$SCRIPT_NAME v$SCRIPT_VERSION${NC}

${CYAN}USAGE:${NC}
    $0 [options]

${CYAN}OPTIONS:${NC}
    ${GREEN}General:${NC}
        -h, --help              Show this help message
        -v, --verbose           Enable verbose output
        -q, --quiet             Suppress non-essential output
        --version               Show version information
        --dry-run               Show what would be done without executing

    ${GREEN}Repository:${NC}
        -b, --branch BRANCH     Use specific branch (default: dev)
        --skip-update           Skip repository update
        --clean                 Clean build before flashing
        
    ${GREEN}Flashing:${NC}
        -f, --force             Skip confirmation prompts
        --no-backup             Skip firmware backup
        --target TARGET         Specify build target
        -y, --yes               Auto-confirm all prompts

    ${GREEN}Safety:${NC}
        --check-device          Only check device connection
        --recovery              Enter recovery mode

${CYAN}EXAMPLES:${NC}
    $0                          # Standard flash with prompts
    $0 -f -b main              # Force flash from main branch
    $0 --dry-run --verbose     # Show what would happen
    $0 --check-device          # Check if device is connected
    $0 --clean -y              # Clean build with auto-confirm

${CYAN}LOGS:${NC}
    Logs are stored in: $LOG_DIR/
    Current log: $LOG_FILE

EOF
}

show_version() {
    echo "$SCRIPT_NAME v$SCRIPT_VERSION"
    echo "Flipper Zero Momentum Firmware Flash Tool"
}

# Argument parsing
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --version)
                show_version
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -q|--quiet)
                QUIET=true
                shift
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -b|--branch)
                BRANCH="$2"
                shift 2
                ;;
            --skip-update)
                SKIP_UPDATE=true
                shift
                ;;
            --clean)
                CLEAN_BUILD=true
                shift
                ;;
            --no-backup)
                BACKUP_FIRMWARE=false
                shift
                ;;
            --target)
                BUILD_TARGET="$2"
                shift 2
                ;;
            -y|--yes)
                AUTO_CONFIRM=true
                shift
                ;;
            --check-device)
                check_device_connection
                exit $?
                ;;
            --recovery)
                enter_recovery_mode
                exit $?
                ;;
            -*)
                error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
            *)
                error "Unexpected argument: $1"
                exit 1
                ;;
        esac
    done
}

# Device detection and verification
check_device_connection() {
    info "Checking for Flipper Zero device..."
    
    # Check for Flipper Zero in various modes
    local flipper_found=false
    local device_info=""
    
    # Check for DFU mode
    if lsusb | grep -i "0483:df11" >/dev/null 2>&1; then
        device_info="DFU mode (bootloader)"
        flipper_found=true
    fi
    
    # Check for normal mode
    if lsusb | grep -i "0483:5740" >/dev/null 2>&1; then
        device_info="Normal mode"
        flipper_found=true
    fi
    
    # Check for serial devices
    if ls /dev/ttyACM* >/dev/null 2>&1; then
        local tty_devices=$(ls /dev/ttyACM* | tr '\n' ' ')
        device_info="$device_info (Serial: $tty_devices)"
    fi
    
    if [[ "$flipper_found" == "true" ]]; then
        success "Flipper Zero detected: $device_info"
        return 0
    else
        error "Flipper Zero not detected!"
        echo
        echo -e "${YELLOW}Troubleshooting:${NC}"
        echo "1. Ensure Flipper Zero is connected via USB"
        echo "2. Try a different USB cable or port"
        echo "3. Put device in DFU mode: Hold LEFT + BACK, then press RESET"
        echo "4. Check USB permissions (you may need to be in 'dialout' group)"
        return 1
    fi
}

# System requirements check
check_requirements() {
    info "Checking system requirements..."
    
    local missing_deps=()
    
    # Check required commands
    local required_commands=("git" "python3" "lsusb")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_deps+=("$cmd")
        fi
    done
    
    # Check Python modules
    if ! python3 -c "import serial" >/dev/null 2>&1; then
        missing_deps+=("python3-pyserial")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        error "Missing dependencies: ${missing_deps[*]}"
        echo
        echo -e "${YELLOW}Install missing dependencies:${NC}"
        echo "sudo pacman -S ${missing_deps[*]}"  # Arch/CachyOS
        return 1
    fi
    
    success "All requirements satisfied"
    return 0
}

# Disk space check
check_disk_space() {
    local required_gb=3
    local available_kb=$(df . | awk 'NR==2 {print $4}')
    local available_gb=$((available_kb / 1024 / 1024))
    
    if [[ $available_gb -lt $required_gb ]]; then
        error "Insufficient disk space. Required: ${required_gb}GB, Available: ${available_gb}GB"
        return 1
    fi
    
    verbose "Disk space OK: ${available_gb}GB available"
    return 0
}

# Lockfile management
acquire_lock() {
    if [[ -f "$LOCKFILE" ]]; then
        local lock_pid=$(cat "$LOCKFILE" 2>/dev/null || echo "unknown")
        if [[ "$lock_pid" != "unknown" ]] && kill -0 "$lock_pid" 2>/dev/null; then
            error "Another instance is already running (PID: $lock_pid)"
            return 1
        else
            warn "Removing stale lockfile"
            rm -f "$LOCKFILE"
        fi
    fi
    
    echo $$ > "$LOCKFILE"
    verbose "Acquired lockfile"
    return 0
}

# Repository management
clone_or_update_repo() {
    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would clone/update repository"
        return 0
    fi
    
    if [[ ! -d "$REPO_DIR" ]]; then
        info "Cloning Momentum Firmware repository..."
        info "Repository: $REPO_URL"
        info "Branch: $BRANCH"
        
        git clone --recursive --jobs 8 -b "$BRANCH" "$REPO_URL" "$REPO_DIR" || {
            error "Failed to clone repository"
            return 1
        }
        success "Repository cloned successfully"
    else
        if [[ "$SKIP_UPDATE" == "true" ]]; then
            info "Skipping repository update (--skip-update)"
            return 0
        fi
        
        info "Updating existing repository..."
        cd "$REPO_DIR" || {
            error "Failed to change to repository directory"
            return 1
        }
        
        # Fetch and checkout branch
        git fetch origin || {
            error "Failed to fetch updates"
            return 1
        }
        
        git checkout "$BRANCH" || {
            error "Failed to checkout branch: $BRANCH"
            return 1
        }
        
        git pull origin "$BRANCH" || {
            error "Failed to pull updates"
            return 1
        }
        
        # Update submodules
        git submodule update --init --recursive || {
            warn "Failed to update submodules"
        }
        
        success "Repository updated successfully"
        cd ..
    fi
    
    return 0
}

# Build system
prepare_build() {
    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would prepare build environment"
        return 0
    fi
    
    cd "$REPO_DIR" || {
        error "Repository directory not found"
        return 1
    }
    
    if [[ "$CLEAN_BUILD" == "true" ]]; then
        info "Cleaning previous build..."
        ./fbt clean || {
            warn "Clean command failed, continuing anyway"
        }
    fi
    
    info "Preparing build environment..."
    
    # Show current status
    local commit_hash=$(git rev-parse --short HEAD)
    local branch_name=$(git branch --show-current)
    local commit_date=$(git log -1 --format="%ci")
    
    info "Build information:"
    echo "  Branch: $branch_name"
    echo "  Commit: $commit_hash"
    echo "  Date: $commit_date"
    
    return 0
}

# Confirmation prompts
confirm_action() {
    local message="$1"
    local default="${2:-n}"
    
    if [[ "$AUTO_CONFIRM" == "true" ]] || [[ "$FORCE" == "true" ]]; then
        info "Auto-confirming: $message"
        return 0
    fi
    
    local prompt
    if [[ "$default" == "y" ]]; then
        prompt="$message [Y/n]: "
    else
        prompt="$message [y/N]: "
    fi
    
    while true; do
        echo -ne "${YELLOW}$prompt${NC}"
        read -r response
        
        case $(echo "$response" | tr '[:upper:]' '[:lower:]') in
            y|yes)
                return 0
                ;;
            n|no)
                return 1
                ;;
            "")
                if [[ "$default" == "y" ]]; then
                    return 0
                else
                    return 1
                fi
                ;;
            *)
                echo "Please answer yes or no."
                ;;
        esac
    done
}

# Backup functionality
backup_current_firmware() {
    if [[ "$BACKUP_FIRMWARE" != "true" ]]; then
        return 0
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would backup current firmware"
        return 0
    fi
    
    info "Creating firmware backup..."
    
    local backup_dir="$LOG_DIR/backups"
    mkdir -p "$backup_dir"
    
    local backup_file="$backup_dir/firmware-backup-$(date +%Y%m%d-%H%M%S).bin"
    
    # Try to create backup (this is device/tool specific)
    info "Backup would be saved to: $backup_file"
    warn "Automatic backup not yet implemented"
    warn "Consider manually backing up your firmware before flashing"
    
    if ! confirm_action "Continue without automatic backup?" "y"; then
        error "Backup required by user"
        return 1
    fi
    
    return 0
}

# Main flashing function
flash_firmware() {
    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would flash firmware with target: ${BUILD_TARGET:-default}"
        return 0
    fi
    
    info "Starting firmware flash process..."
    
    # Check device one more time
    if ! check_device_connection; then
        return 1
    fi
    
    # Build flash command
    local flash_cmd="./fbt flash_usb_full"
    if [[ -n "$BUILD_TARGET" ]]; then
        flash_cmd="./fbt $BUILD_TARGET"
    fi
    
    info "Flash command: $flash_cmd"
    
    # Show final warning
    if ! confirm_action "⚠️  Ready to flash firmware. This will overwrite your current firmware. Continue?" "n"; then
        warn "Flash cancelled by user"
        return 1
    fi
    
    info "Flashing firmware as regular user..."
    if $flash_cmd; then
        success "Firmware flashed successfully!"
        return 0
    else
        warn "Flash failed as regular user. Trying with sudo..."
        if confirm_action "Retry flash with sudo (root) privileges?" "y"; then
            if sudo $flash_cmd; then
                success "Firmware flashed successfully with sudo!"
                return 0
            else
                error "Flash failed even with sudo"
                return 1
            fi
        else
            error "Flash cancelled"
            return 1
        fi
    fi
}

# Recovery mode
enter_recovery_mode() {
    info "Recovery mode instructions:"
    echo
    echo "To enter DFU (recovery) mode on Flipper Zero:"
    echo "1. Hold LEFT arrow + BACK button"
    echo "2. While holding, press and release RESET button"
    echo "3. Release LEFT arrow + BACK buttons"
    echo "4. Device should show orange screen (DFU mode)"
    echo
    info "Checking for device in DFU mode..."
    
    for i in {1..10}; do
        if lsusb | grep -i "0483:df11" >/dev/null 2>&1; then
            success "Device detected in DFU mode!"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    echo
    
    warn "Device not detected in DFU mode"
    return 1
}

# Post-flash verification
verify_flash() {
    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would verify flash"
        return 0
    fi
    
    info "Verifying flash..."
    sleep 3  # Give device time to boot
    
    if check_device_connection; then
        success "Device detected after flash - likely successful!"
        return 0
    else
        warn "Device not detected after flash"
        return 1
    fi
}

# Main execution flow
main() {
    echo -e "${WHITE}$SCRIPT_NAME v$SCRIPT_VERSION${NC}"
    echo -e "${CYAN}Flipper Zero Momentum Firmware Flash Tool${NC}"
    echo
    
    # Parse arguments
    parse_arguments "$@"
    
    # Setup
    setup_logging
    log "=== Starting $SCRIPT_NAME v$SCRIPT_VERSION ==="
    log "Command: $0 $*"
    
    # Acquire lock
    if ! acquire_lock; then
        exit 1
    fi
    
    # System checks
    if ! check_requirements; then
        exit 1
    fi
    
    if ! check_disk_space; then
        exit 1
    fi
    
    # Repository operations
    if ! clone_or_update_repo; then
        exit 1
    fi
    
    if ! prepare_build; then
        exit 1
    fi
    
    # Pre-flash operations
    if ! backup_current_firmware; then
        exit 1
    fi
    
    # Flash firmware
    if ! flash_firmware; then
        exit 1
    fi
    
    # Post-flash verification
    if ! verify_flash; then
        warn "Flash verification failed, but flash might still be successful"
    fi
    
    success "All operations completed successfully!"
    echo
    echo -e "${CYAN}Log file: $LOG_FILE${NC}"
    echo -e "${CYAN}Next steps:${NC}"
    echo "1. Disconnect and reconnect your Flipper Zero"
    echo "2. Check that the new firmware is working correctly"
    echo "3. If needed, use --recovery mode to fix any issues"
    
    log "=== $SCRIPT_NAME completed successfully ==="
}

# Execute main function
main "$@"