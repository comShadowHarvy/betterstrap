#!/bin/bash

# Update the system
sudo pacman -Syu

# Install Chaotic AUR
sudo pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com
sudo pacman-key --lsign-key 3056513887B78AEB
sudo pacman -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'

if ! grep -q "\[chaotic-aur\]" /etc/pacman.conf; then
    echo "
[chaotic-aur]
Include = /etc/pacman.d/chaotic-mirrorlist
SigLevel = Never
" | sudo tee -a /etc/pacman.conf
fi

# Install BlackArch
curl -O https://blackarch.org/strap.sh
echo 8c47cd270afaa486359d18fc79d6a461ebce4bdf strap.sh | sha1sum -c
chmod +x strap.sh
sudo ./strap.sh

if ! grep -q "\[blackarch\]" /etc/pacman.conf; then
    echo "
[blackarch]
Server = https://mirror.blackarch.org/\$repo/os/\$arch
SigLevel = Never
" | sudo tee -a /etc/pacman.conf
fi

# Install ArchStrike
if ! grep -q "\[archstrike\]" /etc/pacman.conf; then
    echo "
[archstrike]
Server = https://mirror.archstrike.org/\$arch/\$repo
" | sudo tee -a /etc/pacman.conf
fi

sudo pacman -Syy

# Bootstrap and install the ArchStrike keyring
sudo pacman-key --init
dirmngr < /dev/null
sudo pacman-key -r 9D5F1C051D146843CDA4858BDE64825E7CBC0D51
sudo pacman-key --lsign-key 9D5F1C051D146843CDA4858BDE64825E7CBC0D51

# If issues with keyserver, download directly
# sudo pacman-key --init
# dirmngr < /dev/null
# wget https://archstrike.org/keyfile.asc
# sudo pacman-key --add keyfile.asc
# sudo pacman-key --lsign-key 9D5F1C051D146843CDA4858BDE64825E7CBC0D51

# Install required packages
sudo pacman -S archstrike-keyring
sudo pacman -S archstrike-mirrorlist

# Configure pacman to use the ArchStrike mirrorlist
sudo sed -i '/\[archstrike\]/,/Include/s/^#//' /etc/pacman.conf
sudo sed -i 's|Server = https://mirror.archstrike.org/\$arch/\$repo|Include = /etc/pacman.d/archstrike-mirrorlist|' /etc/pacman.conf

# Enable multilib repository
sudo sed -i '/\[multilib\]/,/Include/s/^#//' /etc/pacman.conf

# Refresh the package databases and upgrade the system
sudo pacman -Syy

