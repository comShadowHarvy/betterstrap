#!/bin/bash

# Function to prompt and execute a script with a detailed description
run_script() {
    local script_name=$1
    local script_url=$2
    local script_description=$3

    echo -e "\n$script_description"
    while true; do
        read -p "Do you want to download and run $script_name? (y/n): " choice
        case "$choice" in
            [Yy]*)
                echo "Downloading $script_name..."
                if wget -q "$script_url" -O "$script_name"; then
                    chmod +x "$script_name"
                    echo "Running $script_name..."
                    ./"$script_name"
                    rm -f "$script_name"  # Clean up the downloaded script
                else
                    echo "Error: Failed to download $script_name from $script_url."
                fi
                break
                ;;
            [Nn]*)
                echo "Skipping $script_name."
                break
                ;;
            *)
                echo "Invalid input. Please enter 'y' or 'n'."
                ;;
        esac
    done
}

# Define scripts with their URLs and descriptions
declare -A scripts=(
    ["repo.sh"]="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/repo.sh|The repo.sh script manages software repositories on your system. It allows you to easily add, update, or remove repositories, ensuring that your system has access to the latest software from trusted sources."
    ["strap.sh"]="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/strap.sh|The strap.sh script is a bootstrapper for setting up your system with a base configuration. It installs essential packages, applies system configurations, and sets up your environment according to your preferences."
    ["attackinstall.sh"]="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/attackinstall.sh|The attackinstall.sh script installs the necessary tools and dependencies required to perform network attack simulations. It sets up your environment with tools like Nmap, Hydra, or other penetration testing utilities."
    ["attack.sh"]="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/attack.sh|The attack.sh script automates the setup and execution of a network attack simulation. It can be used to test network defenses by simulating various types of attacks such as brute force, DoS, or vulnerability scanning."
    ["smb.sh"]="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/smb.sh|The smb.sh script configures SMB (Samba) shares on your system. It simplifies the process of setting up and managing Samba shares, including setting permissions and configuring access to shared directories."
    ["game.sh"]="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/game.sh|The game.sh script automates the installation and configuration of gaming tools and platforms on your Linux system. It sets up a gaming-ready environment by installing tools like Steam, Lutris, or MangoHud."
    ["backup.sh"]="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/backup.sh|The backup.sh script backs up important configuration files and keys, including SSH keys, GPG keys, and the .api_keys file. It also provides an option to encrypt the backup using GPG, ensuring that your sensitive data is stored securely."
    ["restore.sh"]="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/restore.sh|The restore.sh script restores previously backed-up configuration files and keys. It checks for the existence of the backup files before attempting to restore them, ensuring that your system can be reverted to a previous state with all critical configurations intact."
    ["average.sh"]="https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/average.sh|The average.sh script calculates the average value from a set of numerical inputs. It is useful for quickly determining the mean of a list of numbers, which could be provided manually or read from a file."
)

# Run scripts in the optimal order
for script_name in repo.sh strap.sh attackinstall.sh attack.sh smb.sh game.sh backup.sh restore.sh average.sh; do
    IFS='|' read -r script_url script_description <<< "${scripts[$script_name]}"
    run_script "$script_name" "$script_url" "$script_description"
done

echo "All selected scripts have been downloaded and run."
