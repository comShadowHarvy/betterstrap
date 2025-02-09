# Betterstrap Collection

A collection of utility scripts for system administration, network scanning, and entertainment.

## Scripts Overview

### Aquarium Simulator
- **fish.py**: An interactive terminal-based aquarium simulator featuring multiple marine life forms
  - Controls: 
    - 'q' - Quit
    - 'f' - Add Fish
    - 'o' - Add Octopus
    - 'j' - Add Jellyfish
    - 't' - Add Sea Turtle
    - 'c' - Add Crab
    - 's' - Add School of Fish
    - 'd' - Add Dolphin
    - 'h' - Add Seahorse
    - 'u' - Add Sea Urchin
    - 'w' - Add Shark
    - Space/Left Click - Feed
    - '+/-' - Adjust Speed

### Network Tools
- **scan.py**: Advanced network scanner using nmap
  - Features:
    - Auto-detects network interfaces
    - OS fingerprinting
    - Service version detection
    - Vulnerability scanning
    - Detailed output formatting

- **nmap1.sh**: Basic nmap scanning script
  - Simple subnet scanning
  - Saves results to file

- **nmap2.sh**: Enhanced nmap scanning script
  - Service version detection
  - Timestamped output
  - Detailed port information

### Repository Management
- **repo.sh**: Repository setup script for Arch Linux
  - Installs and configures:
    - Chaotic AUR
    - BlackArch
    - ArchStrike
    - Multilib repository

- **savegit.sh**: Git repository backup utility
  - Scans for Git repositories
  - Saves repository paths and URLs
  - Creates backup inventory

- **downloadgits.sh**: Git repository restoration utility
  - Reads repository inventory
  - Clones repositories to specified location
  - Maintains directory structure

### System Utilities
- **paclock.sh**: Pacman lock file manager
  - Detects pacman database locks
  - Safely removes lock files
  - Interactive confirmation

- **api.sh**: Cloudflare API example script
  - Demonstrates API interaction
  - IPv6 settings modification

### Security Tools
- **laz1**: LaZagne password recovery tool installer
  - Auto-detects distribution
  - Installs dependencies
  - Downloads and configures LaZagne
  - Saves output to Desktop

## Requirements

- Python 3.x
- Nmap
- Git
- Bash
- Curses library (for fish.py)
- Root privileges (for some scripts)

## Installation

1. Clone the repository:
```bash
bash <(curl -s https://raw.githubusercontent.com/comShadowHarvy/betterstrap/main/start.sh)
```

2. Make scripts executable:
```bash
chmod +x *.sh
chmod +x laz1
```

## Usage

Each script can be run directly from the command line. Some scripts require root privileges:

```bash
# Network scanning
sudo python3 scan.py

# Aquarium simulator
python3 fish.py

# Repository setup
sudo ./repo.sh

# Git operations
./savegit.sh
./downloadgits.sh

# System maintenance
sudo ./paclock.sh
```

## Security Notes

- Some scripts require root privileges - review before running
- API script contains example credentials - replace with your own
- LaZagne tool should be used responsibly and legally

## Contributing

Feel free to submit pull requests or create issues for bugs and feature requests.

## License

MIT License - See LICENSE file for details
