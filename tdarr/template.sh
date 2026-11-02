#!/bin/bash
##test script, 3 days at work making it, test it this week after i put on the corrected setup, have to see whats  visible from my vlan at home
# ==========================================
# CONFIGURATION - CHANGE THESE DETAILS
# ==========================================
SMB_SERVER="YOUR_SMB_SERVER_IP"
SMB_SHARE="YOUR_SHARE_NAME"
SMB_USER="YOUR_USERNAME"
SMB_PASS="YOUR_PASSWORD"
MOUNT_PATH="/var/mnt/tdarr_media"
# ==========================================

# Exit immediately if any command fails
set -e

# Detect host user info for permissions
USER_ID=$(id -u)
GROUP_ID=$(id -g)
CURRENT_USER=$(whoami)
HOME_DIR="/var/home/$CURRENT_USER"

echo "🎯 Starting systemd automount setup for Tdarr..."

# 1. Create secure credentials file
echo "🔑 Writing SMB credentials..."
mkdir -p "$HOME_DIR/.smb"
cat << EOF > "$HOME_DIR/.smb/credentials"
username=$SMB_USER
password=$SMB_PASS
EOF
chmod 600 "$HOME_DIR/.smb/credentials"

# 2. Create the mount directory
echo "📁 Creating mount path at $MOUNT_PATH..."
sudo mkdir -p "$MOUNT_PATH"

# 3. Create the Systemd Mount File
echo "⚙️  Generating var-mnt-tdarr_media.mount unit..."
sudo tee /etc/systemd/system/var-mnt-tdarr_media.mount > /dev/null << EOF
[Unit]
Description=Tdarr SMB Media Share Mount
Requires=network-online.target
After=network-online.target
Wants=network-online.target

[Mount]
What=//$SMB_SERVER/$SMB_SHARE
Where=$MOUNT_PATH
Type=cifs
Options=rw,uid=$USER_ID,gid=$GROUP_ID,credentials=$HOME_DIR/.smb/credentials,iocharset=utf8,vers=3.0,_netdev,nofail
TimeoutSec=15

[Install]
WantedBy=multi-user.target
EOF

# 4. Create the Systemd Automount File
echo "⏱️  Generating var-mnt-tdarr_media.automount trigger..."
sudo tee /etc/systemd/system/var-mnt-tdarr_media.automount > /dev/null << EOF
[Unit]
Description=Tdarr SMB Media Share Automount Trigger

[Automount]
Where=$MOUNT_PATH
TimeoutIdleSec=60

[Install]
WantedBy=multi-user.target
EOF

# 5. Reload systemd configurations and activate
echo "🔄 Reloading systemd and enabling the automount service..."
sudo systemctl daemon-reload
sudo systemctl enable --now var-mnt-tdarr_media.automount

# 6. Test the newly added connection
echo "⚡ Testing mount activation..."
echo "-----------------------------------------------"
if ls "$MOUNT_PATH" > /dev/null; then
    echo "✅ SUCCESS! The SMB share successfully mounted on-demand."
    echo "Your files are mapped to: $MOUNT_PATH"
else
    echo "❌ ERROR: Something went wrong. Check logs with: 'journalctl -xeu var-mnt-tdarr_media.mount'"
fi
echo "-----------------------------------------------"
