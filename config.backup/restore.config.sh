#!/bin/bash
# Enhanced Configuration Restore Script
# This script restores configuration backups created by the backup script

set -e

# Terminal colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Define backup directory
BACKUP_DIR="$HOME/back"
DATE=$(date +%Y-%m-%d-%H%M%S)
LOG_FILE="$BACKUP_DIR/restore_$DATE.log"
ERROR_LOG="$BACKUP_DIR/restore_errors_$DATE.log"
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# Create log files
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

# Function to back up existing file before restoring
backup_existing() {
    local file="$1"
    if [ -e "$file" ]; then
        local backup_file="${file}.backup_${TIMESTAMP}"
        cp -r "$file" "$backup_file" 2>> "$ERROR_LOG"
        if [ $? -eq 0 ]; then
            log "INFO" "Created backup of existing file: $backup_file"
            return 0
        else
            log "ERROR" "Failed to back up existing file: $file"
            return 1
        fi
    fi
    return 0
}

# Function to restore a file with validation
restore_file() {
    local source="$1"
    local destination="$2"
    local description="$3"
    
    if [ ! -e "$source" ]; then
        log "WARNING" "$description not found in backup at $source"
        return 1
    fi
    
    # Create destination directory if it doesn't exist
    local dest_dir=$(dirname "$destination")
    if [ ! -d "$dest_dir" ]; then
        mkdir -p "$dest_dir" 2>> "$ERROR_LOG"
        if [ $? -ne 0 ]; then
            log "ERROR" "Failed to create directory: $dest_dir"
            return 1
        fi
    fi
    
    # Back up existing file
    backup_existing "$destination"
    
    # Restore the file
    if [ -d "$source" ]; then
        # For directories, use recursive copy
        cp -r "$source" "$destination" 2>> "$ERROR_LOG"
    else
        # For files, use regular copy
        cp "$source" "$destination" 2>> "$ERROR_LOG"
    fi
    
    if [ $? -eq 0 ]; then
        log "SUCCESS" "Restored $description to $destination"
        
        # Set appropriate permissions for sensitive files
        if [[ "$description" == *"SSH private key"* ]]; then
            chmod 600 "$destination" 2>> "$ERROR_LOG"
            log "INFO" "Set permissions 600 for SSH private key"
        elif [[ "$description" == *"SSH public key"* ]]; then
            chmod 644 "$destination" 2>> "$ERROR_LOG"
            log "INFO" "Set permissions 644 for SSH public key"
        elif [[ "$description" == *"GPG"* ]]; then
            chmod 700 "$destination" 2>> "$ERROR_LOG"
            log "INFO" "Set permissions 700 for GPG directory"
        elif [[ "$description" == *"API keys"* || "$description" == *"credentials"* ]]; then
            chmod 600 "$destination" 2>> "$ERROR_LOG"
            log "INFO" "Set permissions 600 for credentials file"
        fi
        
        return 0
    else
        log "ERROR" "Failed to restore $description to $destination"
        return 1
    fi
}

# Display header
echo -e "${BOLD}${BLUE}=======================================================${NC}"
echo -e "${BOLD}${BLUE}              Configuration Restore Tool               ${NC}"
echo -e "${BOLD}${BLUE}=======================================================${NC}"
echo

log "INFO" "Starting restore process"
echo -e "Log file: ${BOLD}$LOG_FILE${NC}"
echo

# List available backups
echo -e "${BOLD}${BLUE}Checking for available backups...${NC}"
available_backups=($(find "$BACKUP_DIR" -maxdepth 1 \( -name "backup_*" -o -name "backup_*.tar.gz" -o -name "backup_*.tar.gz.aa" \) | sort -r))

if [ ${#available_backups[@]} -eq 0 ]; then
    log "ERROR" "No backups found in $BACKUP_DIR"
    echo -e "${RED}No backups found in $BACKUP_DIR. Exiting.${NC}"
    exit 1
fi

# Group split archives together
declare -A backup_groups
for backup in "${available_backups[@]}"; do
    # Extract filename from path
    filename=$(basename "$backup")
    
    # If it's a split archive, group by base name
    if [[ "$filename" =~ backup_.*\.tar\.gz\.[a-z]{2}$ ]]; then
        base_name="${filename%.tar.gz.*}.tar.gz"
        backup_groups["$base_name"]=1
    # Regular backups (directories or single archives)
    elif [[ "$filename" =~ ^backup_ ]]; then
        backup_groups["$filename"]=1
    fi
done

# Display grouped backups
echo -e "${CYAN}Available backups:${NC}"
PS3="Select a backup to restore: "

select_options=()
for key in "${!backup_groups[@]}"; do
    # Check if it's a split backup
    if find "$BACKUP_DIR" -name "${key}.*" -print -quit | grep -q .; then
        select_options+=("$key (Split Archive)")
    elif [ -f "$BACKUP_DIR/$key" ]; then
        select_options+=("$key (Archive)")
    elif [ -d "$BACKUP_DIR/$key" ]; then
        select_options+=("$key (Directory)")
    fi
done

# Sort options by date (most recent first)
IFS=$'\n' sorted_options=($(sort -r <<<"${select_options[*]}"))
unset IFS

select SELECTED_OPTION in "${sorted_options[@]}" "Quit"; do
    if [ "$SELECTED_OPTION" == "Quit" ]; then
        log "INFO" "User cancelled the restore operation"
        echo -e "${YELLOW}Restore operation cancelled by user.${NC}"
        exit 0
    elif [ -n "$SELECTED_OPTION" ]; then
        # Extract the actual backup name without the type
        SELECTED_BACKUP=$(echo "$SELECTED_OPTION" | sed 's/ (.*)//')
        log "INFO" "Selected backup: $SELECTED_BACKUP"
        echo -e "${GREEN}You selected: $SELECTED_BACKUP${NC}"
        break
    else
        echo -e "${RED}Invalid selection. Please try again.${NC}"
    fi
done

# Create a temporary directory for extraction if needed
TEMP_DIR=$(mktemp -d)
log "INFO" "Created temporary directory: $TEMP_DIR"

# Process the selected backup
if [[ "$SELECTED_OPTION" == *"(Split Archive)"* ]]; then
    log "INFO" "Processing split archive: $SELECTED_BACKUP"
    echo -e "${BLUE}Reassembling split backup: $SELECTED_BACKUP${NC}"
    
    # Count parts to estimate progress
    part_count=$(find "$BACKUP_DIR" -name "${SELECTED_BACKUP}.*" | wc -l)
    log "INFO" "Found $part_count parts of the split archive"
    
    # Concatenate parts
    echo -e "${YELLOW}Reassembling $part_count parts...${NC}"
    cat "$BACKUP_DIR/${SELECTED_BACKUP}".* > "$TEMP_DIR/${SELECTED_BACKUP}" 2>> "$ERROR_LOG"
    
    if [ $? -ne 0 ]; then
        log "ERROR" "Failed to reassemble split archive"
        echo -e "${RED}Failed to reassemble split archive. Exiting.${NC}"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    # Extract the archive
    echo -e "${YELLOW}Extracting archive...${NC}"
    tar -xzf "$TEMP_DIR/${SELECTED_BACKUP}" -C "$TEMP_DIR" 2>> "$ERROR_LOG"
    
    if [ $? -ne 0 ]; then
        log "ERROR" "Failed to extract archive"
        echo -e "${RED}Failed to extract archive. Exiting.${NC}"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    RESTORE_PATH="$TEMP_DIR"
    
elif [[ "$SELECTED_OPTION" == *"(Archive)"* ]]; then
    log "INFO" "Processing single archive: $SELECTED_BACKUP"
    echo -e "${BLUE}Extracting archive: $SELECTED_BACKUP${NC}"
    
    # Extract the archive
    tar -xzf "$BACKUP_DIR/$SELECTED_BACKUP" -C "$TEMP_DIR" 2>> "$ERROR_LOG"
    
    if [ $? -ne 0 ]; then
        log "ERROR" "Failed to extract archive"
        echo -e "${RED}Failed to extract archive. Exiting.${NC}"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    RESTORE_PATH="$TEMP_DIR"
    
elif [[ "$SELECTED_OPTION" == *"(Directory)"* ]]; then
    log "INFO" "Using directory backup: $SELECTED_BACKUP"
    echo -e "${BLUE}Using directory backup: $SELECTED_BACKUP${NC}"
    RESTORE_PATH="$BACKUP_DIR/$SELECTED_BACKUP"
    
    # Verify it's a valid backup directory
    if [ ! -d "$RESTORE_PATH" ]; then
        log "ERROR" "Selected backup is not a valid directory"
        echo -e "${RED}Selected backup is not a valid directory. Exiting.${NC}"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
fi

# Verify backup contents
echo -e "${BLUE}Verifying backup contents...${NC}"

# Check main backup directories we expect to find
backup_valid=true
expected_dirs=("ssh" "gpg" "zsh" "credentials" "config")
missing_dirs=()

for dir in "${expected_dirs[@]}"; do
    if [ ! -d "$RESTORE_PATH/$dir" ] && [ ! -d "$RESTORE_PATH/ssh" ]; then
        # For backwards compatibility, check traditional flat structure too
        case $dir in
            "ssh")
                if [ ! -f "$RESTORE_PATH/id" ] && [ ! -f "$RESTORE_PATH/id.pub" ]; then
                    missing_dirs+=("$dir")
                    backup_valid=false
                fi
                ;;
            "gpg")
                if [ ! -f "$RESTORE_PATH/public-gpg-key.asc" ] && [ ! -f "$RESTORE_PATH/private-gpg-key.asc" ] && [ ! -d "$RESTORE_PATH/gnupg-backup" ]; then
                    missing_dirs+=("$dir")
                    backup_valid=false
                fi
                ;;
            "zsh")
                if [ ! -f "$RESTORE_PATH/.zshrc" ] && [ ! -f "$RESTORE_PATH/.antigenrc" ]; then
                    missing_dirs+=("$dir")
                    backup_valid=false
                fi
                ;;
            "credentials")
                if [ ! -f "$RESTORE_PATH/api_keys-backup" ] && [ ! -d "$RESTORE_PATH/keyrings" ]; then
                    missing_dirs+=("$dir")
                    backup_valid=false
                fi
                ;;
            "config")
                if [ ! -d "$RESTORE_PATH/config-backup" ]; then
                    missing_dirs+=("$dir")
                    backup_valid=false
                fi
                ;;
        esac
    fi
done

if [ "$backup_valid" = false ]; then
    log "WARNING" "Backup is missing some expected directories: ${missing_dirs[*]}"
    echo -e "${YELLOW}Warning: This backup may be incomplete. Missing: ${missing_dirs[*]}${NC}"
    
    read -p "Continue with restoration anyway? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        log "INFO" "User cancelled the restore operation due to incomplete backup"
        echo -e "${YELLOW}Restore operation cancelled.${NC}"
        rm -rf "$TEMP_DIR"
        exit 0
    fi
fi

# Display backup structure for verification
echo -e "${CYAN}Backup structure:${NC}"
if command -v tree &>/dev/null; then
    tree -L 2 "$RESTORE_PATH" | head -n 20
    if [ "$(find "$RESTORE_PATH" -type f -o -type d | wc -l)" -gt 20 ]; then
        echo -e "${YELLOW}(Output truncated for readability)${NC}"
    fi
else
    ls -la "$RESTORE_PATH" | head -n 20
    if [ "$(ls -1 "$RESTORE_PATH" | wc -l)" -gt 20 ]; then
        echo -e "${YELLOW}(Output truncated for readability)${NC}"
    fi
fi

echo
echo -e "${BOLD}${BLUE}=======================================================${NC}"
echo -e "${BOLD}${BLUE}               Restoration Options                     ${NC}"
echo -e "${BOLD}${BLUE}=======================================================${NC}"
echo

# === SSH KEYS RESTORATION ===
echo -e "${BOLD}${CYAN}1. SSH Keys Restoration${NC}"
if [ -d "$RESTORE_PATH/ssh" ] || [ -f "$RESTORE_PATH/id" ] || [ -f "$RESTORE_PATH/id.pub" ]; then
    read -p "Restore SSH keys? (y/n): " RESTORE_SSH
    if [ "$RESTORE_SSH" == "y" ]; then
        log "INFO" "Starting SSH key restoration"
        echo -e "${BLUE}Restoring SSH keys...${NC}"
        
        # Create .ssh directory if it doesn't exist
        mkdir -p ~/.ssh
        
        # For new backup format
        if [ -d "$RESTORE_PATH/ssh" ]; then
            # Restore SSH keys from the ssh directory
            SSH_KEY_TYPES=("id_rsa" "id_ed25519" "id_ecdsa" "id_dsa" "id")
            
            for key_type in "${SSH_KEY_TYPES[@]}"; do
                if [ -f "$RESTORE_PATH/ssh/$key_type" ]; then
                    restore_file "$RESTORE_PATH/ssh/$key_type" "$HOME/.ssh/$key_type" "SSH private key ($key_type)"
                fi
                
                if [ -f "$RESTORE_PATH/ssh/$key_type.pub" ]; then
                    restore_file "$RESTORE_PATH/ssh/$key_type.pub" "$HOME/.ssh/$key_type.pub" "SSH public key ($key_type)"
                fi
            done
            
            # Restore SSH config and known_hosts
            restore_file "$RESTORE_PATH/ssh/config" "$HOME/.ssh/config" "SSH config file"
            restore_file "$RESTORE_PATH/ssh/known_hosts" "$HOME/.ssh/known_hosts" "SSH known hosts file"
            
        # For old backup format
        else
            # Restore individual SSH keys
            if [ -f "$RESTORE_PATH/id" ]; then
                restore_file "$RESTORE_PATH/id" "$HOME/.ssh/id" "SSH private key"
            fi
            
            if [ -f "$RESTORE_PATH/id.pub" ]; then
                restore_file "$RESTORE_PATH/id.pub" "$HOME/.ssh/id.pub" "SSH public key" 
            fi
        fi
        
        log "SUCCESS" "SSH key restoration completed"
        echo -e "${GREEN}SSH keys restored.${NC}"
    else
        log "INFO" "Skipping SSH key restoration as requested"
        echo -e "${YELLOW}Skipping SSH key restoration.${NC}"
    fi
else
    log "WARNING" "No SSH keys found in backup"
    echo -e "${YELLOW}No SSH keys found in backup, skipping...${NC}"
fi

# === GPG KEYS RESTORATION ===
echo -e "${BOLD}${CYAN}2. GPG Keys Restoration${NC}"
if [ -d "$RESTORE_PATH/gpg" ] || [ -f "$RESTORE_PATH/public-gpg-key.asc" ] || [ -f "$RESTORE_PATH/private-gpg-key.asc" ] || [ -d "$RESTORE_PATH/gnupg-backup" ]; then
    read -p "Restore GPG keys? (y/n): " RESTORE_GPG
    if [ "$RESTORE_GPG" == "y" ]; then
        log "INFO" "Starting GPG key restoration"
        echo -e "${BLUE}Restoring GPG keys...${NC}"
        
        # Check if GPG is installed
        if ! command -v gpg &>/dev/null; then
            log "ERROR" "GPG is not installed"
            echo -e "${RED}Error: GPG is not installed. Please install GPG first.${NC}"
        else
            # For new backup format
            if [ -d "$RESTORE_PATH/gpg" ]; then
                # Import GPG keys
                if [ -f "$RESTORE_PATH/gpg/private-gpg-key.asc" ]; then
                    echo -e "${YELLOW}Importing GPG private key...${NC}"
                    gpg --batch --import "$RESTORE_PATH/gpg/private-gpg-key.asc" 2>> "$ERROR_LOG"
                    if [ $? -eq 0 ]; then
                        log "SUCCESS" "Imported GPG private key"
                        echo -e "${GREEN}GPG private key imported.${NC}"
                    else
                        log "ERROR" "Failed to import GPG private key"
                        echo -e "${RED}Failed to import GPG private key.${NC}"
                    fi
                fi
                
                if [ -f "$RESTORE_PATH/gpg/public-gpg-key.asc" ]; then
                    echo -e "${YELLOW}Importing GPG public key...${NC}"
                    gpg --batch --import "$RESTORE_PATH/gpg/public-gpg-key.asc" 2>> "$ERROR_LOG"
                    if [ $? -eq 0 ]; then
                        log "SUCCESS" "Imported GPG public key"
                        echo -e "${GREEN}GPG public key imported.${NC}"
                    else
                        log "ERROR" "Failed to import GPG public key"
                        echo -e "${RED}Failed to import GPG public key.${NC}"
                    fi
                fi
                
                # Restore GPG configuration
                if [ -d "$RESTORE_PATH/gpg/gnupg-backup" ]; then
                    # Backup existing .gnupg
                    backup_existing "$HOME/.gnupg"
                    
                    # Remove existing .gnupg before restoring
                    if [ -d "$HOME/.gnupg" ]; then
                        rm -rf "$HOME/.gnupg"
                    fi
                    
                    # Restore configuration
                    restore_file "$RESTORE_PATH/gpg/gnupg-backup" "$HOME/.gnupg" "GPG configuration"
                    chmod -R 700 "$HOME/.gnupg" 2>> "$ERROR_LOG"
                fi
                
            # For old backup format
            else
                # Import GPG keys
                if [ -f "$RESTORE_PATH/private-gpg-key.asc" ]; then
                    gpg --batch --import "$RESTORE_PATH/private-gpg-key.asc" 2>> "$ERROR_LOG"
                    if [ $? -eq 0 ]; then
                        log "SUCCESS" "Imported GPG private key"
                        echo -e "${GREEN}GPG private key imported.${NC}"
                    else
                        log "ERROR" "Failed to import GPG private key"
                        echo -e "${RED}Failed to import GPG private key.${NC}"
                    fi
                fi
                
                if [ -f "$RESTORE_PATH/public-gpg-key.asc" ]; then
                    gpg --batch --import "$RESTORE_PATH/public-gpg-key.asc" 2>> "$ERROR_LOG"
                    if [ $? -eq 0 ]; then
                        log "SUCCESS" "Imported GPG public key"
                        echo -e "${GREEN}GPG public key imported.${NC}"
                    else
                        log "ERROR" "Failed to import GPG public key"
                        echo -e "${RED}Failed to import GPG public key.${NC}"
                    fi
                fi
                
                # Restore GPG configuration
                if [ -d "$RESTORE_PATH/gnupg-backup" ]; then
                    restore_file "$RESTORE_PATH/gnupg-backup" "$HOME/.gnupg" "GPG configuration"
                    chmod -R 700 "$HOME/.gnupg" 2>> "$ERROR_LOG"
                fi
            fi
            
            log "SUCCESS" "GPG key restoration completed"
            echo -e "${GREEN}GPG keys restored.${NC}"
        fi
    else
        log "INFO" "Skipping GPG key restoration as requested"
        echo -e "${YELLOW}Skipping GPG key restoration.${NC}"
    fi
else
    log "WARNING" "No GPG keys found in backup"
    echo -e "${YELLOW}No GPG keys found in backup, skipping...${NC}"
fi

# === API KEYS RESTORATION ===
echo -e "${BOLD}${CYAN}3. API Keys & Credentials Restoration${NC}"
if [ -d "$RESTORE_PATH/credentials" ] || [ -f "$RESTORE_PATH/api_keys-backup" ]; then
    read -p "Restore API keys and credentials? (y/n): " RESTORE_API
    if [ "$RESTORE_API" == "y" ]; then
        log "INFO" "Starting API keys and credentials restoration"
        echo -e "${BLUE}Restoring API keys and credentials...${NC}"
        
        # For new backup format
        if [ -d "$RESTORE_PATH/credentials" ]; then
            # Restore API key files
            API_KEY_FILES=(".api_keys" ".env" ".credentials" ".tokens")
            
            for file in "${API_KEY_FILES[@]}"; do
                if [ -f "$RESTORE_PATH/credentials/$file" ]; then
                    restore_file "$RESTORE_PATH/credentials/$file" "$HOME/$file" "API keys file ($file)"
                    chmod 600 "$HOME/$file" 2>> "$ERROR_LOG"
                fi
            done
            
            # Restore keyrings
            if [ -d "$RESTORE_PATH/credentials/keyrings" ]; then
                mkdir -p "$HOME/.local/share"
                restore_file "$RESTORE_PATH/credentials/keyrings" "$HOME/.local/share/keyrings" "System keyrings"
                chmod -R 700 "$HOME/.local/share/keyrings" 2>> "$ERROR_LOG"
            fi
            
            # Restore Git credentials
            if [ -f "$RESTORE_PATH/credentials/git-credential-helper" ]; then
                GIT_CRED=$(cat "$RESTORE_PATH/credentials/git-credential-helper")
                git config --global credential.helper "$GIT_CRED" 2>> "$ERROR_LOG"
                log "SUCCESS" "Restored Git credential helper configuration: $GIT_CRED"
                echo -e "${GREEN}Git credential helper configuration restored.${NC}"
            fi
            
        # For old backup format
        else
            if [ -f "$RESTORE_PATH/api_keys-backup" ]; then
                restore_file "$RESTORE_PATH/api_keys-backup" "$HOME/.api_keys" "API keys file"
                chmod 600 "$HOME/.api_keys" 2>> "$ERROR_LOG"
            fi
            
            # Restore keyrings from old format
            if [ -d "$RESTORE_PATH/keyrings" ]; then
                mkdir -p "$HOME/.local/share"
                restore_file "$RESTORE_PATH/keyrings" "$HOME/.local/share/keyrings" "System keyrings"
                chmod -R 700 "$HOME/.local/share/keyrings" 2>> "$ERROR_LOG"
            fi
            
            # Restore Git credential helper from old format
            if [ -f "$RESTORE_PATH/git-credential-helper" ]; then
                GIT_CRED=$(cat "$RESTORE_PATH/git-credential-helper")
                git config --global credential.helper "$GIT_CRED" 2>> "$ERROR_LOG"
                log "SUCCESS" "Restored Git credential helper configuration: $GIT_CRED"
                echo -e "${GREEN}Git credential helper configuration restored.${NC}"
            fi
        }
        
        log "SUCCESS" "API keys and credentials restoration completed"
        echo -e "${GREEN}API keys and credentials restored.${NC}"
    else
        log "INFO" "Skipping API keys and credentials restoration as requested"
        echo -e "${YELLOW}Skipping API keys and credentials restoration.${NC}"
    fi
else
    log "WARNING" "No API keys or credentials found in backup"
    echo -e "${YELLOW}No API keys or credentials found in backup, skipping...${NC}"
fi

# === ZSH CONFIGURATION RESTORATION ===
echo -e "${BOLD}${CYAN}4. Zsh Configuration Restoration${NC}"
if [ -d "$RESTORE_PATH/zsh" ] || [ -f "$RESTORE_PATH/.zshrc" ]; then
    read -p "Restore Zsh configuration? (y/n): " RESTORE_ZSH
    if [ "$RESTORE_ZSH" == "y" ]; then
        log "INFO" "Starting Zsh configuration restoration"
        echo -e "${BLUE}Restoring Zsh configuration...${NC}"
        
        # For new backup format
        if [ -d "$RESTORE_PATH/zsh" ]; then
            # Restore Zsh config files
            ZSH_FILES=(".zshrc" ".zshenv" ".zprofile" ".zlogin" ".zlogout" ".antigenrc" ".extrazshrc" ".zsh1" ".aliases" ".zimrc")
            
            for file in "${ZSH_FILES[@]}"; do
                if [ -f "$RESTORE_PATH/zsh/$file" ]; then
                    restore_file "$RESTORE_PATH/zsh/$file" "$HOME/$file" "Zsh config file ($file)"
                fi
            done
            
            # Restore Zsh directories
            ZSH_DIRS=(".zshrc.d" ".zsh_files" ".zsh")
            
            for dir in "${ZSH_DIRS[@]}"; do
                if [ -d "$RESTORE_PATH/zsh/$dir" ]; then
                    restore_file "$RESTORE_PATH/zsh/$dir" "$HOME/$dir" "Zsh directory ($dir)"
                fi
            done
            
        # For old backup format
        else
            # Restore Zsh config files from flat structure
            ZSH_FILES=(".zshrc" ".antigenrc" ".extrazshrc" ".zsh1" ".aliases" ".zimrc")
            
            for file in "${ZSH_FILES[@]}"; do
                if [ -f "$RESTORE_PATH/$file" ]; then
                    restore_file "$RESTORE_PATH/$file" "$HOME/$file" "Zsh config file ($file)"
                fi
            done
            
            # Restore additional Zsh directories from old format
            if [ -d "$RESTORE_PATH/zsh_files" ]; then
                restore_file "$RESTORE_PATH/zsh_files" "$HOME/.zsh_files" "Zsh files directory"
            fi
            
            if [ -d "$RESTORE_PATH/.zshrc.d" ]; then
                restore_file "$RESTORE_PATH/.zshrc.d" "$HOME/.zshrc.d" "Zsh config directory"
            fi
        fi
        
        log "SUCCESS" "Zsh configuration restoration completed"
        echo -e "${GREEN}Zsh configuration restored.${NC}"
    else
        log "INFO" "Skipping Zsh configuration restoration as requested"
        echo -e "${YELLOW}Skipping Zsh configuration restoration.${NC}"
    fi
else
    log "WARNING" "No Zsh configuration found in backup"
    echo -e "${YELLOW}No Zsh configuration found in backup, skipping...${NC}"
fi

# === CONFIG DIRECTORY RESTORATION ===
echo -e "${BOLD}${CYAN}5. Configuration Directory Restoration${NC}"
if [ -d "$RESTORE_PATH/config" ] || [ -d "$RESTORE_PATH/config-backup" ]; then
    read -p "Restore .config directory? (y/n): " RESTORE_CONFIG
    if [ "$RESTORE_CONFIG" == "y" ]; then
        log "INFO" "Starting .config directory restoration"
        
        # Ask whether to restore the entire directory or select specific configs
        echo -e "${YELLOW}Warning: Restoring the entire .config directory may overwrite current configurations.${NC}"
        echo -e "1. ${BOLD}Restore entire .config directory${NC}"
        echo -e "2. ${BOLD}Select specific config directories to restore${NC}"
        echo -e "3. ${BOLD}Skip .config restoration${NC}"
        
        read -p "Select an option (1-3): " CONFIG_OPTION
        
        case $CONFIG_OPTION in
            1)
                echo -e "${BLUE}Restoring entire .config directory...${NC}"
                
                # For new backup format
                if [ -d "$RESTORE_PATH/config" ]; then
                    # Check if it contains multiple subdirectories or a single config-backup directory
                    if [ -d "$RESTORE_PATH/config/config-backup" ]; then
                        # Handle old format stored in new structure
                        restore_file "$RESTORE_PATH/config/config-backup" "$HOME/.config" "Config directory"
                    else
                        # Backup existing .config
                        backup_existing "$HOME/.config"
                        
                        # For each subdirectory in the backup config, copy it to the .config directory
                        for config_dir in "$RESTORE_PATH/config"/*; do
                            if [ -d "$config_dir" ]; then
                                dir_name=$(basename "$config_dir")
                                restore_file "$config_dir" "$HOME/.config/$dir_name" "Config directory ($dir_name)"
                            fi
                        done
                    fi
                    
                # For old backup format
                elif [ -d "$RESTORE_PATH/config-backup" ]; then
                    restore_file "$RESTORE_PATH/config-backup" "$HOME/.config" "Config directory"
                fi
                ;;
                
            2)
                echo -e "${BLUE}Available config directories:${NC}"
                
                # Determine the path to config directories
                if [ -d "$RESTORE_PATH/config" ]; then
                    CONFIG_BASE="$RESTORE_PATH/config"
                    
                    # Handle old format stored in new structure
                    if [ -d "$RESTORE_PATH/config/config-backup" ]; then
                        CONFIG_BASE="$RESTORE_PATH/config/config-backup"
                    fi
                elif [ -d "$RESTORE_PATH/config-backup" ]; then
                    CONFIG_BASE="$RESTORE_PATH/config-backup"
                fi
                
                # List subdirectories
                available_configs=($(find "$CONFIG_BASE" -maxdepth 1 -type d | grep -v "^$CONFIG_BASE$" | sort))
                
                # If there are no subdirectories, show a message and return
                if [ ${#available_configs[@]} -eq 0 ]; then
                    log "WARNING" "No config subdirectories found in backup"
                    echo -e "${YELLOW}No config subdirectories found in backup, skipping...${NC}"
                    break
                fi
                
                # Format and display the options
                config_options=()
                i=1
                for config in "${available_configs[@]}"; do
                    config_name=$(basename "$config")
                    echo -e "${MAGENTA}$i)${NC} $config_name"
                    config_options[$i]="$config_name"
                    ((i++))
                done
                
                # Ask for selection
                echo -e "${CYAN}Enter the numbers of the configs to restore (separated by spaces, e.g., '1 3 5'):${NC}"
                read -r selected_nums
                
                # Process the selection
                for num in $selected_nums; do
                    if [ -n "${config_options[$num]}" ]; then
                        config_name="${config_options[$num]}"
                        echo -e "${BLUE}Restoring .config/$config_name...${NC}"
                        
                        mkdir -p "$HOME/.config"
                        restore_file "$CONFIG_BASE/$config_name" "$HOME/.config/$config_name" "Config directory ($config_name)"
                        
                        log "SUCCESS" "Restored config directory: $config_name"
                    else
                        log "WARNING" "Invalid config selection: $num"
                        echo -e "${YELLOW}Invalid selection: $num${NC}"
                    fi
                done
                ;;
                
            3|*)
                log "INFO" "Skipping .config directory restoration as requested"
                echo -e "${YELLOW}Skipping .config directory restoration.${NC}"
                ;;
        esac
        
        log "SUCCESS" ".config directory restoration completed"
        echo -e "${GREEN}.config directory restoration completed.${NC}"
    else
        log "INFO" "Skipping .config directory restoration as requested"
        echo -e "${YELLOW}Skipping .config directory restoration.${NC}"
    fi
else
    log "WARNING" "No .config directory found in backup"
    echo -e "${YELLOW}No .config directory found in backup, skipping...${NC}"
fi

# Cleanup
if [ -d "$TEMP_DIR" ]; then
    echo -e "${BLUE}Cleaning up temporary files...${NC}"
    rm -rf "$TEMP_DIR"
    log "INFO" "Removed temporary directory: $TEMP_DIR"
fi

# === RESTORE SUMMARY ===
echo -e "\n${BOLD}${BLUE}=======================================================${NC}"
echo -e "${BOLD}${BLUE}                   Restore Summary                     ${NC}"
echo -e "${BOLD}${BLUE}=======================================================${NC}"

SUCCESS_COUNT=$(grep "\[SUCCESS\]" "$LOG_FILE" | wc -l)
WARNING_COUNT=$(grep "\[WARNING\]" "$LOG_FILE" | wc -l)
ERROR_COUNT=$(grep "\[ERROR\]" "$LOG_FILE" | wc -l)

echo -e "Successful operations: ${GREEN}${SUCCESS_COUNT:-0}${NC}"
echo -e "Warnings: ${YELLOW}${WARNING_COUNT:-0}${NC}"
echo -e "Errors: ${RED}${ERROR_COUNT:-0}${NC}"
echo

if [ "$ERROR_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}Some errors occurred during restoration. Check the error log:${NC}"
    echo -e "${BOLD}$ERROR_LOG${NC}"
    
    # Display the first few errors
    echo -e "\n${BOLD}${RED}First few errors:${NC}"
    grep "\[ERROR\]" "$LOG_FILE" | head -n 3 | sed 's/\[ERROR\]//' | sed 's/^.*\]//'
    
    if [ "$(grep "\[ERROR\]" "$LOG_FILE" | wc -l)" -gt 3 ]; then
        echo -e "${YELLOW}(More errors in the log file)${NC}"
    fi
fi

if [ "$WARNING_COUNT" -gt 0 ]; then
    echo -e "\n${YELLOW}Note: Any existing files that were replaced have been backed up with a timestamp suffix.${NC}"
    echo -e "${YELLOW}Look for files with .backup_${TIMESTAMP} extension if you need to recover the previous versions.${NC}"
fi

echo -e "\n${GREEN}Restore process completed!${NC}"
echo -e "Log file: ${BOLD}$LOG_FILE${NC}"