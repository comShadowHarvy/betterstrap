# GitHub Credential Manager Setup Script
# This script helps install and configure GitHub credential management
# on Linux, macOS, and Windows (via WSL)

set -e
echo "GitHub Credential Manager Setup"
echo "-------------------------------"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
    # Check if running in WSL
    if grep -q Microsoft /proc/version; then
        OS="WSL"
    fi
else
    echo "Unsupported OS detected: $OSTYPE"
    exit 1
fi

echo "Detected OS: $OS"

# Check Git installation
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install Git first."
    exit 1
fi
echo "Git is installed: $(git --version)"

# Function to install GitHub CLI
install_github_cli() {
    echo "Installing GitHub CLI..."
    
    if [[ "$OS" == "macOS" ]]; then
        if command -v brew &> /dev/null; then
            brew install gh
        else
            echo "Homebrew not found. Installing Homebrew first..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            brew install gh
        fi
    elif [[ "$OS" == "Linux" ]] || [[ "$OS" == "WSL" ]]; then
        # Different methods depending on distribution
        if command -v apt &> /dev/null; then
            # Debian, Ubuntu, etc.
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
            sudo apt update
            sudo apt install gh
        elif command -v dnf &> /dev/null; then
            # Fedora, CentOS, RHEL
            sudo dnf install -y 'dnf-command(config-manager)'
            sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
            sudo dnf install -y gh
        elif command -v yum &> /dev/null; then
            # Older RHEL-based distros
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
            sudo yum install -y gh
        else
            echo "Unsupported Linux distribution. Please install GitHub CLI manually."
            echo "Visit: https://github.com/cli/cli#installation"
            exit 1
        fi
    fi
    
    echo "GitHub CLI installed: $(gh --version)"
}

# Function to install GitHub Credential Manager
install_gcm() {
    echo "Installing GitHub Credential Manager..."
    
    if [[ "$OS" == "macOS" ]]; then
        brew tap microsoft/git
        brew install --cask git-credential-manager-core
    elif [[ "$OS" == "Linux" ]] || [[ "$OS" == "WSL" ]]; then
        # Download latest release
        LATEST_GCM_URL=$(curl -s https://api.github.com/repos/GitCredentialManager/git-credential-manager/releases/latest | grep -o "https://github.com/GitCredentialManager/git-credential-manager/releases/download/.*/gcm-linux_amd64.*.deb")
        if [ -z "$LATEST_GCM_URL" ]; then
            echo "Failed to determine latest GCM version. Please install manually."
            exit 1
        fi
        
        # Download and install GCM
        TEMP_DEB=$(mktemp)
        curl -sL "$LATEST_GCM_URL" -o "$TEMP_DEB"
        sudo dpkg -i "$TEMP_DEB"
        rm "$TEMP_DEB"
        
        # Install the credhelper globally
        git-credential-manager-core configure
    fi
    
    echo "GitHub Credential Manager installed successfully."
}

# Function to configure Git credential storage
configure_git_credentials() {
    echo "Configuring Git credential storage..."
    
    if [[ "$OS" == "macOS" ]]; then
        # On macOS, use the osxkeychain helper or GCM
        if command -v git-credential-manager-core &> /dev/null; then
            git config --global credential.helper manager-core
        else
            git config --global credential.helper osxkeychain
        fi
    elif [[ "$OS" == "Linux" ]]; then
        # On Linux, use GCM if installed, otherwise store credentials in a file
        if command -v git-credential-manager-core &> /dev/null; then
            git config --global credential.helper manager-core
        else
            echo "GitHub Credential Manager not found, using cache credential helper."
            # Store credentials for 1 hour (3600 seconds)
            git config --global credential.helper 'cache --timeout=3600'
            
            echo "For permanent storage, consider:"
            echo "1. Installing GitHub Credential Manager"
            echo "2. Using Git's store helper with: git config --global credential.helper store"
            echo "   (Note: This stores credentials in plaintext in ~/.git-credentials)"
        fi
    elif [[ "$OS" == "WSL" ]]; then
        # For WSL, we can use Windows' GCM
        git config --global credential.helper "/mnt/c/Program\\ Files/Git/mingw64/bin/git-credential-manager-core.exe"
    fi
    
    # Set credential.helper to store GitHub tokens specifically
    git config --global credential.https://github.com.helper "$(git config --global credential.helper)"
    
    echo "Git credential helper configured: $(git config --global credential.helper)"
}

# Function to authenticate with GitHub
authenticate_github() {
    echo "Authenticating with GitHub..."
    
    if command -v gh &> /dev/null; then
        echo "Please follow the prompts to log in to GitHub..."
        gh auth login
    else
        echo "GitHub CLI not installed. Manual authentication required."
        echo "Please run 'git push' to your repository and enter your credentials when prompted."
    fi
}

# Main installation process
echo "Starting installation process..."

# Step 1: Install GitHub CLI if not present
if ! command -v gh &> /dev/null; then
    install_github_cli
else
    echo "GitHub CLI is already installed: $(gh --version)"
fi

# Step 2: Install GitHub Credential Manager if needed
if [[ "$OS" != "WSL" ]] && ! command -v git-credential-manager-core &> /dev/null; then
    read -p "Do you want to install GitHub Credential Manager? (recommended) [y/N]: " install_gcm_response
    if [[ "$install_gcm_response" =~ ^[Yy]$ ]]; then
        install_gcm
    fi
fi

# Step 3: Configure Git credential storage
configure_git_credentials

# Step 4: Authenticate with GitHub
read -p "Do you want to authenticate with GitHub now? [y/N]: " auth_response
if [[ "$auth_response" =~ ^[Yy]$ ]]; then
    authenticate_github
fi

echo ""


