#!/bin/bash
# Enhanced Configuration Backup Script
# This script creates comprehensive backups of user configuration files,
# credentials, and settings with validation and compression options

# Terminal colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Backup configuration
BACKUP_DIR="$HOME/back"
DATE=$(date +%Y-%m-%d-%H%M%S)
BACKUP_NAME="backup_$DATE"
FULL_BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
LOG_FILE="$BACKUP_DIR/backup_$DATE.log"
ERROR_LOG="$BACKUP_DIR/backup_errors_$DATE.log"

# GPG key ID - replace with your actual key ID or keep empty
GPG_KEY_ID="6E84E35B67DC0349"

# Create backup directory and log files
mkdir -p "$FULL_BACKUP_PATH"
touch "$LOG_FILE" "$ERROR_LOG"

# Log function
log() {
    local level=$1
    local message=$2
    
    # Format the timestamp
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    # Log to file
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    # Print to console with colors
    case "$level" in
        "INFO")  echo -e "${BLUE}[INFO]${NC} $message" ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} $message" ;;
        "WARNING") echo -e "${YELLOW}[WARNING]${NC} $message" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" 
                 echo "[$timestamp] [$level] $message" >> "$ERROR_LOG"
                 ;;
    esac
}

# Validate path and return success/failure
validate_path() {
    local path="$1"
    local description="$2"
    
    if [ -e "$path" ]; then
        log "INFO" "Found $description at $path"
        return 0
    else
        log "WARNING" "$description not found at $path, will be skipped"
        return 1
    fi
}

# Backup a file with validation
backup_file() {
    local source="$1"
    local destination="$2"
    local description="$3"
    
    if validate_path "$source" "$description"; then
        if [ -d "$source" ]; then
            # For directories, use recursive copy
            cp -r "$source" "$destination" 2>> "$ERROR_LOG"
        else
            # For files, use regular copy
            cp "$source" "$destination" 2>> "$ERROR_LOG"
        fi
        
        if [ $? -eq 0 ]; then
            log "SUCCESS" "Backed up $description to $destination"
            return 0
        else
            log "ERROR" "Failed to backup $description to $destination"
            return 1
        fi
    fi
    return 1
}

# Create directory if it doesn't exist
create_dir_if_needed() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        log "INFO" "Created directory $dir"
    fi
}

# Print header
echo -e "${BOLD}${BLUE}=======================================================${NC}"
echo -e "${BOLD}${BLUE}              Configuration Backup Tool                ${NC}"
echo -e "${BOLD}${BLUE}=======================================================${NC}"
echo

log "INFO" "Starting backup process to $FULL_BACKUP_PATH"
echo -e "Backup location: ${BOLD}$FULL_BACKUP_PATH${NC}"
echo -e "Log file: ${BOLD}$LOG_FILE${NC}"
echo

# === SSH KEYS ===
echo -e "${BOLD}${BLUE}Backing up SSH keys...${NC}"
create_dir_if_needed "$FULL_BACKUP_PATH/ssh"

# Backup multiple possible SSH key types
SSH_KEY_TYPES=("id_rsa" "id_ed25519" "id_ecdsa" "id_dsa" "id")
SSH_KEYS_FOUND=false

for key_type in "${SSH_KEY_TYPES[@]}"; do
    if backup_file "$HOME/.ssh/$key_type" "$FULL_BACKUP_PATH/ssh/" "SSH private key ($key_type)"; then
        SSH_KEYS_FOUND=true
    fi
    backup_file "$HOME/.ssh/$key_type.pub" "$FULL_BACKUP_PATH/ssh/" "SSH public key ($key_type)"
done

# Backup SSH config if it exists
backup_file "$HOME/.ssh/config" "$FULL_BACKUP_PATH/ssh/" "SSH config file"
backup_file "$HOME/.ssh/known_hosts" "$FULL_BACKUP_PATH/ssh/" "SSH known hosts"

if [ "$SSH_KEYS_FOUND" = false ]; then
    log "WARNING" "No SSH keys were found to backup"
fi

# === GPG KEYS ===
echo -e "${BOLD}${BLUE}Backing up GPG keys and configuration...${NC}"
create_dir_if_needed "$FULL_BACKUP_PATH/gpg"

# Check if GPG is installed
if command -v gpg &> /dev/null; then
    # If GPG_KEY_ID is specified, export that key
    if [ -n "$GPG_KEY_ID" ]; then
        log "INFO" "Exporting GPG key $GPG_KEY_ID"
        gpg --armor --export "$GPG_KEY_ID" > "$FULL_BACKUP_PATH/gpg/public-gpg-key.asc" 2>> "$ERROR_LOG"
        if [ $? -eq 0 ]; then
            log "SUCCESS" "Exported GPG public key to $FULL_BACKUP_PATH/gpg/public-gpg-key.asc"
        else
            log "ERROR" "Failed to export GPG public key"
        fi
        
        # Ask for passphrase to export secret key
        echo -e "${YELLOW}Note: You may be prompted for your GPG key passphrase${NC}"
        gpg --armor --export-secret-keys "$GPG_KEY_ID" > "$FULL_BACKUP_PATH/gpg/private-gpg-key.asc" 2>> "$ERROR_LOG"
        if [ $? -eq 0 ]; then
            log "SUCCESS" "Exported GPG private key to $FULL_BACKUP_PATH/gpg/private-gpg-key.asc"
        else
            log "ERROR" "Failed to export GPG private key"
        fi
    else
        # List available GPG keys
        log "INFO" "No GPG key ID specified. Listing available keys:"
        KEY_LIST=$(gpg --list-keys --with-colons | grep "^pub" | cut -d: -f5)
        
        if [ -n "$KEY_LIST" ]; then
            log "INFO" "Available GPG keys: $KEY_LIST"
            echo -e "${YELLOW}Available GPG keys:${NC}"
            gpg --list-keys
            
            read -p "Would you like to export a specific key? (Enter key ID or press Enter to skip): " SELECTED_KEY_ID
            
            if [ -n "$SELECTED_KEY_ID" ]; then
                gpg --armor --export "$SELECTED_KEY_ID" > "$FULL_BACKUP_PATH/gpg/public-gpg-key.asc" 2>> "$ERROR_LOG"
                echo -e "${YELLOW}Note: You may be prompted for your GPG key passphrase${NC}"
                gpg --armor --export-secret-keys "$SELECTED_KEY_ID" > "$FULL_BACKUP_PATH/gpg/private-gpg-key.asc" 2>> "$ERROR_LOG"
                log "SUCCESS" "Exported specified GPG key"
            else
                log "INFO" "Skipping GPG key export"
            fi
        else
            log "WARNING" "No GPG keys found to export"
        fi
    fi
    
    # Backup GPG configuration
    backup_file "$HOME/.gnupg" "$FULL_BACKUP_PATH/gpg/gnupg-backup" "GPG configuration directory"
else
    log "WARNING" "GPG is not installed, skipping GPG backup"
fi

# === ZSH CONFIGURATION ===
echo -e "${BOLD}${BLUE}Backing up Zsh configuration...${NC}"
create_dir_if_needed "$FULL_BACKUP_PATH/zsh"

# Backup various Zsh config files
ZSH_FILES=(".zshrc" ".zshenv" ".zprofile" ".zlogin" ".zlogout" ".antigenrc" ".extrazshrc" ".zsh1" ".aliases" ".zimrc")
ZSH_CONFIGS_FOUND=false

for file in "${ZSH_FILES[@]}"; do
    if backup_file "$HOME/$file" "$FULL_BACKUP_PATH/zsh/" "Zsh config file ($file)"; then
        ZSH_CONFIGS_FOUND=true
    fi
done

# Backup Zsh directories
ZSH_DIRS=(".zshrc.d" ".zsh_files" ".zsh")
for dir in "${ZSH_DIRS[@]}"; do
    if backup_file "$HOME/$dir" "$FULL_BACKUP_PATH/zsh/" "Zsh directory ($dir)"; then
        ZSH_CONFIGS_FOUND=true
    fi
done

if [ "$ZSH_CONFIGS_FOUND" = false ]; then
    log "WARNING" "No Zsh configuration files were found to backup"
fi

# === API KEYS AND CREDENTIALS ===
echo -e "${BOLD}${BLUE}Backing up API keys and credentials...${NC}"
create_dir_if_needed "$FULL_BACKUP_PATH/credentials"

# Backup API keys file(s)
API_KEY_FILES=(".api_keys" ".env" ".credentials" ".tokens")
API_KEYS_FOUND=false

for file in "${API_KEY_FILES[@]}"; do
    if backup_file "$HOME/$file" "$FULL_BACKUP_PATH/credentials/" "API keys file ($file)"; then
        API_KEYS_FOUND=true
    fi
done

# Backup keyrings
if backup_file "$HOME/.local/share/keyrings" "$FULL_BACKUP_PATH/credentials/keyrings" "System keyrings"; then
    API_KEYS_FOUND=true
fi

# Backup Git credentials
GIT_CRED=$(git config --get credential.helper 2>/dev/null)
if [ -n "$GIT_CRED" ]; then
    echo "$GIT_CRED" > "$FULL_BACKUP_PATH/credentials/git-credential-helper"
    log "SUCCESS" "Backed up Git credential helper configuration"
    API_KEYS_FOUND=true
else
    log "WARNING" "Git credential helper not configured"
fi

backup_file "$HOME/.git-credentials" "$FULL_BACKUP_PATH/credentials/" "Git credentials file"

if [ "$API_KEYS_FOUND" = false ]; then
    log "WARNING" "No API keys or credentials were found to backup"
fi

# === CONFIG DIRECTORIES ===
echo -e "${BOLD}${BLUE}Backing up configuration directories...${NC}"

# Ask if user wants to backup .config directory (can be large)
read -p "Would you like to backup the entire .config directory? (y/n): " BACKUP_CONFIG
if [ "$BACKUP_CONFIG" == "y" ] || [ "$BACKUP_CONFIG" == "Y" ]; then
    create_dir_if_needed "$FULL_BACKUP_PATH/config"
    backup_file "$HOME/.config" "$FULL_BACKUP_PATH/config" "Config directory"
else
    log "INFO" "Skipping .config directory as requested"
    
    # Ask for specific config directories to backup
    echo -e "${YELLOW}You can still backup specific config directories.${NC}"
    read -p "Enter specific config directories to backup (separated by space, e.g., 'nvim tmux'): " CONFIG_DIRS
    
    if [ -n "$CONFIG_DIRS" ]; then
        create_dir_if_needed "$FULL_BACKUP_PATH/config"
        for dir in $CONFIG_DIRS; do
            backup_file "$HOME/.config/$dir" "$FULL_BACKUP_PATH/config/" "Config directory ($dir)"
        done
    fi
fi

# === COMPRESSION OPTIONS ===
echo -e "${BOLD}${BLUE}Finalizing backup...${NC}"

# Compression options
echo -e "Compression options:"
echo -e "1. ${BOLD}No compression${NC} - Keep as directory"
echo -e "2. ${BOLD}Single archive${NC} - Create a single compressed file"
echo -e "3. ${BOLD}Split archive${NC} - Split into multiple smaller files"
read -p "Select compression option (1-3): " COMPRESS_OPTION

case $COMPRESS_OPTION in
    1)
        log "INFO" "Keeping backup as directory: $FULL_BACKUP_PATH"
        echo -e "${GREEN}Backup saved as a directory: $FULL_BACKUP_PATH${NC}"
        ;;
    2)
        log "INFO" "Creating compressed backup archive"
        COMPRESSED_FILE="$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
        
        tar -czf "$COMPRESSED_FILE" -C "$FULL_BACKUP_PATH" . 2>> "$ERROR_LOG"
        
        if [ $? -eq 0 ]; then
            rm -rf "$FULL_BACKUP_PATH"
            log "SUCCESS" "Backup compressed to $COMPRESSED_FILE"
            echo -e "${GREEN}Backup compressed to: $COMPRESSED_FILE${NC}"
        else
            log "ERROR" "Failed to compress backup"
            echo -e "${RED}Failed to compress backup. Keeping directory version.${NC}"
        fi
        ;;
    3)
        log "INFO" "Creating split compressed backup archive"
        read -p "Enter split size in MB (default: 60): " SPLIT_SIZE
        SPLIT_SIZE=${SPLIT_SIZE:-60}
        
        COMPRESSED_FILE="$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
        
        echo -e "${YELLOW}Creating split archive (${SPLIT_SIZE}MB parts)...${NC}"
        tar -czf - -C "$FULL_BACKUP_PATH" . 2>> "$ERROR_LOG" | split -b ${SPLIT_SIZE}m - "${COMPRESSED_FILE}."
        
        if [ $? -eq 0 ]; then
            rm -rf "$FULL_BACKUP_PATH"
            log "SUCCESS" "Backup compressed and split into ${SPLIT_SIZE}MB parts: ${COMPRESSED_FILE}.*"
            echo -e "${GREEN}Backup compressed and split into ${SPLIT_SIZE}MB parts: ${COMPRESSED_FILE}.*${NC}"
        else
            log "ERROR" "Failed to compress and split backup"
            echo -e "${RED}Failed to compress and split backup. Keeping directory version.${NC}"
        fi
        ;;
    *)
        log "WARNING" "Invalid compression option, keeping backup as directory"
        echo -e "${YELLOW}Invalid option. Backup saved as a directory: $FULL_BACKUP_PATH${NC}"
        ;;
esac

# === BACKUP SUMMARY ===
echo -e "\n${BOLD}${BLUE}=======================================================${NC}"
echo -e "${BOLD}${BLUE}                   Backup Summary                      ${NC}"
echo -e "${BOLD}${BLUE}=======================================================${NC}"

# Count backups by type
SSH_COUNT=$(find "$FULL_BACKUP_PATH/ssh" -type f 2>/dev/null | wc -l)
GPG_COUNT=$(find "$FULL_BACKUP_PATH/gpg" -type f 2>/dev/null | wc -l)
ZSH_COUNT=$(find "$FULL_BACKUP_PATH/zsh" -type f -o -type d -depth 1 2>/dev/null | wc -l)
CRED_COUNT=$(find "$FULL_BACKUP_PATH/credentials" -type f 2>/dev/null | wc -l)
CONFIG_COUNT=$(find "$FULL_BACKUP_PATH/config" -type d -depth 1 2>/dev/null | wc -l)

# If backup was compressed, use log data
if [ "$COMPRESS_OPTION" -eq 2 ] || [ "$COMPRESS_OPTION" -eq 3 ]; then
    SSH_COUNT=$(grep "Backed up SSH" "$LOG_FILE" | wc -l)
    GPG_COUNT=$(grep "Backed up GPG" "$LOG_FILE" | wc -l)
    ZSH_COUNT=$(grep "Backed up Zsh" "$LOG_FILE" | wc -l)
    CRED_COUNT=$(grep "Backed up.*credentials" "$LOG_FILE" | wc -l)
    CONFIG_COUNT=$(grep "Backed up.*config" "$LOG_FILE" | wc -l)
fi

echo -e "SSH Keys & Configs: ${BOLD}${SSH_COUNT:-0}${NC} items"
echo -e "GPG Keys & Configs: ${BOLD}${GPG_COUNT:-0}${NC} items"
echo -e "Zsh Configuration: ${BOLD}${ZSH_COUNT:-0}${NC} items"
echo -e "Credentials & API Keys: ${BOLD}${CRED_COUNT:-0}${NC} items"
echo -e "Config Directories: ${BOLD}${CONFIG_COUNT:-0}${NC} items"

# Count warnings and errors
WARNING_COUNT=$(grep "\[WARNING\]" "$LOG_FILE" | wc -l)
ERROR_COUNT=$(grep "\[ERROR\]" "$LOG_FILE" | wc -l)

echo
echo -e "Warnings: ${YELLOW}${WARNING_COUNT:-0}${NC}"
echo -e "Errors: ${RED}${ERROR_COUNT:-0}${NC}"
echo

if [ "$ERROR_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}Some errors occurred during backup. Check the error log:${NC}"
    echo -e "${BOLD}$ERROR_LOG${NC}"
fi

echo -e "\n${GREEN}Backup process completed!${NC}"
echo -e "Log file: ${BOLD}$LOG_FILE${NC}"