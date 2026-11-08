#!/bin/bash
# =============================================================================
# NTFS Dirty Bit Detector and Fixer
#
# Scans system for all NTFS drives and partitions, checks for the NTFS volume
# dirty flag (which causes Linux kernel ntfs3/ntfs-3g drivers to refuse
# read-write mounts or fail to mount), and safely clears it using ntfsfix.
#
# Usage:
#   sudo ./fix-ntfs-dirty.sh [options]
# =============================================================================

set -Eeuo pipefail

# Script metadata
readonly SCRIPT_NAME="fix-ntfs-dirty.sh"
readonly SCRIPT_VERSION="1.0.0"

# Colors for terminal output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly MAGENTA='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly NC='\033[0m' # No Color

# Default options
AUTO_FIX=false
CHECK_ONLY=false
TARGET_DEVICE=""
REMOUNT=true

# =============================================================================
# LOGGING AND OUTPUT HELPERS
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

print_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  $*${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${MAGENTA}▶ $*${NC}"
}

prompt_yes_no() {
    local prompt="$1"
    local default="${2:-n}"

    if [ "$AUTO_FIX" = true ]; then
        return 0
    fi

    if [ "$default" = "y" ]; then
        prompt="$prompt [Y/n]: "
    else
        prompt="$prompt [y/N]: "
    fi

    read -p "$prompt" -r response
    response=${response:-$default}

    [[ "$response" =~ ^[Yy]$ ]]
}

# =============================================================================
# ROOT PRIVILEGE AND DEPENDENCY CHECKS
# =============================================================================

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_warn "This script requires root privileges to inspect and repair block devices."
        if command -v sudo &>/dev/null; then
            log_info "Attempting to elevate with sudo..."
            exec sudo "$0" "$@"
        else
            log_error "Please run this script as root or with sudo."
            exit 1
        fi
    fi
}

detect_package_manager() {
    if [ -f /etc/os-release ]; then
        # shellcheck source=/dev/null
        source /etc/os-release
        case "${ID:-}" in
            arch|cachyos|endeavouros|manjaro|garuda)
                echo "pacman -S --needed ntfsprogs"
                ;;
            debian|ubuntu|pop|linuxmint)
                echo "apt-get update && apt-get install -y ntfs-3g"
                ;;
            fedora|rhel|centos|rocky|alma)
                echo "dnf install -y ntfs-3g"
                ;;
            opensuse*|suse)
                echo "zypper install -y ntfs-3g"
                ;;
            *)
                if [[ "${ID_LIKE:-}" == *"arch"* ]]; then
                    echo "pacman -S --needed ntfsprogs"
                elif [[ "${ID_LIKE:-}" == *"debian"* ]] || [[ "${ID_LIKE:-}" == *"ubuntu"* ]]; then
                    echo "apt-get update && apt-get install -y ntfs-3g"
                elif [[ "${ID_LIKE:-}" == *"fedora"* ]]; then
                    echo "dnf install -y ntfs-3g"
                else
                    echo ""
                fi
                ;;
        esac
    else
        echo ""
    fi
}

check_dependencies() {
    local missing=()
    for cmd in lsblk blkid; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing required core utilities: ${missing[*]}"
        exit 1
    fi

    # Check for ntfsfix and ntfsinfo
    if ! command -v ntfsfix &>/dev/null; then
        local install_cmd
        install_cmd=$(detect_package_manager)
        log_warn "'ntfsfix' (from ntfs-3g / ntfsprogs) is not installed."

        if [ -n "$install_cmd" ]; then
            if [ -t 0 ] && prompt_yes_no "Would you like to install it now using '$install_cmd'?" "y"; then
                log_info "Installing NTFS utilities..."
                eval "$install_cmd"
            else
                log_error "Please install 'ntfs-3g' or 'ntfsprogs' to use this script."
                log_info "Suggested installation command: sudo $install_cmd"
                exit 1
            fi
        else
            log_error "Please install 'ntfs-3g' or 'ntfsprogs' from your distribution repository."
            exit 1
        fi
    fi
}

# =============================================================================
# NTFS DRIVE DISCOVERY
# =============================================================================

# Global arrays to store discovered drives
declare -a NTFS_DEVICES=()
declare -A DEV_LABEL=()
declare -A DEV_UUID=()
declare -A DEV_SIZE=()
declare -A DEV_MOUNTPATH=()
declare -A DEV_IS_DIRTY=()

find_ntfs_drives() {
    print_section "Scanning system for NTFS drives..."

    NTFS_DEVICES=()

    # If user passed a specific device via -d / --device
    if [ -n "$TARGET_DEVICE" ]; then
        if [ ! -b "$TARGET_DEVICE" ]; then
            log_error "Specified target device '$TARGET_DEVICE' is not a valid block device."
            exit 1
        fi

        local fstype
        fstype=$(lsblk -n -o FSTYPE "$TARGET_DEVICE" 2>/dev/null || blkid -o value -s TYPE "$TARGET_DEVICE" 2>/dev/null || echo "")
        if [[ ! "$fstype" =~ ^[Nn][Tt][Ff][Ss] ]]; then
            log_error "Device '$TARGET_DEVICE' has filesystem type '${fstype:-unknown}', not NTFS."
            exit 1
        fi

        local d_name="$TARGET_DEVICE"
        local d_label d_uuid d_size d_mount
        d_label=$(lsblk -n -o LABEL "$d_name" 2>/dev/null || echo "")
        d_uuid=$(lsblk -n -o UUID "$d_name" 2>/dev/null || blkid -o value -s UUID "$d_name" 2>/dev/null || echo "")
        d_size=$(lsblk -n -o SIZE "$d_name" 2>/dev/null || echo "Unknown")
        d_mount=$(lsblk -n -o MOUNTPOINTS "$d_name" 2>/dev/null | head -n1 || echo "")

        NTFS_DEVICES+=("$d_name")
        DEV_LABEL["$d_name"]="${d_label:-<no label>}"
        DEV_UUID["$d_name"]="${d_uuid:-<no uuid>}"
        DEV_SIZE["$d_name"]="$d_size"
        DEV_MOUNTPATH["$d_name"]="$d_mount"
        return
    fi

    # Scan all block devices using lsblk pairs
    while IFS= read -r line; do
        if [ -z "$line" ]; then
            continue
        fi

        local NAME="" FSTYPE="" LABEL="" UUID="" MOUNTPOINTS="" SIZE=""
        eval "$line"

        if [[ "$FSTYPE" =~ ^[Nn][Tt][Ff][Ss] ]]; then
            # Clean up mountpoint string (handle \x0a if multiple)
            local clean_mount
            clean_mount=$(echo -e "${MOUNTPOINTS:-}" | head -n 1)

            NTFS_DEVICES+=("$NAME")
            DEV_LABEL["$NAME"]="${LABEL:-<no label>}"
            DEV_UUID["$NAME"]="${UUID:-<no uuid>}"
            DEV_SIZE["$NAME"]="${SIZE:-Unknown}"
            DEV_MOUNTPATH["$NAME"]="$clean_mount"
        fi
    done < <(lsblk -p -P -o NAME,FSTYPE,LABEL,UUID,MOUNTPOINTS,SIZE 2>/dev/null)

    # Secondary check with blkid to catch any partitions lsblk might have missed
    if command -v blkid &>/dev/null; then
        while IFS= read -r dev; do
            if [ -n "$dev" ] && [ -b "$dev" ]; then
                local already_found=false
                for existing in "${NTFS_DEVICES[@]}"; do
                    if [ "$existing" = "$dev" ]; then
                        already_found=true
                        break
                    fi
                done

                if [ "$already_found" = false ]; then
                    local b_label b_uuid b_size b_mount
                    b_label=$(blkid -o value -s LABEL "$dev" 2>/dev/null || echo "")
                    b_uuid=$(blkid -o value -s UUID "$dev" 2>/dev/null || echo "")
                    b_size=$(lsblk -n -o SIZE "$dev" 2>/dev/null || echo "Unknown")
                    b_mount=$(lsblk -n -o MOUNTPOINTS "$dev" 2>/dev/null | head -n 1 || echo "")

                    NTFS_DEVICES+=("$dev")
                    DEV_LABEL["$dev"]="${b_label:-<no label>}"
                    DEV_UUID["$dev"]="${b_uuid:-<no uuid>}"
                    DEV_SIZE["$dev"]="$b_size"
                    DEV_MOUNTPATH["$dev"]="$b_mount"
                fi
            fi
        done < <(blkid -t TYPE=ntfs -o device 2>/dev/null || true)
    fi

    if [ ${#NTFS_DEVICES[@]} -eq 0 ]; then
        log_info "No NTFS drives or partitions found on this system."
        exit 0
    fi

    log_success "Found ${#NTFS_DEVICES[@]} NTFS device(s)."
}

# =============================================================================
# DIRTY BIT CHECKING
# =============================================================================

check_dirty_bit() {
    local dev="$1"
    local is_dirty=false
    local check_method=""
    local reason=""

    # 1. Primary check: ntfsinfo -m (reads $Volume directly)
    if command -v ntfsinfo &>/dev/null; then
        local ntfsinfo_out
        ntfsinfo_out=$(ntfsinfo -m "$dev" 2>&1 || true)

        if echo "$ntfsinfo_out" | grep -qiE 'Volume Flags:.*DIRTY|0x0001|VOLUME_IS_DIRTY'; then
            is_dirty=true
            check_method="ntfsinfo"
            reason="Volume Flags indicate DIRTY (0x0001)"
        fi
    fi

    # 2. Secondary check: ntfsfix -n (dry-run diagnostics)
    if [ "$is_dirty" = false ] && command -v ntfsfix &>/dev/null; then
        local ntfsfix_out
        ntfsfix_out=$(ntfsfix -n "$dev" 2>&1 || true)

        if echo "$ntfsfix_out" | grep -qiE 'volume is corrupt|volume is dirty|startup data can be fixed|dirty flag is set'; then
            is_dirty=true
            check_method="ntfsfix -n"
            reason="Diagnostics reported unclean shutdown or dirty flag"
        fi
    fi

    # 3. Kernel dmesg check (recent kernel rejection of ntfs3 without force)
    if [ "$is_dirty" = false ]; then
        local dev_basename
        dev_basename=$(basename "$dev")
        if dmesg 2>/dev/null | tail -n 50 | grep -qiE "ntfs3:.*${dev_basename}.*volume is dirty"; then
            is_dirty=true
            check_method="kernel dmesg"
            reason="Kernel ntfs3 rejected mount due to dirty volume"
        fi
    fi

    if [ "$is_dirty" = true ]; then
        DEV_IS_DIRTY["$dev"]=true
        log_warn "Device ${BOLD}$dev${NC} -> ${RED}[DIRTY BIT DETECTED]${NC} ($reason)"
    else
        DEV_IS_DIRTY["$dev"]=false
        log_success "Device ${BOLD}$dev${NC} -> ${GREEN}[CLEAN]${NC} (No dirty bit detected)"
    fi
}

# =============================================================================
# DIRTY BIT REPAIR
# =============================================================================

fix_ntfs_drive() {
    local dev="$1"
    local mountpoint="${DEV_MOUNTPATH[$dev]:-}"
    local was_mounted=false

    print_section "Fixing NTFS Dirty Bit on $dev..."

    # Check if currently mounted
    if [ -n "$mountpoint" ] || mountpoint -q "$dev" 2>/dev/null || grep -qs "^$dev " /proc/mounts; then
        was_mounted=true
        if [ -z "$mountpoint" ]; then
            mountpoint=$(grep -m1 "^$dev " /proc/mounts | awk '{print $2}')
        fi

        log_info "Device $dev is currently mounted at '${mountpoint}'. Unmounting for repair..."
        if ! umount "$dev" 2>/dev/null && ! umount -l "$dev" 2>/dev/null; then
            log_error "Failed to unmount $dev. Please close any files or processes accessing $mountpoint."
            return 1
        fi
        log_success "Unmounted $dev successfully."
    fi

    # Execute ntfsfix -d to clear dirty bit
    log_info "Running: ntfsfix -d $dev"
    local fix_output
    if fix_output=$(ntfsfix -d "$dev" 2>&1); then
        echo "$fix_output" | sed 's/^/  │ /'
        log_success "ntfsfix successfully cleared the dirty flag on $dev."
    else
        echo "$fix_output" | sed 's/^/  │ /' >&2
        log_error "ntfsfix failed to clear dirty flag on $dev."
        return 1
    fi

    # Remount if it was previously mounted and REMOUNT is enabled
    if [ "$was_mounted" = true ] && [ "$REMOUNT" = true ]; then
        log_info "Remounting $dev to original mountpoint '${mountpoint}'..."
        if [ -d "$mountpoint" ] && mount "$dev" "$mountpoint" 2>/dev/null; then
            log_success "Remounted $dev at ${mountpoint}."
        else
            log_warn "Could not automatically remount $dev to $mountpoint."
            log_info "You can mount it manually with: sudo mount $dev $mountpoint"
        fi
    fi

    # Re-verify dirty status
    log_info "Verifying volume status post-fix..."
    check_dirty_bit "$dev"
    if [ "${DEV_IS_DIRTY[$dev]}" = false ]; then
        log_success "Verified: $dev is now clean!"
        return 0
    else
        log_warn "Dirty bit is still reported on $dev. Windows 'chkdsk /f' may be required for severe corruption."
        return 1
    fi
}

# =============================================================================
# SUMMARY TABLE
# =============================================================================

print_summary_table() {
    print_header "NTFS DRIVES SUMMARY"

    printf "%-18s %-15s %-8s %-12s %-22s\n" "DEVICE" "LABEL" "SIZE" "STATUS" "MOUNTPOINT"
    echo "─────────────────────────────────────────────────────────────────────────────"

    for dev in "${NTFS_DEVICES[@]}"; do
        local label="${DEV_LABEL[$dev]:-}"
        local size="${DEV_SIZE[$dev]:-}"
        local mount="${DEV_MOUNTPATH[$dev]:-}"
        local dirty="${DEV_IS_DIRTY[$dev]:-false}"
        local status_str

        if [ "$dirty" = true ]; then
            status_str="${RED}DIRTY${NC}"
        else
            status_str="${GREEN}CLEAN${NC}"
        fi

        [ -z "$mount" ] && mount="<unmounted>"
        [ ${#label} -gt 14 ] && label="${label:0:11}..."
        [ ${#mount} -gt 21 ] && mount="${mount:0:18}..."

        printf "%-18s %-15s %-8s %-21b %-22s\n" "$dev" "$label" "$size" "$status_str" "$mount"
    done
    echo ""
}

# =============================================================================
# CLI OPTIONS & HELP
# =============================================================================

show_help() {
    cat << EOF
NTFS Dirty Bit Detector and Fixer (v$SCRIPT_VERSION)

Searches for all NTFS drives and partitions, identifies any with the dirty bit set,
and clears it using ntfsfix so Linux kernel drivers can mount them read-write.

USAGE:
    sudo $SCRIPT_NAME [OPTIONS]

OPTIONS:
    -c, --check, --dry-run      Check drives and report status only (do not modify)
    -f, --fix, -y, --yes        Automatically fix all dirty NTFS drives without prompting
    -d, --device <device>       Inspect/fix a specific device only (e.g. /dev/sdb1)
    --no-remount                Do not remount unmounted drives after fixing
    -h, --help                  Show this help message and exit

EXAMPLES:
    sudo ./$SCRIPT_NAME                    # Interactive scan and prompt to fix dirty drives
    sudo ./$SCRIPT_NAME --check            # Check and report dirty state without fixing
    sudo ./$SCRIPT_NAME -y                 # Automatically find and fix all dirty NTFS drives
    sudo ./$SCRIPT_NAME -d /dev/sdb1       # Target a specific partition

EOF
    exit 0
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -c|--check|--dry-run|--check-only)
                CHECK_ONLY=true
                shift
                ;;
            -f|--fix|-y|--yes|--auto)
                AUTO_FIX=true
                shift
                ;;
            -d|--device)
                if [ -n "${2:-}" ]; then
                    TARGET_DEVICE="$2"
                    shift 2
                else
                    log_error "Error: --device requires a valid device path (e.g. /dev/sdb1)"
                    exit 1
                fi
                ;;
            --no-remount)
                REMOUNT=false
                shift
                ;;
            -h|--help)
                show_help
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                ;;
        esac
    done
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    parse_args "$@"
    check_root "$@"
    check_dependencies

    print_header "NTFS Dirty Bit Detector & Repair Tool"

    # Step 1: Scan for drives
    find_ntfs_drives

    # Step 2: Check dirty bit on each drive
    print_section "Checking NTFS integrity status..."
    local dirty_count=0
    declare -a dirty_drives=()

    for dev in "${NTFS_DEVICES[@]}"; do
        echo -e "Checking ${CYAN}$dev${NC} (${DEV_LABEL[$dev]}, ${DEV_SIZE[$dev]})..."
        check_dirty_bit "$dev"
        if [ "${DEV_IS_DIRTY[$dev]}" = true ]; then
            ((dirty_count++)) || true
            dirty_drives+=("$dev")
        fi
    done

    # Print summary
    print_summary_table

    if [ "$dirty_count" -eq 0 ]; then
        log_success "All NTFS drive(s) are clean! No action needed."
        exit 0
    fi

    log_warn "Found $dirty_count dirty NTFS drive(s): ${dirty_drives[*]}"

    if [ "$CHECK_ONLY" = true ]; then
        log_info "Check-only mode enabled. No changes made."
        exit 0
    fi

    # Step 3: Fix dirty drives
    for dev in "${dirty_drives[@]}"; do
        echo ""
        if [ "$AUTO_FIX" = true ] || prompt_yes_no "Clear dirty bit and fix $dev (${DEV_LABEL[$dev]})?" "y"; then
            fix_ntfs_drive "$dev" || true
        else
            log_info "Skipped repair for $dev."
        fi
    done

    print_header "COMPLETED"
    log_success "Finished processing NTFS drives."
}

main "$@"

