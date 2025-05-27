# Betterstrap Utility Scripts and Tools

This repository is a collection of scripts, utilities, and small programs for Linux system management, automation, and experimentation. It includes shell scripts, Python utilities, configuration backups, and game prototypes. The tools are organized into folders by category and purpose.

## Contents

- **Shell Scripts**: Various `.sh` scripts for system setup, monitoring, git management, USB testing, formatting, and more.
- **Python Utilities**: Small Python programs for games, scanning, and other utilities.
- **Jupyter Notebooks**: Simulations and experiments, e.g., bouncing object simulations.
- **Configuration Backups**: Scripts to backup and restore configuration files.
- **Security Tools**: Scripts for network scanning, Bluetooth, and security tool installation.
- **Server Tools**: Scripts and services for server setup and maintenance.
- **Games**: Simple text-based and graphical games implemented in Python and shell scripts.
- **Installers**: Scripts to automate the installation of software and development tools.

## Directory Overview

- `config.backup/` — Backup and restore scripts for configuration files.
- `git/` — Git repository management scripts.
- `install.scripts/` — Installers for various tools and environments.
- `old.need.to.redo/` — Legacy scripts and backups for reference or rework.
- `scantests/` — Scanning utilities and test scripts.
- `security/` — Security and network-related scripts.
- `server/` — Server management scripts and systemd service files.
- `setupssh/` — SSH setup automation.
- `sig/` — Image processing and related scripts.
- `tdarr/` — Scripts related to the Tdarr media transcoding platform.
- `test.games/` — Game prototypes and experiments.
- `text.games/` — Text-based games in Python.

## Usage

Most scripts are designed for Linux and use bash or zsh. To run a script:

```zsh
./scriptname.sh
```

Or for Python scripts:

```zsh
python3 scriptname.py
```

Some scripts may require root privileges or additional dependencies. Refer to comments within each script for details.

## Requirements

- Linux OS (tested on various distributions)
- zsh or bash shell
- Python 3.x for Python scripts
- Additional dependencies as noted in individual scripts (e.g., requirements.txt in `sig/`)

## Notes

- Many scripts are experimental or for personal use. Review code before running in production environments.
- Contributions and suggestions are welcome!

## License

This repository is provided as-is for personal and educational use. See individual scripts for specific license information if present.
