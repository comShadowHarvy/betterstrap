# Betterstrap - Modern Linux System Management

🚀 **Now Modernized!** This repository has evolved from complex bash scripts to a clean, maintainable **Just** task runner system for Linux system management, automation, and development environment setup.

## ✨ What's New

### Modern Task Runner System
- **Just-based commands**: Replace thousands of lines of bash with simple, clear commands
- **Idempotent operations**: Safe to run multiple times
- **Better error handling**: Cleaner failures and recovery
- **Modular approach**: Run only what you need

### Quick Start
```bash
# Install the task runner (if needed)
cargo install just

# See all available commands
just

# Complete system setup
just setup-complete

# Individual components
just setup-ai           # AI/ML environment
just setup-dev          # Development tools
just daily-maintenance  # System updates & cleanup
```

## 📦 What's Included

- **System Setup**: Automated Arch Linux configuration, package management, and repository setup
- **Development Environment**: Complete dev tools installation (languages, editors, containers)
- **AI/ML Tools**: Ollama, PyTorch, Transformers, and popular AI models
- **Security Tools**: Penetration testing and security analysis tools (authorized use only)
- **System Maintenance**: Automated updates, cleanup, and configuration backups
- **Legacy Support**: All original scripts preserved in `old-install-scripts/`

## 📁 Directory Overview

### Core System
- `justfile` — **Main task runner** (replaces all old installation scripts)
- `install.scripts/` — Documentation for the modern system
- `old-install-scripts/` — **Backup of original bash scripts** (safe to delete after testing)
- `modern-alternatives/` — Advanced alternatives (Docker, Ansible, Nix)

### Utilities & Tools
- `config.backup/` — Configuration backup and restore scripts
- `git/` — Git repository management utilities
- `security/` — Network scanning and security analysis tools
- `server/` — Server management and systemd service files
- `setupssh/` — SSH configuration automation

### Development & Fun
- `sig/` — Image processing and related scripts
- `tdarr/` — Media transcoding platform scripts
- `test.games/` — Game prototypes and experiments
- `text.games/` — Text-based games in Python
- `scantests/` — System scanning utilities

## 🚀 Usage

### Modern Task Runner (Recommended)
```bash
# See all available commands
just

# Get detailed help
just help

# Run specific tasks
just setup-dev          # Install development tools
just setup-ai           # Install AI/ML environment
just daily-maintenance  # Update and clean system
```

### Legacy Scripts (if needed)
Original bash scripts are preserved in `old-install-scripts/`:
```bash
cd old-install-scripts
chmod +x install.sh
./install.sh
```

### Python Utilities
```bash
python3 text.games/snake_game.py
python3 sig/image_processor.py
```

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
