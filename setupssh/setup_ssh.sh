#!/bin/bash
# Detect package manager and install OpenSSH server

if command -v apt-get &>/dev/null; then
    sudo apt-get update
    sudo apt-get install -y openssh-server
elif command -v yum &>/dev/null; then
    sudo yum install -y openssh-server
elif command -v dnf &>/dev/null; then
    sudo dnf install -y openssh-server
elif command -v pacman &>/dev/null; then
    sudo pacman -Syu --noconfirm openssh
elif command -v apk &>/dev/null; then
    sudo apk update
    sudo apk add openssh
    sudo rc-update add sshd default
    sudo service sshd start
else
    echo "Unsupported Linux distribution."
    exit 1
fi

# Enable and start the SSH service
if command -v systemctl &>/dev/null; then
    if systemctl list-unit-files | grep -q '^sshd\.service'; then
        sudo systemctl enable sshd
        sudo systemctl start sshd
    elif systemctl list-unit-files | grep -q '^ssh\.service'; then
        sudo systemctl enable ssh
        sudo systemctl start ssh
    else
        echo "SSH service not found in systemctl units."
    fi
else
    # Fallback for non-systemd systems
    if [ -f /etc/init.d/sshd ]; then
        sudo /etc/init.d/sshd start
    elif [ -f /etc/init.d/ssh ]; then
        sudo /etc/init.d/ssh start
    else
        echo "No known SSH init script found."
    fi
fi

echo "SSH setup is complete."
