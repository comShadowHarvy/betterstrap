#!/bin/bash
# This script creates a cron file that runs the remount.sh script every 2 hours.
# Requires root privileges to write to /etc/cron.d.
CRONFILE="/etc/cron.d/remount"
cat <<EOF > $CRONFILE
# Run remount.sh every 2 hours
0 */2 * * * root /home/me/betterstrap/remount.sh
EOF
echo "Cron job set in $CRONFILE"
