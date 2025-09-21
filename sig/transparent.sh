#!/bin/bash
# Convenient wrapper for processing single PNG files
# Usage: ./transparent.sh filename.png [aggressiveness]

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <png_file> [aggressiveness]"
    echo ""
    echo "Examples:"
    echo "  $0 image.png          # Normal processing (aggressiveness=1.5)"
    echo "  $0 image.png 1.0      # Conservative"
    echo "  $0 image.png 1.8      # Good for text/logos"
    echo "  $0 image.png 2.5      # Ultra aggressive"
    echo ""
    echo "Aggressiveness levels:"
    echo "  0.8  = Conservative (preserves more edge pixels)"
    echo "  1.0  = Normal"
    echo "  1.5  = Default (good balance)"
    echo "  1.8  = Aggressive (good for text with white borders)"
    echo "  2.5+ = Ultra aggressive"
    exit 1
fi

PNG_FILE="$1"
AGGRESSIVENESS="${2:-1.5}"  # Default to 1.5 for good text processing

if [[ ! -f "$PNG_FILE" ]]; then
    echo "Error: File '$PNG_FILE' does not exist"
    exit 1
fi

if [[ ! "$PNG_FILE" =~ \.png$ ]]; then
    echo "Error: File '$PNG_FILE' is not a PNG file"
    exit 1
fi

echo "🔄 Processing: $PNG_FILE"
echo "⚡ Aggressiveness: $AGGRESSIVENESS"
echo ""

# Use the improved transparency script directly
python3 "$(dirname "$0")/png_to_transparent.py" "$PNG_FILE" \
    --aggressiveness "$AGGRESSIVENESS" \
    --inplace \
    --threshold 240

echo ""
echo "✅ Done! White pixels removed from: $PNG_FILE"
echo "💡 Use --backup flag if you want to keep the original"