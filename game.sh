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

# Function to check if a package is installed
is_package_installed() {
    pacman -Qs $1 > /dev/null
}

# Function to display the header
display_header() {
    clear
    echo "============================="
    echo "  Gaming Software Installer"
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
    echo "----------------------------------"
    echo
}

total_steps=12
current_step=0

display_header

# List of gaming software to install
gaming_software=(
    "steam:Popular gaming platform:- Wide range of games.\n- Native Linux support.:- Can be resource-intensive."
    "heroic-games-launcher-bin:Open-source alternative to Epic Games Launcher:- Supports Epic Games and GOG.:- Still in active development."
    "lutris:Game manager for multiple platforms:- Supports multiple platforms.\n- Easy game installation.:- Some games may require tweaking."
    "mangohud:Performance overlay for Vulkan and OpenGL:- Displays performance metrics.:- May require configuration."
    "proton-ge-custom-bin:Custom version of Proton for Steam:- Improved game compatibility.:- Requires manual updates."
    "wine:Compatibility layer for running Windows applications:- Allows running Windows games.:- Some games may not run perfectly."
    "dxvk:Vulkan-based Direct3D 9/10/11 translation layer:- Improves performance in games.:- Requires Vulkan support."
    "vkd3d:Vulkan-based Direct3D 12 translation layer:- Runs Direct3D 12 games on Vulkan.:- Still under development."
    "gamemode:Optimizes system performance for gaming:- Improves game performance.:- May not support all games."
    "obs-studio:Recording and streaming software:- Free and powerful.:- Can be complex to set up."
    "goverlay:GUI for configuring MangoHud and other overlays:- Easy configuration of overlays.:- Limited to supported overlays."
    "discord:VoIP and instant messaging platform:- Essential for gaming communication.:- Can be resource-intensive."
)

# Function to install a software
install_software() {
    local software=$1
    local name=$(echo $software | cut -d: -f1)
    local description=$(echo $software | cut -d: -f2)
    local advantages=$(echo $software | cut -d: -f3)
    local disadvantages=$(echo $software | cut -d: -f4)

    clear
    display_description "Installing $name" "$description" "$advantages" "$disadvantages"
    sleep 5
    if is_package_installed "$name"; then
        echo "$name is already installed."
    else
        yay -S --noconfirm $name
        echo -ne "\n$name installed.\n"
    fi
    loading_bar $((++current_step)) $total_steps
}

# Install each software
for software in "${gaming_software[@]}"; do
    install_software "$software"
done

loading_bar $total_steps $total_steps
echo -ne '\nAll gaming software installed.\n'
