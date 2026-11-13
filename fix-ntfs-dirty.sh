#!/bin/bash
# =============================================================================
# Windows-Compatible Drive Dirty Bit Detector and Fixer
#
# Supports: NTFS, exFAT, and VFAT/FAT32
#
# Scans system for drives/partitions formatted as NTFS, exFAT, or FAT,
# checks for the volume dirty bit on-disk (without relying on stale dmesg logs),
# and safely clears the dirty flag and repairs metadata.
#
# Usage:
#   sudo ./fix-drive-dirty.sh [options]
# =============================================================================

set -Eeuo pipefail

# Script metadata
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_VERSION="2.1.0"

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
FAST_EXFAT=false
INCLUDE_SYSTEM=false
DEEP_CHECK=false
TARGET_DEVICE=""
TARGET_FSTYPE_FILTER=""
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
    local tool="$1"

    if [ -f /etc/os-release ]; then
        # shellcheck source=/dev/null
        source /etc/os-release
        case "${ID:-}" in
            arch|cachyos|endeavouros|manjaro|garuda)
                case "$tool" in
                    ntfsfix) echo "pacman -S --needed ntfsprogs" ;;
                    fsck.exfat) echo "pacman -S --needed exfatprogs" ;;
                    fsck.vfat) echo "pacman -S --needed dosfstools" ;;
                esac
                ;;
            debian|ubuntu|pop|linuxmint)
                case "$tool" in
                    ntfsfix) echo "apt-get update && apt-get install -y ntfs-3g" ;;
                    fsck.exfat) echo "apt-get update && apt-get install -y exfatprogs" ;;
                    fsck.vfat) echo "apt-get update && apt-get install -y dosfstools" ;;
                esac
                ;;
            fedora|rhel|centos|rocky|alma)
                case "$tool" in
                    ntfsfix) echo "dnf install -y ntfs-3g" ;;
                    fsck.exfat) echo "dnf install -y exfatprogs" ;;
                    fsck.vfat) echo "dnf install -y dosfstools" ;;
                esac
                ;;
            *)
                echo ""
                ;;
        esac
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
}

# =============================================================================
# DRIVE DISCOVERY
# =============================================================================

declare -a DISCOVERED_DEVICES=()
declare -A DEV_FSTYPE=()
declare -A DEV_LABEL=()
declare -A DEV_UUID=()
declare -A DEV_SIZE=()
declare -A DEV_MOUNTPATH=()
declare -A DEV_IS_DIRTY=()
declare -A DEV_IS_SYSTEM=()

normalize_fstype() {
    local raw="$1"
    raw="${raw,,}" # lowercase
    case "$raw" in
        ntfs*|ntfs3) echo "ntfs" ;;
        exfat*) echo "exfat" ;;
        vfat*|fat*|msdos) echo "vfat" ;;
        *) echo "$raw" ;;
    esac
}

is_supported_fstype() {
    local fs="$1"
    case "$fs" in
        ntfs|exfat|vfat) return 0 ;;
        *) return 1 ;;
    esac
}

is_system_partition() {
    local dev="$1"
    local mount="$2"
    local label="$3"
    local parttype="${4:-}"

    # Mounted at critical OS paths
    case "$mount" in
        /|/boot|/boot/*|/efi|/efi/*)
            return 0
            ;;
    esac

    # EFI System Partition GUID or MBR type 0xef
    local pt_lower="${parttype,,}"
    if [ "$pt_lower" = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b" ] || [ "$pt_lower" = "0xef" ]; then
        return 0
    fi

    # Common EFI partition label when unmounted
    if [ "${label^^}" = "EFI" ]; then
        return 0
    fi

    return 1
}

find_drives() {
    print_section "Scanning system for NTFS, exFAT, and FAT drives..."

    DISCOVERED_DEVICES=()

    # If user passed a specific device via -d / --device
    if [ -n "$TARGET_DEVICE" ]; then
        if [ ! -b "$TARGET_DEVICE" ]; then
            log_error "Specified target device '$TARGET_DEVICE' is not a valid block device."
            exit 1
        fi

        local raw_fstype norm_fs
        raw_fstype=$(lsblk -n -o FSTYPE "$TARGET_DEVICE" 2>/dev/null || blkid -o value -s TYPE "$TARGET_DEVICE" 2>/dev/null || echo "")
        norm_fs=$(normalize_fstype "$raw_fstype")

        if ! is_supported_fstype "$norm_fs"; then
            log_error "Device '$TARGET_DEVICE' has filesystem type '${raw_fstype:-unknown}', not NTFS, exFAT, or FAT."
            exit 1
        fi

        local d_name="$TARGET_DEVICE"
        local d_label d_uuid d_size d_mount d_parttype
        d_label=$(lsblk -n -o LABEL "$d_name" 2>/dev/null || blkid -o value -s LABEL "$d_name" 2>/dev/null || echo "")
        d_uuid=$(lsblk -n -o UUID "$d_name" 2>/dev/null || blkid -o value -s UUID "$d_name" 2>/dev/null || echo "")
        d_size=$(lsblk -n -o SIZE "$d_name" 2>/dev/null || echo "Unknown")
        d_mount=$(lsblk -n -o MOUNTPOINTS "$d_name" 2>/dev/null | head -n1 || echo "")
        d_parttype=$(lsblk -n -o PARTTYPE "$d_name" 2>/dev/null || echo "")

        DISCOVERED_DEVICES+=("$d_name")
        DEV_FSTYPE["$d_name"]="$norm_fs"
        DEV_LABEL["$d_name"]="${d_label:-<no label>}"
        DEV_UUID["$d_name"]="${d_uuid:-<no uuid>}"
        DEV_SIZE["$d_name"]="$d_size"
        DEV_MOUNTPATH["$d_name"]="$d_mount"
        DEV_IS_SYSTEM["$d_name"]=false
        return
    fi

    # Scan all block devices using lsblk pairs
    while IFS= read -r line; do
        if [ -z "$line" ]; then
            continue
        fi

        local NAME="" FSTYPE="" LABEL="" UUID="" MOUNTPOINTS="" SIZE="" PARTTYPE=""
        eval "$line"

        local norm_fs
        norm_fs=$(normalize_fstype "${FSTYPE:-}")

        if is_supported_fstype "$norm_fs"; then
            if [ -n "$TARGET_FSTYPE_FILTER" ] && [ "$norm_fs" != "$TARGET_FSTYPE_FILTER" ]; then
                continue
            fi

            local clean_mount
            clean_mount=$(echo -e "${MOUNTPOINTS:-}" | head -n 1)

            local sys_part=false
            if is_system_partition "$NAME" "$clean_mount" "${LABEL:-}" "${PARTTYPE:-}"; then
                sys_part=true
                if [ "$INCLUDE_SYSTEM" = false ]; then
                    log_info "Skipping system/EFI partition $NAME (${LABEL:-$clean_mount}) — use --include-system to check it"
                    continue
                fi
            fi

            DISCOVERED_DEVICES+=("$NAME")
            DEV_FSTYPE["$NAME"]="$norm_fs"
            DEV_LABEL["$NAME"]="${LABEL:-<no label>}"
            DEV_UUID["$NAME"]="${UUID:-<no uuid>}"
            DEV_SIZE["$NAME"]="${SIZE:-Unknown}"
            DEV_MOUNTPATH["$NAME"]="$clean_mount"
            DEV_IS_SYSTEM["$NAME"]="$sys_part"
        fi
    done < <(lsblk -p -P -o NAME,FSTYPE,LABEL,UUID,MOUNTPOINTS,SIZE,PARTTYPE 2>/dev/null)

    if [ ${#DISCOVERED_DEVICES[@]} -eq 0 ]; then
        log_info "No non-system NTFS, exFAT, or FAT drives found on this system."
        exit 0
    fi

    log_success "Found ${#DISCOVERED_DEVICES[@]} drive(s) to inspect."
}

# =============================================================================
# ON-DISK DIRTY BIT CHECKING (NO STALE DMESG FALSE POSITIVES)
# =============================================================================

read_exfat_volume_flags() {
    local dev="$1"
    dd if="$dev" bs=1 skip=106 count=2 2>/dev/null | od -An -t u2 | tr -d ' \n' || echo ""
}

check_dirty_exfat() {
    local dev="$1"

    # 1. Direct inspection of VolumeFlags (Byte 106, 2 bytes LE) in the Volume Boot Record
    # Bit 1 (0x0002) is VolumeDirty: 1 = volume is dirty, 0 = clean
    if [ -r "$dev" ]; then
        local vol_flags
        vol_flags=$(read_exfat_volume_flags "$dev")
        if [ -n "$vol_flags" ] && [[ "$vol_flags" =~ ^[0-9]+$ ]]; then
            if (( vol_flags & 2 )); then
                echo "exFAT VolumeFlags (0x$(printf '%04x' "$vol_flags")) has VolumeDirty bit set"
                return 0
            fi
        fi
    fi

    # 2. Optional deep check with fsck.exfat -n (slow on multi-TB HDDs)
    if [ "$DEEP_CHECK" = true ] && command -v fsck.exfat &>/dev/null; then
        local fsck_out
        fsck_out=$(fsck.exfat -n "$dev" 2>&1 || true)
        if echo "$fsck_out" | grep -qiE 'Volume was not properly unmounted|corrupt|dirty|errors found'; then
            echo "fsck.exfat -n reported errors or unclean state"
            return 0
        fi
    fi

    return 1
}

check_dirty_ntfs() {
    local dev="$1"

    # 1. ntfsinfo -m (reads $Volume flags directly)
    if command -v ntfsinfo &>/dev/null; then
        local ntfsinfo_out
        ntfsinfo_out=$(ntfsinfo -m "$dev" 2>&1 || true)
        if echo "$ntfsinfo_out" | grep -qiE 'Volume Flags:.*DIRTY|0x0001|VOLUME_IS_DIRTY'; then
            echo "NTFS Volume Flags indicate DIRTY (0x0001)"
            return 0
        fi
    fi

    # 2. ntfsfix -n (dry-run diagnostics)
    if command -v ntfsfix &>/dev/null; then
        local ntfsfix_out
        ntfsfix_out=$(ntfsfix -n "$dev" 2>&1 || true)
        if echo "$ntfsfix_out" | grep -qiE 'volume is corrupt|volume is dirty|startup data can be fixed|dirty flag is set'; then
            echo "ntfsfix -n reported dirty flag or unclean shutdown"
            return 0
        fi
    fi

    return 1
}

check_dirty_vfat() {
    local dev="$1"

    # fsck.vfat -n checks the actual on-disk FAT dirty bit without modifying anything
    if command -v fsck.vfat &>/dev/null; then
        local fsck_out
        fsck_out=$(fsck.vfat -n "$dev" 2>&1 || true)
        if echo "$fsck_out" | grep -qiE 'Dirty bit is set|Filesystem has been marked dirty'; then
            echo "fsck.vfat -n reported Dirty bit is set"
            return 0
        fi
    fi

    return 1
}

check_dirty_bit() {
    local dev="$1"
    local fs="${DEV_FSTYPE[$dev]}"
    local is_dirty=false
    local reason=""

    case "$fs" in
        exfat)
            if reason=$(check_dirty_exfat "$dev"); then
                is_dirty=true
            fi
            ;;
        ntfs)
            if reason=$(check_dirty_ntfs "$dev"); then
                is_dirty=true
            fi
            ;;
        vfat)
            if reason=$(check_dirty_vfat "$dev"); then
                is_dirty=true
            fi
            ;;
    esac

    if [ "$is_dirty" = true ]; then
        DEV_IS_DIRTY["$dev"]=true
        log_warn "Device ${BOLD}$dev${NC} (${fs}) -> ${RED}[DIRTY BIT DETECTED]${NC} ($reason)"
    else
        DEV_IS_DIRTY["$dev"]=false
        log_success "Device ${BOLD}$dev${NC} (${fs}) -> ${GREEN}[CLEAN]${NC} (No dirty bit detected)"
    fi
}

# =============================================================================
# DIRTY BIT REPAIR
# =============================================================================

fast_clear_exfat_dirty_bit() {
    local dev="$1"

    log_info "Clearing exFAT VolumeDirty bit directly in primary & backup VBR..."

    if command -v python3 &>/dev/null; then
        python3 - "$dev" << 'PYEOF'
import struct, sys

dev = sys.argv[1]
with open(dev, "r+b") as f:
    vbr = bytearray(f.read(512))
    if len(vbr) < 512 or vbr[3:11] != b"EXFAT   ":
        print("Error: Not a valid exFAT Volume Boot Record", file=sys.stderr)
        sys.exit(1)

    bps_shift = vbr[108]
    if bps_shift < 9 or bps_shift > 12:
        print(f"Error: Unexpected BytesPerSectorShift={bps_shift}", file=sys.stderr)
        sys.exit(1)
    sector_size = 1 << bps_shift

    flags = struct.unpack_from("<H", vbr, 106)[0]
    new_flags = flags & ~0x0002
    print(f"Primary VBR VolumeFlags: 0x{flags:04x} -> 0x{new_flags:04x}")

    # Primary VBR (sector 0, offset 106)
    struct.pack_into("<H", vbr, 106, new_flags)
    f.seek(0)
    f.write(vbr)

    # Backup VBR (sector 12, offset 106)
    backup_offset = 12 * sector_size
    f.seek(backup_offset)
    bvbr = bytearray(f.read(512))
    if len(bvbr) == 512 and bvbr[3:11] == b"EXFAT   ":
        bflags = struct.unpack_from("<H", bvbr, 106)[0]
        bnew_flags = bflags & ~0x0002
        print(f"Backup VBR VolumeFlags:  0x{bflags:04x} -> 0x{bnew_flags:04x}")
        struct.pack_into("<H", bvbr, 106, bnew_flags)
        f.seek(backup_offset)
        f.write(bvbr)

    f.flush()
PYEOF
    else
        # Pure shell fallback using dd (clears bit 1 of byte 106 in sector 0)
        local vol_flags new_flags low_byte hex_byte
        vol_flags=$(read_exfat_volume_flags "$dev")
        if [ -z "$vol_flags" ] || ! [[ "$vol_flags" =~ ^[0-9]+$ ]]; then
            log_error "Could not read exFAT VolumeFlags from $dev"
            return 1
        fi
        new_flags=$(( vol_flags & ~2 ))
        low_byte=$(( new_flags & 255 ))
        hex_byte=$(printf '\\x%02x' "$low_byte")
        printf '%b' "$hex_byte" | dd of="$dev" bs=1 seek=106 count=1 conv=notrunc status=none
        log_info "Updated Primary VBR VolumeFlags: 0x$(printf '%04x' "$vol_flags") -> 0x$(printf '%04x' "$new_flags")"
    fi

    sync
}

fix_drive() {
    local dev="$1"
    local fs="${DEV_FSTYPE[$dev]}"
    local mountpoint="${DEV_MOUNTPATH[$dev]:-}"
    local was_mounted=false

    print_section "Fixing $fs Dirty Bit on $dev..."

    # Check if currently mounted
    if [ -n "$mountpoint" ] || mountpoint -q "$dev" 2>/dev/null || grep -qs "^$dev " /proc/mounts; then
        was_mounted=true
        if [ -z "$mountpoint" ]; then
            mountpoint=$(grep -m1 "^$dev " /proc/mounts | awk '{print $2}')
        fi

        log_info "Device $dev is currently mounted at '${mountpoint}'. Unmounting for repair..."
        if ! umount "$dev" 2>/dev/null; then
            log_error "Failed to unmount $dev. Please close any files or processes accessing $mountpoint."
            return 1
        fi
        log_success "Unmounted $dev successfully."
    fi

    # Execute filesystem specific fix
    case "$fs" in
        exfat)
            local use_fast="$FAST_EXFAT"
            if [ "$use_fast" = false ] && [ "$AUTO_FIX" = false ] && [ -t 0 ]; then
                echo ""
                echo -e "${YELLOW}Note:${NC} A full 'fsck.exfat' on a multi-TB USB drive (${DEV_SIZE[$dev]}) can take a long time."
                echo -e "  ${GREEN}1)${NC} Fast clear (clears VolumeDirty bit in VBR in <1s, like ntfsfix -d)"
                echo -e "  ${GREEN}2)${NC} Full fsck.exfat scan & repair (verifies all files/clusters with live progress)"
                read -p "Choose repair mode [1=fast / 2=full] (default: 1): " -r exfat_choice
                exfat_choice="${exfat_choice:-1}"
                if [ "$exfat_choice" = "1" ]; then
                    use_fast=true
                fi
            fi

            if [ "$use_fast" = true ]; then
                if fast_clear_exfat_dirty_bit "$dev"; then
                    log_success "Fast-cleared exFAT dirty bit on $dev."
                else
                    log_error "Failed to fast-clear exFAT dirty bit on $dev."
                    return 1
                fi
            else
                if ! command -v fsck.exfat &>/dev/null; then
                    local inst
                    inst=$(detect_package_manager fsck.exfat)
                    log_error "Missing 'fsck.exfat' (package: exfatprogs). Install with: sudo $inst"
                    return 1
                fi

                log_info "Running: fsck.exfat -y -P $dev (unbuffered live output)"
                # Run directly without pipe buffering so progress bar updates live
                if fsck.exfat -y -P "$dev"; then
                    log_success "fsck.exfat successfully repaired and cleared dirty flag on $dev."
                else
                    log_error "fsck.exfat encountered issues repairing $dev."
                fi
            fi
            ;;

        ntfs)
            if ! command -v ntfsfix &>/dev/null; then
                local inst
                inst=$(detect_package_manager ntfsfix)
                log_error "Missing 'ntfsfix' (package: ntfsprogs / ntfs-3g). Install with: sudo $inst"
                return 1
            fi

            log_info "Running: ntfsfix -d $dev"
            if ntfsfix -d "$dev"; then
                log_success "ntfsfix successfully cleared the dirty flag on $dev."
            else
                log_error "ntfsfix failed to clear dirty flag on $dev."
            fi
            ;;

        vfat)
            if ! command -v fsck.vfat &>/dev/null; then
                local inst
                inst=$(detect_package_manager fsck.vfat)
                log_error "Missing 'fsck.vfat' (package: dosfstools). Install with: sudo $inst"
                return 1
            fi

            log_info "Running: fsck.vfat -a -w $dev"
            if fsck.vfat -a -w "$dev"; then
                log_success "fsck.vfat successfully repaired and cleared dirty flag on $dev."
            else
                log_error "fsck.vfat encountered issues on $dev."
            fi
            ;;
    esac

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

    # Re-verify on-disk dirty status
    log_info "Verifying on-disk volume status post-fix..."
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
    print_header "DRIVES SUMMARY"

    printf "%-16s %-7s %-15s %-7s %-12s %-20s\n" "DEVICE" "FSTYPE" "LABEL" "SIZE" "STATUS" "MOUNTPOINT"
    echo "──────────────────────────────────────────────────────────────────────────────────"

    for dev in "${DISCOVERED_DEVICES[@]}"; do
        local fs="${DEV_FSTYPE[$dev]:-}"
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
        [ ${#mount} -gt 19 ] && mount="${mount:0:16}..."

        printf "%-16s %-7s %-15s %-7s %-21b %-20s\n" "$dev" "$fs" "$label" "$size" "$status_str" "$mount"
    done
    echo ""
}

# =============================================================================
# CLI OPTIONS & HELP
# =============================================================================

show_help() {
    cat << EOF
Windows-Compatible Drive Dirty Bit Detector and Fixer (v$SCRIPT_VERSION)
Supports: NTFS, exFAT, and VFAT/FAT32

Searches for non-system NTFS, exFAT, and FAT drives/partitions, checks the actual
on-disk dirty bit, and repairs/clears it cleanly.

USAGE:
    sudo $SCRIPT_NAME [OPTIONS]

OPTIONS:
    -c, --check, --dry-run      Check drives and report status only (do not modify)
    -f, --fix, -y, --yes        Automatically fix all dirty drives without prompting
    --fast                      Fast-clear exFAT VolumeDirty bit in VBR (<1s, skips full scan)
    --deep-check                Also run fsck.exfat -n during detection (slow on large HDDs)
    --include-system            Include EFI / /boot / root system partitions in scan
    -d, --device <device>       Inspect/fix a specific device only (e.g. /dev/sda2)
    --ntfs                      Only scan NTFS drives
    --exfat                     Only scan exFAT drives
    --fat, --vfat               Only scan FAT/VFAT drives
    --no-remount                Do not remount unmounted drives after fixing
    -h, --help                  Show this help message and exit

EXAMPLES:
    sudo ./$SCRIPT_NAME                    # Interactive scan of data drives
    sudo ./$SCRIPT_NAME --check            # Check and report status without modifying
    sudo ./$SCRIPT_NAME -d /dev/sda2 --fast -y  # Fast-clear dirty bit on /dev/sda2
    sudo ./$SCRIPT_NAME -y                 # Automatically fix all dirty drives

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
            --fast)
                FAST_EXFAT=true
                shift
                ;;
            --deep-check)
                DEEP_CHECK=true
                shift
                ;;
            --include-system)
                INCLUDE_SYSTEM=true
                shift
                ;;
            -d|--device)
                if [ -n "${2:-}" ]; then
                    TARGET_DEVICE="$2"
                    shift 2
                else
                    log_error "Error: --device requires a valid device path (e.g. /dev/sda2)"
                    exit 1
                fi
                ;;
            --ntfs)
                TARGET_FSTYPE_FILTER="ntfs"
                shift
                ;;
            --exfat)
                TARGET_FSTYPE_FILTER="exfat"
                shift
                ;;
            --fat|--vfat)
                TARGET_FSTYPE_FILTER="vfat"
                shift
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

    print_header "Drive Dirty Bit Detector & Repair Tool"

    # Step 1: Scan for drives
    find_drives

    # Step 2: Check dirty bit on each drive
    print_section "Checking on-disk filesystem dirty flags..."
    local dirty_count=0
    declare -a dirty_drives=()

    for dev in "${DISCOVERED_DEVICES[@]}"; do
        echo -e "Checking ${CYAN}$dev${NC} (${DEV_FSTYPE[$dev]}, ${DEV_LABEL[$dev]}, ${DEV_SIZE[$dev]})..."
        check_dirty_bit "$dev"
        if [ "${DEV_IS_DIRTY[$dev]}" = true ]; then
            ((dirty_count++)) || true
            dirty_drives+=("$dev")
        fi
    done

    # Print summary
    print_summary_table

    if [ "$dirty_count" -eq 0 ]; then
        log_success "All scanned drive(s) are clean! No action needed."
        exit 0
    fi

    log_warn "Found $dirty_count dirty drive(s): ${dirty_drives[*]}"

    if [ "$CHECK_ONLY" = true ]; then
        log_info "Check-only mode enabled. No changes made."
        exit 0
    fi

    # Step 3: Fix dirty drives
    for dev in "${dirty_drives[@]}"; do
        echo ""
        if [ "$AUTO_FIX" = true ] || prompt_yes_no "Clear dirty bit and fix $dev (${DEV_FSTYPE[$dev]} - ${DEV_LABEL[$dev]})?" "y"; then
            fix_drive "$dev" || true
        else
            log_info "Skipped repair for $dev."
        fi
    done

    print_header "COMPLETED"
    log_success "Finished processing drives."
}

main "$@"
