#!/bin/bash
# =============================================================================
# Enhanced Cross-Platform Package Installer
# A smart script for installing packages across different Linux distributions,
# macOS, and language-specific package managers.
# =============================================================================

# Configuration and command-line argument parsing
PACKAGE=""
VERBOSE=0
SAFE_MODE=0
UNINSTALL=0
FORCE=0
UPDATE=0
SEARCH=0
LIST=0
installed=0
LOG_FILE="$HOME/.install_history.log"

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Show help message
show_help() {
  echo "Usage: $0 <package> [options]"
  echo "Options:"
  echo "  --verbose    Show detailed output during installation"
  echo "  --safe       Ask for confirmation before executing sudo commands"
  echo "  --uninstall  Remove the specified package"
  echo "  --force      Skip dependency checks and verification"
  echo "  --update     Update the specified package or all packages if none specified"
  echo "  --search     Search for available packages (if supported by package manager)"
  echo "  --list       List installed packages from the installation history"
  echo "  --help       Show this help message"
  echo ""
  echo "Examples:"
  echo "  $0 neovim                 # Install neovim"
  echo "  $0 yazi --verbose         # Install yazi with verbose output"
  echo "  $0 ripgrep --safe         # Install ripgrep with confirmation prompts"
  echo "  $0 node --uninstall       # Uninstall node"
  echo "  $0 --update               # Update all installed packages"
  echo "  $0 python --update        # Update only python"
  echo "  $0 zsh --search           # Search for zsh in available packages"
  echo "  $0 --list                 # List installation history"
  exit 0
}

# Process command-line arguments
process_args() {
  # Check if no arguments provided
  if [ $# -eq 0 ]; then
    show_help
  fi
  
  # Check if the first argument is an option
  if [[ "$1" == --* ]]; then
    case "$1" in
      --update)
        UPDATE=1
        shift
        PACKAGE="$1"  # Optional package name
        ;;
      --search)
        SEARCH=1
        shift
        PACKAGE="$1"  # Required package name
        if [ -z "$PACKAGE" ]; then
          echo -e "${RED}Error: --search requires a package name${NC}"
          exit 1
        fi
        ;;
      --list)
        LIST=1
        ;;
      --help)
        show_help
        ;;
      *)
        echo -e "${RED}Unknown option: $1${NC}"
        show_help
        ;;
    esac
  else
    # Standard package installation logic
    PACKAGE="$1"
    shift
  fi

  # Process remaining options
  while [ $# -gt 0 ]; do
    case "$1" in
      --verbose)
        VERBOSE=1
        ;;
      --safe)
        SAFE_MODE=1
        echo -e "${BLUE}Running in safe mode. Will ask for confirmation before each sudo operation.${NC}"
        ;;
      --uninstall)
        UNINSTALL=1
        echo -e "${BLUE}Running in uninstall mode.${NC}"
        ;;
      --force)
        FORCE=1
        echo -e "${BLUE}Running in force mode. Skipping dependency checks and verification.${NC}"
        ;;
      --update)
        UPDATE=1
        echo -e "${BLUE}Running in update mode.${NC}"
        ;;
      --search)
        SEARCH=1
        ;;
      --list)
        LIST=1
        ;;
      --help)
        show_help
        ;;
      *)
        echo -e "${RED}Unknown option: $1${NC}"
        show_help
        ;;
    esac
    shift
  done
}

# Function to log messages if verbose is enabled
log() {
  if [ $VERBOSE -eq 1 ]; then
    echo -e "${BLUE}[LOG] $1${NC}"
  fi
}

# Function to log error messages
error() {
  echo -e "${RED}[ERROR] $1${NC}" >&2
}

# Function to log success messages
success() {
  echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Function to log warning messages
warning() {
  echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Function to map package names for different package managers
map_package_name() {
  local pkg="$1"
  local manager="$2"
  
  case "$pkg:$manager" in
    # Editors and IDEs
    "neovim:apt-get") echo "neovim" ;;
    "neovim:pacman") echo "neovim" ;;
    "neovim:brew") echo "neovim" ;;
    "neovim:snap") echo "nvim" ;;
    "neovim:flatpak") echo "io.neovim.nvim" ;;
    "vim:apt-get") echo "vim" ;;
    "emacs:apt-get") echo "emacs" ;;
    "vscode:apt-get") echo "code" ;;
    "vscode:brew") echo "visual-studio-code" ;;
    "vscode:snap") echo "code" ;;
    "vscode:flatpak") echo "com.visualstudio.code" ;;
    
    # File managers
    "yazi:cargo") echo "yazi-fm" ;;
    "yazi:pacman") echo "yazi" ;;
    "yazi:apt-get") echo "yazi" ;;
    "lf:apt-get") echo "lf" ;;
    "lf:brew") echo "lf" ;;
    "ranger:apt-get") echo "ranger" ;;
    "ranger:pip") echo "ranger-fm" ;;
    
    # Terminal utilities
    "ripgrep:apt-get") echo "ripgrep" ;;
    "ripgrep:brew") echo "ripgrep" ;;
    "ripgrep:cargo") echo "ripgrep" ;;
    "rg:apt-get") echo "ripgrep" ;;
    "rg:pacman") echo "ripgrep" ;;
    "fd:apt-get") echo "fd-find" ;;
    "fd:pacman") echo "fd" ;;
    "fzf:brew") echo "fzf" ;;
    "fzf:apt-get") echo "fzf" ;;
    "bat:apt-get") echo "bat" ;;
    "bat:pacman") echo "bat" ;;
    "eza:apt-get") echo "eza" ;;
    "eza:cargo") echo "eza" ;;
    "eza:brew") echo "eza" ;;
    "lazygit:apt-get") echo "lazygit" ;;
    "lazygit:brew") echo "lazygit" ;;
    "lazygit:go") echo "github.com/jesseduffield/lazygit" ;;
    
    # Programming languages
    "node:apt-get") echo "nodejs" ;;
    "nodejs:apt-get") echo "nodejs" ;;
    "node:snap") echo "node" ;;
    "python:apt-get") echo "python3" ;;
    "python:pacman") echo "python" ;;
    "python:snap") echo "python" ;;
    "rust:apt-get") echo "rustc" ;;
    "rust:pacman") echo "rust" ;;
    "go:apt-get") echo "golang" ;;
    "golang:apt-get") echo "golang" ;;
    "go:snap") echo "go" ;;
    "julia:apt-get") echo "julia" ;;
    "julia:brew") echo "julia" ;;
    "julia:snap") echo "julia" ;;
    "java:apt-get") echo "default-jdk" ;;
    "java:brew") echo "openjdk" ;;
    "kotlin:apt-get") echo "kotlin" ;;
    "kotlin:brew") echo "kotlin" ;;
    "kotlin:snap") echo "kotlin" ;;
    
    # Shell enhancements
    "zsh:apt-get") echo "zsh" ;;
    "ohmyzsh:curl") echo "ohmyzsh" ;;
    "ohmyposh:apt-get") echo "oh-my-posh" ;;
    "starship:apt-get") echo "starship" ;;
    "starship:brew") echo "starship" ;;
    "starship:cargo") echo "starship" ;;
    
    # Containers and virtualization
    "docker:apt-get") echo "docker.io" ;;
    "docker:pacman") echo "docker" ;;
    "docker:brew") echo "docker" ;;
    "podman:apt-get") echo "podman" ;;
    "podman:brew") echo "podman" ;;
    "kubectl:apt-get") echo "kubectl" ;;
    "kubectl:brew") echo "kubernetes-cli" ;;
    
    # Default to the original name
    *) echo "$pkg" ;;
  esac
}

# Function to try a command and mark success if it runs successfully
try_install() {
  local manager="$1"
  local cmd="$2"
  local pkg=$(map_package_name "$PACKAGE" "$manager")
  
  echo -e "${BLUE}Trying: $cmd $pkg${NC}"
  
  # Check for safe mode with sudo
  if [[ "$cmd" == sudo* ]] && [ $SAFE_MODE -eq 1 ]; then
    echo -e "${YELLOW}About to run with sudo: $cmd $pkg${NC}"
    read -p "Continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Operation cancelled by user"
      return 1
    fi
  fi
  
  # Execute the command with a progress spinner
  local output=""
  local exit_code=0
  
  if [ $VERBOSE -eq 1 ]; then
    $cmd "$pkg"
    exit_code=$?
  else
    # Show a spinner during installation
    echo -n "Installing... "
    output=$($cmd "$pkg" 2>&1) &
    pid=$!
    
    # Display spinner
    spin='-\|/'
    i=0
    while kill -0 $pid 2>/dev/null; do
      i=$(( (i+1) % 4 ))
      printf "\r${YELLOW}Installing...${spin:$i:1}${NC}"
      sleep .1
    done
    printf "\r                    \r"
    
    wait $pid
    exit_code=$?
  fi
  
  # Handle the result
  if [ $exit_code -eq 0 ]; then
    installed=1
    # Log successful installation
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Installed $pkg using $manager" >> "$LOG_FILE"
    success "Successfully installed $pkg using $manager"
    return 0
  else
    log "Failed to install with $manager: $output"
    return 1
  fi
}

# Function to try update
try_update() {
  local manager="$1"
  local pkg=$(map_package_name "$PACKAGE" "$manager")
  local cmd=""
  
  case "$manager" in
    "pacman") 
      if [ -z "$pkg" ]; then
        cmd="sudo pacman -Syu"
      else
        cmd="sudo pacman -S"
      fi
      ;;
    "yay") 
      if [ -z "$pkg" ]; then
        cmd="yay -Syu"
      else
        cmd="yay -S"
      fi
      ;;
    "apt-get") 
      if [ -z "$pkg" ]; then
        cmd="sudo apt-get update && sudo apt-get upgrade -y"
        $cmd && success "Successfully updated all packages" && return 0
      else
        cmd="sudo apt-get install --only-upgrade -y"
      fi
      ;;
    "dnf") 
      if [ -z "$pkg" ]; then
        cmd="sudo dnf upgrade -y"
      else
        cmd="sudo dnf upgrade -y"
      fi
      ;;
    "zypper") 
      if [ -z "$pkg" ]; then
        cmd="sudo zypper update -y"
      else
        cmd="sudo zypper update -y"
      fi
      ;;
    "brew") 
      if [ -z "$pkg" ]; then
        cmd="brew upgrade"
      else
        cmd="brew upgrade"
      fi
      ;;
    "flatpak") 
      if [ -z "$pkg" ]; then
        cmd="flatpak update -y"
      else
        cmd="flatpak update -y"
      fi
      ;;
    "snap") 
      if [ -z "$pkg" ]; then
        cmd="sudo snap refresh"
      else
        cmd="sudo snap refresh"
      fi
      ;;
    "pip") cmd="pip install --upgrade" ;;
    "npm") cmd="npm update -g" ;;
    "cargo") 
      if [ -z "$pkg" ]; then
        cmd="cargo install-update -a"
      else
        cmd="cargo install-update"
      fi
      ;;
    *) 
      return 1 
      ;;
  esac
  
  echo -e "${BLUE}Trying to update $pkg using $cmd...${NC}"
  
  # Check for safe mode with sudo
  if [[ "$cmd" == sudo* ]] && [ $SAFE_MODE -eq 1 ]; then
    echo -e "${YELLOW}About to run with sudo: $cmd $pkg${NC}"
    read -p "Continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Operation cancelled by user"
      return 1
    fi
  fi
  
  # For commands that don't need a package name
  if [ -z "$pkg" ] && [[ "$cmd" != *"-a"* ]]; then
    $cmd
    exit_code=$?
  else
    $cmd "$pkg"
    exit_code=$?
  fi
  
  if [ $exit_code -eq 0 ]; then
    success "Successfully updated $pkg using $manager"
    return 0
  else
    warning "Failed to update with $manager"
    return 1
  fi
}

# Function to try uninstallation
try_uninstall() {
  local manager="$1"
  local pkg=$(map_package_name "$PACKAGE" "$manager")
  local cmd=""
  
  case "$manager" in
    "pacman") cmd="sudo pacman -R" ;;
    "yay") cmd="yay -R" ;;
    "apt-get") cmd="sudo apt-get remove -y" ;;
    "dnf") cmd="sudo dnf remove -y" ;;
    "zypper") cmd="sudo zypper remove -y" ;;
    "apk") cmd="sudo apk del" ;;
    "brew") cmd="brew uninstall" ;;
    "flatpak") cmd="flatpak uninstall -y" ;;
    "snap") cmd="sudo snap remove" ;;
    "cargo") cmd="cargo uninstall" ;;
    "pip") cmd="pip uninstall -y" ;;
    "npm") cmd="npm uninstall -g" ;;
    "gem") cmd="gem uninstall" ;;
    "go") cmd="go clean -i" ;;
    *) 
      echo "Uninstall not supported for $manager"
      return 1 
      ;;
  esac
  
  echo -e "${BLUE}Trying to uninstall $pkg using $cmd...${NC}"
  
  # Check for safe mode with sudo
  if [[ "$cmd" == sudo* ]] && [ $SAFE_MODE -eq 1 ]; then
    echo -e "${YELLOW}About to run with sudo: $cmd $pkg${NC}"
    read -p "Continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Operation cancelled by user"
      return 1
    fi
  fi
  
  if [ $VERBOSE -eq 1 ]; then
    $cmd "$pkg"
    exit_code=$?
  else
    output=$($cmd "$pkg" 2>&1)
    exit_code=$?
  fi
  
  if [ $exit_code -eq 0 ]; then
    installed=1
    # Log successful uninstallation
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Uninstalled $pkg using $manager" >> "$LOG_FILE"
    success "Successfully uninstalled $pkg using $manager"
    return 0
  else
    log "Failed to uninstall with $manager: $output"
    return 1
  fi
}

# Function to search for a package
try_search() {
  local manager="$1"
  local pkg="$PACKAGE"
  local cmd=""
  
  case "$manager" in
    "pacman") cmd="pacman -Ss" ;;
    "yay") cmd="yay -Ss" ;;
    "apt-get") cmd="apt-cache search" ;;
    "dnf") cmd="dnf search" ;;
    "zypper") cmd="zypper search" ;;
    "apk") cmd="apk search" ;;
    "brew") cmd="brew search" ;;
    "flatpak") cmd="flatpak search" ;;
    "snap") cmd="snap find" ;;
    "cargo") cmd="cargo search" ;;
    "pip") cmd="pip search" ;;
    "npm") cmd="npm search" ;;
    "gem") cmd="gem search" ;;
    *) 
      return 1 
      ;;
  esac
  
  echo -e "${BLUE}Searching for $pkg using $cmd...${NC}"
  $cmd "$pkg"
  return 0
}

# Function to list installation history
list_installation_history() {
  if [ -f "$LOG_FILE" ]; then
    echo -e "${BLUE}Installation History:${NC}"
    cat "$LOG_FILE"
  else
    echo -e "${YELLOW}No installation history found.${NC}"
  fi
}

# Detect available package managers
detect_package_managers() {
  declare -a managers
  
  # Desktop/server package managers
  [ -x "$(command -v pacman)" ] && managers+=("pacman")
  [ -x "$(command -v yay)" ] && managers+=("yay")
  [ -x "$(command -v apt-get)" ] && managers+=("apt-get")
  [ -x "$(command -v dnf)" ] && managers+=("dnf")
  [ -x "$(command -v zypper)" ] && managers+=("zypper")
  [ -x "$(command -v apk)" ] && managers+=("apk")
  
  # Language-specific package managers
  [ -x "$(command -v pip)" ] && managers+=("pip")
  [ -x "$(command -v npm)" ] && managers+=("npm")
  [ -x "$(command -v cargo)" ] && managers+=("cargo")
  [ -x "$(command -v gem)" ] && managers+=("gem")
  [ -x "$(command -v go)" ] && managers+=("go")
  
  # macOS package managers
  [ -x "$(command -v brew)" ] && managers+=("brew")
  [ -x "$(command -v port)" ] && managers+=("port")
  
  # Flatpak and Snap
  [ -x "$(command -v flatpak)" ] && managers+=("flatpak")
  [ -x "$(command -v snap)" ] && managers+=("snap")
  
  # Special installations
  [ -x "$(command -v curl)" ] && managers+=("curl")
  
  echo "${managers[@]}"
}

# Resolve dependencies for packages
resolve_dependencies() {
  local pkg="$1"
  local manager="$2"
  
  # Skip if in force mode
  if [ $FORCE -eq 1 ]; then
    return 0
  fi
  
  case "$pkg:$manager" in
    "neovim:apt-get")
      echo "Checking dependencies for neovim..."
      try_install "$manager" "sudo apt-get install -y" "software-properties-common"
      ;;
    "yazi:cargo")
      echo "Checking dependencies for yazi..."
      for dep in gcc make pkg-config; do
        if ! command -v $dep >/dev/null 2>&1; then
          echo "Installing dependency: $dep"
          if command -v apt-get >/dev/null 2>&1; then
            sudo apt-get install -y $dep
          elif command -v pacman >/dev/null 2>&1; then
            sudo pacman -S --noconfirm $dep
          # Add more package managers as needed
          fi
        fi
      done
      ;;
    "node:apt-get"|"nodejs:apt-get")
      echo "Checking dependencies for nodejs..."
      try_install "$manager" "sudo apt-get install -y" "curl"
      ;;
    "docker:apt-get")
      echo "Checking dependencies for docker..."
      try_install "$manager" "sudo apt-get install -y" "apt-transport-https ca-certificates curl gnupg lsb-release"
      ;;
    "starship:apt-get")
      echo "Checking dependencies for starship..."
      try_install "$manager" "sudo apt-get install -y" "curl"
      ;;
  esac
}

# Verify that installation was successful
verify_installation() {
  local pkg="$1"
  local binary="${2:-$1}"
  
  # Skip if in force mode
  if [ $FORCE -eq 1 ]; then
    return 0
  fi
  
  # Map common packages to their binaries
  case "$pkg" in
    "neovim") binary="nvim" ;;
    "ripgrep") binary="rg" ;;
    "fd-find") binary="fdfind" ;;
    "nodejs") binary="node" ;;
    "yazi-fm") binary="yazi" ;;
    "lazygit") binary="lazygit" ;;
    "eza") binary="eza" ;;
    "starship") binary="starship" ;;
    "kubectl") binary="kubectl" ;;
  esac
  
  if command -v "$binary" >/dev/null 2>&1; then
    success "Verified: $binary is now available"
    if [ $VERBOSE -eq 1 ]; then
      echo "Version information:"
      $binary --version 2>/dev/null || echo "No version information available"
    fi
    return 0
  else
    warning "Warning: $binary was not found in PATH after installation"
    return 1
  fi
}

# Handle special cases for certain packages
handle_special_cases() {
  case "$PACKAGE" in
    "yazi")
      # For Yazi, try cargo installation as fallback
      if command -v cargo >/dev/null 2>&1; then
        echo "Trying cargo installation for Yazi..."
        cargo install --locked yazi-fm && installed=1 && return 0
      fi
      ;;
    "ohmyzsh")
      # For Oh My Zsh, use the official installation method
      echo "Installing Oh My Zsh..."
      sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended && installed=1 && return 0
      ;;
    "nvm")
      # For Node Version Manager
      echo "Installing NVM..."
      curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash && installed=1 && return 0
      ;;
    "rust")
      # For Rust, use rustup
      echo "Installing Rust using rustup..."
      curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && installed=1 && return 0
      ;;
    "starship")
      # For Starship prompt
      echo "Installing Starship prompt..."
      curl -sS https://starship.rs/install.sh | sh -s -- -y && installed=1 && return 0
      ;;
    "deno")
      # For Deno
      echo "Installing Deno..."
      curl -fsSL https://deno.land/x/install/install.sh | sh && installed=1 && return 0
      ;;
    "bun")
      # For Bun
      echo "Installing Bun..."
      curl -fsSL https://bun.sh/install | bash && installed=1 && return 0
      ;;
  esac
  return 1
}

# Handle uninstallation for special cases
handle_special_uninstall() {
  case "$PACKAGE" in
    "ohmyzsh")
      echo "Uninstalling Oh My Zsh..."
      if [ -f "$HOME/.oh-my-zsh/tools/uninstall.sh" ]; then
        sh "$HOME/.oh-my-zsh/tools/uninstall.sh" && installed=1 && return 0
      fi
      ;;
    "nvm")
      echo "To uninstall NVM, please remove the NVM directory (usually ~/.nvm) and the NVM initialization lines from your profile."
      echo "You may want to use: rm -rf ~/.nvm"
      installed=1 && return 0
      ;;
    "rust")
      echo "Uninstalling Rust using rustup..."
      if command -v rustup >/dev/null 2>&1; then
        rustup self uninstall -y && installed=1 && return 0
      fi
      ;;
    "starship")
      echo "To uninstall Starship, please remove the binary and the initialization lines from your profile."
      echo "rm -f ~/.local/bin/starship /usr/local/bin/starship"
      installed=1 && return 0
      ;;
    "deno")
      echo "To uninstall Deno, please remove the Deno directory and the initialization lines from your profile."
      echo "rm -rf ~/.deno"
      installed=1 && return 0
      ;;
    "bun")
      echo "To uninstall Bun, please remove the Bun directory and the initialization lines from your profile."
      echo "rm -rf ~/.bun"
      installed=1 && return 0
      ;;
  esac
  return 1
}

# Main installation function
install_package() {
  # Get available package managers
  IFS=' ' read -r -a managers <<< "$(detect_package_managers)"
  
  if [ ${#managers[@]} -eq 0 ]; then
    error "No supported package managers found on your system."
    exit 1
  fi
  
  log "Available package managers: ${managers[*]}"
  
  # Try system package managers first
  for manager in "${managers[@]}"; do
    case "$manager" in
      # System package managers
      "pacman")
        try_install "$manager" "sudo pacman -S --noconfirm"
        [ $installed -eq 1 ] && verify_installation "$PACKAGE" && success "Successfully installed $PACKAGE using pacman" && return 0
        ;;
      "yay")
        try_install "$manager" "yay -S --noconfirm"
        [ $installed -eq 1 ] && verify_installation "$PACKAGE" && success "Successfully installed $PACKAGE using yay" && return 0
        ;;
      "apt-get")
        # Update package lists first
        log "Updating apt package lists..."
        if [ $SAFE_MODE -eq 1 ]; then
          echo -e "${YELLOW}About to run: sudo apt-get update${NC}"
          read -p "Continue? [y/N] " -n 1 -r
          echo
          if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo apt-get update >/dev/null 2>&1
          fi
        else
          sudo apt-get update >/dev/null 2>&1
        fi
        
        # Resolve dependencies
        resolve_dependencies "$PACKAGE" "$manager"
        
        # Install package
        try_install "$manager" "sudo apt-get install -y"
        [ $installed -eq 1 ] && verify_installation "$PACKAGE" && success "Successfully installed $PACKAGE using apt-get" && return 0
        ;;
      "dnf")
        try_install "$manager" "sudo dnf install -y"
        [ $installed -eq 1 ] && verify_installation "$PACKAGE" && success "Successfully installed $PACKAGE using dnf" && return 0
        ;;
      "zypper")
        try_install "$manager" "sudo zypper install -y"
        [ $installed -eq 1 ] && verify_installation "$PACKAGE" && success "Successfully installed $PACKAGE using zypper" && return 0
        ;;
      "apk")
        try_install "$manager" "sudo apk add"
        [ $installed -eq 1 ] && verify_installation "$PACKAGE" && success "Successfully installed $PACKAGE using apk" && return 0
        ;;
      "brew")
        try_install "$manager" "brew install"
        [ $installed -eq 1 ] && verify_installation "$PACKAGE" && success "Successfully installed $PACKAGE using brew" && return 0
        ;;
      "port")
        try_install "$manager" "sudo port install"
        [ $installed -eq 1 ] && verify_installation "$PACKAGE" && success "Successfully installed $PACKAGE using MacPorts" && return 0
        ;;
      "flatpak")
        try_install "$manager" "flatpak install -y"
        [ $installed -eq 1 ] && success "Successfully installed $PACKAGE using Flatpak" && return 0
        ;;
      "snap")
        try_install "$manager" "sudo snap install"
        [ $installed -eq 1 ] && success "Successfully installed $PACKAGE using Snap" && return 0
        ;;
        
      # Language-specific package managers
      "pip")
        # Only use pip for Python packages
        case "$PACKAGE" in
          python-*|py-*|pip-*)
            try_install "$manager" "pip install --user"
            [ $installed -eq 1 ] && success "Successfully installed $PACKAGE using pip" && return 0
            ;;
        esac
        ;;
      "npm")
        # Only use npm for JavaScript packages
        case "$PACKAGE" in
          node-*|npm-*|js-*)
            try_install "$manager" "npm install -g"
            [ $installed -eq 1 ] && success "Successfully installed $PACKAGE using npm" && return 0
            ;;
        esac
        ;;
      "cargo")
        # For Rust packages
        case "$PACKAGE" in
          "yazi"|"yazi-fm"|"ripgrep"|"rg"|"fd"|"bat"|"eza"|"cargo-*"|"rust-*")
            try_install "$manager" "cargo install --locked"
            [ $installed -eq 1 ] && verify_installation "$PACKAGE" && success "Successfully installed $PACKAGE using cargo" && return 0
            ;;
        esac
        ;;
      "go")
        # For Go packages
        case "$PACKAGE" in
          "lazygit"|"go-*")
            try_install "$manager" "go install"
            [ $installed -eq 1 ] && verify_installation "$PACKAGE" && success "Successfully installed $PACKAGE using go" && return 0
            ;;
        esac
        ;;
    esac
  done
  
  # Try handling special cases as a last resort
  handle_special_cases
  [ $installed -eq 1 ] && success "Successfully installed $PACKAGE using special handling" && return 0
  
  error "No supported package manager found or installation failed for $PACKAGE."
  echo "You may need to install it manually or check the package name."
  return 1
}

# Main uninstallation function
uninstall_package() {
  # Try special uninstall handlers first
  handle_special_uninstall
  [ $installed -eq 1 ] && success "Successfully uninstalled $PACKAGE" && return 0

  # Get available package managers
  IFS=' ' read -r -a managers <<< "$(detect_package_managers)"
  
  for manager in "${managers[@]}"; do
    try_uninstall "$manager"
    [ $installed -eq 1 ] && success "Successfully uninstalled $PACKAGE using $manager" && return 0
  done
  
  error "Failed to uninstall $PACKAGE or package not found."
  return 1
}

# Main update function
update_package() {
  # Get available package managers
  IFS=' ' read -r -a managers <<< "$(detect_package_managers)"
  
  for manager in "${managers[@]}"; do
    try_update "$manager"
    [ $? -eq 0 ] && [ -z "$PACKAGE" ] && return 0
  done
  
  [ -z "$PACKAGE" ] && warning "No packages were updated." && return 1
  error "Failed to update $PACKAGE."
  return 1
}

# Main search function
search_package() {
  # Get available package managers
  IFS=' ' read -r -a managers <<< "$(detect_package_managers)"
  local found=0
  
  for manager in "${managers[@]}"; do
    echo -e "${BLUE}Searching in $manager:${NC}"
    try_search "$manager"
    [ $? -eq 0 ] && found=1
  done
  
  [ $found -eq 0 ] && error "No package managers support search or no results found."
  return 0
}

# Main execution
process_args "$@"

if [ $LIST -eq 1 ]; then
  list_installation_history
elif [ $SEARCH -eq 1 ]; then
  search_package
elif [ $UPDATE -eq 1 ]; then
  update_package
elif [ $UNINSTALL -eq 1 ]; then
  uninstall_package
else
  install_package
fi

exit $?