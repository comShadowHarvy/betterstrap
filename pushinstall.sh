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

# Function to display the header
display_header() {
    clear
    echo "============================="
    echo "  QPush & RipDVD Installer"
    echo "============================="
    echo
}

# Function to display a description
display_description() {
    local title=$1
    local description=$2

    tput cup 4 0
    echo "============================="
    echo "   $title"
    echo "============================="
    echo
    echo "Description:"
    echo "$description"
    echo "----------------------------------"
    echo
}

# Variables
total_steps=7
current_step=0
qpush_script_path="$HOME/git/betterstrap/push.sh"
ripdvd_script_path="$HOME/scripts/ripdvd.sh"
destination_path="/usr/local/bin"
home_bin="$HOME/bin"
qpush_final_path=""
ripdvd_final_path=""

display_header

# Step 1: Make the scripts executable
display_description "Step 1: Make the Scripts Executable" \
"Ensuring that the QPush and RipDVD scripts are executable by setting the appropriate permissions."
chmod +x "$qpush_script_path"
chmod +x "$ripdvd_script_path"
loading_bar $((++current_step)) $total_steps
sleep 1

# Step 2: Copy the QPush script to a directory in PATH
display_description "Step 2: Copy QPush Script to PATH Directory" \
"Copying the QPush script to a directory included in your PATH, such as /usr/local/bin or ~/bin."
if [ -d "$destination_path" ]; then
    sudo cp "$qpush_script_path" "$destination_path/qpush"
    qpush_final_path="$destination_path/qpush"
else
    mkdir -p "$home_bin"
    cp "$qpush_script_path" "$home_bin/qpush"
    qpush_final_path="$home_bin/qpush"
fi
loading_bar $((++current_step)) $total_steps
sleep 1

# Step 3: Copy the RipDVD script to a directory in PATH
display_description "Step 3: Copy RipDVD Script to PATH Directory" \
"Copying the RipDVD script to a directory included in your PATH, such as /usr/local/bin or ~/bin."
if [ -d "$destination_path" ]; then
    sudo cp "$ripdvd_script_path" "$destination_path/ripdvd"
    ripdvd_final_path="$destination_path/ripdvd"
else
    mkdir -p "$home_bin"
    cp "$ripdvd_script_path" "$home_bin/ripdvd"
    ripdvd_final_path="$home_bin/ripdvd"
fi
loading_bar $((++current_step)) $total_steps
sleep 1

# Step 4: Ensure the directory is in PATH (for ~/bin)
display_description "Step 4: Ensure PATH Includes ~/bin" \
"Making sure your shell configuration includes ~/bin in the PATH variable for global access."
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
    source ~/.bashrc || source ~/.zshrc
fi
loading_bar $((++current_step)) $total_steps
sleep 1

# Step 5: Rename the scripts (if necessary)
display_description "Step 5: Rename Scripts" \
"Renaming the scripts to 'qpush' and 'ripdvd' if they have different names, for easy access."
if [ -f "${qpush_final_path}.sh" ]; then
    mv "${qpush_final_path}.sh" "$qpush_final_path"
fi
if [ -f "${ripdvd_final_path}.sh" ]; then
    mv "${ripdvd_final_path}.sh" "$ripdvd_final_path"
fi
loading_bar $((++current_step)) $total_steps
sleep 1

# Step 6: Verify QPush script
display_description "Step 6: Verify QPush Script" \
"Verifying that the qpush script is now executable from anywhere by typing 'qpush' in the terminal."
if command -v qpush > /dev/null; then
    echo "Verification complete: 'qpush' is now executable from anywhere."
else
    echo "Error: 'qpush' is not found in PATH."
fi
loading_bar $((++current_step)) $total_steps
sleep 1

# Step 7: Verify RipDVD script
display_description "Step 7: Verify RipDVD Script" \
"Verifying that the RipDVD script is now executable from anywhere by typing 'ripdvd' in the terminal."
if command -v ripdvd > /dev/null; then
    echo "Verification complete: 'ripdvd' is now executable from anywhere."
else
    echo "Error: 'ripdvd' is not found in PATH."
fi
loading_bar $((++current_step)) $total_steps
sleep 1

echo -ne '\nAll steps completed. QPush and RipDVD scripts setup is complete.\n'
