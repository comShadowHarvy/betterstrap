
#!/bin/bash

# Wait for 30 seconds before attempting to mount
sleep 30

# Mount the drives using labels
mount -L "Backup Plus" /mnt/usb
mount -L "My Passport" /mnt/usb2

# Restart Samba to recognize the new mounts
systemctl restart smbd

