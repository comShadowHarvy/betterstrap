#!/bin/bash

# Script Author: ShadowHarvy
# Purpose: Simulate a loading screen and run a sequence of custom setup scripts, showing their live output.
# Disclaimer: Run with caution. Ensure you understand the commands being executed.
#             This script will execute other scripts and download and run one from the internet.

# --- Configuration ---
AUTHOR="ShadowHarvy"
LOG_FILE="custom_setup_log_$(date +%Y-%m-%d_%H-%M-%S).txt"
STEPS_TOTAL=8 # Total number of "loading" steps + actual script execution steps

# --- Helper Functions ---

# Function to print a centered message
print_centered() {
  local term_width=$(tput cols)
  local text_width=${#1}
  local padding=$(( (term_width - text_width) / 2 ))
  printf "%*s%s\n" "$padding" "" "$1"
}

# Function to simulate a progress bar
fake_progress() {
  local duration=$1 # How long the progress bar animation should run
  local message=$2
  local current_step=$3
  local total_steps=$4

  echo -ne "\n" # Start with a newline for spacing
  print_centered "$message [$current_step/$total_steps]"
  local progress_bar_width=50
  # Ensure duration is not zero to avoid division by zero if progress_bar_width is > 0
  if (( $(echo "$duration > 0" | bc -l) )) && (( progress_bar_width > 0 )); then
    local sleep_interval=$(echo "$duration / $progress_bar_width" | bc -l)
  else
    local sleep_interval=0
  fi

  echo -n "  [" # Start progress bar
  for ((i=0; i<progress_bar_width; i++)); do
    echo -n "#"
    if (( $(echo "$sleep_interval > 0" | bc -l) )); then
      sleep "$sleep_interval"
    fi
  done
  echo -n "] 100%" # End progress bar
  echo -e "\n" # Newline after progress bar
  sleep 0.5 # Small pause after completion
}

# Function to log messages to console and file (this script's own messages)
log_message() {
  echo "$(date +'%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to execute a command, show its live output, log it, and log its status
run_command() {
  local cmd_description="$1"
  local current_step_num="$2"
  local total_step_count="$3"
  shift 3 # Remove the first three arguments (description, current_step, total_steps)
  local cmd="$@"

  log_message "Starting: $cmd_description [$current_step_num/$total_step_count]"
  echo "----------------------------------------------------------------------" | tee -a "$LOG_FILE"
  echo "Executing: $cmd" | tee -a "$LOG_FILE"
  echo "Output from '$cmd_description' will now be displayed and logged:" | tee -a "$LOG_FILE"
  echo "----------------------------------------------------------------------" | tee -a "$LOG_FILE"

  # Execute the command.
  # (set -o pipefail; ...) ensures that if 'eval "$cmd"' fails, the pipeline's exit status reflects that failure.
  # 'eval "$cmd" 2>&1' executes the command and merges its standard error into its standard output.
  # '| tee -a "$LOG_FILE"' pipes this combined output to 'tee', which displays it on the terminal
  # and appends it to the specified log file.
  if (set -o pipefail; eval "$cmd" 2>&1 | tee -a "$LOG_FILE"); then
    # This block executes if the entire pipeline was successful (i.e., eval "$cmd" succeeded)
    log_message "SUCCESS: $cmd_description completed."
  else
    # This block executes if the pipeline failed (i.e., eval "$cmd" likely failed)
    local exit_code=$? # Capture the pipeline's exit code
    log_message "ERROR: $cmd_description failed with exit code $exit_code. Check $LOG_FILE for details."
    # Optionally, you could add 'exit 1' here to stop the entire script on error
  fi
  echo "----------------------------------------------------------------------" | tee -a "$LOG_FILE"
  echo # Newline for better readability in console after command output
  sleep 1 # Small pause after command
}

# --- Main Script ---

# Clear the screen for a cleaner look
clear

# 0. Initial Message and Log File Creation
echo "Custom Linux Setup Script by $AUTHOR" | tee "$LOG_FILE" # Overwrite or create log file
echo "Log file: $PWD/$LOG_FILE" | tee -a "$LOG_FILE"
echo "----------------------------------------------------------------------" | tee -a "$LOG_FILE"
echo "IMPORTANT: This script will execute:" | tee -a "$LOG_FILE"
echo "1. ./repo.sh" | tee -a "$LOG_FILE"
echo "2. ./recomended.software.installer.sh" | tee -a "$LOG_FILE"
echo "3. ./dev.tools.install.sh" | tee -a "$LOG_FILE"
echo "4. ./attack.install.sh" | tee -a "$LOG_FILE"
echo "5. ./waypipe.sh" | tee -a "$LOG_FILE"
echo "6. A script downloaded from christitus.com" | tee -a "$LOG_FILE"
echo "Ensure you trust these sources and scripts before proceeding." | tee -a "$LOG_FILE"
echo "----------------------------------------------------------------------" | tee -a "$LOG_FILE"
sleep 4 # Give user time to read the warning

# 1. Fake Loading Screen - Initialization
current_step_display=1
fake_progress 2 "Initializing Setup Sequence..." "$current_step_display" "$STEPS_TOTAL"
log_message "Initialization sequence started."

# 2. Fake Loading Screen - Preparing Environment
((current_step_display++))
fake_progress 2 "Preparing Environment..." "$current_step_display" "$STEPS_TOTAL"
log_message "Environment preparation simulated."

# --- Actual Script Executions ---

# 3. Run repo.sh
((current_step_display++))
# Assuming repo.sh is in the current directory and executable.
run_command "Executing repo.sh script" "$current_step_display" "$STEPS_TOTAL" "./repo.sh"

# 4. Run recomended.software.installer.sh
((current_step_display++))
# Assuming recomended.software.installer.sh is in the current directory and executable.
run_command "Executing recomended.software.installer.sh" "$current_step_display" "$STEPS_TOTAL" "./recomended.software.installer.sh"

# 5. Run dev.tools.install.sh
((current_step_display++))
# Assuming dev.tools.install.sh is in the current directory and executable.
run_command "Executing dev.tools.install.sh script" "$current_step_display" "$STEPS_TOTAL" "./dev.tools.install.sh"

# 6. Run attack.install.sh
((current_step_display++))
# Assuming attack.install.sh is in the current directory and executable.
run_command "Executing attack.install.sh script" "$current_step_display" "$STEPS_TOTAL" "./attack.install.sh"

# 7. Run waypipe.sh
((current_step_display++))
# Assuming waypipe.sh is in the current directory and executable.
run_command "Executing waypipe.sh script" "$current_step_display" "$STEPS_TOTAL" "./waypipe.sh"

# 8. Run Chris Titus Linux script
((current_step_display++))
run_command "Fetching and executing Chris Titus Linux script" "$current_step_display" "$STEPS_TOTAL" "curl -fsSL https://christitus.com/linux | sh"

# --- Completion ---
log_message "All setup tasks processed."
echo ""
print_centered "========================================="
print_centered "Custom Linux Setup Script Finished!"
print_centered "Authored by: $AUTHOR"
print_centered "Log available at: $PWD/$LOG_FILE"
print_centered "Review the log for details on each step."
print_centered "========================================="
echo ""

exit 0
