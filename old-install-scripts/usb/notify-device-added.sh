#!/usr/bin/env bash
set -Eeuo pipefail

devnode="${1:-}"

# Require a valid block device
if [[ -z "$devnode" || ! -b "$devnode" ]]; then
  exit 0
fi

# Point to the user's session bus (works for most Wayland/X11 setups)
uid=$(id -u)
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$uid}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=$XDG_RUNTIME_DIR/bus}"

# Give auto-mounters a brief moment to mount and set udev props
sleep 0.8

# Determine the parent disk for richer metadata
pkname="$(lsblk -no PKNAME "$devnode" 2>/dev/null | head -n1 || true)"
if [[ -n "$pkname" ]]; then
  disk="/dev/$pkname"
else
  disk="$devnode"
fi

# Collect udev properties for both the node and the disk
udev_props_node="$(udevadm info -q property -n "$devnode" 2>/dev/null || true)"
udev_props_disk="$(udevadm info -q property -n "$disk" 2>/dev/null || true)"
getprop() {
  local key="$1"
  printf '%s\n' "$udev_props_node"$'\n'"$udev_props_disk" \
    | awk -F= -v k="$key" '$1==k{ $1=""; sub(/^=/,""); print; }' \
    | head -n1
}

vendor="$(getprop ID_VENDOR_FROM_DATABASE)"
model="$(getprop ID_MODEL_FROM_DATABASE)"
if [[ -z "$vendor" ]]; then vendor="$(getprop ID_VENDOR)"; fi
if [[ -z "$model" ]]; then model="$(getprop ID_MODEL)"; fi
serial="$(getprop ID_SERIAL_SHORT)"
bus="$(getprop ID_BUS)"
wwid="$(getprop ID_WWN_WITH_EXTENSION)"
fstype="$(getprop ID_FS_TYPE)"
fslabel="$(getprop ID_FS_LABEL_ENC)"
uuid="$(getprop ID_FS_UUID)"
usage="$(getprop ID_FS_USAGE)"

# Fallbacks via lsblk/blkid
if [[ -z "$vendor" ]]; then vendor="$(lsblk -dnro VENDOR "$disk" 2>/dev/null || true)"; fi
if [[ -z "$model" ]]; then model="$(lsblk -dnro MODEL "$disk" 2>/dev/null || true)"; fi
if [[ -z "$serial" ]]; then serial="$(lsblk -dnro SERIAL "$disk" 2>/dev/null || true)"; fi
if [[ -z "$bus" ]]; then bus="$(lsblk -dnro TRAN "$disk" 2>/dev/null || true)"; fi
if [[ -z "$fstype" ]]; then fstype="$(blkid -s TYPE -o value "$devnode" 2>/dev/null || true)"; fi
if [[ -z "$fslabel" ]]; then fslabel="$(blkid -s LABEL -o value "$devnode" 2>/dev/null || true)"; fi
if [[ -z "$uuid" ]]; then uuid="$(blkid -s UUID -o value "$devnode" 2>/dev/null || true)"; fi

size_h="$(lsblk -dnro SIZE "$devnode" 2>/dev/null | head -n1 || true)"
ro="$(lsblk -dnro RO "$devnode" 2>/dev/null || true)"
rmflag="$(lsblk -dnro RM "$disk" 2>/dev/null || true)"
rota="$(lsblk -dnro ROTA "$disk" 2>/dev/null || true)"
type="$(lsblk -dnro TYPE "$devnode" 2>/dev/null || true)"
mpoints="$(lsblk -no MOUNTPOINTS "$devnode" 2>/dev/null || true)"

# Title
name="$(printf '%s %s' "$vendor" "$model" | sed 's/^ *//; s/ *$//')"
label_part="${fslabel:-no-label}"
fs_part="${fstype:-unknown}"
size_part="${size_h:-?}"
title="Device added: $label_part [$fs_part] • $size_part"
if [[ -n "$name" ]]; then
  title="$name — $title"
fi

# Body
info=()
info+=("Path: $devnode")
if [[ "$devnode" != "$disk" ]]; then info+=("Parent: $disk"); fi
if [[ -n "$type" ]]; then info+=("Type: $type"); fi
if [[ -n "$mpoints" ]]; then info+=("Mounted: $mpoints"); else info+=("Mounted: no"); fi
if [[ -n "$size_h" ]]; then info+=("Size: $size_h"); fi
if [[ -n "$usage" ]]; then info+=("Usage: $usage"); fi
if [[ -n "$fstype" ]]; then info+=("Filesystem: $fstype"); fi
if [[ -n "$fslabel" ]]; then info+=("Label: $fslabel"); fi
if [[ -n "$uuid" ]]; then info+=("UUID: $uuid"); fi
if [[ -n "$wwid" ]]; then info+=("WWID: $wwid"); fi
if [[ -n "$serial" ]]; then info+=("Serial: $serial"); fi
if [[ -n "$bus" ]]; then info+=("Bus: $bus"); fi
if [[ -n "$rmflag" ]]; then info+=("Removable: $rmflag"); fi
if [[ -n "$rota" ]]; then info+=("Rotational: $rota"); fi
if [[ -n "$ro" ]]; then info+=("Read-only: $ro"); fi

icon="drive-removable-media-usb"
case "$bus" in
  usb) icon="drive-removable-media-usb" ;;
  sata|ata) icon="drive-harddisk" ;;
  nvme|pcie) icon="drive-harddisk" ;;
  *) icon="drive-harddisk" ;;
esac
if [[ "$type" == "rom" ]]; then icon="media-optical"; fi

body="$(printf '%s\n' "${info[@]}")"

/usr/bin/notify-send -a "Device Monitor" -i "$icon" -u low "$title" "$body" >/dev/null 2>&1 || true

exit 0
