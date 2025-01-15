#!/usr/bin/env bash
#
# detect_usb.sh - Lists all block devices and suggests which one(s) is likely a USB thumb drive.

echo "========================================="
echo " All Block Devices"
echo "========================================="
lsblk -o NAME,SIZE,TYPE,MODEL,TRAN
echo

echo "========================================="
echo " Likely USB Thumb Drive(s)"
echo "========================================="
# Use lsblk in a 'machine-friendly' mode (no partitions/children) to parse.
# -d = do not print children (partitions), -n = no headings, -o = specify columns
while read -r name type tran size model; do
  # We look for lines where TYPE = 'disk' and TRAN = 'usb'
  if [[ "$type" == "disk" && "$tran" == "usb" ]]; then
    echo "Found USB disk: /dev/$name"
    echo "  Size : $size"
    echo "  Model: $model"
    echo
  fi
done < <( lsblk -dn -o NAME,TYPE,TRAN,SIZE,MODEL )
