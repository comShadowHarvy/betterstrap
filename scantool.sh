#!/bin/bash
#
# Network Scanning Tools Installer
# A comprehensive installer script for popular network reconnaissance and scanning tools
# 

# Define colors for better visualization
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="$HOME/network_tools_install.log"

# Function to log messages
log() {
    local message="$1"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo -e "${timestamp} - ${message}" >> "$LOG_FILE"
}

# Function to display error messages
error() {
    echo -e "${RED}[ERROR]${NC} $1"
    log "[ERROR] $1"
}

# Function to display success messages
success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    log "[SUCCESS] $1"
}

# Function to display info messages
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    log "[INFO] $1"
}

# Function to display warning messages
warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    log "[WARNING] $1"
}

# Function to check if script is run with sudo
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root directly."
        error "It will call sudo when necessary. Please run without sudo."
        exit 1
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to check available disk space
check_disk_space() {
    local required_space=2000000 # 2GB in KB
    local available_space=$(df "$HOME" | awk '/[0-9]%/{print $4}')
    
    if [[ $available_space -lt $required_space ]]; then
        warning "Low disk space. At least 2GB recommended. Available: $(($available_space / 1024))MB"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Function to display a spinner during long operations
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while ps -p $pid > /dev/null; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Improved loading bar with percentage and elapsed time
loading_bar() {
    local current=$1
    local total=$2
    local percent=$(( 100 * current / total ))
    local bar_length=30
    local filled_length=$(( bar_length * current / total ))
    local empty_length=$(( bar_length - filled_length ))
    
    # Create the bar
    printf -v bar "%0.s#" $(seq 1 $filled_length)
    printf -v space "%0.s " $(seq 1 $empty_length)
    
    # Calculate elapsed time
    local current_time=$(date +%s)
    local elapsed=$((current_time - start_time))
    local elapsed_min=$((elapsed / 60))
    local elapsed_sec=$((elapsed % 60))
    
    # Estimate remaining time
    local remaining="N/A"
    if [[ $current -gt 0 ]]; then
        local total_time=$(( elapsed * total / current ))
        local remaining_time=$(( total_time - elapsed ))
        local remaining_min=$(( remaining_time / 60 ))
        local remaining_sec=$(( remaining_time % 60 ))
        remaining="${remaining_min}m ${remaining_sec}s"
    fi
    
    echo -ne "${CYAN}Progress: [${bar}${space}] ${percent}%${NC} | Elapsed: ${elapsed_min}m ${elapsed_sec}s | Est. Remaining: ${remaining}\r"
}

# Function to display a header
display_header() {
    clear
    echo -e "${PURPLE}=================================================${NC}"
    echo -e "${PURPLE}       Network Scanning Tools Installer         ${NC}"
    echo -e "${PURPLE}=================================================${NC}"
    echo -e "${YELLOW}This script will install several network scanning and"
    echo -e "reconnaissance tools to help with security assessments.${NC}"
    echo
    echo -e "${CYAN}Installation Log:${NC} $LOG_FILE"
    echo
}

# Function to check and install system dependencies
install_dependencies() {
    info "Checking and installing system dependencies..."
    
    local dependencies=("git" "curl" "python" "python-pip" "make" "gcc" "nmap" "whois" "dig" "traceroute")
    local to_install=()
    
    for dep in "${dependencies[@]}"; do
        if ! command_exists "$dep"; then
            to_install+=("$dep")
        fi
    done
    
    if [[ ${#to_install[@]} -gt 0 ]]; then
        info "Installing missing dependencies: ${to_install[*]}"
        if sudo pacman -S --needed "${to_install[@]}" --noconfirm; then
            success "Dependencies installed successfully"
        else
            error "Failed to install some dependencies"
            return 1
        fi
    else
        success "All base dependencies are already installed"
    fi
    
    return 0
}

# Function to install AUR helper
install_aur_helper() {
    if ! command_exists "yay"; then
        info "Installing AUR helper (yay)..."
        
        # Create a temporary directory
        local temp_dir=$(mktemp -d)
        if [[ ! "$temp_dir" || ! -d "$temp_dir" ]]; then
            error "Failed to create temporary directory"
            return 1
        fi
        
        # Make sure to clean up on exit
        trap "rm -rf $temp_dir" EXIT
        
        # Clone and install yay
        cd "$temp_dir" || return 1
        if git clone https://aur.archlinux.org/yay.git; then
            cd yay || return 1
            if makepkg -si --noconfirm; then
                success "Yay installed successfully"
                cd "$OLDPWD" || return 1
                return 0
            else
                error "Failed to build and install yay"
                cd "$OLDPWD" || return 1
                return 1
            fi
        else
            error "Failed to clone yay repository"
            cd "$OLDPWD" || return 1
            return 1
        fi
    else
        success "AUR helper (yay) is already installed"
        return 0
    fi
}

# Function to prepare directory structure
prepare_directories() {
    info "Preparing directory structure..."
    
    # Create main directory
    mkdir -p "$HOME/git/scan"
    
    if [[ ! -d "$HOME/git/scan" ]]; then
        error "Failed to create directory structure"
        return 1
    fi
    
    success "Directory structure prepared"
    return 0
}

# Function to clone a repository and install its dependencies
clone_and_install() {
    local repo_url=$1
    local repo_name=$(basename "$repo_url" .git)
    local target_dir="$HOME/git/scan/$repo_name"
    local description=$2
    
    info "Installing $repo_name: $description..."
    
    # Check if already installed
    if [[ -d "$target_dir" ]]; then
        read -p "Repository $repo_name already exists. Update it? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            info "Updating $repo_name..."
            cd "$target_dir" || return 1
            if git pull; then
                success "Updated $repo_name successfully"
            else
                error "Failed to update $repo_name"
                cd - > /dev/null || return 1
                return 1
            fi
            cd - > /dev/null || return 1
        else
            info "Skipping $repo_name..."
            return 0
        fi
    else
        # Clone the repository
        info "Cloning $repo_name into $target_dir..."
        if git clone "$repo_url" "$target_dir"; then
            success "Cloned $repo_name successfully"
        else
            error "Failed to clone $repo_name"
            return 1
        fi
    fi
    
    # Navigate to the repository directory
    cd "$target_dir" || return 1
    
    # Install dependencies
    if [[ -f "requirements.txt" ]]; then
        info "Installing Python dependencies for $repo_name..."
        if pip install -r requirements.txt; then
            success "Installed Python dependencies for $repo_name"
        else
            warning "Failed to install some Python dependencies for $repo_name"
        fi
    fi
    
    if [[ -f "install.sh" ]]; then
        info "Running install.sh for $repo_name..."
        chmod +x install.sh
        if ./install.sh; then
            success "Ran install.sh for $repo_name successfully"
        else
            warning "install.sh for $repo_name exited with an error"
        fi
    fi
    
    if [[ -f "setup.py" ]]; then
        info "Running setup.py for $repo_name..."
        if python setup.py install --user; then
            success "Ran setup.py for $repo_name successfully"
        else
            warning "setup.py for $repo_name exited with an error"
        fi
    fi
    
    # Create a symlink in ~/.local/bin if there's an executable file
    if [[ -f "$repo_name.py" || -f "$repo_name.sh" ]]; then
        mkdir -p "$HOME/.local/bin"
        
        if [[ -f "$repo_name.py" ]]; then
            chmod +x "$repo_name.py"
            ln -sf "$target_dir/$repo_name.py" "$HOME/.local/bin/$repo_name"
            success "Created symlink for $repo_name in ~/.local/bin"
        elif [[ -f "$repo_name.sh" ]]; then
            chmod +x "$repo_name.sh"
            ln -sf "$target_dir/$repo_name.sh" "$HOME/.local/bin/$repo_name"
            success "Created symlink for $repo_name in ~/.local/bin"
        fi
    fi
    
    cd - > /dev/null || return 1
    success "$repo_name installation completed"
    return 0
}

# Main function
main() {
    # Check if running as root
    check_root
    
    # Display header
    display_header
    
    # Initialize log file
    echo "=== Network Scanning Tools Installation Log ===" > "$LOG_FILE"
    log "Installation started"
    
    # Check disk space
    check_disk_space
    
    # Confirm installation
    echo -e "${YELLOW}This script will install several network scanning tools."
    echo -e "These tools are meant for security professionals and ethical hackers."
    echo -e "Please ensure you have the proper authorization before using them.${NC}"
    echo
    read -p "Do you want to continue with the installation? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Installation cancelled by user"
        exit 0
    fi
    
    # Record start time
    start_time=$(date +%s)
    
    # Install dependencies
    if ! install_dependencies; then
        error "Failed to install dependencies. Exiting."
        exit 1
    fi
    
    # Install AUR helper
    if ! install_aur_helper; then
        error "Failed to install AUR helper. Exiting."
        exit 1
    fi
    
    # Prepare directory structure
    if ! prepare_directories; then
        error "Failed to prepare directories. Exiting."
        exit 1
    fi
    
    # List of repositories to clone and install with descriptions
    declare -A repos
    repos["https://github.com/21y4d/nmapAutomator.git"]="A script to automate all the process of recon/enumeration"
    repos["https://github.com/haroonawanofficial/ReconCobra.git"]="Complete automated pentest framework for Information Gathering"
    repos["https://github.com/Tib3rius/AutoRecon.git"]="Multi-threaded network reconnaissance tool"
    repos["https://github.com/j3ssie/Osmedeus.git"]="Fully automated offensive security framework for reconnaissance"
    repos["https://github.com/nahamsec/lazyrecon.git"]="Script to automate reconnaissance process"
    repos["https://github.com/1N3/Sn1per.git"]="Automated pentest framework for scanning and exploitation"
    repos["https://github.com/arismelachroinos/lscript.git"]="Linux security script for managing Wi-Fi related tools"
    repos["https://github.com/six2dez/reconftw.git"]="Reconnaissance framework with customizable scanning options"
    repos["https://github.com/ygsk/VulnScan.git"]="Vulnerability scanner for web applications"
    repos["https://github.com/intrigueio/intrigue-core.git"]="Automated discovery tool and attack surface management platform"
    
    # Additional tools that might be useful
    repos["https://github.com/projectdiscovery/nuclei.git"]="Fast and customizable vulnerability scanner"
    repos["https://github.com/OJ/gobuster.git"]="Directory/file & DNS busting tool written in Go"
    
    total_steps=${#repos[@]}
    current_step=0
    
    # Clone each repository and install its tools
    for repo_url in "${!repos[@]}"; do
        description=${repos[$repo_url]}
        if clone_and_install "$repo_url" "$description"; then
            ((current_step++))
        else
            warning "Failed to install $(basename "$repo_url" .git)"
        fi
        loading_bar "$current_step" "$total_steps"
    done
    
    # Add tools directory to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        info "Adding ~/.local/bin to PATH in your shell profile"
        if [[ -f "$HOME/.bashrc" ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
            success "Added to .bashrc"
        fi
        if [[ -f "$HOME/.zshrc" ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
            success "Added to .zshrc"
        fi
    fi
    
    # Calculate installation time
    end_time=$(date +%s)
    total_time=$((end_time - start_time))
    minutes=$((total_time / 60))
    seconds=$((total_time % 60))
    
    echo -e "\n\n${GREEN}==================================================${NC}"
    echo -e "${GREEN}          Installation Completed!                ${NC}"
    echo -e "${GREEN}==================================================${NC}"
    echo -e "${CYAN}Total time: ${minutes} minutes and ${seconds} seconds${NC}"
    echo -e "${CYAN}Total tools installed: ${current_step}/${total_steps}${NC}"
    echo -e "${CYAN}Installation log: ${LOG_FILE}${NC}"
    echo
    echo -e "${YELLOW}You may need to restart your terminal or run 'source ~/.bashrc'${NC}"
    echo -e "${YELLOW}to update your PATH to include the newly installed tools.${NC}"
    echo
    echo -e "${PURPLE}Happy Scanning! Remember to use these tools responsibly.${NC}"
    
    log "Installation completed. Total time: ${minutes}m ${seconds}s. Tools installed: ${current_step}/${total_steps}"
}

# Run the main function
main