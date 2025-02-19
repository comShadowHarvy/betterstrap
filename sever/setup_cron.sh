#!/bin/bash
# This script creates a cron file that runs the remount.sh script every 2 hours.
# Requires root privileges to write to /etc/cron.d.

# Copy the remount script to /bin
cp "$(dirname "$0")/remount.sh" /bin/remount.sh && chmod +x /bin/remount.sh

# Create a cron file that runs the remount.sh script every 2 hours.
CRONFILE="/etc/cron.d/remount"
cat <<EOF > $CRONFILE
# Run remount.sh every 2 hours
0 */2 * * * root /bin/remount.sh
EOF
echo "Cron job set in $CRONFILE"
