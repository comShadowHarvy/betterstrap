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
    echo "  QPush Script Installer"
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
total_steps=5
current_step=0
script_path="$HOME/git/betterstrap/push.sh"
destination_path="/usr/local/bin/qpush"
home_bin="$HOME/bin/qpush"

display_header

# Step 1: Make the script executable
display_description "Step 1: Make the Script Executable" \
"Ensuring that the qpush script is executable by setting the appropriate permissions."
chmod +x "$script_path"
loading_bar $((++current_step)) $total_steps
sleep 1

# Step 2: Move the script to a directory in PATH
display_description "Step 2: Move Script to PATH Directory" \
"Moving the qpush script to a directory included in your PATH, such as /usr/local/bin or ~/bin."
if [ -d "/usr/local/bin" ]; then
    sudo mv "$script_path" "$destination_path"
    final_path="$destination_path"
else
    mkdir -p "$HOME/bin"
    mv "$script_path" "$home_bin"
    final_path="$home_bin"
fi
loading_bar $((++current_step)) $total_steps
sleep 1

# Step 3: Ensure the directory is in PATH (for ~/bin)
display_description "Step 3: Ensure PATH Includes ~/bin" \
"Making sure your shell configuration includes ~/bin in the PATH variable for global access."
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
    source ~/.bashrc || source ~/.zshrc
fi
loading_bar $((++current_step)) $total_steps
sleep 1

# Step 4: Rename the script (if necessary)
display_description "Step 4: Rename Script to 'qpush'" \
"Renaming the script to 'qpush' if it has a different name, for easy access."
if [ -f "${final_path}.sh" ]; then
    mv "${final_path}.sh" "$final_path"
fi
loading_bar $((++current_step)) $total_steps
sleep 1

# Step 5: Verify and finish
display_description "Step 5: Verification" \
"Verifying that the qpush script is now executable from anywhere by typing 'qpush' in the terminal."
if command -v qpush > /dev/null; then
    echo "Verification complete: 'qpush' is now executable from anywhere."
else
    echo "Error: 'qpush' is not found in PATH."
fi
loading_bar $((++current_step)) $total_steps
sleep 1

echo -ne '\nAll steps completed. QPush script setup is complete.\n'
