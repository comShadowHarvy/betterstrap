#!/usr/bin/env bash
# Enhanced bolt.diy Installer Script
# This script installs prerequisites, sets up bolt.diy, and provides options for configuration

# Set strict mode and error handling
set -eo pipefail

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Create log file
LOG_FILE="boltdiy_install_$(date +%Y%m%d_%H%M%S).log"
touch "$LOG_FILE"

# Function to log messages
log() {
    local level=$1
    local message=$2
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo -e "${timestamp} [${level}] ${message}" >> "$LOG_FILE"
}

# Function to display info message
info() {
    local message=$1
    echo -e "${BLUE}[INFO]${NC} ${message}"
    log "INFO" "$message"
}

# Function to display success message
success() {
    local message=$1
    echo -e "${GREEN}[SUCCESS]${NC} ${message}"
    log "SUCCESS" "$message"
}

# Function to display warning message
warning() {
    local message=$1
    echo -e "${YELLOW}[WARNING]${NC} ${message}"
    log "WARNING" "$message"
}

# Function to display error message and exit
error() {
    local message=$1
    local exit_code=${2:-1}
    echo -e "${RED}[ERROR]${NC} ${message}"
    log "ERROR" "$message"
    echo -e "\nInstallation failed. Check the log file: ${BOLD}${LOG_FILE}${NC} for details."
    exit "$exit_code"
}

# Display header
show_header() {
    echo -e "${BOLD}${MAGENTA}"
    echo "╔════════════════════════════════════════════════╗"
    echo "║                bolt.diy Installer              ║"
    echo "╚════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Function to check required commands
check_command() {
    local cmd=$1
    local package=$2
    if ! command -v "$cmd" &>/dev/null; then
        warning "$cmd is not installed. Will attempt to install $package."
        return 1
    else
        return 0
    fi
}

# Function to check system requirements
check_requirements() {
    info "Checking system requirements..."
    
    # Check internet connectivity
    if ! ping -c 1 github.com &>/dev/null; then
        warning "Internet connectivity check failed. The installation might not complete successfully."
    fi

    # Check disk space (minimum 1GB free)
    local free_space=$(df -k . | tail -1 | awk '{print $4}')
    if [ "$free_space" -lt 1048576 ]; then
        warning "Less than 1GB free disk space available. You might encounter issues during installation."
    fi

    # Check if we can use sudo
    check_command sudo sudo || {
        error "sudo is not installed or not available. Please install sudo or run as root."
    }
}

# Function to detect operating system
detect_os() {
    info "Detecting operating system..."
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        os_id=$(echo "${ID}" | tr '[:upper:]' '[:lower:]')
        os_id_like=$(echo "${ID_LIKE:-}" | tr '[:upper:]' '[:lower:]')
        os_version="${VERSION_ID:-}"
        os_name="${NAME:-}"
    else
        error "/etc/os-release not found; cannot determine OS."
    fi

    # Determine OS family (Arch, Fedora, Debian-based, RHEL-based, Alpine, openSUSE)
    OS_FAMILY=""
    if [[ "$os_id" == *arch* ]] || [[ "$os_id_like" == *arch* ]]; then
        OS_FAMILY="arch"
    elif [[ "$os_id" == *fedora* ]] || [[ "$os_id_like" == *fedora* ]]; then
        OS_FAMILY="fedora"
    elif [[ "$os_id" == *rhel* ]] || [[ "$os_id" == *centos* ]] || [[ "$os_id_like" == *rhel* ]]; then
        OS_FAMILY="rhel"
    elif [[ "$os_id" == *debian* ]] || [[ "$os_id" == *ubuntu* ]] || [[ "$os_id_like" == *debian* ]]; then
        OS_FAMILY="debian"
    elif [[ "$os_id" == *alpine* ]]; then
        OS_FAMILY="alpine"
    elif [[ "$os_id" == *suse* ]] || [[ "$os_id_like" == *suse* ]]; then
        OS_FAMILY="suse"
    else
        warning "Unrecognized OS: $os_name (ID=${os_id}, ID_LIKE=${os_id_like})"
        warning "Will attempt to proceed with best-guess approach."
        
        # Attempt to identify by checking common package managers
        if command -v pacman &>/dev/null; then
            OS_FAMILY="arch"
        elif command -v dnf &>/dev/null; then
            OS_FAMILY="fedora"
        elif command -v yum &>/dev/null; then
            OS_FAMILY="rhel"
        elif command -v apt &>/dev/null || command -v apt-get &>/dev/null; then
            OS_FAMILY="debian"
        elif command -v apk &>/dev/null; then
            OS_FAMILY="alpine"
        elif command -v zypper &>/dev/null; then
            OS_FAMILY="suse"
        else
            error "Could not determine a supported package manager. Installation cannot proceed."
        fi
    fi

    success "Detected OS: $os_name $os_version (Family: $OS_FAMILY)"
}

# Function to install prerequisites
install_prerequisites() {
    info "Installing prerequisites (Node.js, npm, and git)..."
    
    case "$OS_FAMILY" in
        arch)
            info "Using pacman package manager..."
            sudo pacman -Syu --noconfirm --needed nodejs npm git
            ;;
        fedora)
            info "Using dnf package manager..."
            sudo dnf install -y nodejs npm git
            ;;
        rhel)
            info "Using yum package manager..."
            # Enable EPEL repository for Node.js if needed
            if ! rpm -qa | grep -q epel-release; then
                sudo yum install -y epel-release
            fi
            sudo yum install -y nodejs npm git
            ;;
        debian)
            info "Using apt package manager..."
            # Check if nodejs is available and install/update if needed
            if ! apt-cache show nodejs &>/dev/null; then
                warning "Node.js package not found in current repositories. Adding NodeSource repository..."
                # First, install curl if not available
                if ! command -v curl &>/dev/null; then
                    sudo apt-get update
                    sudo apt-get install -y curl
                fi
                # Add NodeSource repository (for Node.js 18.x)
                curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            fi
            
            sudo apt-get update
            sudo apt-get install -y nodejs git
            # npm comes with nodejs from the NodeSource repository
            ;;
        alpine)
            info "Using apk package manager..."
            sudo apk add --update nodejs npm git
            ;;
        suse)
            info "Using zypper package manager..."
            sudo zypper refresh
            sudo zypper install -y nodejs npm git
            ;;
        *)
            error "Unsupported OS family: ${OS_FAMILY}"
            ;;
    esac
    
    # Verify installations
    for cmd in node npm git; do
        if ! command -v "$cmd" &>/dev/null; then
            error "Failed to install $cmd. Please install it manually and try again."
        fi
    done
    
    # Check Node.js version (minimum recommended version: 16)
    local node_version=$(node -v | cut -d 'v' -f 2 | cut -d '.' -f 1)
    if [ "$node_version" -lt 16 ]; then
        warning "Node.js version $node_version detected. bolt.diy may require Node.js 16 or newer."
    else
        info "Node.js version: $(node -v)"
    fi
}

# Function to install pnpm
install_pnpm() {
    info "Checking for pnpm..."
    
    if ! command -v pnpm &>/dev/null; then
        info "Installing pnpm globally using npm..."
        npm install -g pnpm || {
            warning "Failed to install pnpm using npm. Trying alternative installation method..."
            curl -fsSL https://get.pnpm.io/install.sh | sh - || {
                error "Failed to install pnpm. Please install it manually and try again."
            }
            # Source shell profile to make pnpm available
            source ~/.bashrc 2>/dev/null || source ~/.bash_profile 2>/dev/null || source ~/.profile 2>/dev/null
        }
        
        # Verify pnpm installation
        if ! command -v pnpm &>/dev/null; then
            error "pnpm installation failed. Please install it manually and try again."
        fi
    fi
    
    success "pnpm is installed: $(pnpm --version)"
}

# Function to clone or update repository
setup_repository() {
    local repo_url="${1:-https://github.com/stackblitz-labs/bolt.diy}"
    local repo_dir="${2:-bolt.diy}"
    local branch="${3:-stable}"
    
    info "Setting up bolt.diy repository (branch: $branch)..."
    
    if [ -d "$repo_dir" ]; then
        info "Directory '$repo_dir' already exists. Updating repository..."
        cd "$repo_dir"
        
        # Check if directory is a git repository
        if [ -d ".git" ]; then
            # Stash any local changes to avoid conflicts
            git stash -q || warning "Failed to stash local changes. There might be conflicts during update."
            
            # Fetch updates
            git fetch origin "$branch" || error "Failed to fetch updates from repository."
            
            # If current branch isn't the requested branch, check it out
            if [[ "$(git rev-parse --abbrev-ref HEAD)" != "$branch" ]]; then
                git checkout "$branch" || error "Failed to checkout $branch branch."
            else
                git pull origin "$branch" || error "Failed to pull updates from repository."
            fi
            
            info "Repository updated successfully."
        else
            warning "Directory exists but is not a git repository. Creating a backup and cloning fresh."
            cd ..
            mv "$repo_dir" "${repo_dir}_backup_$(date +%s)"
            git clone -b "$branch" "$repo_url" || error "Failed to clone repository."
            cd "$repo_dir"
        fi
    else
        info "Cloning the bolt.diy repository from ${repo_url} (branch: $branch)..."
        git clone -b "$branch" "$repo_url" || error "Failed to clone repository."
        cd "$repo_dir"
    fi
    
    success "Repository setup completed."
}

# Function to install dependencies
install_dependencies() {
    info "Installing project dependencies with pnpm..."
    
    pnpm install || error "Failed to install project dependencies."
    
    success "Dependencies installed successfully."
}

# Function to setup environment
setup_environment() {
    info "Setting up environment configuration..."
    
    if [ ! -f ".env.local" ]; then
        if [ -f ".env.example" ]; then
            info "Creating .env.local from .env.example."
            cp .env.example .env.local
            success ".env.local created."
            
            echo -e "${YELLOW}IMPORTANT:${NC} Please open .env.local and add your API keys:"
            echo -e "  - ${BOLD}GROQ_API_KEY${NC}"
            echo -e "  - ${BOLD}OPENAI_API_KEY${NC}"
            echo -e "  - ${BOLD}ANTHROPIC_API_KEY${NC}"
            
            # Ask if user wants to set up API keys now
            read -p "Would you like to set up API keys now? [y/N]: " setup_keys
            if [[ "$setup_keys" =~ ^[Yy]$ ]]; then
                # GROQ API key
                read -p "Enter GROQ_API_KEY (leave empty to skip): " groq_key
                if [ -n "$groq_key" ]; then
                    sed -i "s|GROQ_API_KEY=.*|GROQ_API_KEY=$groq_key|" .env.local
                fi
                
                # OpenAI API key
                read -p "Enter OPENAI_API_KEY (leave empty to skip): " openai_key
                if [ -n "$openai_key" ]; then
                    sed -i "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=$openai_key|" .env.local
                fi
                
                # Anthropic API key
                read -p "Enter ANTHROPIC_API_KEY (leave empty to skip): " anthropic_key
                if [ -n "$anthropic_key" ]; then
                    sed -i "s|ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$anthropic_key|" .env.local
                fi
                
                success "API keys updated in .env.local"
            fi
        else
            warning ".env.example not found. Skipping API keys setup."
        fi
    else
        info ".env.local already exists; skipping creation."
    fi
}

# Function to display completion message
show_completion() {
    local dir=$(pwd)
    
    echo -e "\n${BOLD}${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${GREEN}             bolt.diy Installation Complete!                ${NC}"
    echo -e "${BOLD}${GREEN}════════════════════════════════════════════════════════════${NC}\n"
    
    echo -e "Installation directory: ${BOLD}${dir}${NC}"
    echo -e "Log file: ${BOLD}${LOG_FILE}${NC}\n"
    
    echo -e "${BOLD}Next steps:${NC}"
    echo -e "  1. Navigate to the installation directory: ${CYAN}cd ${dir}${NC}"
    echo -e "  2. Start the development server: ${CYAN}pnpm run dev${NC}"
    echo -e "  3. Access the application in your browser: ${CYAN}http://localhost:3000${NC}\n"
    
    echo -e "${YELLOW}Need help?${NC} Visit the bolt.diy GitHub repository: ${CYAN}https://github.com/stackblitz-labs/bolt.diy${NC}\n"
}

# Main function
main() {
    local REPO_URL="https://github.com/stackblitz-labs/bolt.diy"
    local REPO_DIR="bolt.diy"
    local BRANCH="stable"
    
    show_header
    
    # Process command line arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --repo-url=*)
                REPO_URL="${1#*=}"
                shift
                ;;
            --repo-dir=*)
                REPO_DIR="${1#*=}"
                shift
                ;;
            --branch=*)
                BRANCH="${1#*=}"
                shift
                ;;
            --help|-h)
                echo "Usage: ./install_boltdiy.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --repo-url=URL    Set repository URL (default: https://github.com/stackblitz-labs/bolt.diy)"
                echo "  --repo-dir=DIR    Set directory name (default: bolt.diy)"
                echo "  --branch=BRANCH   Set branch to use (default: stable)"
                echo "  --help, -h        Show this help message"
                exit 0
                ;;
            *)
                warning "Unknown option: $1"
                shift
                ;;
        esac
    done
    
    info "Starting bolt.diy installation..."
    info "Repository: $REPO_URL"
    info "Directory: $REPO_DIR"
    info "Branch: $BRANCH"
    
    check_requirements
    detect_os
    install_prerequisites
    install_pnpm
    setup_repository "$REPO_URL" "$REPO_DIR" "$BRANCH"
    install_dependencies
    setup_environment
    
    # Ask the user if they want to start the development server
    read -p "Do you want to start the application now (pnpm run dev)? [y/N]: " start_app
    if [[ "$start_app" =~ ^[Yy]$ ]]; then
        info "Starting the development server..."
        pnpm run dev
    else
        show_completion
    fi
}

# Run the main function
main "$@"