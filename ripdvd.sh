#!/bin/bash

# Check if the user provided an input file and output file name
if [ "$#" -ne 2 ]; then
    echo "Usage: ripdvd.sh <input.iso> <output.mp4>"
    exit 1
fi

input="$1"
output="$2"

# Run ffmpeg with the specified input and output
ffmpeg -i "$input" -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 192k -ac 2 "$output"
