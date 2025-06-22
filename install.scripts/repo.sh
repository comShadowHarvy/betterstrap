#!/bin/bash
#
# Comprehensive and Interactive Arch Linux Setup Script
#
# This script will:
# 1. Check for dependencies.
# 2. Configure repositories: Interactively add/enable official and third-party repos.
# 3. Configure pacman: Interactively apply performance and cosmetic tweaks.
# 4. Provide a final summary.
#

# --- Configuration & Globals ---
set -o pipefail # Fail a pipe if any command in it fails

# Color codes for better output
C_RESET='\e[0m'
C_RED='\e[0;31m'
C_GREEN='\e[0;32m'
C_YELLOW='\e[0;33m'
C_BLUE='\e[0;34m'
C_BOLD='\e[1m'

# Symbols for status messages
TICK="[${C_GREEN}✓${C_RESET}]"
CROSS="[${C_RED}✗${C_RESET}]"
INFO="[${C_BLUE}*${C_RESET}]"
WARN="[${C_YELLOW}!${C_RESET}]"

# List of repositories the script knows how to handle
REPOS_TO_MANAGE=("cachyos" "chaotic-aur" "blackarch" "archstrike" "multilib" "standard-arch")

# Create a temporary directory and set a trap to clean it up on exit
TMP_DIR=$(mktemp -d)
trap 'rm -rf -- "$TMP_DIR"' EXIT

# --- Core Functions ---

log() {
    local type="$1"; shift; local msg="$@";
    case "$type" in
        success) echo -e "\n$TICK ${C_GREEN}$msg${C_RESET}" ;;
        error)   echo -e "\n$CROSS ${C_RED}$msg${C_RESET}" ;;
        info)    echo -e "$INFO ${C_BLUE}$msg${C_RESET}" ;;
        warn)    echo -e "\n$WARN ${C_YELLOW}$msg${C_RESET}" ;;
        header)  echo -e "\n${C_BOLD}${C_BLUE}==> $msg${C_RESET}" ;;
        *)       echo -e "$msg" ;;
    esac
}

handle_error() {
    log error "Error in step: $1. See output above for details."
    return 1 # Indicate failure
}

check_dependencies() {
    log header "Checking for required dependencies..."
    local missing_deps=0
    for cmd in curl gawk grep sed pacman-key dirmngr; do
        if ! command -v "$cmd" &>/dev/null; then
            log error "Dependency missing: $cmd. Please install it first."
            ((missing_deps++))
        else
            log info "Found dependency: $cmd"
        fi
    done
    [ "$missing_deps" -eq 0 ]
}

repo_exists() {
    local repo_name="$1"
    if [[ "$repo_name" == "standard-arch" ]]; then
        grep -q "^\s*\[core\]" /etc/pacman.conf
    elif [[ "$repo_name" == "cachyos" ]]; then
        grep -q "^\s*\[cachyos" /etc/pacman.conf
    else
        grep -q "^\s*\[$repo_name\]" /etc/pacman.conf
    fi
}

# --- Pacman Configuration Functions ---

# Ensures a specific option is set in /etc/pacman.conf under the [options] block.
# Usage: ensure_option "Exact line to be present" "Keyword to find"
ensure_option() {
    local desired_line="$1"
    local keyword="$2"

    # If the keyword line exists (commented or not), replace it with the desired line.
    if grep -q -E "^\s*#?\s*$keyword" /etc/pacman.conf; then
        sudo sed -i -E "s|^\s*#?\s*$keyword.*|$desired_line|" /etc/pacman.conf
    # If it doesn't exist, add it under [options].
    else
        sudo sed -i "/^\[options\]/a $desired_line" /etc/pacman.conf
    fi
}

apply_pacman_tweaks() {
    log header "Applying Pacman Configuration Tweaks"
    read -p "$(echo -e "\n${C_YELLOW}?${C_RESET} Do you want to apply recommended UI and performance options to /etc/pacman.conf? (This enables color, parallel downloads, etc.) (y/N) ")" answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        log info "Applying options to /etc/pacman.conf..."
        
        ensure_option "#UseSyslog" "UseSyslog"
        ensure_option "Color" "Color"
        ensure_option "ILoveCandy" "ILoveCandy"
        ensure_option "#NoProgressBar" "NoProgressBar"
        ensure_option "CheckSpace" "CheckSpace"
        ensure_option "VerbosePkgLists" "VerbosePkgLists"
        ensure_option "DisableDownloadTimeout" "DisableDownloadTimeout"
        ensure_option "ParallelDownloads = 10" "ParallelDownloads"
        ensure_option "DownloadUser = alpm" "DownloadUser"
        ensure_option "#DisableSandbox" "DisableSandbox"

        log success "Pacman options have been configured."
    else
        log info "Skipping Pacman configuration tweaks."
    fi
}

# --- Repository Setup Functions ---

setup_cachyos() {
    log header "Setting up CachyOS Repository"
    cd "$TMP_DIR" || return 1
    curl -O 'https://mirror.cachyos.org/cachyos-repo.tar.zst' || { handle_error "Failed to download cachyos-repo.tar.zst"; return 1; }
    tar -xvf cachyos-repo.tar.zst || { handle_error "Failed to extract cachyos-repo.tar.zst"; return 1; }
    cd cachyos-repo || return 1
    sudo ./cachyos-repo.sh || { handle_error "CachyOS setup script failed."; return 1; }
    log success "CachyOS repository and keyring have been added."
    log warn "${C_BOLD}ACTION REQUIRED:${C_RESET} ${C_YELLOW}For CachyOS packages to have priority, you ${C_BOLD}MUST${C_RESET}${C_YELLOW} manually edit '/etc/pacman.conf' and move the CachyOS repo blocks ${C_BOLD}BEFORE${C_RESET}${C_YELLOW} the standard repos."
}

add_standard_arch_repos() {
    log header "Adding Standard Arch Linux Repositories"
    log warn "This is for systems like CachyOS that replace the default repos."
    local standard_repos_block; standard_repos_block=$(cat <<'EOF'
[core]
Include = /etc/pacman.d/mirrorlist
[extra]
Include = /etc/pacman.d/mirrorlist
[community]
Include = /etc/pacman.d/mirrorlist
EOF
)
    echo "$standard_repos_block" | sudo tee -a /etc/pacman.conf > /dev/null
    log success "Standard Arch repositories added. You may need to edit /etc/pacman.d/mirrorlist."
}

# (Other repo setup functions like setup_chaotic_aur, etc., remain the same)

setup_chaotic_aur() { log header "Setting up Chaotic-AUR"; sudo pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com || { handle_error "Failed to receive Chaotic-AUR key"; return 1; }; sudo pacman-key --lsign-key 3056513887B78AEB || { handle_error "Failed to sign Chaotic-AUR key"; return 1; }; sudo pacman -U --noconfirm 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst' || { handle_error "Failed to install Chaotic-AUR packages"; return 1; }; if ! grep -q "chaotic-mirrorlist" /etc/pacman.conf; then echo -e "\n[chaotic-aur]\nInclude = /etc/pacman.d/chaotic-mirrorlist" | sudo tee -a /etc/pacman.conf >/dev/null; fi; log success "Chaotic-AUR repository added successfully."; }
setup_blackarch() { log header "Setting up BlackArch"; pushd "$TMP_DIR" >/dev/null || return 1; curl -O https://blackarch.org/strap.sh || { handle_error "Failed to download BlackArch strap.sh"; return 1; }; echo "86eb4efb68918dbfdd1e22862a48fda20a8145ff strap.sh" | sha1sum -c --quiet || { handle_error "BlackArch script verification failed (SHA1 mismatch)"; return 1; }; chmod +x strap.sh; sudo ./strap.sh || { handle_error "BlackArch bootstrap script failed"; return 1; }; popd >/dev/null || return 1; log success "BlackArch repository added successfully."; }
setup_archstrike() { log header "Setting up ArchStrike"; if ! sudo pacman-key --recv-key "9D5F1C051D146843CDA4858BDE64825E7CBC0D51" --keyserver hkps://keys.openpgp.org && ! sudo pacman-key --recv-key "9D5F1C051D146843CDA4858BDE64825E7CBC0D51" --keyserver keyserver.ubuntu.com; then return $(handle_error "Could not receive ArchStrike key from keyservers."); fi; sudo pacman-key --lsign-key "9D5F1C051D146843CDA4858BDE64825E7CBC0D51" || return $(handle_error "Failed to sign ArchStrike key"); if ! grep -q "archstrike-mirrorlist" /etc/pacman.conf; then echo "Server = https://mirror.archstrike.org/\$arch/\$repo" | sudo tee /etc/pacman.d/archstrike-mirrorlist > /dev/null; echo -e "\n[archstrike]\nInclude = /etc/pacman.d/archstrike-mirrorlist" | sudo tee -a /etc/pacman.conf > /dev/null; fi; log info "Refreshing databases and installing archstrike-keyring..."; sudo pacman -Syy; sudo pacman -S --noconfirm archstrike-keyring || return $(handle_error "Failed to install archstrike-keyring package"); sudo pacman -Syyu; log success "ArchStrike repository added successfully."; }
enable_multilib() { log header "Enabling Multilib Repository"; if grep -q "^\s*#\s*\[multilib\]" /etc/pacman.conf; then sudo sed -i '/^#\[multilib\]$/,/^#Include/s/^#//' /etc/pacman.conf; log success "Multilib repository has been enabled."; else log warn "Multilib repository is already enabled or was not found in a commented state."; fi; }


# --- Main Script Logic ---
main() {
    # Initial checks
    [[ "$EUID" -ne 0 ]] && log error "This script must be run with sudo or as root. Example: sudo ./setup.sh" && exit 1
    check_dependencies || exit 1

    # --- Step 1: Repository Setup ---
    local missing_repos=()
    log header "Step 1: Checking Repository Configurations"
    for repo in "${REPOS_TO_MANAGE[@]}"; do
        if repo_exists "$repo"; then
            log info "Repository '$repo' is already configured."
        else
            log warn "Repository '$repo' is missing or disabled."
            missing_repos+=("$repo")
        fi
    done

    if [ "${#missing_repos[@]}" -eq 0 ]; then
        log success "All managed repositories are already configured."
    else
        for repo in "${missing_repos[@]}"; do
            read -p "$(echo -e "\n${C_YELLOW}?${C_RESET} Do you want to add/enable the '${C_BOLD}$repo${C_RESET}' repository? (y/N) ")" answer
            if [[ "$answer" =~ ^[Yy]$ ]]; then
                case "$repo" in
                    "cachyos")       setup_cachyos ;;
                    "standard-arch") add_standard_arch_repos ;;
                    "chaotic-aur")   setup_chaotic_aur ;;
                    "blackarch")     setup_blackarch ;;
                    "archstrike")    setup_archstrike ;;
                    "multilib")      enable_multilib ;;
                esac
            else
                log info "Skipping '$repo' repository."
            fi
        done
    fi

    # --- Step 2: Pacman Options ---
    apply_pacman_tweaks

    # --- Step 3: Final System Update ---
    log header "Step 2: Finalizing Setup"
    log info "Refreshing all package databases and checking for upgrades..."
    if sudo pacman -Syyu --noconfirm; then
        log success "System is up-to-date."
    else
        handle_error "Final system update failed."
    fi

    log header "Setup Summary"
    local configured_count=0
    for repo in "${REPOS_TO_MANAGE[@]}"; do
        if repo_exists "$repo"; then
            echo -e " $TICK ${C_BOLD}$repo${C_RESET} is configured."
            ((configured_count++))
        else
            echo -e " $CROSS ${C_BOLD}$repo${C_RESET} is not configured."
        fi
    done

    log header "Setup finished. ($configured_count/${#REPOS_TO_MANAGE[@]} managed repositories are now active)"
}

# Run the main function
main "$@"