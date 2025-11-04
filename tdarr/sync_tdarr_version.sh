#!/bin/bash
set -e

# Tdarr Version Sync Script
# Automatically checks server version and updates node container if needed
# Preserves all existing configuration including /share directory access

# Configuration (can be overridden with environment variables)
SERVER_IP="${TDARR_SERVER_IP:-192.168.1.210}"
SERVER_PORT="${TDARR_SERVER_PORT:-8266}"
CONTAINER_NAME="${TDARR_CONTAINER_NAME:-tdarr-node}"
NODE_NAME="${TDARR_NODE_NAME:-omarchy-node}"
SHARE_PATH="${TDARR_SHARE_PATH:-/share}"
TRANS_PATH="${TDARR_TRANS_PATH:-/share/trans}"
LOG_FILE="${TDARR_LOG_FILE:-$HOME/.local/log/tdarr-version-sync.log}"
DRY_RUN="${TDARR_DRY_RUN:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Color based on level
    case "$level" in
        "INFO")  color="$GREEN" ;;
        "WARN")  color="$YELLOW" ;;
        "ERROR") color="$RED" ;;
        "DEBUG") color="$BLUE" ;;
        *)       color="$NC" ;;
    esac
    
    # Print to stderr with color (avoid polluting stdout for command substitution)
    echo -e "${color}[$timestamp] [$level] $message${NC}" >&2
    
    # Log to file without color
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Function to get server version
get_server_version() {
    local timeout=10
    local server_version=""
    
    log "INFO" "Checking Tdarr server version at $SERVER_IP:$SERVER_PORT"
    
    # Try to get version from server API
    if command -v curl >/dev/null 2>&1; then
        server_version=$(timeout $timeout curl -s "http://$SERVER_IP:$SERVER_PORT/api/v2/status" 2>/dev/null | \
            grep -o '"version":"[^"]*"' | cut -d'"' -f4 || echo "")
    else
        log "WARN" "curl not available, trying alternative method"
        # Fallback: try to extract from a simple HTTP request
        server_version=$(timeout $timeout bash -c "echo 'GET /api/v2/status HTTP/1.1\r\nHost: $SERVER_IP:$SERVER_PORT\r\n\r\n' | nc $SERVER_IP $SERVER_PORT" 2>/dev/null | \
            grep -o '"version":"[^"]*"' | cut -d'"' -f4 || echo "")
    fi
    
    if [ -z "$server_version" ]; then
        log "ERROR" "Could not retrieve server version from $SERVER_IP:$SERVER_PORT"
        return 1
    fi
    
    log "INFO" "Server version: $server_version"
    echo "$server_version"
}

# Function to get current node container version
get_node_version() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log "WARN" "Container $CONTAINER_NAME is not running"
        return 1
    fi
    
    local node_version=$(docker inspect "$CONTAINER_NAME" --format '{{.Config.Image}}' | cut -d':' -f2)
    
    if [ -z "$node_version" ]; then
        log "ERROR" "Could not determine node container version"
        return 1
    fi
    
    log "INFO" "Node version: $node_version"
    echo "$node_version"
}

# Function to check if versions match
versions_match() {
    local server_version="$1"
    local node_version="$2"
    
    if [ "$server_version" = "$node_version" ]; then
        log "INFO" "Versions match: $server_version"
        return 0
    else
        log "WARN" "Version mismatch - Server: $server_version, Node: $node_version"
        return 1
    fi
}

# Function to backup current container configuration
backup_container_config() {
    local backup_file="/tmp/tdarr-container-backup-$(date +%Y%m%d-%H%M%S).json"
    
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log "INFO" "Backing up container configuration to $backup_file"
        docker inspect "$CONTAINER_NAME" > "$backup_file"
        echo "$backup_file"
    else
        log "WARN" "No container to backup"
        return 1
    fi
}

# Function to update node container
update_node_container() {
    local new_version="$1"
    
    if [ "$DRY_RUN" = "true" ]; then
        log "INFO" "DRY RUN: Would update container to version $new_version"
        return 0
    fi
    
    log "INFO" "Updating Tdarr node container to version $new_version"
    
    # Backup current configuration
    backup_container_config
    
    # Check if /share paths exist
    if [ ! -d "$SHARE_PATH" ]; then
        log "ERROR" "Share path $SHARE_PATH does not exist!"
        return 1
    fi
    
    if [ ! -d "$TRANS_PATH" ]; then
        log "ERROR" "Trans path $TRANS_PATH does not exist!"
        return 1
    fi
    
    # Stop existing container
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log "INFO" "Stopping existing container"
        docker stop "$CONTAINER_NAME"
    fi
    
    # Remove existing container
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log "INFO" "Removing existing container"
        docker rm "$CONTAINER_NAME"
    fi
    
    # Pull new image
    log "INFO" "Pulling new image: haveagitgat/tdarr_node:$new_version"
    if ! docker pull "haveagitgat/tdarr_node:$new_version"; then
        log "ERROR" "Failed to pull image version $new_version"
        return 1
    fi
    
    # Start new container with same configuration
    log "INFO" "Starting new container with version $new_version"
    
    # Build docker command (replicating your exact current setup)
    local docker_cmd="docker run -d \\
        --name $CONTAINER_NAME \\
        --restart unless-stopped \\
        --gpus all \\
        --device /dev/dri:/dev/dri \\
        -v $TRANS_PATH:/tmp \\
        -v $SHARE_PATH:/media \\
        -v $HOME/Tdarr/configs:/app/configs \\
        -e serverIP=$SERVER_IP \\
        -e serverPort=$SERVER_PORT \\
        -e nodeName=$NODE_NAME \\
        -e internalNode=true \\
        -e inContainer=true \\
        -e LIBVA_DRIVER_NAME=iHD \\
        haveagitgat/tdarr_node:$new_version"
    
    if eval "$docker_cmd"; then
        log "INFO" "Container successfully started with version $new_version"
        
        # Wait a bit and check if container is running
        sleep 10
        if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
            log "INFO" "Container is running successfully"
        else
            log "ERROR" "Container failed to start properly"
            log "INFO" "Container logs:"
            docker logs "$CONTAINER_NAME" --tail 20 >> "$LOG_FILE" 2>&1
            return 1
        fi
    else
        log "ERROR" "Failed to start new container"
        return 1
    fi
}

# Function to clean up old images
cleanup_old_images() {
    if [ "$DRY_RUN" = "true" ]; then
        log "INFO" "DRY RUN: Would clean up old Tdarr images"
        return 0
    fi
    
    log "INFO" "Cleaning up old Tdarr node images"
    docker image prune -f --filter "dangling=true" || true
    
    # Remove old tagged images (keep current one)
    local current_version=$(get_node_version)
    docker images --format "{{.Repository}}:{{.Tag}}" | grep "haveagitgat/tdarr_node:" | \
        grep -v ":$current_version" | while read -r image; do
        log "INFO" "Removing old image: $image"
        docker rmi "$image" || true
    done
}

# Main function
main() {
    local force_update=false
    local skip_cleanup=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force|-f)
                force_update=true
                shift
                ;;
            --dry-run|-n)
                DRY_RUN=true
                shift
                ;;
            --skip-cleanup)
                skip_cleanup=true
                shift
                ;;
            --server-ip)
                SERVER_IP="$2"
                shift 2
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --force, -f           Force update even if versions match"
                echo "  --dry-run, -n         Show what would be done without making changes"
                echo "  --skip-cleanup        Don't clean up old Docker images"
                echo "  --server-ip IP        Override server IP address"
                echo "  --help, -h            Show this help message"
                exit 0
                ;;
            *)
                log "ERROR" "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    log "INFO" "Starting Tdarr version sync check"
    
    # Ensure log directory exists
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Check if Docker is available
    if ! command -v docker >/dev/null 2>&1; then
        log "ERROR" "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        log "ERROR" "Docker is not running or not accessible"
        exit 1
    fi
    
    # Get versions
    local server_version
    local node_version
    
    server_version=$(get_server_version)
    if [ $? -ne 0 ] || [ -z "$server_version" ]; then
        log "ERROR" "Failed to get server version"
        exit 1
    fi
    
    node_version=$(get_node_version)
    if [ $? -ne 0 ] || [ -z "$node_version" ]; then
        log "WARN" "Failed to get node version, container might not be running"
        node_version="unknown"
    fi
    
    # Check if update is needed
    if [ "$force_update" = "true" ] || ! versions_match "$server_version" "$node_version"; then
        log "INFO" "Update required: updating to version $server_version"
        
        if update_node_container "$server_version"; then
            log "INFO" "Successfully updated Tdarr node to version $server_version"
            
            # Clean up old images unless skipped
            if [ "$skip_cleanup" != "true" ]; then
                cleanup_old_images
            fi
        else
            log "ERROR" "Failed to update Tdarr node"
            exit 1
        fi
    else
        log "INFO" "No update needed, versions are synchronized"
    fi
    
    log "INFO" "Tdarr version sync completed successfully"
}

# Run main function with all arguments
main "$@"