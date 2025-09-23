# Betterstrap - Professional Linux System Management & Automation Suite

<div align="center">

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Shell Script](https://img.shields.io/badge/language-Shell-89e051.svg)]()
[![Arch Linux](https://img.shields.io/badge/platform-Arch%20Linux-blue.svg)]()
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)]()

*A comprehensive system management toolkit that has evolved from complex bash scripts to modern, maintainable automation solutions*

</div>

## 🚀 What is Betterstrap?

Betterstrap is a professional-grade system management and automation suite designed for Linux power users and system administrators. What started as a collection of bash scripts has evolved into a modern, multi-approach toolkit that provides:

- **🏗️ Complete System Setup**: Automated Linux configuration and software installation
- **⚙️ Development Environment Management**: One-command dev environment setup with all necessary tools
- **🤖 AI/ML Toolkit**: Streamlined installation of AI/ML tools including Ollama, PyTorch, and Transformers
- **🔒 Security Utilities**: Network scanning, penetration testing tools (authorized use only)
- **🔧 System Maintenance**: Automated updates, cleanup, and configuration management
- **📁 Utility Collection**: File management, Git automation, formatting tools, and more

## ✨ Modern Architecture

### Evolution from Bash to Modern Solutions
This project has been **completely modernized** with multiple implementation approaches:

1. **Just Task Runner** (Primary) - Clean, maintainable commands
2. **Container Solutions** - Isolated, reproducible environments
3. **Nix Flakes** - Declarative, reproducible system configurations
4. **Ansible Playbooks** - Infrastructure as Code
5. **Modern Bash Scripts** - Enhanced legacy scripts with safety features

### Key Improvements
- ✅ **Idempotent Operations**: Safe to run multiple times
- ✅ **Better Error Handling**: Comprehensive error reporting and recovery
- ✅ **Modular Design**: Run only what you need
- ✅ **Safety First**: Built-in safeguards and confirmation prompts
- ✅ **Cross-Platform**: Support for multiple Linux distributions
- ✅ **Documentation**: Comprehensive guides and help systems

## 🏃‍♂️ Quick Start

### Option 1: Modern Task Runner (Recommended)
```bash
# Install Just task runner
cargo install just
# or: sudo pacman -S just
# or: brew install just

# Clone the repository
git clone <repository-url>
cd betterstrap

# See all available commands
just

# Complete system setup
just setup-complete

# Individual components
just setup-dev          # Development environment
just setup-ai           # AI/ML tools
just daily-maintenance  # System updates & cleanup
```

### Option 2: Container Development Environment
```bash
# Using DevContainer (VS Code)
code .  # VS Code will detect .devcontainer and prompt to reopen

# Using Docker directly
docker build -f modern-alternatives/Dockerfile.dev-env -t betterstrap-dev .
docker run -it --rm -v $(pwd):/workspace betterstrap-dev
```

### Option 3: Legacy Scripts (Fallback)
```bash
# Use original bash scripts if modern approaches aren't suitable
cd old-install-scripts
chmod +x install.sh
./install.sh
```

## 📦 What's Included

### 🎯 Core System Tools
- **`justfile`** - Modern task runner with 20+ automation commands
- **`install.sh`** - Enhanced cross-platform package installer with safety features
- **`format.sh`** - Professional drive formatting tool with comprehensive safety checks
- **`git.sh`** - Git environment setup with authentication and dependency management
- **`nvim.sh`** - Neovim development environment installer

### 🔧 Development & Productivity
- **Git Management** (`git/`) - Repository automation, backup, and update utilities
- **Configuration Backup** (`config.backup/`) - System configuration backup and restore
- **Monitor Scripts** - System monitoring and new file detection utilities

### 🤖 AI & Machine Learning
- **Ollama Integration** - Local LLM setup and model management
- **PyTorch & Transformers** - Complete ML development environment
- **Model Automation** - Automatic model downloading and updates

### 🛡️ Security & Network Tools
- **Network Scanning** - Comprehensive network analysis utilities
- **Security Auditing** - System security assessment tools
- **Penetration Testing** - Authorized security testing utilities

### 🏗️ Modern Alternatives
- **DevContainers** (`modern-alternatives/.devcontainer/`) - VS Code development containers
- **Nix Flakes** (`modern-alternatives/flake.nix`) - Reproducible development environments
- **Ansible Playbooks** (`modern-alternatives/setup-system.yml`) - Infrastructure as Code
- **Docker Environments** - Isolated development and testing environments

## 📁 Directory Structure

```
betterstrap/
├── 🎯 Core Scripts
│   ├── justfile              # Modern task runner (PRIMARY)
│   ├── install.sh            # Enhanced package installer
│   ├── format.sh             # Professional drive formatter
│   ├── git.sh                # Git environment setup
│   ├── nvim.sh               # Neovim installer
│   └── monitor*.sh           # System monitoring tools
│
├── 📂 Organized Utilities
│   ├── config.backup/        # Configuration backup system
│   ├── git/                  # Git automation utilities
│   │   ├── backup_repos.sh   # Repository backup automation
│   │   ├── update_repos.sh   # Mass repository updates
│   │   └── install.gpm.sh    # Git Package Manager
│   └── old-install-scripts/  # Legacy bash scripts (preserved)
│
├── 🚀 Modern Solutions
│   └── modern-alternatives/  # Next-generation approaches
│       ├── .devcontainer/    # VS Code dev containers
│       ├── Dockerfile.dev-env# Development environment image
│       ├── flake.nix         # Nix reproducible environments
│       ├── setup-system.yml  # Ansible infrastructure
│       └── modern-setup.sh   # Enhanced bash automation
│
└── 📚 Documentation
    ├── README.md             # This comprehensive guide
    ├── install.scripts/      # Modern system documentation
    └── old.need.to.redo/     # Archive of experimental scripts
```

## 🎯 Usage Examples

### 💻 Development Environment Setup
```bash
# Complete development environment
just setup-complete

# Specific language environments
just setup-dev              # General dev tools
just setup-ai               # AI/ML environment
just setup-security         # Security tools (with warnings)
```

### 🔄 System Maintenance
```bash
# Daily maintenance routine
just daily-maintenance       # Updates + cleanup

# Individual operations
just update-system          # Update all packages
just cleanup-system         # Clean caches and orphans
just backup-configs         # Backup important configs
```

### 🤖 AI/ML Operations
```bash
# AI environment management
just setup-ai               # Install AI tools
just ai-models               # List available models
just ai-pull phi3:mini       # Download specific model
just ai-run phi3:mini        # Interactive AI chat
```

### 🛠️ Utility Scripts
```bash
# Enhanced package installation
./install.sh neovim --verbose
./install.sh --search python
./install.sh --update

# Professional drive formatting
sudo ./format.sh --verbose
sudo ./format.sh --dry-run   # Preview operations
sudo ./format.sh --wipe      # Secure wipe + format

# Git environment setup
./git.sh                     # Interactive setup
./nvim.sh                    # Neovim development environment
```

## 🔒 Safety Features

### Built-in Safeguards
- **🛡️ System Drive Detection**: Prevents accidental system drive formatting
- **✅ Confirmation Prompts**: Multiple confirmation layers for destructive operations
- **📝 Operation Logging**: Comprehensive logging of all operations
- **🔄 Dry Run Mode**: Preview operations without executing them
- **💾 Configuration Backups**: Automatic backup of important system configurations

### Security Considerations
- **🔐 Privilege Management**: Minimal privilege requirements with clear escalation
- **📋 Audit Trails**: Complete operation logging for security auditing
- **⚠️ Warning Systems**: Clear warnings for potentially dangerous operations
- **🚫 System Protection**: Built-in protection against common misconfigurations

## 🌟 Modern Alternatives

For advanced users, explore the `modern-alternatives/` directory:

### 🐳 Container-Based Development
```bash
# DevContainer (VS Code)
code .  # Automatic container detection

# Docker development environment
docker build -f modern-alternatives/Dockerfile.dev-env -t betterstrap-dev .
```

### ❄️ Nix Reproducible Environments
```bash
# Enable Nix flakes
echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf

# Enter development environment
nix develop
```

### 📋 Ansible Infrastructure as Code
```bash
# System configuration with Ansible
ansible-playbook -K modern-alternatives/setup-system.yml
```

## ⚙️ Requirements

### Minimum Requirements
- **OS**: Linux (Arch, Ubuntu, Debian, Fedora, CentOS)
- **Shell**: bash 4.0+ or zsh
- **Privileges**: sudo access for system operations
- **Network**: Internet connection for package downloads

### Optional Dependencies
- **Just**: For modern task runner (`cargo install just`)
- **Docker**: For container-based environments
- **Nix**: For reproducible environments
- **Ansible**: For infrastructure automation
- **Python 3.6+**: For utility scripts

### Recommended Setup
```bash
# Install core dependencies (Arch Linux)
sudo pacman -S just docker python git curl

# Install core dependencies (Ubuntu/Debian)
sudo apt install python3 git curl
cargo install just
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **🔍 Review existing code** before adding new features
2. **📝 Document all new functionality** with clear examples
3. **🧪 Test thoroughly** on multiple distributions
4. **🛡️ Follow safety practices** with appropriate safeguards
5. **📋 Update documentation** for any new features

### Development Workflow
```bash
# Use the development container
code .  # VS Code DevContainer

# Or use Nix development environment
nix develop

# Test changes safely
just --dry-run <command>
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**Important Safety Notice:**
- This toolkit includes powerful system management tools
- Always review scripts before execution in production environments
- Security tools are for authorized testing only
- Drive formatting tools can permanently destroy data
- Use appropriate caution with system-level operations

## 🆘 Support & Documentation

- **📖 Full Documentation**: See `install.scripts/README.md` for detailed guides
- **🔧 Modern Alternatives**: See `modern-alternatives/README.md` for advanced setups
- **📋 Task Reference**: Run `just help` for comprehensive command documentation
- **🐛 Issues**: Report bugs and feature requests via GitHub issues
- **💬 Discussions**: Community support and feature discussions

---

<div align="center">

**Betterstrap** - *Professional Linux System Management Made Simple*

*From complex bash scripts to modern, maintainable automation solutions*

</div>
