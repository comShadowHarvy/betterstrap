#!/bin/bash

# Set strict error handling
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default settings
VERBOSE=false
GROUPS=("dialout" "uucp" "tty")
BACKUP=true

# Help function
show_help() {
    echo "Usage: $(basename "$0") [OPTIONS]"
    echo "Add current user to serial port access groups"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Enable verbose output"
    echo "  -n, --no-backup Don't create backup"
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) show_help ;;
        -v|--verbose) VERBOSE=true ;;
        -n|--no-backup) BACKUP=false ;;
        *) echo "Unknown option: $1"; show_help ;;
    esac
    shift
done

# Logging function
log() {
    local level=$1
    shift
    case $level in
        "INFO") echo -e "${GREEN}[INFO]${NC} $*" ;;
        "WARN") echo -e "${YELLOW}[WARN]${NC} $*" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $*" ;;
    esac
}

# Validate user exists
USER=$(whoami)
if ! id "$USER" &>/dev/null; then
    log "ERROR" "User '$USER' does not exist"
    exit 1
fi

# Backup current groups
if $BACKUP; then
    BACKUP_FILE="/tmp/groups_backup_$(date +%Y%m%d_%H%M%S).txt"
    groups "$USER" > "$BACKUP_FILE"
    log "INFO" "Current groups backed up to $BACKUP_FILE"
fi

# Process each group
for GROUP in "${GROUPS[@]}"; do
    # Check if group exists
    if ! getent group "$GROUP" > /dev/null 2>&1; then
        log "WARN" "Group '$GROUP' does not exist. Creating it..."
        if sudo groupadd "$GROUP"; then
            log "INFO" "Group '$GROUP' created successfully"
        else
            log "ERROR" "Failed to create group '$GROUP'"
            exit 1
        fi
    else
        $VERBOSE && log "INFO" "Group '$GROUP' already exists"
    fi

    # Add user to group if not already a member
    if ! groups "$USER" | grep -q "\b$GROUP\b"; then
        log "INFO" "Adding user '$USER' to group '$GROUP'..."
        if sudo usermod -aG "$GROUP" "$USER"; then
            log "INFO" "User '$USER' added to group '$GROUP'"
        else
            log "ERROR" "Failed to add user to group '$GROUP'"
            exit 1
        fi
    else
        $VERBOSE && log "INFO" "User '$USER' is already in group '$GROUP'"
    fi
done

log "INFO" "All operations completed successfully"
log "WARN" "Please log out and back in for the changes to take effect"

# Verify changes
for GROUP in "${GROUPS[@]}"; do
    if ! groups "$USER" | grep -q "\b$GROUP\b"; then
        log "ERROR" "Verification failed: User '$USER' is not in group '$GROUP'"
        exit 1
    fi
done

exit 0
