# Modern Betterstrap Installation System

This directory has been modernized! The old bash scripts have been replaced with a cleaner, more maintainable **Just** task runner approach.

## 🔄 What Changed

### Old Approach (moved to `../old-install-scripts/`)
- Complex bash scripts with thousands of lines
- Difficult to maintain and debug
- Non-idempotent (unsafe to run multiple times)
- Hard to test individual components

### New Approach (current `justfile`)
- ✅ Clean, organized task runner
- ✅ Idempotent operations
- ✅ Easy to understand and modify
- ✅ Safer execution with better error handling
- ✅ Modular commands you can run individually

## 🚀 Quick Start

### 1. Install Just (if not already installed)
```bash
cargo install just
```

### 2. See Available Commands
```bash
cd /home/me/git/betterstrap
just
```

### 3. Get Detailed Help
```bash
just help
```

## 📦 Common Use Cases

### Complete System Setup
```bash
just setup-complete
```
This replaces the old `install.sh` script and runs:
- Repository configuration
- Essential software installation
- Development environment setup

### Individual Components
```bash
just setup-repos         # Configure Arch Linux repositories (replaces repo.sh)
just install-recommended  # Install recommended software (replaces recomended.software.installer.sh)
just setup-dev           # Install development tools (replaces dev.tools.install.sh)
just setup-ai            # Install AI/ML tools (replaces ai.installer.sh)
just setup-security      # Install security tools (replaces attack.install.sh)
just setup-plymouth      # Configure Plymouth (replaces plymouth.sh)
just install-waypipe     # Install Waypipe (replaces waypipe.sh)
```

### Daily Maintenance
```bash
just daily-maintenance   # Update system and clean up
just update-system       # Update all packages and tools
just cleanup-system      # Clean caches and remove orphaned packages
```

### AI/ML Tools
```bash
just setup-ai            # Install AI environment
just ai-models           # List installed models
just ai-pull phi3:mini   # Download specific model
just ai-run phi3:mini    # Start interactive chat
```

### Utilities
```bash
just system-info         # Show system information
just backup-configs      # Backup important configurations
```

## 🔧 Benefits of the New System

1. **Safer**: Each command is idempotent and includes error handling
2. **Cleaner**: No more complex bash script maintenance  
3. **Faster**: Only run what you need
4. **Easier**: Simple commands with helpful descriptions
5. **Testable**: Each function can be tested independently

## 📁 Directory Structure

```
betterstrap/
├── justfile                 # New task runner (replaces all old scripts)
├── install.scripts/         # This directory (now just contains this README)
├── old-install-scripts/     # Backup of original bash scripts
└── modern-alternatives/     # Additional modern approaches (Docker, Ansible, Nix)
```

## 🔄 Migration Guide

### If you were using:
- `install.sh` → `just setup-complete`
- `repo.sh` → `just setup-repos`
- `ai.installer.sh` → `just setup-ai`
- `dev.tools.install.sh` → `just setup-dev`
- `attack.install.sh` → `just setup-security`
- `plymouth.sh` → `just setup-plymouth`
- Manual updates → `just daily-maintenance`

## 🔙 Rollback Option

If you need the old scripts, they're safely stored in `../old-install-scripts/`. You can:

```bash
cd ../old-install-scripts
chmod +x install.sh
./install.sh
```

## 🚀 What's Next

The `justfile` approach is just the beginning. For even more advanced setups, check out `../modern-alternatives/` which includes:

- **Docker/DevContainers**: Isolated development environments
- **Nix Flakes**: Reproducible system configurations  
- **Ansible**: Infrastructure as code
- **Modern bash**: Improved scripting practices

## 🆘 Troubleshooting

### Command not found: just
```bash
# Make sure Cargo bin is in your PATH
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Want to see what a command does before running?
```bash
just --dry-run setup-dev  # Shows what would be executed
```

### Need to modify a command?
Edit the `justfile` in the root directory. It's much easier than bash scripts!

---

**🎉 Congratulations!** You've successfully modernized your installation system. The new approach is cleaner, safer, and much easier to maintain.
