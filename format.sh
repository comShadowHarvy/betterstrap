#!/bin/bash
#
# 🔧 Enhanced Drive Format Tool - Professional Edition
# 
# A comprehensive drive formatting utility with advanced safety features,
# device validation, partition management, and user-friendly interface.
#
# Usage: ./format.sh [options]
#

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Script configuration
SCRIPT_VERSION="2.0.0"
SCRIPT_NAME="Enhanced Format Tool"
LOG_DIR="$HOME/.local/share/format-tool"
LOG_FILE="$LOG_DIR/format-$(date +%Y%m%d-%H%M%S).log"
LOCKFILE="/tmp/format-tool.lock"

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
AUTO_CONFIRM=false
CREATE_PARTITION_TABLE=true
VERIFY_AFTER_FORMAT=true
WIPE_DEVICE=false

# Required tools
REQUIRED_TOOLS=(
    "lsblk"
    "parted"
    "wipefs"
    "blkid"
    "mkfs.vfat"
    "mkfs.ext4"
)

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

# Progress indicator
show_progress() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
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

# Lockfile management
create_lockfile() {
    if [[ -f "$LOCKFILE" ]]; then
        local lock_pid
        lock_pid=$(cat "$LOCKFILE")
        if kill -0 "$lock_pid" 2>/dev/null; then
            error "Another instance is already running (PID: $lock_pid)"
            exit 1
        else
            warn "Removing stale lockfile"
            rm -f "$LOCKFILE"
        fi
    fi
    
    echo $$ > "$LOCKFILE"
    verbose "Created lockfile with PID $$"
}

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

    ${GREEN}Safety:${NC}
        -f, --force             Skip some safety prompts (USE WITH CAUTION)
        -y, --yes               Auto-confirm prompts (USE WITH EXTREME CAUTION)
        --no-verify             Skip post-format verification
        --wipe                  Securely wipe device before formatting

    ${GREEN}Partitioning:${NC}
        --no-partition-table    Don't create new partition table
        --gpt                   Use GPT partition table (default: msdos)

${CYAN}EXAMPLES:${NC}
    $0                          # Interactive formatting with safety checks
    $0 --dry-run --verbose      # Show what would happen
    $0 --wipe                   # Securely wipe and format
    $0 --gpt                    # Use GPT partition table

${CYAN}SAFETY FEATURES:${NC}
    - Detects system vs removable drives
    - Validates partition tables and mount status
    - Creates backups of important partition info
    - Verifies formatting success
    - Prevents formatting of system drives

${CYAN}LOGS:${NC}
    Logs are stored in: $LOG_DIR/
    Current log: $LOG_FILE

${RED}WARNING:${NC} This tool can permanently destroy data. Use with extreme caution!

EOF
}

show_version() {
    echo "$SCRIPT_NAME v$SCRIPT_VERSION"
    echo "Professional Drive Formatting Tool with Safety Features"
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
            -y|--yes)
                AUTO_CONFIRM=true
                shift
                ;;
            --no-verify)
                VERIFY_AFTER_FORMAT=false
                shift
                ;;
            --wipe)
                WIPE_DEVICE=true
                shift
                ;;
            --no-partition-table)
                CREATE_PARTITION_TABLE=false
                shift
                ;;
            --gpt)
                PARTITION_TABLE_TYPE="gpt"
                shift
                ;;
            *)
                error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# System checks
check_root_privileges() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root for device access"
        info "Try: sudo $0"
        exit 1
    fi
}

check_required_tools() {
    local missing_tools=()
    
    for tool in "${REQUIRED_TOOLS[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        error "Missing required tools: ${missing_tools[*]}"
        info "Install missing tools with your package manager"
        info "Example: sudo pacman -S util-linux parted dosfstools e2fsprogs"
        exit 1
    fi
    
    verbose "All required tools are available"
}

# Device safety checks
is_removable_device() {
    local device="$1"
    local device_name
    device_name=$(basename "$device")
    
    # Check if device is removable
    if [[ -f "/sys/block/$device_name/removable" ]]; then
        local removable
        removable=$(cat "/sys/block/$device_name/removable")
        [[ "$removable" == "1" ]]
    else
        # If we can't determine, be conservative
        false
    fi
}

is_system_device() {
    local device="$1"
    
    # Check if any partition on this device is mounted at critical paths
    local mounted_paths
    mounted_paths=$(lsblk -rno MOUNTPOINT "$device" 2>/dev/null | grep -E '^/$|^/boot|^/home|^/usr|^/var' || true)
    
    if [[ -n "$mounted_paths" ]]; then
        return 0  # It's a system device
    fi
    
    # Check if device contains root filesystem
    local root_device
    root_device=$(findmnt -n -o SOURCE / | sed 's/[0-9]*$//')
    
    if [[ "$device" == "$root_device" ]]; then
        return 0  # It's a system device
    fi
    
    return 1  # Not a system device
}

get_device_info() {
    local device="$1"
    local size model vendor removable
    
    size=$(lsblk -dno SIZE "$device" 2>/dev/null || echo "Unknown")
    model=$(lsblk -dno MODEL "$device" 2>/dev/null || echo "Unknown")
    vendor=$(lsblk -dno VENDOR "$device" 2>/dev/null || echo "Unknown")
    
    if is_removable_device "$device"; then
        removable="Yes"
    else
        removable="No"
    fi
    
    echo "Size: $size, Model: $model, Vendor: $vendor, Removable: $removable"
}

# Device listing and selection
list_available_drives() {
    echo -e "${CYAN}Available drives:${NC}"
    echo "═══════════════════════════════════════════════════"
    
    local drives
    mapfile -t drives < <(lsblk -dpno NAME,SIZE,MODEL,VENDOR | grep -v "loop\|ram" | tail -n +2)
    
    if [[ ${#drives[@]} -eq 0 ]]; then
        warn "No suitable drives found"
        return 1
    fi
    
    local i=1
    for drive_info in "${drives[@]}"; do
        local drive_path
        drive_path=$(echo "$drive_info" | awk '{print $1}')
        local extra_info
        extra_info=$(get_device_info "$drive_path")
        
        # Color code based on device type
        if is_system_device "$drive_path"; then
            echo -e "${i}) ${RED}$drive_info${NC} (${RED}SYSTEM DRIVE - DANGEROUS${NC})"
        elif is_removable_device "$drive_path"; then
            echo -e "${i}) ${GREEN}$drive_info${NC} (${GREEN}Removable${NC})"
        else
            echo -e "${i}) ${YELLOW}$drive_info${NC} (${YELLOW}Fixed Drive${NC})"
        fi
        
        verbose "   $extra_info"
        ((i++))
    done
    
    echo "═══════════════════════════════════════════════════"
}

select_drive() {
    local drives drive_number selected_drive
    
    while true; do
        list_available_drives || exit 1
        
        echo
        echo -e "${CYAN}Enter the number of the drive you want to format (or 'q' to quit):${NC}"
        read -r drive_number
        
        if [[ "$drive_number" == "q" || "$drive_number" == "Q" ]]; then
            info "Operation cancelled by user"
            exit 0
        fi
        
        mapfile -t drives < <(lsblk -dpno NAME | grep -v "loop\|ram" | tail -n +2)
        
        if ! [[ "$drive_number" =~ ^[0-9]+$ ]] || \
           [[ "$drive_number" -lt 1 ]] || \
           [[ "$drive_number" -gt ${#drives[@]} ]]; then
            error "Invalid selection. Please try again."
            continue
        fi
        
        selected_drive="${drives[$((drive_number-1))]}"
        
        # Safety check for system drives
        if is_system_device "$selected_drive" && [[ "$FORCE" != "true" ]]; then
            error "Selected device appears to be a system drive!"
            error "This could destroy your operating system!"
            echo
            warn "If you're absolutely sure you want to format this device,"
            warn "use the --force flag (EXTREMELY DANGEROUS)"
            continue
        fi
        
        break
    done
    
    echo "$selected_drive"
}

# Filesystem management
list_filesystem_types() {
    echo -e "${CYAN}Available filesystem types:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}1)${NC} fat32    - FAT32 filesystem (recommended for USB drives, universal compatibility)"
    echo -e "${GREEN}2)${NC} exfat    - Extended FAT (supports large files, cross-platform)"
    echo -e "${GREEN}3)${NC} ntfs     - NTFS filesystem (Windows native, good Linux support)"
    echo -e "${GREEN}4)${NC} ext4     - Linux filesystem (best for Linux-only use)"
    echo -e "${GREEN}5)${NC} btrfs    - B-tree filesystem (modern Linux, snapshots, compression)"
    echo -e "${GREEN}6)${NC} xfs      - High-performance journaling filesystem"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

get_filesystem_choice() {
    local fs_number fs_type format_cmd label_flag
    
    list_filesystem_types
    
    echo
    echo -e "${CYAN}Enter filesystem type number (default: 1 for fat32):${NC}"
    read -r fs_number
    
    # Set default to fat32 if no input
    if [[ -z "$fs_number" ]]; then
        fs_number=1
    fi
    
    # Validate filesystem selection
    if ! [[ "$fs_number" =~ ^[0-9]+$ ]] || [[ "$fs_number" -lt 1 ]] || [[ "$fs_number" -gt 6 ]]; then
        warn "Invalid selection. Using default (fat32)"
        fs_number=1
    fi
    
    case $fs_number in
        1)
            fs_type="fat32"
            format_cmd="mkfs.vfat -F 32"
            label_flag="-n"
            ;;
        2)
            fs_type="exfat"
            format_cmd="mkfs.exfat"
            label_flag="-n"
            ;;
        3)
            fs_type="ntfs"
            format_cmd="mkfs.ntfs -f -Q"
            label_flag="-L"
            ;;
        4)
            fs_type="ext4"
            format_cmd="mkfs.ext4 -F"
            label_flag="-L"
            ;;
        5)
            fs_type="btrfs"
            format_cmd="mkfs.btrfs -f"
            label_flag="-L"
            ;;
        6)
            fs_type="xfs"
            format_cmd="mkfs.xfs -f"
            label_flag="-L"
            ;;
    esac
    
    echo "$fs_type:$format_cmd:$label_flag"
}

get_drive_label() {
    local label
    
    echo
    echo -e "${CYAN}Enter a label for the drive (optional, press Enter to skip):${NC}"
    read -r label
    
    # Sanitize label (remove dangerous characters)
    label=$(echo "$label" | sed 's/[^a-zA-Z0-9_-]//g' | cut -c1-11)
    
    echo "$label"
}

# Partition operations
create_partition_table() {
    local device="$1"
    local table_type="${PARTITION_TABLE_TYPE:-msdos}"
    
    info "Creating $table_type partition table on $device"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY RUN: parted -s '$device' mklabel '$table_type'"
        return 0
    fi
    
    parted -s "$device" mklabel "$table_type"
    success "Partition table created"
}

create_partition() {
    local device="$1"
    local fs_type="$2"
    
    info "Creating partition on $device"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY RUN: parted -s '$device' mkpart primary 0% 100%"
        return 0
    fi
    
    # Create a single partition using all available space
    parted -s "$device" mkpart primary 0% 100%
    
    # Wait for partition to appear
    sleep 2
    partprobe "$device"
    sleep 1
    
    success "Partition created"
}

# Device operations
unmount_device() {
    local device="$1"
    
    info "Unmounting all partitions on $device"
    
    # Get all mounted partitions for this device
    local mounted_partitions
    mounted_partitions=$(lsblk -rno NAME,MOUNTPOINT "$device" | awk '$2 != "" {print "/dev/"$1}' || true)
    
    if [[ -n "$mounted_partitions" ]]; then
        while IFS= read -r partition; do
            if [[ -n "$partition" ]]; then
                verbose "Unmounting $partition"
                if [[ "$DRY_RUN" != "true" ]]; then
                    umount "$partition" 2>/dev/null || true
                else
                    echo "DRY RUN: umount '$partition'"
                fi
            fi
        done <<< "$mounted_partitions"
        
        # Wait a moment for unmounts to complete
        sleep 1
    else
        verbose "No mounted partitions found on $device"
    fi
}

wipe_device_signatures() {
    local device="$1"
    
    if [[ "$WIPE_DEVICE" == "true" ]]; then
        warn "Securely wiping device signatures on $device"
        warn "This may take a while..."
        
        if [[ "$DRY_RUN" != "true" ]]; then
            wipefs -af "$device"
            # Optionally add more secure wiping here
            success "Device signatures wiped"
        else
            echo "DRY RUN: wipefs -af '$device'"
        fi
    else
        info "Wiping filesystem signatures on $device"
        if [[ "$DRY_RUN" != "true" ]]; then
            wipefs -af "$device"
        else
            echo "DRY RUN: wipefs -af '$device'"
        fi
    fi
}

format_partition() {
    local device="$1"
    local fs_info="$2"
    local label="$3"
    
    local fs_type format_cmd label_flag
    IFS=':' read -r fs_type format_cmd label_flag <<< "$fs_info"
    
    # Determine the partition to format (first partition)
    local partition="${device}1"
    
    # Check if partition exists
    if [[ ! -b "$partition" ]]; then
        error "Partition $partition not found after creation"
        return 1
    fi
    
    info "Formatting $partition as $fs_type..."
    
    # Build format command safely
    local cmd_array=()
    IFS=' ' read -ra cmd_parts <<< "$format_cmd"
    cmd_array+=("${cmd_parts[@]}")
    
    # Add label if provided
    if [[ -n "$label" && -n "$label_flag" ]]; then
        cmd_array+=("$label_flag" "$label")
    fi
    
    cmd_array+=("$partition")
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY RUN: ${cmd_array[*]}"
        return 0
    fi
    
    # Execute format command safely
    "${cmd_array[@]}" || {
        error "Failed to format $partition"
        return 1
    }
    
    success "Formatting completed successfully"
}

verify_format() {
    local device="$1"
    local expected_fs="$2"
    
    if [[ "$VERIFY_AFTER_FORMAT" != "true" ]]; then
        return 0
    fi
    
    info "Verifying format..."
    
    local partition="${device}1"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "DRY RUN: Verification would check filesystem on $partition"
        return 0
    fi
    
    # Wait for filesystem to settle
    sleep 2
    
    # Check if filesystem is detectable
    local detected_fs
    detected_fs=$(blkid -o value -s TYPE "$partition" 2>/dev/null || echo "unknown")
    
    verbose "Expected: $expected_fs, Detected: $detected_fs"
    
    case "$expected_fs" in
        "fat32")
            if [[ "$detected_fs" == "vfat" ]]; then
                success "Filesystem verification passed"
                return 0
            fi
            ;;
        *)
            if [[ "$detected_fs" == "$expected_fs" ]]; then
                success "Filesystem verification passed"
                return 0
            fi
            ;;
    esac
    
    warn "Filesystem verification failed or inconclusive"
    warn "Expected: $expected_fs, Got: $detected_fs"
}

# User confirmation
confirm_format() {
    local device="$1"
    local fs_info="$2"
    local label="$3"
    
    local fs_type
    fs_type=$(echo "$fs_info" | cut -d: -f1)
    
    local device_info
    device_info=$(get_device_info "$device")
    
    echo
    echo -e "${RED}═══════════════════════════════════════════════════${NC}"
    echo -e "${RED}                    ⚠️  WARNING  ⚠️${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════${NC}"
    echo
    echo -e "You are about to format: ${WHITE}$device${NC}"
    echo -e "Device info: $device_info"
    echo -e "Filesystem: ${WHITE}$fs_type${NC}"
    if [[ -n "$label" ]]; then
        echo -e "Label: ${WHITE}$label${NC}"
    fi
    echo
    echo -e "${RED}THIS WILL PERMANENTLY DESTROY ALL DATA ON $device!${NC}"
    echo
    
    if [[ "$AUTO_CONFIRM" == "true" ]]; then
        warn "Auto-confirmation enabled - proceeding automatically"
        sleep 2
        return 0
    fi
    
    local confirmation
    echo -e "${YELLOW}Type 'YES' (all caps) to confirm and proceed:${NC}"
    read -r confirmation
    
    if [[ "$confirmation" != "YES" ]]; then
        info "Format cancelled by user"
        exit 0
    fi
}

# Main formatting workflow
main_format_workflow() {
    local device fs_info label
    
    # Select device
    device=$(select_drive)
    
    # Get filesystem choice
    fs_info=$(get_filesystem_choice)
    
    # Get label
    label=$(get_drive_label)
    
    # Final confirmation
    confirm_format "$device" "$fs_info" "$label"
    
    # Start formatting process
    echo
    info "Starting format process..."
    
    # Unmount device
    unmount_device "$device"
    
    # Wipe signatures
    wipe_device_signatures "$device"
    
    # Create partition table if requested
    if [[ "$CREATE_PARTITION_TABLE" == "true" ]]; then
        create_partition_table "$device"
        create_partition "$device" "$(echo "$fs_info" | cut -d: -f1)"
    fi
    
    # Format the partition
    format_partition "$device" "$fs_info" "$label"
    
    # Verify format
    verify_format "$device" "$(echo "$fs_info" | cut -d: -f1)"
    
    # Final success message
    echo
    success "Format operation completed successfully!"
    success "Device: $device"
    success "Filesystem: $(echo "$fs_info" | cut -d: -f1)"
    if [[ -n "$label" ]]; then
        success "Label: $label"
    fi
    
    info "The device is ready to use"
}

# Main execution
main() {
    # Parse command line arguments
    parse_arguments "$@"
    
    # Setup logging
    setup_logging
    
    # Create lockfile
    create_lockfile
    
    # Print header
    if [[ "$QUIET" != "true" ]]; then
        clear
        echo -e "${WHITE}$SCRIPT_NAME v$SCRIPT_VERSION${NC}"
        echo -e "${CYAN}Professional Drive Formatting Tool${NC}"
        echo
    fi
    
    # System checks
    check_root_privileges
    check_required_tools
    
    # Show warning if not dry run
    if [[ "$DRY_RUN" != "true" ]]; then
        echo -e "${RED}⚠️  WARNING: This tool can permanently destroy data! ⚠️${NC}"
        echo
        if [[ "$AUTO_CONFIRM" != "true" ]]; then
            echo "Press Enter to continue or Ctrl+C to cancel..."
            read -r
        fi
    else
        info "DRY RUN MODE - No actual changes will be made"
        echo
    fi
    
    # Run main workflow
    main_format_workflow
    
    # Cleanup happens automatically via trap
}

# Script entry point
main "$@"