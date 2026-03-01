#!/bin/bash

set -e

echo "=== Rclone Google Drive Setup ==="

echo ">>> Installing rclone..."
if command -v rclone &> /dev/null; then
  echo "rclone already installed: $(rclone version | head -1)"
else
  curl -s https://rclone.org/install.sh | sudo bash
fi

echo ">>> Creating mount point..."
mkdir -p "$HOME/gdrive"

echo ">>> Configuring Google Drive remote..."
if rclone listremotes | grep -q "^gdrive$"; then
  echo "Remote 'gdrive' already exists. Skipping config."
  echo "To reconfigure, run: rclone config"
else
  echo "Setting up new remote..."
  echo "When asked:"
  echo "  - Select 'n' for New remote"
  echo "  - Name: gdrive"
  echo "  - Select '15' for Google Drive"
  echo "  - Follow OAuth prompts in browser"
  echo ""
  rclone config
fi

echo ">>> Creating systemd user service..."
mkdir -p "$HOME/.config/systemd/user"

cat > "$HOME/.config/systemd/user/rclone-gdrive.service" <<'EOF'
[Unit]
Description=rclone mount for Google Drive
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStartPre=sleep 2
ExecStart=rclone mount gdrive: %h/gdrive \
  --vfs-cache-mode writes \
  --vfs-cache-max-age 24h \
  --vfs-write-back 5s \
  --allow-other \
  --dir-cache-time 1h \
  --poll-interval 15s \
  --umask 002

Restart=on-failure
RestartSec=5s

[Install]
WantedBy=default.target
EOF

echo ">>> Reloading systemd and enabling service..."
systemctl --user daemon-reload
systemctl --user enable rclone-gdrive.service

echo ">>> Starting rclone mount..."
systemctl --user start rclone-gdrive.service

sleep 2

if systemctl --user is-active --quiet rclone-gdrive.service; then
  echo ""
  echo "=== Setup Complete ==="
  echo "Google Drive mounted at: $HOME/gdrive"
  echo ""
  echo "Commands:"
  echo "  systemctl --user start rclone-gdrive.service   # Start"
  echo "  systemctl --user stop rclone-gdrive.service    # Stop"
  echo "  systemctl --user restart rclone-gdrive.service # Restart"
  echo "  rclone lsd gdrive:                            # List drive contents"
else
  echo "ERROR: Service failed to start. Check logs:"
  echo "  journalctl --user -u rclone-gdrive.service"
fi
