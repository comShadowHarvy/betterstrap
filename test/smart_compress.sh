#!/bin/bash

# Smart Compression Script
# Usage: ./smart_compress.sh [.ext] <files/dirs...>

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 [.extension] <files_or_directories...>"
    echo "Example: $0 .zip myfolder"
    echo "Example: $0 myfolder (defaults to max compression)"
    exit 1
fi

# Check if first argument is an extension
TARGET_EXT=""
FILES=()

if [[ "$1" == .* ]]; then
    TARGET_EXT="$1"
    shift
fi

FILES=("$@")

if [ ${#FILES[@]} -eq 0 ]; then
    echo "Error: No files specified to compress."
    exit 1
fi

# Determine Base Name from first file
BASE_NAME=$(basename "${FILES[0]}")
# Remove extension if it's a file, just to be clean, though usually user compresses folders
if [ -f "${FILES[0]}" ]; then
    BASE_NAME="${BASE_NAME%.*}"
fi

# Default Extension Logic if not specified
if [ -z "$TARGET_EXT" ]; then
    if command -v 7z &> /dev/null; then
        TARGET_EXT=".7z"
    elif command -v ouch &> /dev/null; then
         # ouch supports 7z too, giving it priority if ouch is the tool
         TARGET_EXT=".7z"
    else
        # Fallback to tar.xz which usually exists
        TARGET_EXT=".tar.xz"
    fi
    echo "No format specified. Defaulting to '$TARGET_EXT' for best compression."
fi

OUTPUT_FILE="${BASE_NAME}${TARGET_EXT}"

# Check for 'ouch'
if command -v ouch &> /dev/null; then
    echo "Using 'ouch' to compress to '$OUTPUT_FILE'..."
    ouch compress "${FILES[@]}" "$OUTPUT_FILE"
    status=$?
    if [ $status -eq 0 ]; then
        echo "Compression successful: $OUTPUT_FILE"
        exit 0
    else
        echo "Compression failed with ouch."
        exit $status
    fi
fi

# Fallback Logic
echo "'ouch' not found. Using fallback tools..."

case "$TARGET_EXT" in
    .zip)
        zip -r -9 "$OUTPUT_FILE" "${FILES[@]}"
        ;;
    .tar.gz|.tgz)
        tar czf "$OUTPUT_FILE" "${FILES[@]}"
        ;;
    .tar.bz2)
        tar cjf "$OUTPUT_FILE" "${FILES[@]}"
        ;;
    .tar.xz)
        tar cJf "$OUTPUT_FILE" "${FILES[@]}"
        ;;
    .7z)
        if command -v 7z &> /dev/null; then
            7z a -mx=9 "$OUTPUT_FILE" "${FILES[@]}"
        else
            echo "Error: '7z' command not found."
            exit 1
        fi
        ;;
    .rar)
        if command -v rar &> /dev/null; then
            rar a "$OUTPUT_FILE" "${FILES[@]}"
        else
            echo "Error: 'rar' command not found."
            exit 1
        fi
        ;;
    *)
        echo "Error: Unsupported extension '$TARGET_EXT' for manual fallback."
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    echo "Compression successful: $OUTPUT_FILE"
else
    echo "Compression failed."
    exit 2
fi
