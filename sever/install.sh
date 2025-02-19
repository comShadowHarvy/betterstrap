#!/bin/bash
# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root."
    exit 1
fi

# Copy remount script to /bin and set up the cron job
cp "$(dirname "$0")/remount.sh" /bin/remount.sh && chmod +x /bin/remount.sh
"$(dirname "$0")/setup_cron.sh"

# Install delaymount.service to systemd directory for a one-shot 15-second delayed remount after boot
cp "$(dirname "$0")/delaymount.service" /etc/systemd/system/delaymount.service

# Reload systemd daemon and enable/start the delay mount service
systemctl daemon-reload
systemctl enable delaymount.service
systemctl start delaymount.service

echo "Installation complete."
