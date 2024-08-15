
# My Shell Scripts Collection

This repository contains a collection of useful shell scripts designed to automate various tasks, from system setup to backup and restoration. Below is a detailed description of each script included in this repository.
My new start isnt downloading right so i included the old one.

## Scripts Included

### 1. `attack.sh`
This script is designed to automate the setup and execution of a network attack simulation. It can be used to test network defenses by simulating various types of attacks such as brute force, DoS, or vulnerability scanning.

### 2. `attackinstall.sh`
This script installs the necessary tools and dependencies required to perform network attack simulations. It sets up your environment with tools like Nmap, Hydra, or other penetration testing utilities.

### 3. `average.sh`
This script is designed to automate the installation of recommended software on an Arch-based system. It provides detailed descriptions, advantages, and disadvantages for each software package and includes a progress bar to show installation status. The script uses yay to manage installations and checks if the software is already installed before attempting to install it.

### 4. `backup.sh`
This script backs up important configuration files and keys, including:
- SSH keys (`~/.ssh/id` and `~/.ssh/id.pub`)
- GPG keys (`~/.gnupg`)
- API keys (`~/.api_keys`)

It also provides an option to encrypt the backup using GPG, ensuring that your sensitive data is stored securely.

### 5. `game.sh`
This script automates the installation and configuration of gaming tools and platforms on your Linux system, such as Steam, Lutris, or MangoHud. It streamlines the setup process for a gaming-ready environment on Linux.

### 6. `repo.sh`
This script manages software repositories on your system. It allows you to easily add, update, or remove repositories for package management. It ensures that your system has access to the latest software from trusted sources.

### 7. `restore.sh`
This script restores previously backed-up configuration files and keys. It checks for the existence of the necessary backup files before attempting to restore them, ensuring that your system can be reverted to a previous state with all critical configurations intact.

### 8. `smb.sh`
This script configures SMB (Samba) shares on your system, allowing you to share directories with other computers on your network. It simplifies the process of setting up and managing Samba shares, including setting permissions and configuring access.

### 9. `strap.sh`
This script is a bootstrapper for setting up your system with a base configuration. It installs essential packages, applies system configurations, and sets up the environment according to your preferences. This is particularly useful for quickly setting up a new system or VM.

## Usage

### Quick Start

To quickly start with this repository, you can run the following one-liner to download and execute the `start.sh` script:

```bash
bash <(curl -s https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/start.sh)
```

### Backup and Restore
To back up your configuration files and keys:
```bash
./backup.sh
```

To restore your configuration files and keys:
```bash
./restore.sh
```

### Other Scripts
For all other scripts, simply make them executable and run them with the following command:
```bash
chmod +x script_name.sh
./script_name.sh
```

Replace `script_name.sh` with the name of the script you want to execute.

## Contributions
Feel free to contribute to this repository by submitting pull requests or opening issues if you encounter any bugs or have feature requests.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
