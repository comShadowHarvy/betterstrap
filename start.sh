#!/bin/bash

# Function to prompt and execute a script with a detailed description
run_script() {
    local script_name=$1
    local script_url=$2
    local script_description=$3

    echo -e "\n$script_description"
    read -p "Do you want to download and run $script_name? (y/n): " choice
    if [ "$choice" == "y" ]; then
        echo "Downloading $script_name..."
        wget -q $script_url -O $script_name
        chmod +x $script_name
        echo "Running $script_name..."
        ./$script_name
    else
        echo "Skipping $script_name."
    fi
}


# URLs to each script
url_attack="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/attack.sh"
url_attackinstall="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/attackinstall.sh"
url_average="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/average.sh"
url_backup="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/backup.sh"
url_game="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/game.sh"
url_repo="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/repo.sh"
url_restore="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/restore.sh"
url_smb="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/smb.sh"
url_strap="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/strap.sh"


# Detailed descriptions of each script
desc_repo="The repo.sh script manages software repositories on your system. It allows you to easily add, update, or remove repositories, ensuring that your system has access to the latest software from trusted sources."
desc_strap="The strap.sh script is a bootstrapper for setting up your system with a base configuration. It installs essential packages, applies system configurations, and sets up your environment according to your preferences."
desc_attackinstall="The attackinstall.sh script installs the necessary tools and dependencies required to perform network attack simulations. It sets up your environment with tools like Nmap, Hydra, or other penetration testing utilities."
desc_attack="The attack.sh script automates the setup and execution of a network attack simulation. It can be used to test network defenses by simulating various types of attacks such as brute force, DoS, or vulnerability scanning."
desc_smb="The smb.sh script configures SMB (Samba) shares on your system. It simplifies the process of setting up and managing Samba shares, including setting permissions and configuring access to shared directories."
desc_game="The game.sh script automates the installation and configuration of gaming tools and platforms on your Linux system. It sets up a gaming-ready environment by installing tools like Steam, Lutris, or MangoHud."
desc_backup="The backup.sh script backs up important configuration files and keys, including SSH keys, GPG keys, and the .api_keys file. It also provides an option to encrypt the backup using GPG, ensuring that your sensitive data is stored securely."
desc_restore="The restore.sh script restores previously backed-up configuration files and keys. It checks for the existence of the backup files before attempting to restore them, ensuring that your system can be reverted to a previous state with all critical configurations intact."
desc_average="The average.sh script calculates the average value from a set of numerical inputs. It is useful for quickly determining the mean of a list of numbers, which could be provided manually or read from a file."

# Optimal order to download and run the scripts
run_script "repo.sh" $url_repo "$desc_repo"
run_script "strap.sh" $url_strap "$desc_strap"
run_script "attackinstall.sh" $url_attackinstall "$desc_attackinstall"
run_script "attack.sh" $url_attack "$desc_attack"
run_script "smb.sh" $url_smb "$desc_smb"
run_script "game.sh" $url_game "$desc_game"
run_script "backup.sh" $url_backup "$desc_backup"
run_script "restore.sh" $url_restore "$desc_restore"
run_script "average.sh" $url_average "$desc_average"

echo "All selected scripts have been downloaded and run."
