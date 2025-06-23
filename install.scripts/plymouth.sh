# This script installs and configures Plymouth on Arch Linux.

# --- Configuration Variables ---
# Choose your desired Plymouth theme. Common themes include:
#   spinfinity, solar, fade-in, bgrt, tribar, script
# You can list available themes with: `ls /usr/share/plymouth/themes/`
PLYMOUTH_THEME="spinfinity"

# --- Functions ---

# Function to display messages
display_message() {
    echo -e "\n---> $1 <---\n"
}

# Function to check for root privileges
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "This script must be run as root. Please use 'sudo'."
        exit 1
    fi
}

# Function for the title screen
show_title_screen() {
    clear
    echo "-----------------------------------------------------"
    echo "                 Plymouth Installer"
    echo "           for Arch Linux Systems"
    echo "-----------------------------------------------------"
    echo ""
    echo "This script automates the installation and basic"
    echo "configuration of Plymouth, providing a graphical"
    echo "boot animation for your Arch Linux system."
    echo ""
    echo "Author: ShadowHarvy"
    echo "-----------------------------------------------------"
    echo ""
    echo "Press Enter to begin..."
    read -r
    clear
}

# Function for a fake loading screen
fake_loading_screen() {
    local duration=3  # Duration in seconds for the fake load
    local steps=20    # Number of steps in the progress bar
    local delay=$(echo "scale=2; $duration / $steps" | bc)
    local progress_char="█"
    local empty_char="░"
    local bar_length=50

    echo "Preparing for installation, please wait..."
    echo -n "["
    for ((i=0; i<steps; i++)); do
        echo -n "${progress_char}"
        sleep "$delay"
    done
    echo "]"
    echo "Loading complete!"
    sleep 1
    clear
}

# Function to install Plymouth
install_plymouth() {
    display_message "Synchronizing package databases..."
    sudo pacman -Sy || { echo "Failed to synchronize package databases. Exiting."; exit 1; }

    display_message "Installing Plymouth..."
    sudo pacman -S --noconfirm plymouth || { echo "Failed to install Plymouth. Exiting."; exit 1; }
    echo "Plymouth installed successfully."
}

# Function to set the Plymouth theme
set_plymouth_theme() {
    display_message "Setting Plymouth theme to '$PLYMOUTH_THEME'..."
    sudo plymouth-set-default-theme "$PLYMOUTH_THEME" || { echo "Failed to set Plymouth theme. Exiting."; exit 1; }
    echo "Theme set to '$PLYMOUTH_THEME'."
}

# Function to update initramfs and GRUB for Arch Linux
update_system_arch() {
    display_message "Configuring /etc/mkinitcpio.conf for Plymouth..."
    # Add 'plymouth' hook before 'udev' hook
    # This sed command assumes 'udev' is present and adds 'plymouth' before it if not already there.
    if ! grep -q "HOOKS=.*udev" /etc/mkinitcpio.conf; then
        echo "Warning: 'udev' hook not found in /etc/mkinitcpio.conf. Please ensure your HOOKS line is correctly configured."
        echo "Attempting to add 'plymouth' hook without 'udev' reference."
        # This might not be ideal, but it prevents the script from failing completely
        # if udev is missing or named differently. Manual intervention might be needed.
        sudo sed -i '/^HOOKS=/s/\(HOOKS=".*\)"/\1 plymouth"/' /etc/mkinitcpio.conf
    elif ! grep -q "HOOKS=.*plymouth" /etc/mkinitcpio.conf; then
        sudo sed -i '/^HOOKS=/s/\(udev\)/plymouth \1/' /etc/mkinitcpio.conf
        display_message "Added 'plymouth' hook to /etc/mkinitcpio.conf."
    else
        display_message "'plymouth' hook already present in /etc/mkinitcpio.conf. Skipping modification."
    fi

    display_message "Updating initramfs to apply Plymouth changes..."
    sudo mkinitcpio -P || { echo "Failed to update initramfs. Exiting."; exit 1; }
    echo "Initramfs updated successfully."

    display_message "Updating GRUB configuration..."
    # Add `splash` and `quiet` to kernel boot parameters for graphical boot in GRUB
    # Check if 'splash' is already present in GRUB_CMDLINE_LINUX_DEFAULT
    if ! grep -q "splash" /etc/default/grub; then
        sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="\(.*\)"/GRUB_CMDLINE_LINUX_DEFAULT="\1 splash"/' /etc/default/grub
        display_message "Added 'splash' to GRUB_CMDLINE_LINUX_DEFAULT."
    else
        display_message "'splash' already present in GRUB_CMDLINE_LINUX_DEFAULT. Skipping modification."
    fi

    # Ensure quiet is present, which is often used with splash
    if ! grep -q "quiet" /etc/default/grub; then
        sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="\(.*\)"/GRUB_CMDLINE_LINUX_DEFAULT="\1 quiet"/' /etc/default/grub
        display_message "Added 'quiet' to GRUB_CMDLINE_LINUX_DEFAULT."
    else
        display_message "'quiet' already present in GRUB_CMDLINE_LINUX_DEFAULT. Skipping modification."
    fi

    sudo grub-mkconfig -o /boot/grub/grub.cfg || { echo "Failed to update GRUB configuration. Exiting."; exit 1; }
    echo "GRUB configuration updated successfully."
}

# Function to verify installation (optional)
verify_plymouth() {
    display_message "Verifying Plymouth configuration..."
    echo "Current default theme: $(plymouth-set-default-theme -R)"
    if grep -q "splash" /etc/default/grub; then
        echo "'splash' parameter found in /etc/default/grub."
    else
        echo "'splash' parameter NOT found in /etc/default/grub. Plymouth might not show."
    fi
    if grep -q "HOOKS=.*plymouth" /etc/mkinitcpio.conf; then
        echo "'plymouth' hook found in /etc/mkinitcpio.conf."
    else
        echo "'plymouth' hook NOT found in /etc/mkinitcpio.conf. Plymouth might not show."
    fi
    echo "Check output of 'mkinitcpio -P' for any errors during boot image generation."
}

# --- Main Script Execution ---

show_title_screen
fake_loading_screen
check_root
install_plymouth
set_plymouth_theme
update_system_arch
verify_plymouth

display_message "Plymouth installation and configuration complete for Arch Linux!"
display_message "Reboot your system to see the changes: sudo reboot"

# --- End of Script ---