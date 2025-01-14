#!/bin/bash

# Function to display a loading bar with percentage
loading_bar() {
    local current=$1
    local total=$2
    local percent=$((100 * current / total))
    local bar_length=20
    local filled_length=$((bar_length * current / total))
    local empty_length=$((bar_length - filled_length))

    printf -v bar "%0.s#" $(seq 1 $filled_length)
    printf -v space "%0.s " $(seq 1 $empty_length)

    echo -ne "Progress: [${bar}${space}] (${percent}%%)\r"
}

# Function to check if a package is installed
is_package_installed() {
    pacman -Qs "$1" > /dev/null 2>&1
}

# Function to display the header
display_header() {
    clear
    echo "============================="
    echo "  Recommended Software Installer"
    echo "============================="
    echo
}

# Function to display a description
display_description() {
    local title=$1
    local description=$2
    local advantages=$3
    local disadvantages=$4

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

# Ensure yay is installed
if ! command -v yay > /dev/null 2>&1; then
    echo "Error: yay is not installed. Please install yay and rerun the script."
    exit 1
fi

# List of software to install
software=(

    "libreoffice:Free and powerful office suite, compatible with Microsoft Office formats:- Comprehensive office suite.\n- Free and open-source.:- May not have all features of Microsoft Office.\n- Interface may be different for MS Office users."
    "onlyoffice:Powerful office suite with collaborative features:- Collaborative editing.\n- Good compatibility with MS Office.:- Some advanced features require a subscription."
    "firefox:Fast and privacy-focused web browser:- Strong privacy protections.\n- Wide range of extensions.:- Can be resource-intensive."
    "google-chrome:Popular and fast web browser with a wide range of extensions:- Fast performance.\n- Extensive extension library.:- Privacy concerns.\n- Closed source."
    "thunderbird:Free and open-source email client:- Supports multiple email protocols.\n- Extensible with add-ons.:- Interface may seem dated."
    "slack:Collaboration hub for work, providing chat and file sharing:- Integrates with many services.\n- Good team collaboration features.:- Free version has limitations."
    "discord:VoIP, instant messaging, and digital distribution platform:- Free and feature-rich.\n- Large user base.:- Can be resource-intensive."
    "vlc:Free and open-source multimedia player:- Plays almost any media file.:- Interface may seem basic."
    "spotify:Digital music service providing access to millions of songs:- Huge music library.\n- Easy to use.:- Free version has ads."
    "gimp:Powerful and free image editor:- Comparable to Adobe Photoshop.\n- Free and open-source.:- Can have a steep learning curve."
    "krita:Professional and open-source painting program:- Great for digital painting.\n- Free and open-source.:- Not as versatile as Photoshop for photo editing."
    "filezilla:Free FTP solution for transferring files:- Easy to use.\n- Supports multiple protocols.:- May have more features than needed for basic users."
    "kdeconnect:Enables all your devices to communicate with each other:- Seamless integration with KDE desktop.:- Requires KDE environment for best experience."
    "bleachbit:Disk space cleaner and privacy manager:- Free up space and protect privacy.:- Can delete important files if not used carefully."
    "keepassxc:Cross-platform password manager:- Strong encryption.\n- Free and open-source.:- Interface can seem complex."
    "timeshift:System restore tool for Linux:- Easy system backups and restores.:- Can use a lot of disk space."
    "code:Powerful and popular code editor:- Highly extensible.\n- Free and open-source.:- Can be resource-intensive with many extensions."
    "git:Free and open-source distributed version control system:- Essential for version control.:- Requires learning Git commands."
    "deja-dup:Simple backup tool for GNOME:- Easy to use.\n- Integrated with GNOME.:- Limited advanced features."
    "rclone:Command-line program to manage files on cloud storage:- Supports many cloud providers.\n- Powerful and flexible.:- Requires command-line knowledge."
    "rambox:Messaging and emailing app that combines common web applications into one:- Combines multiple services in one app.:- Can be resource-intensive."
    "virtualbox:Powerful x86 and AMD64/Intel64 virtualization product:- Free and versatile.:- Performance can be lower than native."
    "vmware-player:Free virtualization tool for running multiple operating systems:- Good performance.\n- Free for non-commercial use.:- Advanced features require the paid version."
    "dropbox:Cloud storage service for file syncing and sharing:- Easy to use.\n- Cross-platform support.:- Limited free storage."
    "nextcloud:Self-hosted productivity platform that keeps you in control:- Complete control over data.\n- Many plugins available.:- Requires self-hosting knowledge."
    "simplenote:Simple and fast note-taking app:- Fast and easy to use.\n- Cross-platform support.:- Limited advanced features."
    "htop:Interactive process viewer for Unix systems:- Easy-to-use interface.\n- Detailed system monitoring.:- No built-in logging."
    "glances:Cross-platform system monitoring tool:- Detailed and comprehensive monitoring.:- Requires command-line knowledge."
    "kedit:Simple and lightweight text editor:- Lightweight and fast.\n- Easy to use.:- Limited advanced features."
    "microsoft-edge:Fast and secure web browser from Microsoft:- Fast performance.\n- Good integration with Microsoft services.:- Closed source.\n- Privacy concerns."
    "visual-studio-code:Popular code editor from Microsoft:- Highly extensible.\n- Large community and support.:- Some features require extensions."
    "anbox:Run Android applications on a Linux system:- Allows running Android apps on Linux.\n- Free and open-source.:- May have compatibility issues with some apps."
    "waydroid:Container-based approach to running full Android systems on Linux:- Full Android experience on Linux.\n- Good performance.:- Requires kernel modules and setup."
    "fzf:Fuzzy finder command-line tool for searching:- Fast and efficient.\n- Works with any text input.:- May require configuration for advanced usage."
    "zoxide:Fast directory jumper, an alternative to cd:- Simple and efficient.\n- Learns your directory habits.:- Requires shell configuration."

)

# Dynamically calculate the total number of steps
total_steps=${#software[@]}
current_step=0

# Display header
display_header

# Function to install software
install_software() {
    local software=$1
    local name=$(echo "$software" | cut -d: -f1)
    local description=$(echo "$software" | cut -d: -f2)
    local advantages=$(echo "$software" | cut -d: -f3)
    local disadvantages=$(echo "$software" | cut -d: -f4)

    if is_package_installed "$name"; then
        echo "$name is already installed. Skipping installation."
    else
        clear
        display_description "Installing $name" "$description" "$advantages" "$disadvantages"
        echo "Installing $name..."
        if yay -S --noconfirm "$name"; then
            echo "$name installed successfully."
        else
            echo "Error installing $name. Skipping to the next software."
        fi
    fi
    loading_bar $((++current_step)) $total_steps
}

# Install each software
for software in "${software[@]}"; do
    install_software "$software"
done

loading_bar $total_steps $total_steps
echo -e '\nAll software installed.\n'
