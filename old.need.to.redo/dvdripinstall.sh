#!/bin/bash

# Function to display a loading bar with percentage
loading_bar() {
    local current=$1
    local total=$2
    local percent=$(( 100 * current / total ))
    local bar_length=20
    local filled_length=$(( bar_length * current / total ))
    local empty_length=$(( bar_length - filled_length ))
    printf -v bar "%0.s#" $(seq 1 $filled_length)
    printf -v space "%0.s " $(seq 1 $empty_length)
    echo -ne "Progress: [${bar}${space}] (${percent}%%)\r"
}

# Function to display a header and description
display_section() {
    local title="$1"
    local description="$2"
    clear
    echo "============================="
    echo "  QPush & RipDVD Installer"
    echo "============================="
    echo
    echo "   $title"
    echo "============================="
    echo
    echo "Description:"
    echo "$description"
    echo "----------------------------------"
    echo
}

# Function to copy a script to PATH
copy_script() {
    local src="$1"
    local name="$2"
    if [ -d "$destination_path" ]; then
        sudo cp "$src" "$destination_path/$name"
        echo "$destination_path/$name"
    else
        mkdir -p "$home_bin"
        cp "$src" "$home_bin/$name"
        echo "$home_bin/$name"
    fi
}

# Variables
total_steps=7
current_step=0
qpush_script_path="$HOME/git/betterstrap/push.sh"
ripdvd_script_path="$HOME/scripts/ripdvd.sh"
destination_path="/usr/local/bin"
home_bin="$HOME/bin"

# Step 1: Make the scripts executable
display_section "Step 1: Make the Scripts Executable" \
"Ensuring that the QPush and RipDVD scripts are executable."
chmod +x "$qpush_script_path"
chmod +x "$ripdvd_script_path"
((++current_step))
loading_bar "$current_step" "$total_steps"
sleep 1

# Step 2: Copy the QPush script to a PATH directory
display_section "Step 2: Copy QPush Script to PATH" \
"Copying the QPush script so that it can be executed from anywhere."
qpush_final_path=$(copy_script "$qpush_script_path" "qpush")
((++current_step))
loading_bar "$current_step" "$total_steps"
sleep 1

# Step 3: Copy the RipDVD script to a PATH directory
display_section "Step 3: Copy RipDVD Script to PATH" \
"Copying the RipDVD script for global access."
ripdvd_final_path=$(copy_script "$ripdvd_script_path" "ripdvd")
((++current_step))
loading_bar "$current_step" "$total_steps"
sleep 1

# Step 4: Ensure ~/bin is in PATH
display_section "Step 4: Ensure ~/bin in PATH" \
"Appending ~/bin to your PATH in your shell config, if not already present."
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
    source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null
fi
((++current_step))
loading_bar "$current_step" "$total_steps"
sleep 1

# Step 5: Rename scripts if they have a .sh extension
display_section "Step 5: Rename Scripts" \
"Renaming scripts to remove possible .sh suffix for easier access."
for final in "$qpush_final_path" "$ripdvd_final_path"; do
    [ -f "${final}.sh" ] && mv "${final}.sh" "$final"
done
((++current_step))
loading_bar "$current_step" "$total_steps"
sleep 1

# Step 6: Verify QPush script installation
display_section "Step 6: Verify QPush Script" \
"Verifying that 'qpush' is available in your PATH."
if command -v qpush &>/dev/null; then
    echo "Verification complete: 'qpush' is executable."
else
    echo "Error: 'qpush' is not found in PATH."
fi
((++current_step))
loading_bar "$current_step" "$total_steps"
sleep 1

# Step 7: Verify RipDVD script installation
display_section "Step 7: Verify RipDVD Script" \
"Verifying that 'ripdvd' is available in your PATH."
if command -v ripdvd &>/dev/null; then
    echo "Verification complete: 'ripdvd' is executable."
else
    echo "Error: 'ripdvd' is not found in PATH."
fi
((++current_step))
loading_bar "$current_step" "$total_steps"
sleep 1

echo -e "\nAll steps completed. QPush and RipDVD scripts setup is complete."
