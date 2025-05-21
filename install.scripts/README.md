# Installation Scripts

This directory contains a collection of scripts designed to automate the installation and setup of various tools and environments on a Linux system.

## Scripts

Below is a list of the scripts available in this directory, along with a brief description of their purpose and any important notes.

### `ai.installer.sh`

*   **Description**: Installs the Ollama ecosystem, including Ollama itself, various UI options (Open WebUI, Pinokio, LobeHub, Ollama Web UI, Enchanted), and allows selection and download of DeepSeek AI models.
*   **Notes**:
    *   Detects package manager (apt, dnf, yum, pacman, apk).
    *   Installs Docker if no container runtime is found.
    *   Supports Arch User Repository (AUR) helpers (yay, paru) for Pinokio installation on Arch-based systems.
    *   Provides detailed logging and interactive prompts.

### `attack.install.sh`

*   **Description**: An interactive script for installing a comprehensive set of penetration testing tools. Tools are categorized (Network Scanning, Vulnerability Scanning, Exploitation, Web Application Testing, etc.).
*   **Notes**:
    *   Primarily designed for Arch Linux and uses an AUR helper (yay or paru).
    *   Should be run as a non-root user.
    *   Provides descriptions, advantages, and disadvantages for each tool before installation.

### `bolt.diy.sh`

*   **Description**: Installs and configures `bolt.diy`, a project by StackBlitz Labs. It handles the setup of Node.js, npm, git, and pnpm, clones the repository, and helps with initial environment configuration (API keys).
*   **Notes**:
    *   Detects OS (Arch, Fedora, Debian, RHEL, Alpine, openSUSE).
    *   Installs `pnpm` globally.
    *   Prompts for API keys (GROQ, OpenAI, Anthropic) during setup.

### `dev.tools.install.sh`

*   **Description**: An interactive installer for a wide array of development tools. Tools are categorized (Compilers, Build Systems, Scripting Languages, Version Control, etc.).
*   **Notes**:
    *   Detects package manager (apt, dnf, yum, pacman, zypper, apk).
    *   Provides descriptions, advantages, and disadvantages for tools.
    *   Supports special installation methods for tools like Rust and Nix.

### `install.sh`

*   **Description**: A master script that orchestrates the execution of several other installation scripts located in this directory. It simulates a loading screen and logs the output of each executed script.
*   **Notes**:
    *   Executes the following scripts in order:
        1.  `./repo.sh`
        2.  `./recomended.software.installer.sh`
        3.  `./dev.tools.install.sh`
        4.  `./attack.install.sh`
        5.  `./waypipe.sh`
        6.  A script downloaded from `christitus.com/linux`.
    *   Logs all operations to `custom_setup_log_<timestamp>.txt`.
    *   **Caution**: This script runs other scripts and downloads and executes one from the internet. Ensure you trust all involved sources.

### `recomended.software.installer.sh`

*   **Description**: An interactive script to install recommended software across various categories (Office, Internet, Multimedia, Graphics, Utilities, Development, Security, Games).
*   **Notes**:
    *   Detects distribution and package manager (apt, dnf, pacman, zypper).
    *   Supports installation from system repositories, Flatpak, Snap, and AUR (for Arch-based systems).
    *   Provides descriptions, advantages, and disadvantages for software.

### `repo.sh`

*   **Description**: Configures additional package repositories for Arch Linux systems.
*   **Notes**:
    *   Specifically for Arch Linux.
    *   Sets up the following repositories if they are not already configured:
        *   Chaotic AUR
        *   BlackArch
        *   ArchStrike
        *   Multilib
    *   Updates the system and refreshes package databases after adding repositories.

### `waypipe.sh`

*   **Description**: Sets up Waypipe, a tool for forwarding Wayland applications over SSH. It can configure the current machine as a Waypipe server, client, or both.
*   **Notes**:
    *   Detects package manager (apt, dnf, pacman, zypper).
    *   Checks for an active Wayland session.
    *   Configures SSH server (for server setup) and client (for client setup).
    *   Creates helper scripts (`waypipe-server-run`, `waypipe-run`) for easier usage.

## General Usage Notes

*   Most scripts require `sudo` privileges for package installation.
*   It's generally recommended to review a script before running it, especially if it performs system-wide changes or installs software from third-party sources.
*   Check individual script headers or comments for more specific instructions or dependencies.
```
