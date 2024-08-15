#!/bin/bash

# Function to display a loading bar with percentage
loading_bar() {
    local current=$1
    local total=$2
    local percent=$(( 100 * current / total ))
    local bar_length=20
    local filled_length=$(( bar_length * current / total ))
    local empty_length=$(( bar_length - filled_length ))

    printf -v bar "%0.s#" $(seq 1 $filled_length)
    printf -v space "%0.s " $(seq 1 $empty_length)

    echo -ne "Progress: [${bar}${space}] (${percent}%%)\r"
}

# Function to check if a repository is already added
is_repo_added() {
    grep -q "\[$1\]" /etc/pacman.conf
}

# Function to check if a package is installed
is_package_installed() {
    pacman -Qs $1 > /dev/null
}

# Function to display the header
display_header() {
    clear
    echo "============================="
    echo "   Ultimate Repo Installer"
    echo "============================="
    echo
}

# Function to display a description
display_description() {
    local title=$1
    local description=$2
    local advantages=$3
    local disadvantages=$4

    tput cup 4 0
    echo "============================="
    echo "   $title"
    echo "============================="
    echo
    echo "Description:"
    echo "$description"
    echo
    echo "Advantages:"
    echo -e "$advantages"
    echo
    echo "Disadvantages:"
    echo -e "$disadvantages"
    echo
}

total_steps=12
current_step=0

display_header

# Add Chaotic AUR repository
loading_bar $current_step $total_steps
if is_repo_added "chaotic-aur"; then
    echo "Chaotic AUR repository already added."
else
    display_description "Adding Chaotic AUR Repository" \
        "Chaotic AUR is a repository that provides pre-built versions of popular AUR packages." \
        "- Faster installation since packages are pre-built.\n- Reduces the need to compile packages locally." \
        "- May not always have the latest version of every package.\n- Trusting third-party binaries requires a level of trust in the maintainers."
    sleep 7
    sudo pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com
    sudo pacman-key --lsign-key 3056513887B78AEB
    sudo pacman -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst'
    sudo pacman -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'

    echo "[chaotic-aur]
Include = /etc/pacman.d/chaotic-mirrorlist" | sudo tee -a /etc/pacman.conf

    loading_bar $((++current_step)) $total_steps
    echo -ne '\nChaotic AUR repository added.\n'
fi

# Add ArchStrike repository
loading_bar $current_step $total_steps
if is_repo_added "archstrike"; then
    echo "ArchStrike repository already added."
else
    display_description "Adding ArchStrike Repository" \
        "ArchStrike is a repository for security professionals and enthusiasts containing a large collection of security software." \
        "- Extensive collection of security tools.\n- Regularly updated and maintained." \
        "- May include tools that require advanced knowledge to use safely.\n- Can be overwhelming due to the sheer number of tools available."
    sleep 7
    sudo pacman-key --recv-key 5B5F5BBF9A2D15A019E20608A106C36A3170E57D --keyserver keyserver.ubuntu.com
    sudo pacman-key --lsign-key 5B5F5BBF9A2D15A019E20608A106C36A3170E57D

    echo "[archstrike]
Server = https://mirror.archstrike.org/\$arch/\$repo" | sudo tee -a /etc/pacman.conf

    loading_bar $((++current_step)) $total_steps
    echo -ne '\nArchStrike repository added.\n'
fi

# Add BlackArch repository
loading_bar $current_step $total_steps
if is_repo_added "blackarch"; then
    echo "BlackArch repository already added."
else
    display_description "Adding BlackArch Repository" \
        "BlackArch is an Arch Linux-based distribution for penetration testers and security researchers, including a large collection of security tools." \
        "- Comprehensive suite of tools for penetration testing and security research.\n- Regular updates and community support." \
        "- Requires careful usage to avoid legal issues.\n- Can be resource-intensive due to the number of tools installed."
    sleep 7
    curl -O https://blackarch.org/strap.sh
    sudo chmod +x strap.sh
    sudo ./strap.sh

    loading_bar $((++current_step)) $total_steps
    echo -ne '\nBlackArch repository added.\n'
fi

# Update package database
loading_bar $current_step $total_steps
display_description "Updating Package Database" \
    "This step updates the package database to ensure that all repositories are in sync and that the latest packages are available." \
    "- Ensures you have the latest package lists.\n- Synchronizes your local package database with the remote repositories." \
    "- May take some time depending on your internet connection.\n- Must be done regularly to keep your system up to date."
sleep 7
sudo pacman -Syyu

loading_bar $((++current_step)) $total_steps
echo -ne '\nPackage database updated.\n'

# Install fakeroot
loading_bar $current_step $total_steps
if is_package_installed "fakeroot"; then
    echo "fakeroot is already installed."
else
    display_description "Installing fakeroot" \
        "fakeroot provides a simulated root environment for building packages without needing actual root permissions." \
        "- Allows non-root users to create packages.\n- Enhances security by reducing the need for root access." \
        "- Only simulates root privileges, not a substitute for actual root access."
    sleep 7
    sudo pacman -S --noconfirm fakeroot
    loading_bar $((++current_step)) $total_steps
    echo -ne '\nfakeroot installed.\n'
fi

# Install apparmor
loading_bar $current_step $total_steps
if is_package_installed "apparmor"; then
    echo "apparmor is already installed."
else
    display_description "Installing AppArmor" \
        "AppArmor is a Linux security module that provides mandatory access control for programs, confining them to a limited set of resources." \
        "- Enhances system security by restricting applications' capabilities.\n- Easy to use and configure with profile-based policies." \
        "- Requires configuration and maintenance of profiles.\n- May cause issues with applications if profiles are not correctly set up."
    sleep 7
    sudo pacman -S --noconfirm apparmor
    sudo systemctl enable apparmor
    sudo systemctl start apparmor
    loading_bar $((++current_step)) $total_steps
    echo -ne '\napparmor installed and started.\n'
fi

# Install yay
loading_bar $current_step $total_steps
if is_package_installed "yay"; then
    echo "yay is already installed."
else
    display_description "Installing yay" \
        "yay (Yet Another Yaourt) is a popular AUR helper that simplifies the process of installing and managing AUR packages." \
        "- Combines the functionality of pacman and AUR helpers.\n- Provides an interactive search and update interface." \
        "- May introduce additional dependencies.\n- Users need to trust the AUR package maintainers."
    sleep 7
    sudo pacman -S --noconfirm yay
    loading_bar $((++current_step)) $total_steps
    echo -ne '\nyay installed.\n'
fi

# Install paru
loading_bar $current_step $total_steps
if is_package_installed "paru"; then
    echo "paru is already installed."
else
    display_description "Installing paru" \
        "paru is a modern AUR helper written in Rust, focusing on speed, security, and a user-friendly interface." \
        "- Fast and secure with a Rust backend.\n- Intuitive and user-friendly." \
        "- May have a steeper learning curve for new users.\n- Still gaining community traction compared to older AUR helpers."
    sleep 7
    sudo pacman -S --noconfirm paru
    loading_bar $((++current_step)) $total_steps
    echo -ne '\nparu installed.\n'
fi

# Install pamac
loading_bar $current_step $total_steps
if is_package_installed "pamac-aur"; then
    echo "pamac is already installed."
else
    display_description "Installing pamac" \
        "pamac is a graphical package manager from Manjaro that supports both official repositories and the AUR." \
        "- User-friendly graphical interface.\n- Supports both official repositories and the AUR." \
        "- May not offer as many advanced features as command-line AUR helpers.\n- Slightly higher resource usage due to the graphical interface."
    sleep 7
    sudo pacman -S --noconfirm pamac-aur
    loading_bar $((++current_step)) $total_steps
    echo -ne '\npamac installed.\n'
fi

# Install aurman
loading_bar $current_step $total_steps
if is_package_installed "aurman"; then
    echo "aurman is already installed."
else
    display_description "Installing aurman" \
        "aurman is an AUR helper that aims to provide a simple and efficient interface for managing AUR packages." \
        "- Lightweight and fast.\n- Similar command structure to pacman." \
        "- May not be as actively maintained as some other AUR helpers.\n- Fewer advanced features compared to newer AUR helpers."
    sleep 7
    yay -S --noconfirm aurman
    loading_bar $((++current_step)) $total_steps
    echo -ne '\naurman installed.\n'
fi

loading_bar $total_steps $total_steps
echo -ne '\nAll steps completed.\n'
