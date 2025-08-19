#!/bin/bash

# Script Author: ShadowHarvy
# Purpose: Simulate a loading screen and run a sequence of custom setup scripts.
# Disclaimer: Run with caution. Ensure you understand the commands being executed.
#             This script will execute other scripts and download and run one from the internet.
# Version: 2.2

# --- Configuration ---
AUTHOR="ShadowHarvy"
LOG_FILE="custom_setup_log_$(date +%Y-%m-%d_%H-%M-%S).txt"

# --- Style and Color Configuration ---
# Using tput for compatibility. See if `tput colors` is > 8.
if [[ $(tput colors) -ge 8 ]]; then
  C_RESET=$(tput sgr0)
  C_BOLD=$(tput bold)
  C_RED=$(tput setaf 1)
  C_GREEN=$(tput setaf 2)
  C_YELLOW=$(tput setaf 3)
  C_BLUE=$(tput setaf 4)
  C_MAGENTA=$(tput setaf 5)
  C_CYAN=$(tput setaf 6)
  C_WHITE=$(tput setaf 7)
else
  # No color support
  C_RESET="" C_BOLD="" C_RED="" C_GREEN="" C_YELLOW="" C_BLUE="" C_MAGENTA="" C_CYAN="" C_WHITE=""
fi

# --- Script Steps Definition ---
# Define all steps in an array. This makes adding, removing, or reordering steps trivial.
# Each step has three parts:
# 1. Description: A human-readable string.
# 2. Type: 'local' for a local script, 'remote' for a script to be downloaded.
# 3. Command/URL: The actual command to run or the URL to download from.

# Note: We'll add two "fake" steps for the initialization animation.
declare -a STEPS
STEPS=(
  "Initializing Setup Sequence...;fake;2"
  "Preparing Environment...;fake;2"
  "Executing repo.sh script;local;./repo.sh"
  "Executing recomended.software.installer.sh;local;./recomended.software.installer.sh"
  "Executing dev.tools.install.sh script;local;./dev.tools.install.sh"
  "Executing attack.install.sh script;local;./attack.install.sh"
  "Executing waypipe.sh script;local;./waypipe.sh"
  "Executing plymouth.sh script;local;./plymouth.sh"
  "Fetching and executing Chris Titus Linux script;remote;https://christitus.com/linux"
)
STEPS_TOTAL=${#STEPS[@]}

# --- Helper Functions ---

# Function to print a centered message
print_centered() {
  local term_width=$(tput cols)
  local text_width=${#1}
  local padding=$(( (term_width - text_width) / 2 ))
  printf "%*s%s\n" "$padding" "" "$1"
}

# Function to log messages to console and file
# It strips color codes before writing to the log file for cleanliness.
log_message() {
  local clean_message
  clean_message=$(echo -e "$1" | sed 's/\x1B\[[0-9;]*[a-zA-Z]//g')
  echo -e "$1${C_RESET}"
  echo "$(date +'%Y-%m-%d %H:%M:%S') - ${clean_message}" >> "$LOG_FILE"
}

# Function for a fake progress bar animation
progress_bar() {
  local duration=$1
  local message=$2
  local current_step=$3
  local total_steps=$4

  log_message "\n${C_BOLD}${C_CYAN}$message [$current_step/$total_steps]${C_RESET}"
  
  local progress_bar_width=50
  # Use integer arithmetic; avoids `bc` dependency
  local sleep_interval_ms=$(( (duration * 1000) / progress_bar_width ))

  echo -n "  ["
  for ((i=0; i<progress_bar_width; i++)); do
    echo -n "#"
    sleep ".$(($sleep_interval_ms / 10))" # sleep takes seconds, so we use decimals
  done
  echo -n "] 100%"
  echo -e "\n"
  sleep 0.5
}

# Function to execute a command, requesting sudo if needed
run_command() {
  local cmd_description="$1"
  local cmd="$2"
  local exec_cmd="$cmd"
  local sudo_msg=""

  if [[ "$cmd" == sudo* ]]; then
    read -p "The step '$cmd_description' requires sudo. Grant permission? (y/N): " -r choice
    echo
    if [[ ! "$choice" =~ ^[Yy]$ ]]; then
      log_message "${C_YELLOW}Skipped '$cmd_description' by user decision.${C_RESET}"
      return
    fi
    sudo_msg=" (with sudo)"
  fi

  log_message "${C_BLUE}----------------------------------------------------------------------${C_RESET}"
  log_message "${C_BOLD}${C_MAGENTA}Executing: $cmd_description$sudo_msg${C_RESET}"
  log_message "${C_BLUE}Command: $exec_cmd${C_RESET}"
  log_message "${C_BLUE}----------------------------------------------------------------------${C_RESET}"

  if (set -o pipefail; $exec_cmd 2>&1 | tee -a "$LOG_FILE"); then
    log_message "${C_GREEN}SUCCESS: $cmd_description completed.${C_RESET}"
  else
    local exit_code=$?
    log_message "\n${C_RED}######################################################################"
    log_message "${C_RED}${C_BOLD}ERROR: '$cmd_description' failed with exit code $exit_code."
    log_message "${C_RED}${C_BOLD}Check '$LOG_FILE' for details."
    log_message "${C_RED}${C_BOLD}Aborting script."
    log_message "${C_RED}######################################################################${C_RESET}"
    exit "$exit_code"
  fi
  log_message "${C_BLUE}----------------------------------------------------------------------${C_RESET}"
  echo
  sleep 1
}

# Safer way to handle remote scripts
run_remote_script() {
    local description="$1"
    local url="$2"
    local temp_script
    temp_script=$(mktemp) # Create a secure temporary file

    log_message "${C_BLUE}----------------------------------------------------------------------${C_RESET}"
    log_message "${C_BOLD}${C_MAGENTA}Processing Remote Script: $description${C_RESET}"
    log_message "${C_CYAN}Downloading from URL: $url${C_RESET}"

    if curl -fsSL "$url" -o "$temp_script"; then
        log_message "${C_GREEN}Download successful. Script saved to: $temp_script${C_RESET}"
    else
        log_message "${C_RED}ERROR: Failed to download script from $url.${C_RESET}"
        rm -f "$temp_script"
        exit 1
    fi

    echo
    log_message "${C_YELLOW}${C_BOLD}SECURITY WARNING:${C_RESET}"
    log_message "${C_YELLOW}The script has been downloaded. You can review it before execution."
    log_message "${C_YELLOW}Review command: ${C_BOLD}cat $temp_script${C_RESET}"
    
    read -p "Do you want to execute this script? (y/N): " -r choice
    echo

    if [[ "$choice" =~ ^[Yy]$ ]]; then
        read -p "Execute with sudo? (y/N): " -r sudo_choice
        echo
        
        local cmd_to_run="bash $temp_script"
        if [[ "$sudo_choice" =~ ^[Yy]$ ]]; then
            cmd_to_run="sudo $cmd_to_run"
        fi
        
        log_message "${C_CYAN}User approved execution. Running script...${C_RESET}"
        run_command "$description" "$cmd_to_run"
    else
        log_message "${C_YELLOW}Execution skipped by user.${C_RESET}"
    fi

    rm -f "$temp_script"
    log_message "${C_CYAN}Cleaned up temporary script file.${C_RESET}"
    log_message "${C_BLUE}----------------------------------------------------------------------${C_RESET}"
    echo
    sleep 1
}


# --- Pre-flight Checks ---
check_dependencies() {
    local missing=0
    for cmd in tput curl; do # Removed sudo from this check
        if ! command -v "$cmd" &> /dev/null; then
            echo "${C_RED}Error: Required command '$cmd' is not installed.${C_RESET}"
            missing=1
        fi
    done

    for step in "${STEPS[@]}"; do
        IFS=';' read -r description type command <<< "$step"
        if [[ "$type" == "local" ]] && [[ ! -x "$command" ]]; then
            echo "${C_RED}Error: Local script '$command' not found or not executable.${C_RESET}"
            missing=1
        fi
    done

    if [[ $missing -eq 1 ]]; then
        echo "${C_RED}Please install missing dependencies and ensure scripts are executable, then try again.${C_RESET}"
        exit 1
    fi
}


# --- Main Script ---

# 0. Initialization
clear
echo "${C_BOLD}${C_CYAN}Custom Linux Setup Script by $AUTHOR (v2.2)${C_RESET}" > "$LOG_FILE"
echo "Log file: $PWD/$LOG_FILE" >> "$LOG_FILE"
log_message "${C_BLUE}======================================================================${C_RESET}"

check_dependencies

log_message "${C_BOLD}${C_YELLOW}IMPORTANT: This script will execute the following tasks. Some may require root privileges:${C_RESET}"
current_step=1
for step in "${STEPS[@]}"; do
    IFS=';' read -r description type _ <<< "$step"
    if [[ "$type" != "fake" ]]; then
        log_message "${C_YELLOW}$current_step. $description${C_RESET}"
        ((current_step++))
    }
done
log_message "${C_YELLOW}Ensure you trust these sources and scripts before proceeding.${C_RESET}"
log_message "${C_BLUE}======================================================================${C_RESET}"

# 2. Final Confirmation
read -p "Press [Enter] to begin the setup, or [Ctrl+C] to abort."

# 3. Main Execution Loop
current_step_display=0
for step in "${STEPS[@]}"; do
    ((current_step_display++))
    IFS=';' read -r description type command_or_url <<< "$step"

    case "$type" in
        fake)
            progress_bar "$command_or_url" "$description" "$current_step_display" "$STEPS_TOTAL"
            log_message "Simulated Step: $description"
            ;;
        local)
            run_command "$description" "$command_or_url"
            ;;
        remote)
            run_remote_script "$description" "$command_or_url"
            ;;
        *)
            log_message "${C_RED}Unknown step type '$type' in configuration. Aborting.${C_RESET}"
            exit 1
            ;;
    esac
done

# --- Completion ---
log_message "\n${C_GREEN}${C_BOLD}All setup tasks processed successfully!${C_RESET}"
print_centered "${C_BLUE}=========================================${C_RESET}"
print_centered "${C_BOLD}${C_GREEN}Custom Linux Setup Script Finished!${C_RESET}"
print_centered "${C_CYAN}Authored by: $AUTHOR${C_RESET}"
print_centered "Log available at: ${C_BOLD}$PWD/$LOG_FILE${C_RESET}"
print_centered "Review the log for details on each step."
print_centered "${C_BLUE}=========================================${C_RESET}"
echo

exit 0