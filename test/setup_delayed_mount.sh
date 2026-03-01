#!/bin/bash

set -e

echo "=== Delayed Mount Setup ==="

MOUNT_SCRIPT="/usr/local/bin/delayed-mount.sh"
MOUNT_SERVICE="/etc/systemd/system/delayed-mount.service"

echo "Creating mount script..."
cat > "$MOUNT_SCRIPT" <<'EOF'
#!/bin/bash

sleep 30

mount -L "Backup Plus" /mnt/usb
mount -L "My Passport" /mnt/usb2
mount -L "rom" /mnt/rom

systemctl restart smbd
EOF

chmod +x "$MOUNT_SCRIPT"

echo "Creating systemd service..."
cat > "$MOUNT_SERVICE" <<'EOF'
[Unit]
Description=Delayed Mount of USB Drives
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/delayed-mount.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable delayed-mount.service

echo "Creating mount points..."
mkdir -p /mnt/usb /mnt/usb2 /mnt/rom

echo "=== Delayed Mount Setup Complete ==="
