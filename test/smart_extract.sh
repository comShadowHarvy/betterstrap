#!/bin/bash

# Smart Extraction Script
# Usage: ./smart_extract.sh <archive_file>

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <archive_file>"
    exit 1
fi

FILE="$1"

if [ ! -f "$FILE" ]; then
    echo "Error: File '$FILE' not found."
    exit 1
fi

# Check for 'ouch'
if command -v ouch &> /dev/null; then
    echo "Using 'ouch' to decompress..."
    ouch decompress "$FILE"
    exit $?
fi

# Fallback Logic
echo "'ouch' not found. Using fallback tools..."

# Get file extension (lowercase)
EXT=$(echo "$FILE" | grep -o '\.[^.]\+\(\.[^.]\+\)\?$' | tr '[:upper:]' '[:lower:]')
# If double extension not found or too long, just take single
if [[ -z "$EXT" || ${#EXT} -gt 8 ]]; then
    EXT=$(echo "$FILE" | grep -o '\.[^.]\+$' | tr '[:upper:]' '[:lower:]')
fi

echo "Detected extension: $EXT"

case "$EXT" in
    *.tar.gz|*.tgz)
        tar xzf "$FILE"
        ;;
    *.tar.bz2|*.tbz2)
        tar xjf "$FILE"
        ;;
    *.tar.xz|*.txz)
        tar xJf "$FILE"
        ;;
    *.tar)
        tar xf "$FILE"
        ;;
    *.zip)
        if command -v unzip &> /dev/null; then
            unzip "$FILE"
        else
            7z x "$FILE"
        fi
        ;;
    *.7z)
        7z x "$FILE"
        ;;
    *.rar)
        if command -v unrar &> /dev/null; then
            unrar x "$FILE"
        else
            7z x "$FILE"
        fi
        ;;
    *.gz)
        gunzip -k "$FILE"
        ;;
    *.bz2)
        bunzip2 -k "$FILE"
        ;;
    *.xz)
        unxz -k "$FILE"
        ;;
    *.z)
        uncompress "$FILE"
        ;;
    *)
        echo "Error: Unknown or unsupported format '$EXT'"
        echo "Attempting to guess with 'file' command..."
        FILE_TYPE=$(file -b "$FILE")
        echo "File type says: $FILE_TYPE"
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    echo "Extraction successful."
else
    echo "Extraction failed."
    exit 2
fi
