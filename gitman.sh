#!/bin/bash

set -eo pipefail

# Logging functions with levels
log() { local level="$1"; shift; echo -e "\033[1;${level}m[${2:-INFO}]\033[0m $*"; }
info() { log "34" "$@"; }
error() { log "31" "ERROR" "$@" >&2; }
warn() { log "33" "WARN" "$@"; }

# Detect Linux distribution
detect_distro() {
    if command -v pacman >/dev/null 2>&1; then
        echo "arch"
    elif command -v apt >/dev/null 2>&1; then
        echo "debian"
    elif command -v dnf >/dev/null 2>&1; then
        echo "fedora"
    else
        error "Unsupported distribution"
        exit 1
    fi
}

# Check dependencies based on distribution
check_deps() {
    local distro=$(detect_distro)
    local missing=()
    local pkg_cmd

    case $distro in
        arch)
            pkg_cmd="pacman -Qi"
            # Map commands to package names for Arch
            local pkg_map=(
                ["curl"]="curl"
                ["git"]="git"
                ["secret-tool"]="libsecret"
            )
            for cmd in "${!pkg_map[@]}"; do
                if ! command -v "$cmd" >/dev/null 2>&1; then
                    missing+=("${pkg_map[$cmd]}")
                fi
            done
            ;;
        debian)
            pkg_cmd="dpkg -l"
            for cmd in curl git libsecret-tools; do
                $pkg_cmd "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
            done
            ;;
        fedora)
            pkg_cmd="rpm -q"
            for cmd in curl git libsecret; do
                $pkg_cmd "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
            done
            ;;
    esac

    if [[ ${#missing[@]} -gt 0 ]]; then
        warn "Missing dependencies: ${missing[*]}"
        install_deps "${missing[@]}" "$distro"
    fi
}

# Install missing dependencies
install_deps() {
    local deps=("$@")
    local distro="${deps[-1]}"
    unset 'deps[-1]'

    info "Installing missing dependencies: ${deps[*]}"
    case $distro in
        arch)
            sudo pacman -Sy --noconfirm "${deps[@]}"
            ;;
        debian)
            sudo apt-get update
            sudo apt-get install -y "${deps[@]}"
            ;;
        fedora)
            sudo dnf install -y "${deps[@]}"
            ;;
    esac
}

# Install GCM more efficiently
install_gcm() {
    [[ -x "$(command -v git-credential-manager)" ]] && {
        info "GCM already installed: $(git-credential-manager --version)"
        return 0
    }

    local distro=$(detect_distro)
    
    if command -v dotnet >/dev/null 2>&1; then
        info "Installing GCM via dotnet..."
        dotnet tool install --global git-credential-manager
    else
        info "Installing GCM from GitHub release..."
        local version=$(curl -sL https://api.github.com/repos/GitCredentialManager/git-credential-manager/releases/latest | 
                       awk -F'"' '/"tag_name":/ {print substr($4,2)}')
        
        case $distro in
            arch)
                local package="gcm-linux_amd64.${version}.tar.gz"
                curl -sL -o "$package" "https://github.com/GitCredentialManager/git-credential-manager/releases/download/v${version}/$package"
                sudo tar -xvf "$package" -C /usr/local/bin
                rm -f "$package"
                ;;
            debian)
                local package="gcm-linux_amd64.${version}.deb"
                curl -sL -o "$package" "https://github.com/GitCredentialManager/git-credential-manager/releases/download/v${version}/$package"
                sudo dpkg -i "$package"
                rm -f "$package"
                ;;
            fedora)
                local package="gcm-linux_amd64.${version}.rpm"
                curl -sL -o "$package" "https://github.com/GitCredentialManager/git-credential-manager/releases/download/v${version}/$package"
                sudo rpm -i "$package"
                rm -f "$package"
                ;;
        esac
    fi
}

# Configure GCM
configure_gcm() {
    local gcm_path=$(command -v git-credential-manager)
    [[ -z "$gcm_path" ]] && { error "GCM not found after installation"; exit 1; }

    info "Configuring GCM at: $gcm_path"
    git config --global credential.helper "$gcm_path"
    git config --global credential.credentialStore secretservice
}

# Main execution
main() {
    check_deps
    
    # Backup with cleanup trap
    local backup_file="git_credentials_backup_$(date +%Y%m%d_%H%M%S).conf"
    trap 'rm -f "$backup_file"' EXIT
    git config --global --get-regexp credential > "$backup_file" 2>/dev/null || true
    
    install_gcm
    configure_gcm
    
    info "Configuration completed successfully"
}

main "$@"
