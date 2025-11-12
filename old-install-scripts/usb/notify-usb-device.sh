#!/usr/bin/env bash
set -Eeuo pipefail

devpath="${1:-}"
if [[ -z "$devpath" ]]; then exit 0; fi

uid=$(id -u)
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$uid}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=$XDG_RUNTIME_DIR/bus}"

sys="/sys${devpath}"
if [[ ! -d "$sys" ]]; then exit 0; fi

props="$(udevadm info -q property -p "$sys" 2>/dev/null || true)"
getp() { local k="$1"; printf '%s\n' "$props" | awk -F= -v k="$k" '$1==k{ $1=""; sub(/^=/,""); print; }' | head -n1; }

vendor="$(getp ID_VENDOR_FROM_DATABASE)"
model="$(getp ID_MODEL_FROM_DATABASE)"
if [[ -z "$vendor" ]]; then vendor="$(getp ID_VENDOR)"; fi
if [[ -z "$model" ]]; then model="$(getp ID_MODEL)"; fi

vid="$(getp ID_VENDOR_ID)"
pid="$(getp ID_MODEL_ID)"
serial="$(getp ID_SERIAL_SHORT)"
speed="$(cat "$sys/speed" 2>/dev/null || true)"
version="$(cat "$sys/version" 2>/dev/null || true)"

title="USB device added"
body_lines=()
if [[ -n "$vendor$model" ]]; then body_lines+=("Model: $vendor $model"); fi
if [[ -n "$vid$pid" ]]; then body_lines+=("VID:PID: $vid:$pid"); fi
if [[ -n "$serial" ]]; then body_lines+=("Serial: $serial"); fi
if [[ -n "$version" ]]; then body_lines+=("USB Version: $version"); fi
if [[ -n "$speed" ]]; then body_lines+=("Link speed: ${speed} Mb/s"); fi
body_lines+=("Sysfs: $sys")

body="$(printf '%s\n' "${body_lines[@]}")"

/usr/bin/notify-send -a "Device Monitor" -i "device-usb" -u low "$title" "$body" >/dev/null 2>&1 || true

exit 0
