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

# Function to display a header
display_header() {
    clear
    echo "============================="
    echo "  Network Scanning Tools Installer"
    echo "============================="
    echo
}

# Function to install required tools
install_tools() {
    echo "Installing required tools..."
    sudo pacman -S --needed git curl --noconfirm
    if ! command -v yay &> /dev/null; then
        echo "Yay is not installed. Installing yay..."
        git clone https://aur.archlinux.org/yay.git /tmp/yay
        cd /tmp/yay
        makepkg -si --noconfirm
        cd -
    fi
}

# Function to clone a repository and install its dependencies
clone_and_install() {
    local repo_url=$1
    local repo_name=$(basename $repo_url .git)
    local target_dir="$HOME/git/scan/$repo_name"

    echo "Cloning $repo_name into $target_dir..."
    git clone $repo_url $target_dir
    cd $target_dir

    # Install dependencies if a specific instruction file exists
    if [ -f "requirements.txt" ]; then
        echo "Installing Python dependencies for $repo_name..."
        pip install -r requirements.txt
    fi
    if [ -f "install.sh" ]; then
        echo "Running install.sh for $repo_name..."
        chmod +x install.sh
        ./install.sh
    fi
    if [ -f "setup.py" ]; then
        echo "Running setup.py for $repo_name..."
        python setup.py install
    fi

    cd -
    echo "$repo_name installation complete."
}

# List of repositories to clone and install
repos=(
    "https://github.com/21y4d/nmapAutomator.git"
    "https://github.com/haroonawanofficial/ReconCobra.git"
    "https://github.com/Tib3rius/AutoRecon.git"
    "https://github.com/j3ssie/Osmedeus.git"
    "https://github.com/nahamsec/lazyrecon.git"
    "https://github.com/1N3/Sn1per.git"
    "https://github.com/arismelachroinos/lscript.git"
    "https://github.com/six2dez/reconftw.git"
    "https://github.com/ygsk/VulnScan.git"
    "https://github.com/intrigueio/intrigue-core.git"
)

total_steps=${#repos[@]}
current_step=0

display_header
install_tools

# Clone each repository and install its tools
for repo in "${repos[@]}"; do
    clone_and_install $repo
    loading_bar $((++current_step)) $total_steps
done

echo -ne '\nAll repositories have been cloned and required tools installed.\n'
