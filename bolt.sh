#!/usr/bin/env bash
# install_boltdiy.sh - Install prerequisites, clone/setup bolt.diy, and optionally start the app
#
# This script will:
#   1. Detect your Linux distribution (Arch, Fedora, Debian-based).
#   2. Install Node.js, npm, and Git using the appropriate package manager.
#   3. Check for and install pnpm globally (if needed).
#   4. Clone (or update) the bolt.diy repository from GitHub.
#   5. Install bolt.diy’s dependencies using pnpm.
#   6. Copy .env.example to .env.local (if not already present) so you can add your API keys.
#   7. Optionally start the development server.
#
# Usage:
#   chmod +x install_boltdiy.sh
#   ./install_boltdiy.sh
#

set -e

# Check if sudo is available
if ! command -v sudo &>/dev/null; then
    echo "Error: sudo is not installed. Please install sudo or run as root."
    exit 1
fi

# Detect OS by sourcing /etc/os-release
if [ -f /etc/os-release ]; then
    . /etc/os-release
    os_id=$(echo "${ID}" | tr '[:upper:]' '[:lower:]')
    os_id_like=$(echo "${ID_LIKE:-}" | tr '[:upper:]' '[:lower:]')
else
    echo "Error: /etc/os-release not found; cannot determine OS."
    exit 1
fi

# Determine OS family (Arch, Fedora, Debian-based)
OS_FAMILY=""
if [[ "$os_id" == *arch* ]] || [[ "$os_id_like" == *arch* ]]; then
    OS_FAMILY="arch"
elif [[ "$os_id" == *fedora* ]] || [[ "$os_id_like" == *fedora* ]]; then
    OS_FAMILY="fedora"
elif [[ "$os_id" == *debian* ]] || [[ "$os_id" == *ubuntu* ]] || [[ "$os_id_like" == *debian* ]]; then
    OS_FAMILY="debian"
else
    echo "Unsupported OS: ID=${ID}, ID_LIKE=${ID_LIKE}"
    exit 1
fi

echo "Detected OS family: ${OS_FAMILY}"

# Install prerequisites: Node.js, npm, and git
install_prerequisites() {
    case "$OS_FAMILY" in
        arch)
            echo "Installing prerequisites using pacman..."
            sudo pacman -Syu --noconfirm nodejs npm git
            ;;
        fedora)
            echo "Installing prerequisites using dnf..."
            sudo dnf install -y nodejs npm git
            ;;
        debian)
            echo "Updating package lists with apt-get..."
            sudo apt-get update
            echo "Installing prerequisites using apt-get..."
            sudo apt-get install -y nodejs npm git
            ;;
        *)
            echo "Unsupported OS family: ${OS_FAMILY}"
            exit 1
            ;;
    esac
}

install_prerequisites

# Check for pnpm and install if it's not available
if ! command -v pnpm &>/dev/null; then
    echo "pnpm not found. Installing pnpm globally using npm..."
    sudo npm install -g pnpm
else
    echo "pnpm is already installed."
fi

# Clone or update the bolt.diy repository
REPO_URL="https://github.com/stackblitz-labs/bolt.diy"
REPO_DIR="bolt.diy"

if [ -d "$REPO_DIR" ]; then
    echo "Directory '$REPO_DIR' already exists. Updating repository..."
    cd "$REPO_DIR"
    git pull origin stable
    cd ..
else
    echo "Cloning the bolt.diy repository from ${REPO_URL}..."
    git clone -b stable "$REPO_URL"
fi

# Change into the repository directory and install dependencies
cd "$REPO_DIR"
echo "Installing project dependencies with pnpm..."
pnpm install

# Setup API keys file: copy .env.example to .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env.local from .env.example."
        cp .env.example .env.local
        echo "IMPORTANT: Please open .env.local and add your API keys (e.g., GROQ_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY) before running the app."
    else
        echo "Warning: .env.example not found. Skipping API keys setup."
    fi
else
    echo ".env.local already exists; skipping creation."
fi

# Ask the user if they want to start the development server now
read -p "Do you want to start the application now (pnpm run dev)? [y/N]: " start_app
if [[ "$start_app" =~ ^[Yy]$ ]]; then
    echo "Starting the development server..."
    pnpm run dev
else
    echo "Installation complete! To start the application later, navigate to '$(pwd)' and run 'pnpm run dev'."
fi
