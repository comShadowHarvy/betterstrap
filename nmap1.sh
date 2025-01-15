#!/bin/bash

# Define the subnet or IP range
SUBNET="192.168.1.0/24"

# Define the output file
OUTPUT_FILE="/path/to/output_file.txt"

# Run nmap scan
nmap -sV $SUBNET -oN $OUTPUT_FILE

# Optional: add more commands or logs
echo "Scan completed: $(date)" >> $OUTPUT_FILE
