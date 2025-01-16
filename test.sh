#!/bin/bash

echo "Starting setup..."

# Define key ID and keyserver for Chaotic AUR
keyID="3056513887B78AEB"
keyServer="keyserver.ubuntu.com"
keyringPackageUrl="https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst"
mirrorlistPackageUrl="https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst"
deviousDiamondsUrl="https://github.com/JanDeDobbeleer/oh-my-posh/raw/main/themes/devious-diamonds.omp.yaml"
echo "Defined key variables and package URLs."

# Define temporary directory and log files
tempDir=$(mktemp -d)
logFile="$tempDir/setup.log"
paclockUrl="https://raw.githubusercontent.com/comShadowHarvy/conf/main/paclock.sh"
repoScriptUrl="https://raw.githubusercontent.com/comShadowHarvy/conf/main/repo.sh"
zshrcUrl="https://raw.githubusercontent.com/comShadowHarvy/conf/main/.zshrc"
aliasesUrl="https://raw.githubusercontent.com/comShadowHarvy/conf/main/.aliases"
antigenrcUrl="https://raw.githubusercontent.com/comShadowHarvy/conf/main/.antigenrc"
zsh1Url="https://raw.githubusercontent.com/comShadowHarvy/conf/main/.zsh1"
fabricRepo="https://github.com/danielmiessler/fabric.git"
confRepo="https://github.com/comShadowHarvy/conf"
installedLogFile="$HOME/installed.log"
failedLogFile="$HOME/failed.log"

# Initialize log files
echo "Installed Packages:" > "$installedLogFile"
echo "Failed Packages:" > "$failedLogFile"

# Function to log and run commands
run_command() {
    echo "Running: $1"
    echo "Running: $1" >> "$logFile"
    eval "$1" >> "$logFile" 2>&1
    if [ $? -ne 0 ]; then
        echo "Error: Command failed - $1" | tee -a "$failedLogFile"
    else
        echo "Success: Command succeeded - $1" >> "$installedLogFile"
    fi
}

# Function to run repo.sh script as sudo
run_repo_script() {
    echo "Running repo.sh script as sudo..."
    run_command "sudo bash -c \"\$(curl -fsSL $repoScriptUrl)\""
}

# Function to update system and install base packages
install_packages() {
    echo "Updating system and installing base packages..."
    echo "Installing base-devel (development tools), git (version control), wget (file retrieval), curl (data transfer), zsh (shell), yadm (dotfiles manager)"
    run_command "sudo pacman -Sy --noconfirm base-devel git wget curl zsh yadm"
}

# Function to install and configure Chaotic AUR
install_chaotic_aur() {
    echo "Installing and configuring Chaotic AUR..."
    echo "Adding Chaotic AUR key and installing keyring and mirrorlist packages"
    run_command "sudo pacman-key --recv-key $keyID --keyserver $keyServer"
    run_command "sudo pacman-key --lsign-key $keyID"
    run_command "sudo pacman -U $keyringPackageUrl --noconfirm"
    run_command "sudo pacman -U $mirrorlistPackageUrl --noconfirm"
}

# Function to install BlackArch repository
install_blackarch() {
    echo "Installing BlackArch repository..."
    echo "Downloading and running the BlackArch strap script"
    if ! command -v blackarch &> /dev/null; then
        run_command "wget https://blackarch.org/strap.sh -O $tempDir/strap.sh"
        run_command "chmod +x $tempDir/strap.sh"
        run_command "sudo $tempDir/strap.sh"
    else
        echo "BlackArch is already installed"
    fi
}

# Function to install paru AUR helper
install_paru() {
    echo "Installing paru AUR helper..."
    echo "Cloning, building, and installing paru"
    if ! command -v paru &> /dev/null; then
        run_command "git clone https://aur.archlinux.org/paru.git $tempDir/paru"
        (cd $tempDir/paru && run_command "makepkg -si --noconfirm")
        rm -rf $tempDir/paru
    else
        echo "paru is already installed"
    fi
}

# Function to install specific packages
install_specific_packages() {
    echo "Installing specific packages..."
    echo "Installing metasploit (penetration testing framework), pacui (AUR helper), snapd (package manager), flatpak (package manager), appimagelauncher (AppImage integration), docker (container platform), python-pip (Python package manager)"
    packages=("metasploit" "pacui" "snapd" "flatpak" "appimagelauncher" "docker" "python-pip")
    for pkg in "${packages[@]}"; do
        if ! pacman -Qi $pkg &> /dev/null; then
            run_command "paru -S $pkg --noconfirm"
        else
            echo "$pkg is already installed"
        fi
    done
    run_command "sudo systemctl enable --now snapd.socket docker.service"
}

# Function to install pipx
install_pipx() {
    echo "Installing pipx..."
    if ! command -v pipx &> /dev/null; then
        run_command "pip3 install --user pipx"
        run_command "pipx ensurepath"
        if ! command -v pipx &> /dev/null; then
            echo "Error: pipx installation failed" | tee -a "$failedLogFile"
        else
            echo "Success: pipx installed" >> "$installedLogFile"
        fi
    else
        echo "pipx is already installed"
    fi
}

# Function to install Zinit
install_zinit() {
    echo "Installing Zinit..."
    run_command "sh -c \"\$(curl -fsSL https://git.io/zinit-install)\""
}

# Function to install Antigen and set zsh as default shell
install_antigen_zsh() {
    echo "Installing Antigen and setting zsh as default shell..."
    echo "Cloning Antigen repository and changing default shell to zsh"
    if [ ! -d "$HOME/.antigen" ]; then
        run_command "git clone https://github.com/zsh-users/antigen.git $HOME/.antigen"
    else
        echo "Antigen is already installed"
    fi
    if [ "$SHELL" != "$(which zsh)" ]; then
        run_command "sudo chsh -s $(which zsh) $USER"
    else
        echo "zsh is already the default shell"
    fi
}

# Function to install Oh My Posh and configure the Devious Diamonds theme
install_oh_my_posh() {
    echo "Installing Oh My Posh..."
    run_command "paru -S oh-my-posh-bin --noconfirm"
    echo "Downloading Devious Diamonds theme..."
    run_command "wget $deviousDiamondsUrl -O $HOME/.poshthemes/devious-diamonds.omp.yaml"
    echo "Setting up Oh My Posh with Devious Diamonds theme in .zshrc"
    echo 'eval "$(oh-my-posh --init --shell zsh --config ~/.poshthemes/devious-diamonds.omp.yaml)"' >> "$HOME/.zshrc"
}

# Function to download configuration files
download_configs() {
    echo "Downloading configuration files..."
    echo "Downloading .zshrc, .aliases, .antigenrc, and .zsh1 from the provided URLs"
    run_command "wget $zshrcUrl -O $HOME/.zshrc"
    run_command "wget $aliasesUrl -O $HOME/.aliases"
    run_command "wget $antigenrcUrl -O $HOME/.antigenrc"
    run_command "wget $zsh1Url -O $HOME/.zsh1"
}

# Function to download paclock.sh script
download_paclock_script() {
    echo "Downloading paclock.sh script..."
    echo "Downloading and making paclock.sh script executable"
    run_command "sudo wget $paclockUrl -O /usr/local/bin/paclock.sh"
    run_command "sudo chmod +x /usr/local/bin/paclock.sh"
}

# Function to clone Fabric repository
clone_fabric_repo() {
    echo "Cloning Fabric repository to ~/git..."
    mkdir -p $HOME/git
    if [ ! -d "$HOME/git/fabric" ]; then
        run_command "git clone $fabricRepo $HOME/git/fabric"
    else
        echo "Fabric repository already cloned"
    fi
}

# Function to install elia-chat using pipx
install_elia_chat() {
    echo "Installing elia-chat using pipx..."
    run_command "pipx install elia-chat"
}

# Function to install yadm and clone the configuration repository
install_yadm_clone_repo() {
    echo "Installing yadm and cloning the configuration repository..."
    run_command "yadm clone $confRepo"
}

# Function to install Oh My Zsh, Prezto, Zplug, and Zgenom
install_zsh_management_tools() {
    echo "Installing Oh My Zsh..."
    run_command "sh -c \"\$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)\""
    echo "Installing Prezto..."
    run_command "zsh -c \"\$(curl -fsSL https://raw.githubusercontent.com/sorin-ionescu/prezto/master/install.sh)\""
    echo "Installing Zplug..."
    run_command "curl -sL zplug.sh/installer | zsh"
    echo "Installing Zgenom..."
    run_command "git clone https://github.com/jandamm/zgenom.git \"${HOME}/.zgenom\""
}

# Main installation process
run_repo_script
install_packages
install_chaotic_aur
install_blackarch
install_paru
install_specific_packages
install_pipx
download_paclock_script
install_zinit
install_antigen_zsh
install_oh_my_posh
install_zsh_management_tools
download_configs
clone_fabric_repo
install_elia_chat
install_yadm_clone_repo

echo "Setup complete. All selected packages have been installed and configured."
echo "Log file is located at $logFile"

# Clean up temporary directory
rm -rf $tempDir
