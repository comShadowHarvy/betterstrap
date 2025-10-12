#!/bin/bash
set -e

# Tdarr Auto-Sync Installation Script
# Sets up automatic version synchronization on system startup

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="tdarr-version-sync"
SERVICE_FILE="$SCRIPT_DIR/$SERVICE_NAME.service"
SYNC_SCRIPT="$SCRIPT_DIR/sync_tdarr_version.sh"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if running as regular user
    if [ "$EUID" -eq 0 ]; then
        print_error "Please run this script as a regular user, not as root"
        print_warning "The script will use sudo when needed"
        exit 1
    fi
    
    # Check if sync script exists and is executable
    if [ ! -f "$SYNC_SCRIPT" ]; then
        print_error "Sync script not found: $SYNC_SCRIPT"
        exit 1
    fi
    
    if [ ! -x "$SYNC_SCRIPT" ]; then
        print_status "Making sync script executable"
        chmod +x "$SYNC_SCRIPT"
    fi
    
    # Check if service file exists
    if [ ! -f "$SERVICE_FILE" ]; then
        print_error "Service file not found: $SERVICE_FILE"
        exit 1
    fi
    
    # Check if Docker is available
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check if user is in docker group
    if ! groups "$USER" | grep -q docker; then
        print_warning "User $USER is not in the docker group"
        print_warning "Adding user to docker group (will require logout/login to take effect)"
        sudo usermod -aG docker "$USER"
    fi
    
    print_status "Prerequisites check completed"
}

# Install the systemd service
install_service() {
    print_status "Installing systemd service..."
    
    # Copy service file to systemd directory
    sudo cp "$SERVICE_FILE" "/etc/systemd/system/$SERVICE_NAME.service"
    
    # Reload systemd daemon
    sudo systemctl daemon-reload
    
    # Enable the service
    sudo systemctl enable "$SERVICE_NAME.service"
    
    print_status "Systemd service installed and enabled"
}

# Test the sync script
test_sync_script() {
    print_status "Testing sync script with dry run..."
    
    if "$SYNC_SCRIPT" --dry-run; then
        print_status "Sync script test completed successfully"
    else
        print_warning "Sync script test showed some issues, but continuing..."
    fi
}

# Show usage instructions
show_usage() {
    echo ""
    echo "===========================================" 
    echo "  Tdarr Auto-Sync Installation Complete!"
    echo "==========================================="
    echo ""
    echo "✅ The following has been set up:"
    echo "   • Automatic version sync on system startup"
    echo "   • Systemd service: $SERVICE_NAME"
    echo "   • Sync script: $SYNC_SCRIPT"
    echo ""
    echo "🔧 Management Commands:"
    echo "   • Start sync now:        sudo systemctl start $SERVICE_NAME"
    echo "   • Check service status:  sudo systemctl status $SERVICE_NAME"
    echo "   • View logs:             sudo journalctl -u $SERVICE_NAME -f"
    echo "   • View sync logs:        sudo tail -f /var/log/tdarr-version-sync.log"
    echo "   • Manual sync:           $SYNC_SCRIPT"
    echo "   • Test run:              $SYNC_SCRIPT --dry-run"
    echo ""
    echo "🚀 What happens automatically:"
    echo "   • Every system startup: Checks Tdarr server version"
    echo "   • If versions differ: Updates node container automatically"
    echo "   • Preserves all settings including /share directory access"
    echo "   • Logs all activities to /var/log/tdarr-version-sync.log"
    echo ""
    echo "⚙️  Manual sync options:"
    echo "   • Force update:          $SYNC_SCRIPT --force"
    echo "   • Different server:      $SYNC_SCRIPT --server-ip 192.168.1.xxx"
    echo "   • Dry run test:          $SYNC_SCRIPT --dry-run"
    echo ""
    echo "🗑️  Uninstall:"
    echo "   • Disable service:       sudo systemctl disable $SERVICE_NAME"
    echo "   • Remove service:        sudo rm /etc/systemd/system/$SERVICE_NAME.service"
    echo "   • Reload systemd:        sudo systemctl daemon-reload"
    echo ""
    
    if ! groups "$USER" | grep -q docker; then
        echo "⚠️  IMPORTANT: You need to log out and back in for docker group membership to take effect!"
        echo ""
    fi
}

# Main installation function
main() {
    local skip_test=false
    local start_now=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-test)
                skip_test=true
                shift
                ;;
            --start-now)
                start_now=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-test    Skip testing the sync script"
                echo "  --start-now    Start the service immediately after installation"
                echo "  --help, -h     Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    print_status "Starting Tdarr auto-sync installation"
    
    # Run installation steps
    check_prerequisites
    install_service
    
    if [ "$skip_test" != "true" ]; then
        test_sync_script
    fi
    
    # Start service if requested
    if [ "$start_now" = "true" ]; then
        print_status "Starting service now..."
        sudo systemctl start "$SERVICE_NAME"
        sleep 2
        sudo systemctl status "$SERVICE_NAME" --no-pager
    fi
    
    show_usage
    
    print_status "Installation completed successfully!"
}

# Run main function with all arguments
main "$@"