#!/usr/bin/env bash

# YubiKey Comprehensive Installer and Configurator
# Automated installation and configuration for YubiKey on Arch Linux
# Features: SSH FIDO2, PAM U2F, GPG/PGP, WebAuthn support
# Version 1.0

set -Eeuo pipefail

# --- Script Metadata ---
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_TIME="$(date +%Y%m%d_%H%M%S)"
TARGET_USER="${SUDO_USER:-${USER}}"
HOME_DIR="$(eval echo ~"${TARGET_USER}")"
LOG_DIR="${HOME_DIR}/betterstrap/logs"
LOG_FILE="${LOG_DIR}/yubikey.installer.${START_TIME}.log"

# --- Color Configuration ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# --- Global State ---
PAM_MODIFIED=false
PAM_BACKUP=""

# --- Initialize Logging ---
init_logging() {
    mkdir -p "${LOG_DIR}"
    exec > >(tee -a "${LOG_FILE}") 2>&1
    echo "=== YubiKey Installer Started: $(date) ==="
    echo "Target User: ${TARGET_USER}"
    echo "Home Directory: ${HOME_DIR}"
    echo "Log: ${LOG_FILE}"
    echo ""
}

# --- Logging Functions ---
log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_success() {
    echo -e "${BOLD}${GREEN}[SUCCESS]${NC} $*"
}

section() {
    echo ""
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo -e "${BOLD}${CYAN} $*${NC}"
    echo -e "${BOLD}${BLUE}=====================================================${NC}"
    echo ""
}

# --- Error Handler ---
error_handler() {
    local line_no=$1
    local exit_code=$2
    log_error "Script failed at line ${line_no} with exit code ${exit_code}"
    log_error "Check log file: ${LOG_FILE}"
    
    if [[ "${PAM_MODIFIED}" == "true" && -n "${PAM_BACKUP}" ]]; then
        log_warn "PAM was modified. If sudo is broken, restore with:"
        echo -e "${YELLOW}  sudo cp ${PAM_BACKUP} /etc/pam.d/sudo${NC}"
    fi
    
    exit "${exit_code}"
}

trap 'error_handler ${LINENO} $?' ERR

# --- Sudo Management ---
setup_sudo() {
    if [[ "$EUID" -eq 0 ]]; then
        log_error "This script should not be run as root. Run as a regular user."
        exit 1
    fi
    
    if ! command -v sudo &>/dev/null; then
        log_error "sudo is required but not found."
        exit 1
    fi
    
    if ! sudo -v; then
        log_error "User must have sudo privileges."
        exit 1
    fi
    
    # Keep sudo alive
    (while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null) &
    log_info "Sudo privileges acquired and will be kept alive."
}

# --- Preflight Checks ---
preflight_checks() {
    section "Preflight Checks"
    
    # Verify Arch Linux
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        if [[ "${ID}" != "arch" ]]; then
            log_error "This script is designed for Arch Linux. Detected: ${ID}"
            exit 1
        fi
        log_info "Detected: ${PRETTY_NAME}"
    else
        log_error "Cannot detect Linux distribution."
        exit 1
    fi
    
    # Network check
    log_info "Checking network connectivity..."
    if ping -c 1 -W 5 archlinux.org &>/dev/null; then
        log_success "Network is reachable."
    elif host archlinux.org &>/dev/null; then
        log_warn "DNS works but ping blocked. Continuing..."
    else
        log_error "Network connectivity issue. Cannot reach archlinux.org"
        exit 1
    fi
    
    # Check for pacman
    if ! command -v pacman &>/dev/null; then
        log_error "pacman not found. This is impossible on Arch."
        exit 1
    fi
    
    # Check for udevadm
    if ! command -v udevadm &>/dev/null; then
        log_error "udevadm not found. Install systemd."
        exit 1
    fi
    
    # Detect AUR helper
    if command -v yay &>/dev/null; then
        AUR_HELPER="yay"
        log_info "AUR helper detected: yay"
    elif command -v paru &>/dev/null; then
        AUR_HELPER="paru"
        log_info "AUR helper detected: paru"
    else
        AUR_HELPER=""
        log_warn "No AUR helper found (yay/paru). Some packages may need manual installation."
    fi
    
    log_success "Preflight checks completed."
}

# --- Package Installation ---
install_packages() {
    section "Installing YubiKey Packages"
    
    local PACMAN_LIST=()
    local AUR_LIST=()
    
    local ALL_PACKAGES=(
        "yubikey-manager"
        "yubikey-manager-qt"
        "pam-u2f"
        "yubico-pam"
        "libfido2"
        "libu2f-host"
        "gnupg"
        "ccid"
        "pcsc-tools"
        "openssh"
    )
    
    # Detect pinentry variant
    local PINENTRY=""
    if [[ "${XDG_CURRENT_DESKTOP}" == *"KDE"* ]] || command -v pinentry-qt &>/dev/null; then
        PINENTRY="pinentry-qt"
    elif [[ "${XDG_CURRENT_DESKTOP}" == *"GNOME"* ]]; then
        PINENTRY="pinentry-gnome3"
    elif command -v pinentry-curses &>/dev/null; then
        PINENTRY="pinentry-curses"
    else
        PINENTRY="pinentry-tty"
    fi
    ALL_PACKAGES+=("${PINENTRY}")
    
    # Separate packages into repo and AUR
    log_info "Categorizing packages..."
    for pkg in "${ALL_PACKAGES[@]}"; do
        if pacman -Si "${pkg}" &>/dev/null; then
            PACMAN_LIST+=("${pkg}")
        else
            log_warn "${pkg} not in official repos, will try AUR."
            AUR_LIST+=("${pkg}")
        fi
    done
    
    # Install repo packages
    if [[ ${#PACMAN_LIST[@]} -gt 0 ]]; then
        log_info "Installing ${#PACMAN_LIST[@]} packages from official repos..."
        sudo pacman -Sy --needed --noconfirm "${PACMAN_LIST[@]}" || log_error "Some repo packages failed to install."
    fi
    
    # Install AUR packages
    if [[ ${#AUR_LIST[@]} -gt 0 ]]; then
        if [[ -n "${AUR_HELPER}" ]]; then
            log_info "Installing ${#AUR_LIST[@]} packages from AUR..."
            ${AUR_HELPER} -S --needed --noconfirm "${AUR_LIST[@]}" || log_warn "Some AUR packages failed."
        else
            log_warn "AUR packages needed but no helper available: ${AUR_LIST[*]}"
            log_warn "Install manually with: yay -S ${AUR_LIST[*]}"
        fi
    fi
    
    # Verify installations
    log_info "Verifying installed packages..."
    for pkg in "${ALL_PACKAGES[@]}"; do
        if pacman -Qi "${pkg}" &>/dev/null; then
            log_success "${pkg} installed."
        else
            log_warn "${pkg} not found in installed packages."
        fi
    done
    
    # Show versions
    if command -v ykman &>/dev/null; then
        log_info "ykman version: $(ykman --version 2>&1 | head -n1)"
    fi
    if command -v gpg &>/dev/null; then
        log_info "gpg version: $(gpg --version 2>&1 | head -n1)"
    fi
    
    log_success "Package installation completed."
}

# --- Udev Rules ---
ensure_udev_rules() {
    section "Configuring Udev Rules"
    
    local RULES_UPDATED=false
    
    # Check for existing rules
    if [[ -f /usr/lib/udev/rules.d/70-u2f.rules && -f /usr/lib/udev/rules.d/69-yubikey.rules ]]; then
        log_success "Udev rules already present in /usr/lib/udev/rules.d/"
    else
        log_warn "Some udev rules missing. Installing fallback rules..."
        
        # Create 70-u2f.rules
        sudo tee /etc/udev/rules.d/70-u2f.rules >/dev/null <<'EOF'
# U2F FIDO Security Key udev rules
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1050", TAG+="uaccess", MODE="0660"
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="2581", TAG+="uaccess", MODE="0660"
EOF
        log_success "Created /etc/udev/rules.d/70-u2f.rules"
        RULES_UPDATED=true
        
        # Create 69-yubikey.rules
        sudo tee /etc/udev/rules.d/69-yubikey.rules >/dev/null <<'EOF'
# YubiKey udev rules
ACTION=="add|change", SUBSYSTEM=="usb", ATTRS{idVendor}=="1050", TAG+="uaccess", MODE="0660"
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1050", TAG+="uaccess", MODE="0660"
EOF
        log_success "Created /etc/udev/rules.d/69-yubikey.rules"
        RULES_UPDATED=true
    fi
    
    # Reload udev
    if [[ "${RULES_UPDATED}" == "true" ]]; then
        log_info "Reloading udev rules..."
        sudo udevadm control --reload-rules
        sudo udevadm trigger --attr-match=subsystem=hidraw
        log_success "Udev rules reloaded."
    fi
    
    # Check for YubiKey
    log_info "Checking for connected YubiKey..."
    if ykman list 2>/dev/null | grep -q "YubiKey"; then
        log_success "YubiKey detected:"
        ykman list 2>/dev/null | sed 's/^/  /'
    else
        log_warn "No YubiKey detected. Insert and replug after script completes."
    fi
    
    if lsusb 2>/dev/null | grep -qi yubico; then
        log_info "YubiKey visible in lsusb:"
        lsusb | grep -i yubico | sed 's/^/  /'
    fi
}

# --- User Access ---
ensure_user_access() {
    section "Ensuring User Access to YubiKey"
    
    log_info "Verifying systemd-logind session for uaccess..."
    if loginctl show-user "${TARGET_USER}" &>/dev/null; then
        log_success "User ${TARGET_USER} has an active session."
    else
        log_warn "No active session detected for ${TARGET_USER}."
        log_warn "Run this script from your desktop environment or replug YubiKey after login."
    fi
    
    log_info "On Arch Linux with udev TAG+=uaccess, no additional groups are required."
    log_success "User access configuration complete."
}

# --- SSH Configuration ---
setup_ssh_config() {
    section "Configuring SSH for FIDO2 Keys"
    
    local SSH_DIR="${HOME_DIR}/.ssh"
    local SSH_CONFIG="${SSH_DIR}/config"
    
    # Create .ssh directory
    install -d -m 700 -o "${TARGET_USER}" "${SSH_DIR}"
    log_success "Ensured ${SSH_DIR} exists with correct permissions."
    
    # Create or update config
    if [[ ! -f "${SSH_CONFIG}" ]]; then
        touch "${SSH_CONFIG}"
        chown "${TARGET_USER}:$(id -gn "${TARGET_USER}")" "${SSH_CONFIG}"
        chmod 600 "${SSH_CONFIG}"
        log_info "Created ${SSH_CONFIG}"
    fi
    
    # Insert configuration block
    local MARKER_BEGIN="# BEGIN Betterstrap YubiKey"
    local MARKER_END="# END Betterstrap YubiKey"
    
    if grep -q "${MARKER_BEGIN}" "${SSH_CONFIG}"; then
        log_info "Updating existing Betterstrap YubiKey block in SSH config..."
        sed -i "/${MARKER_BEGIN}/,/${MARKER_END}/d" "${SSH_CONFIG}"
    else
        log_info "Adding new Betterstrap YubiKey block to SSH config..."
    fi
    
    cat >> "${SSH_CONFIG}" <<'EOF'
# BEGIN Betterstrap YubiKey
Host *
    AddKeysToAgent yes
    IdentityFile ~/.ssh/id_ed25519
    PubkeyAcceptedAlgorithms ssh-ed25519,sk-ssh-ed25519@openssh.com,ecdsa-sha2-nistp256,sk-ecdsa-sha2-nistp256@openssh.com
    HostKeyAlgorithms ssh-ed25519,ecdsa-sha2-nistp256
    PreferredAuthentications publickey,keyboard-interactive,password
# END Betterstrap YubiKey
EOF
    
    log_success "SSH configuration updated."
    
    # Check for FIDO2 support
    if ssh -Q key 2>/dev/null | grep -qE 'sk-'; then
        log_success "OpenSSH FIDO2 support detected:"
        ssh -Q key 2>/dev/null | grep -E 'sk-' | sed 's/^/  /'
    else
        log_warn "OpenSSH FIDO2 support not detected. Update OpenSSH or compile with libfido2."
    fi
}

# --- PAM U2F Configuration ---
configure_pam_u2f() {
    section "Configuring PAM U2F for Sudo"
    
    local PAM_FILE="/etc/pam.d/sudo"
    PAM_BACKUP="/etc/pam.d/sudo.betterstrap.backup.${START_TIME}"
    
    # Backup
    if [[ ! -f "${PAM_BACKUP}" ]]; then
        sudo cp "${PAM_FILE}" "${PAM_BACKUP}"
        log_success "Created backup: ${PAM_BACKUP}"
    fi
    
    local MARKER_BEGIN="# BEGIN Betterstrap YubiKey"
    local MARKER_END="# END Betterstrap YubiKey"
    
    # Check if already configured
    if sudo grep -q "${MARKER_BEGIN}" "${PAM_FILE}"; then
        log_info "Betterstrap YubiKey block already exists in ${PAM_FILE}. Skipping."
        return
    fi
    
    log_info "Adding PAM U2F configuration to ${PAM_FILE}..."
    
    # Create temporary file
    local TEMP_PAM=$(mktemp)
    sudo cp "${PAM_FILE}" "${TEMP_PAM}"
    
    # Insert before first "auth include system-auth"
    sudo awk -v begin="${MARKER_BEGIN}" -v end="${MARKER_END}" '
        !done && /^auth.*include.*system-auth/ {
            print begin
            print "auth       [success=1 default=ignore]  pam_u2f.so cue"
            print end
            done=1
        }
        {print}
    ' "${TEMP_PAM}" | sudo tee "${PAM_FILE}" >/dev/null
    
    rm -f "${TEMP_PAM}"
    PAM_MODIFIED=true
    
    log_success "PAM U2F configured for sudo."
    log_info "This allows YubiKey touch to authenticate sudo, with password fallback."
    
    # Test sudo still works
    log_info "Testing sudo still works with password..."
    if sudo -k && echo "test" | sudo -S true 2>/dev/null; then
        log_success "Sudo password authentication still functional."
    else
        log_warn "Could not verify sudo. Test manually after script completes."
    fi
}

# --- GPG Agent Configuration ---
configure_gpg_agent() {
    section "Configuring GnuPG and GPG Agent"
    
    local GNUPG_DIR="${HOME_DIR}/.gnupg"
    local GPG_AGENT_CONF="${GNUPG_DIR}/gpg-agent.conf"
    
    # Create .gnupg directory
    install -d -m 700 -o "${TARGET_USER}" "${GNUPG_DIR}"
    log_success "Ensured ${GNUPG_DIR} exists with correct permissions."
    
    # Detect pinentry
    local PINENTRY_PATH=""
    for pe in pinentry-qt pinentry-gnome3 pinentry-curses pinentry-tty; do
        if command -v "${pe}" &>/dev/null; then
            PINENTRY_PATH="$(command -v "${pe}")"
            log_info "Selected pinentry: ${PINENTRY_PATH}"
            break
        fi
    done
    
    if [[ -z "${PINENTRY_PATH}" ]]; then
        log_warn "No pinentry found. GPG PIN entry may not work."
        PINENTRY_PATH="/usr/bin/pinentry"
    fi
    
    # Create or update gpg-agent.conf
    local MARKER_BEGIN="# BEGIN Betterstrap YubiKey"
    local MARKER_END="# END Betterstrap YubiKey"
    
    if [[ -f "${GPG_AGENT_CONF}" ]] && grep -q "${MARKER_BEGIN}" "${GPG_AGENT_CONF}"; then
        log_info "Updating existing Betterstrap YubiKey block in gpg-agent.conf..."
        sed -i "/${MARKER_BEGIN}/,/${MARKER_END}/d" "${GPG_AGENT_CONF}"
    else
        log_info "Adding new Betterstrap YubiKey block to gpg-agent.conf..."
    fi
    
    cat >> "${GPG_AGENT_CONF}" <<EOF
${MARKER_BEGIN}
enable-ssh-support
pinentry-program ${PINENTRY_PATH}
default-cache-ttl 600
max-cache-ttl 7200
${MARKER_END}
EOF
    
    chown "${TARGET_USER}:$(id -gn "${TARGET_USER}")" "${GPG_AGENT_CONF}"
    chmod 600 "${GPG_AGENT_CONF}"
    log_success "GPG agent configuration updated."
    
    # Configure SSH_AUTH_SOCK via environment.d
    local ENV_D_DIR="${HOME_DIR}/.config/environment.d"
    local ENV_D_FILE="${ENV_D_DIR}/10-gnupg-ssh-agent.conf"
    
    install -d -m 755 -o "${TARGET_USER}" "${ENV_D_DIR}"
    
    cat > "${ENV_D_FILE}" <<'EOF'
SSH_AUTH_SOCK=$XDG_RUNTIME_DIR/gnupg/S.gpg-agent.ssh
EOF
    
    chown "${TARGET_USER}:$(id -gn "${TARGET_USER}")" "${ENV_D_FILE}"
    log_success "Created ${ENV_D_FILE}"
    
    # Fallback to shell rc files
    for RC in "${HOME_DIR}/.bashrc" "${HOME_DIR}/.zshrc"; do
        if [[ -f "${RC}" ]]; then
            if ! grep -q "GPG_AGENT SSH" "${RC}"; then
                log_info "Adding SSH_AUTH_SOCK export to $(basename "${RC}")..."
                cat >> "${RC}" <<'EOF'

# BEGIN Betterstrap YubiKey - GPG_AGENT SSH
export SSH_AUTH_SOCK="${XDG_RUNTIME_DIR}/gnupg/S.gpg-agent.ssh"
# END Betterstrap YubiKey
EOF
                chown "${TARGET_USER}:$(id -gn "${TARGET_USER}")" "${RC}"
            fi
        fi
    done
    
    # Restart gpg-agent
    log_info "Restarting gpg-agent..."
    sudo -u "${TARGET_USER}" gpgconf --kill gpg-agent 2>/dev/null || true
    sudo -u "${TARGET_USER}" gpgconf --launch gpg-agent 2>/dev/null || true
    log_success "GPG agent restarted."
}

# --- Browser Support Note ---
browser_support_note() {
    section "FIDO2 and U2F Browser Support"
    
    log_info "Confirming FIDO2 library support..."
    if command -v fido2-token &>/dev/null; then
        log_info "fido2-token available. Devices:"
        fido2-token -L 2>/dev/null | sed 's/^/  /' || log_warn "No FIDO2 devices detected yet."
    else
        log_warn "fido2-token not found. Install libfido2."
    fi
    
    log_info "Firefox and Chromium on Arch Linux include WebAuthn by default."
    log_success "Browser support ready for FIDO2/U2F."
}

# --- Final Notes ---
final_notes() {
    section "Installation Complete!"
    
    log_success "YubiKey tools installed and configured."
    echo ""
    echo -e "${BOLD}${CYAN}Modified Files:${NC}"
    echo -e "  - ${SSH_DIR}/config"
    echo -e "  - ${GNUPG_DIR}/gpg-agent.conf"
    echo -e "  - ${HOME_DIR}/.config/environment.d/10-gnupg-ssh-agent.conf"
    if [[ "${PAM_MODIFIED}" == "true" ]]; then
        echo -e "  - /etc/pam.d/sudo (backup: ${PAM_BACKUP})"
    fi
    echo ""
    echo -e "${BOLD}${CYAN}Log File:${NC} ${LOG_FILE}"
    echo ""
    echo -e "${BOLD}${YELLOW}===== NEXT STEPS =====${NC}"
    echo ""
    echo -e "${BOLD}1) Replug your YubiKey${NC} after udev rules reload."
    echo ""
    echo -e "${BOLD}2) Enroll U2F for sudo:${NC}"
    echo -e "   ${CYAN}mkdir -p ~/.config/Yubico${NC}"
    echo -e "   ${CYAN}pamu2fcfg --origin=pam://\$(hostname) --appid=pam://\$(hostname) > ~/.config/Yubico/u2f_keys${NC}"
    echo -e "   ${CYAN}# Add backup key (optional):${NC}"
    echo -e "   ${CYAN}pamu2fcfg -n --origin=pam://\$(hostname) --appid=pam://\$(hostname) >> ~/.config/Yubico/u2f_keys${NC}"
    echo -e "   ${CYAN}# Test:${NC}"
    echo -e "   ${CYAN}sudo -k && sudo true${NC}"
    echo ""
    echo -e "${BOLD}3) Create SSH FIDO2 key:${NC}"
    echo -e "   ${CYAN}ssh-keygen -t ed25519-sk -C \"yubikey-fido2@\$(hostname)\" -f ~/.ssh/id_ed25519_sk${NC}"
    echo -e "   ${CYAN}# For resident key (stored on YubiKey):${NC}"
    echo -e "   ${CYAN}ssh-keygen -t ed25519-sk -O resident -C \"yubikey@\$(hostname)\" -f ~/.ssh/id_ed25519_sk${NC}"
    echo -e "   ${CYAN}# Copy to server:${NC}"
    echo -e "   ${CYAN}ssh-copy-id -i ~/.ssh/id_ed25519_sk.pub user@server${NC}"
    echo ""
    echo -e "${BOLD}4) Configure GPG with YubiKey:${NC}"
    echo -e "   ${CYAN}gpg --card-status${NC}"
    echo -e "   ${CYAN}ykman openpgp info${NC}"
    echo -e "   ${CYAN}# Follow Yubico documentation to move subkeys to card:${NC}"
    echo -e "   ${CYAN}# https://developers.yubico.com/PGP/${NC}"
    echo ""
    echo -e "${BOLD}5) Test WebAuthn:${NC}"
    echo -e "   ${CYAN}Visit: https://webauthn.io${NC}"
    echo -e "   ${CYAN}   or: https://demo.yubico.com/webauthn-technical${NC}"
    echo ""
    if [[ "${PAM_MODIFIED}" == "true" ]]; then
        echo -e "${BOLD}${YELLOW}⚠ PAM Rollback (if needed):${NC}"
        echo -e "   ${CYAN}sudo cp ${PAM_BACKUP} /etc/pam.d/sudo${NC}"
        echo ""
    fi
    echo -e "${BOLD}${GREEN}Enjoy your YubiKey!${NC}"
    echo ""
}

# --- Main ---
main() {
    init_logging
    section "YubiKey Comprehensive Installer v1.0"
    log_info "Starting automated installation and configuration..."
    echo ""
    
    setup_sudo
    preflight_checks
    install_packages
    ensure_udev_rules
    ensure_user_access
    setup_ssh_config
    configure_pam_u2f
    configure_gpg_agent
    browser_support_note
    final_notes
    
    log_success "Script completed successfully at $(date)"
}

main "$@"
