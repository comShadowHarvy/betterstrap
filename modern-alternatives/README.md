# Modern Alternatives to Betterstrap Scripts

This directory contains modern alternatives to the complex bash scripts in `../install.scripts/`. These approaches offer better maintainability, reproducibility, and security.

## Why These Alternatives are Better

### Problems with Original Scripts
- **Non-idempotent**: Running multiple times can cause issues
- **Complex error handling**: Difficult to debug when things go wrong  
- **Hard to maintain**: Monolithic bash scripts become unwieldy
- **Security concerns**: Downloading and executing remote scripts
- **No rollback mechanism**: Hard to undo changes
- **Limited testing**: Difficult to test complex bash logic

### Benefits of Modern Approaches
- ✅ **Idempotent**: Safe to run multiple times
- ✅ **Declarative**: Describe what you want, not how to do it
- ✅ **Version controlled**: Track changes and rollback easily
- ✅ **Reproducible**: Same result every time
- ✅ **Testable**: Can be tested in isolated environments
- ✅ **Secure**: Better handling of secrets and downloads

## Available Alternatives

### 1. Container Approach (Recommended for Dev Environments)

```bash
# Build development environment
docker build -f Dockerfile.dev-env -t my-dev-env .

# Run development environment  
docker run -it --rm -v $(pwd):/workspace my-dev-env

# Or use DevContainer in VS Code
code --folder-uri vscode-remote://dev-container+$(pwd)
```

**Best for**: Isolated development environments, onboarding new developers

### 2. Nix Flakes (Recommended for Reproducibility)

```bash
# Install Nix (if not already installed)
curl -L https://nixos.org/nix/install | sh

# Enable flakes
echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf

# Enter development environment
nix develop

# Install specific package sets
nix build .#ai-env
nix build .#security-tools
```

**Best for**: Reproducible environments, multiple language versions, scientific computing

### 3. Ansible (Recommended for System Configuration)

```bash
# Install Ansible
pip install ansible

# Run system setup
ansible-playbook -K setup-system.yml

# With custom variables
ansible-playbook -K setup-system.yml \
  -e install_ai_tools=true \
  -e install_security_tools=false
```

**Best for**: Server configuration, fleet management, compliance

### 4. Just Task Runner (Recommended for Daily Tasks)

```bash
# Install Just
cargo install just
# or: brew install just
# or: sudo pacman -S just

# See available commands
just

# Run specific tasks
just setup-dev
just setup-ai  
just update-all
just cleanup
```

**Best for**: Everyday development tasks, team workflows

### 5. Modern Bash Script (For Simple Cases)

```bash
# Make executable and run
chmod +x modern-setup.sh

# See available options
./modern-setup.sh

# Run specific setups
./modern-setup.sh dev rust
./modern-setup.sh -f all  # Force mode
```

**Best for**: Simple automation where other tools are overkill

## Migration Strategy

### Immediate (Low Risk)
1. Start using **Just** for daily tasks like updates and cleanup
2. Use **DevContainers** for project-specific development environments
3. Keep existing scripts as backup

### Short Term (Medium Risk)
1. Migrate development environment setup to **Nix** or **containers**
2. Use **Ansible** for new system configurations
3. Gradually replace bash scripts with declarative configs

### Long Term (Higher Risk)
1. Full migration to **NixOS** for reproducible systems
2. Infrastructure as Code for all configurations
3. Retire bash scripts entirely

## Quick Start Examples

### For a New Developer Machine:
```bash
# Option 1: Container-based (safest)
git clone <repo>
code . # VS Code will detect .devcontainer and prompt to reopen

# Option 2: Nix-based (most reproducible) 
nix develop
```

### For Server Configuration:
```bash
# Use Ansible
ansible-playbook -i inventory setup-system.yml \
  --limit production_servers \
  -e install_security_tools=true
```

### For Daily Development:
```bash
# Use Just
just setup-dev    # One-time setup
just update-all   # Regular updates  
just cleanup      # Clean up system
```

## Tool Comparison

| Tool | Learning Curve | Reproducibility | Flexibility | Best For |
|------|---------------|-----------------|-------------|----------|
| **DevContainers** | Low | High | Medium | Individual dev environments |
| **Just** | Low | Medium | High | Daily tasks and workflows |
| **Ansible** | Medium | High | High | System administration |
| **Nix** | High | Very High | Very High | Reproducible everything |
| **Docker** | Medium | High | Medium | Isolated applications |

## Getting Started

1. **Choose your use case**:
   - Dev environment → DevContainer or Nix
   - Server setup → Ansible  
   - Daily tasks → Just
   - Simple automation → Modern bash script

2. **Try the safest option first** (containers/Just)

3. **Gradually migrate** more complex workflows

4. **Keep the original scripts** as reference until fully migrated

## Resources

- [Nix Pills](https://nixos.org/guides/nix-pills/) - Learn Nix concepts
- [Ansible Documentation](https://docs.ansible.com/) - Comprehensive Ansible guide
- [DevContainer Reference](https://containers.dev/) - DevContainer specifications
- [Just Manual](https://github.com/casey/just) - Task runner documentation

## Contributing

When adding new automation:
1. **Start declarative**: Use Nix, Ansible, or containers
2. **Make it idempotent**: Safe to run multiple times
3. **Add tests**: Verify it works in clean environments  
4. **Document**: Clear usage examples and prerequisites
