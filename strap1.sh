#!/bin/bash

# Function to display a fake loading bar
loading_bar() {
    bar="##################################################"
    bar_length=${#bar}
    percentage=0

    echo -n "["
    while [ $percentage -lt 100 ]; do
        n=$(($percentage * $bar_length / 100))
        printf "%s" "${bar:0:n}"
        printf "%s" ">"
        printf "%*s" $(($bar_length - $n - 1)) ""
        echo -n "] $percentage% "
        sleep 0.05
        percentage=$((percentage + 1))
        echo -ne "\r"
    done
    echo "[${bar}] 100%"
}

echo "Starting setup..."
loading_bar

# Define key ID and keyserver
keyID="3056513887B78AEB"
keyServer="keyserver.ubuntu.com"
echo "Defined key variables."
loading_bar

# Define package URLs
keyringPackageUrl="https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst"
mirrorlistPackageUrl="https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst"
echo "Package URLs defined."
loading_bar

# Update system and install necessary packages
echo "Updating system and installing necessary packages..."
loading_bar
sudo pacman -Sy --noconfirm base-devel git wget curl

# Check if zsh is installed
echo "Checking if zsh is installed..."
loading_bar
if ! command -v zsh &> /dev/null; then
    echo "zsh is not installed. Installing zsh..."
    loading_bar
    sudo pacman -S zsh --noconfirm
else
    echo "zsh is already installed."
    loading_bar
fi

# Receive the key
echo "Receiving key..."
loading_bar
sudo pacman-key --recv-key $keyID --keyserver $keyServer

# Locally sign the key
echo "Signing key..."
loading_bar
sudo pacman-key --lsign-key $keyID

# Install the chaotic keyring package
echo "Installing the Chaotic AUR keyring package..."
loading_bar
sudo pacman -U $keyringPackageUrl --noconfirm

# Install the chaotic mirrorlist package
echo "Installing the Chaotic AUR mirrorlist package..."
loading_bar
sudo pacman -U $mirrorlistPackageUrl --noconfirm

# Append Chaotic AUR repo to pacman.conf
echo "Configuring pacman to use the Chaotic AUR..."
loading_bar
echo -e "\n[chaotic-aur]\nInclude = /etc/pacman.d/chaotic-mirrorlist" | sudo tee -a /etc/pacman.conf > /dev/null

# Disable signature verification in pacman.conf
echo "Disabling signature verification in pacman.conf..."
loading_bar
sudo sed -i 's/^SigLevel    = Required DatabaseOptional$/SigLevel = Never/' /etc/pacman.conf

# Download the BlackArch strap.sh script
echo "Downloading the BlackArch strap.sh script..."
loading_bar
wget https://blackarch.org/strap.sh
echo "Making strap.sh executable..."
loading_bar
chmod +x strap.sh

# Execute the strap.sh script with superuser privileges
echo "Running strap.sh..."
loading_bar
sudo ./strap.sh

# Install paru from AUR
echo "Cloning the paru repository..."
loading_bar
git clone https://aur.archlinux.org/paru.git
cd paru
echo "Building and installing paru..."
loading_bar
makepkg -si --noconfirm
cd ..
rm -rf paru

# Install Metasploit
echo "Installing Metasploit..."
loading_bar
sudo pacman -S metasploit --noconfirm

# Refresh the package databases and update the system packages
echo "Refreshing package databases and updating system packages..."
loading_bar
sudo pacman -Syu --noconfirm

# Install Pacui from AUR
echo "Installing Pacui from AUR..."
loading_bar
paru -S pacui --noconfirm

# Install Snapd
echo "Installing Snapd and enabling the service..."
loading_bar
sudo pacman -S snapd --noconfirm
sudo systemctl enable --now snapd.socket

# Install Flatpak
echo "Installing Flatpak..."
loading_bar
sudo pacman -S flatpak --noconfirm

# Install AppImageLauncher
echo "Installing AppImageLauncher from AUR..."
loading_bar
paru -S appimagelauncher --noconfirm

# Install Docker
echo "Installing Docker..."
loading_bar
sudo pacman -S docker --noconfirm
echo "Enabling and starting Docker service..."
loading_bar
sudo systemctl enable --now docker.service

# Add environment variables and Git configuration to ~/.zshrc if not already present
echo "Adding environment variables and Git configuration to ~/.zshrc if not already present..."
loading_bar


echo "Setup complete. All selected packages have been installed and configured."
loading_bar
