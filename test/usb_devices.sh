#!/bin/bash

trap 'echo -e "\n\e[0m"; exit' INT

red="\e[1;31m"
green="\e[1;32m"
yellow="\e[1;33m"
blue="\e[1;34m"
magenta="\e[1;35m"
cyan="\e[1;36m"
white="\e[1;37m"
gray="\e[0;90m"
reset="\e[0m"

clear

echo ""
echo -e "${cyan}       ██╗███╗   ██╗███████╗████████╗ █████╗ ██╗${reset}"
echo -e "${cyan}       ██║████╗  ██║██╔════╝╚══██╔══╝██╔══██╗██║${reset}"
echo -e "${cyan}       ██║██╔██╗ ██║█████╗     ██║   ███████║██║${reset}"
echo -e "${cyan}       ██║██║╚██╗██║██╔══╝     ██║   ██╔══██║██║${reset}"
echo -e "${cyan}       ██║██║ ╚████║███████╗   ██║   ██║  ██║███████╗${reset}"
echo -e "${cyan}       ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝${reset}"
echo ""
echo -e "${gray}  Scanning...${reset}"

printf "  ${gray}["
for i in {1..20}; do
    printf "▓"
    sleep 0.03
done
printf "${gray}]${reset} ${green}100%${reset}"
echo -e "\r"
echo ""

USB_OUTPUT=$(lsusb 2>/dev/null)
USB_TREE=$(lsusb -t 2>/dev/null)

TOTAL_USB=$(echo "$USB_OUTPUT" | wc -l)

STORAGE_DEVS=$(lsblk -dn 2>/dev/null | grep -E "^sd" | wc -l)
TOTAL_STORAGE=$STORAGE_DEVS

MOUNTED_COUNT=$(mount | grep -E "^/dev/sd" 2>/dev/null | wc -l)

echo -e "${white}┌──────────────────────────────────────────────────────────────────────────┐${reset}"
echo -e "${white}│${reset}  ${cyan}USB DEVICES${reset}  ${gray}│${reset}  ${cyan}STORAGE${reset}  ${gray}│${reset}  ${cyan}MOUNTED${reset}  ${gray}│${reset}  ${cyan}$(date '+%Y-%m-%d %H:%M')${reset}                          ${white}│${reset}"
echo -e "${white}│${reset}     ${green}${TOTAL_USB}${reset}           ${green}${TOTAL_STORAGE}${reset}          ${green}${MOUNTED_COUNT}${reset}                                           ${white}│${reset}"
echo -e "${white}└──────────────────────────────────────────────────────────────────────────┘${reset}"
echo ""

echo "$USB_OUTPUT" | while read line; do
    bus=$(echo "$line" | awk '{print $2}')
    dev=$(echo "$line" | awk '{print $4}' | tr -d ':')
    desc=$(echo "$line" | cut -d' ' -f7-)
    vendor=$(echo "$line" | awk '{print $6}')
    prod=$(echo "$line" | awk '{print $7}')

    case "$desc" in
        *hub*)        icon="🔌" ;;
        *webcam*|*camera*|*Webcam*|*Camera*) icon="📷" ;;
        *bluetooth*|*Bluetooth*) icon="📶" ;;
        *mouse*|*Mouse*) icon="🖱️" ;;
        *keyboard*|*Keyboard*) icon="⌨️" ;;
        *audio*|*Audio*|*speaker*|*Speaker*) icon="🔊" ;;
        *mass*|*Mass*|*storage*|*Storage*) icon="💾" ;;
        *wireless*)   icon="📶" ;;
        *)            icon="📦" ;;
    esac

    echo -e "${blue}│${reset}  ${icon} ${desc}"
    echo -e "${blue}│${reset}      Bus: ${bus}  Device: ${dev}  ID: ${vendor}:${prod}"
    echo -e "${blue}│${reset}"
done

STORAGE_FOUND=0
for dev in /sys/block/sd*; do
    if [ -d "$dev" ]; then
        drive="${dev##*/}"
        vendor=$(cat "$dev/device/vendor" 2>/dev/null | xargs)
        model=$(cat "$dev/device/model" 2>/dev/null | xargs)
        size=$(cat "$dev/size" 2>/dev/null)
        removable=$(cat "$dev/removable" 2>/dev/null)

        if [ -n "$vendor" ] || [ -n "$model" ] || [ -n "$size" ]; then
            STORAGE_FOUND=1

            echo -e "${green}│${reset}"
            echo -e "${green}┌─ Storage: /dev/${drive} ${gray}────────────────────────────────────────────${reset}"
            echo -e "${green}│${reset}"

            [ -n "$vendor" ] && echo -e "${green}│${reset}  ${gray}Vendor:${reset}  $vendor"
            [ -n "$model" ] && echo -e "${green}│${reset}  ${gray}Model:${reset}   $model"
            if [ -n "$size" ]; then
                sectors=$((size * 512))
                human_size=$(numfmt --to=iec $sectors 2>/dev/null)
                echo -e "${green}│${reset}  ${gray}Size:${reset}    $human_size"
            fi
            if [ -n "$removable" ]; then
                [ "$removable" = "0" ] && echo -e "${green}│${reset}  ${gray}Type:${reset}   Fixed Disk" || echo -e "${green}│${reset}  ${gray}Type:${reset}   Removable"
            fi

            echo -e "${green}│${reset}"
            echo -e "${green}│${reset}  ${white}Partitions:${reset}"

            PART_COUNT=0
            for part in /dev/${drive}[0-9]* /dev/${drive}p[0-9]*; do
                [ -b "$part" ] || continue
                ((PART_COUNT++))

                fs=$(lsblk -no FSTYPE "$part" 2>/dev/null)
                mount=$(lsblk -no MOUNTPOINT "$part" 2>/dev/null)
                psize=$(blockdev --getsize64 "$part" 2>/dev/null | numfmt --to=iec 2>/dev/null)
                [ -z "$fs" ] && fs="─"
                [ -z "$mount" ] && mount="[not mounted]"
                [ -z "$psize" ] && psize="─"

                if [ "$mount" != "[not mounted]" ]; then
                    printf "${green}│${reset}    ${green}●${reset} ${part}  ${cyan}[${fs}]${reset}  ${yellow}${psize}${reset}  →  ${white}${mount}${reset}\n"
                else
                    printf "${green}│${reset}    ${gray}●${reset} ${part}  ${cyan}[${fs}]${reset}  ${yellow}${psize}${reset}  ${gray}→  ${mount}${reset}\n"
                fi
            done

            if [ $PART_COUNT -eq 0 ]; then
                echo -e "${green}│${reset}    ${gray}No partitions found${reset}"
            fi

            echo -e "${green}└────────────────────────────────────────────────────────────────────${reset}"
        fi
    fi
done

echo ""

if [ $STORAGE_FOUND -eq 0 ]; then
    echo -e "${yellow}│${reset}"
    echo -e "${yellow}┌─ Storage Devices ${gray}─────────────────────────────────────────────────────${reset}"
    echo -e "${yellow}│${reset}"
    echo -e "${yellow}│${reset}  ${gray}No storage devices detected${reset}"
    echo -e "${yellow}└────────────────────────────────────────────────────────────────────${reset}"
fi

echo ""

MOUNTED_USB=$(mount | grep -E "^/dev/sd" 2>/dev/null)
if [ -n "$MOUNTED_USB" ]; then
    echo -e "${magenta}┌─ Mounted Drives ${gray}──────────────────────────────────────────────────────────${reset}"
    echo -e "${magenta}│${reset}"
    echo "$MOUNTED_USB" | while read line; do
        dev=$(echo "$line" | awk '{print $1}')
        mp=$(echo "$line" | awk '{print $3}')
        opts=$(echo "$line" | awk -F'[][]' '{print $2}')
        fs=$(echo "$line" | awk '{print $5}')
        echo -e "${magenta}│${reset}  ${cyan}💿${reset} $dev  ${white}${fs}${reset}  →  $mp"
    done
    echo -e "${magenta}└────────────────────────────────────────────────────────────────────────────${reset}"
    echo ""
fi

echo -e "${gray}──────────────────────────────────────────────────────────────────────────────${reset}"
echo -e "  ${green}✓${reset} Scan complete  |  ${green}${TOTAL_USB}${reset} USB devices  |  ${green}$(date '+%H:%M:%S')${reset}"
echo -e "${gray}──────────────────────────────────────────────────────────────────────────────${reset}"
echo ""
echo -e "  ${gray}Press any key to exit...${reset}"
read -n1
echo ""
