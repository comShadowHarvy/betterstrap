#!/bin/bash
# Enhanced Arch Linux Rice Setup Script with selective repository installation

# Error handling function - logs error but doesn't exit
handle_error() {
    echo "Error: $1"
    echo "Continuing with next step..."
}

# Function to check if repository already exists in pacman.conf
repo_exists() {
    grep -q "\[$1\]" /etc/pacman.conf
}

# Check which repositories are already configured
echo "==> Checking existing repositories..."
REPOS=("chaotic-aur" "blackarch" "archstrike" "multilib")
EXISTING=()
MISSING=()

for repo in "${REPOS[@]}"; do
    if repo_exists "$repo"; then
        EXISTING+=("$repo")
    else
        MISSING+=("$repo")
    fi
done

echo "* Already configured repositories: ${EXISTING[*]:-None}"
echo "* Missing repositories: ${MISSING[*]:-None}"
echo

# Update the system first
echo "==> Updating system packages..."
sudo pacman -Syu --noconfirm || handle_error "Failed to update system"

# Only proceed with repositories that are missing
for repo in "${MISSING[@]}"; do
    case "$repo" in
        "chaotic-aur")
            # ----------------------
            # CHAOTIC AUR REPOSITORY
            # ----------------------
            echo "==> Setting up Chaotic AUR repository..."
            # Import and sign key
            sudo pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com || handle_error "Failed to receive Chaotic AUR key"
            sudo pacman-key --lsign-key 3056513887B78AEB || handle_error "Failed to sign Chaotic AUR key"

            # Install keyring and mirrorlist
            sudo pacman -U --noconfirm 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst' || handle_error "Failed to install Chaotic AUR packages"

            # Add to pacman.conf
            echo -e "\n[chaotic-aur]\nInclude = /etc/pacman.d/chaotic-mirrorlist\n" | sudo tee -a /etc/pacman.conf > /dev/null
            echo "Chaotic AUR repository added successfully"
            ;;

        "blackarch")
            # ----------------------
            # BLACKARCH REPOSITORY
            # ----------------------
            echo "==> Setting up BlackArch repository..."
            # Download and verify strap.sh
            curl -O https://blackarch.org/strap.sh || handle_error "Failed to download BlackArch strap.sh"

            # Only continue with BlackArch setup if the download succeeded
            if [ -f "strap.sh" ]; then
                echo "86eb4efb68918dbfdd1e22862a48fda20a8145ff strap.sh" | sha1sum -c || handle_error "BlackArch script verification failed"

                # Make executable and install
                chmod +x strap.sh
                sudo ./strap.sh || handle_error "BlackArch bootstrap failed"

                # Clean up
                rm strap.sh

                # Update and sync packages after successful installation
                sudo pacman -Syyu || handle_error "Failed to sync BlackArch packages"

                echo "BlackArch repository added successfully"
            else
                echo "Skipping BlackArch setup due to download failure"
            fi
            ;;

        "archstrike")
            # ----------------------
            # ARCHSTRIKE REPOSITORY
            # ----------------------
            echo "==> Setting up ArchStrike repository..."
            # Initialize pacman keyring if needed
            sudo pacman-key --init || handle_error "Failed to initialize pacman keyring"

            # Import and sign ArchStrike key
            echo "Importing ArchStrike key..."
            # Make sure dirmngr is running
            dirmngr < /dev/null
            KEY_IMPORTED=false

            # First try: direct key reception from keyserver
            if sudo pacman-key -r 9D5F1C051D146843CDA4858BDE64825E7CBC0D51; then
                KEY_IMPORTED=true
            else
                # Try an alternative keyserver if the default fails
                echo "Default keyserver unreachable, trying alternative keyserver..."
                if sudo pacman-key --keyserver hkps://keys.openpgp.org -r 9D5F1C051D146843CDA4858BDE64825E7CBC0D51; then
                    KEY_IMPORTED=true
                else
                    # Last attempt: try direct download
                    echo "Key servers might be unreachable, trying direct download..."
                    if curl -O https://archstrike.org/keyfile.asc; then
                        if sudo pacman-key --add keyfile.asc; then
                            KEY_IMPORTED=true
                        else
                            handle_error "Failed to add ArchStrike key"
                        fi
                        rm -f keyfile.asc
                    else
                        handle_error "Failed to download ArchStrike keyfile"
                    fi
                fi
            fi

            if [ "$KEY_IMPORTED" = true ]; then
                # Sign the key
                sudo pacman-key --lsign-key 9D5F1C051D146843CDA4858BDE64825E7CBC0D51 || handle_error "Failed to sign ArchStrike key"

                # Create mirrorlist file first
                sudo mkdir -p /etc/pacman.d/
                echo "Server = https://mirror.archstrike.org/\$arch/\$repo" | sudo tee /etc/pacman.d/archstrike-mirrorlist > /dev/null

                # Add ArchStrike repository to pacman.conf
                echo -e "\n[archstrike]\nInclude = /etc/pacman.d/archstrike-mirrorlist\n" | sudo tee -a /etc/pacman.conf > /dev/null

                # Refresh package databases
                sudo pacman -Syy || handle_error "Failed to refresh package databases"

                # Install ArchStrike keyring
                sudo pacman -S --noconfirm archstrike-keyring || handle_error "Failed to install ArchStrike keyring"
                echo "ArchStrike repository added successfully"
            else
                echo "Skipping ArchStrike setup due to key import failure"
            fi
            ;;

        "multilib")
            # ----------------------
            # ENABLE MULTILIB
            # ----------------------
            echo "==> Enabling multilib repository..."
            if grep -q "^\s*#\s*\[multilib\]" /etc/pacman.conf; then
                sudo sed -i '/\[multilib\]/,/Include/s/^#//' /etc/pacman.conf
                echo "Multilib repository enabled"
            else
                if grep -q "^\s*\[multilib\]" /etc/pacman.conf; then
                    echo "Multilib repository already enabled"
                else
                    echo "Multilib section not found in /etc/pacman.conf."
                    echo "Consider adding it manually if needed."
                fi
            fi
            ;;
    esac
done

# ----------------------
# FINAL SYSTEM UPDATE
# ----------------------
echo "==> Refreshing package databases and upgrading system..."
sudo pacman -Syyu --noconfirm || handle_error "Final system update failed"

SUCCESSFUL=0
FAILED=0

# Check which repositories are now successfully configured
echo -e "\n==> Repository Setup Summary:"
for repo in "${REPOS[@]}"; do
    if repo_exists "$repo"; then
        echo "✓ $repo repository configured successfully"
        ((SUCCESSFUL++))
    else
        echo "✗ $repo repository configuration failed or incomplete"
        ((FAILED++))
    fi
done

echo -e "\n==> Setup completed with $SUCCESSFUL repositories configured successfully and $FAILED failed."
echo "==> You can now proceed with installing your ricing packages."
