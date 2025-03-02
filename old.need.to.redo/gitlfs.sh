#!/bin/bash
set -e

# Define the threshold for large files in bytes (60 MB)
THRESHOLD=$((60 * 1024 * 1024))

# Define the global Git template directory and hooks directory
TEMPLATE_DIR="${HOME}/.git-templates"
HOOKS_DIR="${TEMPLATE_DIR}/hooks"
mkdir -p "$HOOKS_DIR"

# Write pre-commit hook for auto-tracking large files with Git LFS
PRE_COMMIT_HOOK="${HOOKS_DIR}/pre-commit"
cat << 'EOF' > "$PRE_COMMIT_HOOK"
#!/bin/bash
THRESHOLD=$((60 * 1024 * 1024))
large_files=$(git diff --cached --name-only | while read -r file; do
    if [[ -f "$file" ]]; then
        size=$(wc -c <"$file")
        if [[ $size -ge $THRESHOLD ]]; then
            echo "$file"
        fi
    fi
done)
if [[ -n "$large_files" ]]; then
    echo "The following files exceed $((THRESHOLD / (1024 * 1024))) MB and will be tracked by Git LFS:"
    echo "$large_files"
    echo "$large_files" | xargs -I {} git lfs track "{}"
    git add .gitattributes $large_files
fi
EOF
chmod +x "$PRE_COMMIT_HOOK"

# Set the global Git template directory
git config --global init.templateDir "$TEMPLATE_DIR"

# Function to install Git LFS using the appropriate package manager
install_git_lfs() {
    if command -v brew &>/dev/null; then
        brew install git-lfs
    elif command -v apt &>/dev/null; then
        sudo apt update && sudo apt install -y git-lfs
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y git-lfs
    elif command -v pacman &>/dev/null; then
        sudo pacman -Syu --noconfirm git-lfs
    else
        echo "Unsupported package manager. Please install Git LFS manually."
        exit 1
    fi
}

# Install Git LFS if not already installed
if ! command -v git-lfs &>/dev/null; then
    echo "Git LFS is not installed. Installing it now..."
    install_git_lfs
fi

# Initialize Git LFS globally
git lfs install --skip-repo

echo "Git LFS auto-track setup complete!"
echo "New repositories will automatically track files larger than 60 MB with Git LFS."
