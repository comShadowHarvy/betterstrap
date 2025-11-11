#!/bin/bash
# Enhanced Ollama Ecosystem Installer with Original Style + Enhancements
# This script installs Ollama, multiple UI options, and sets up various models

# Terminal colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="ollama_install_$(date +%Y%m%d_%H%M%S).log"

# --- Command Line Argument Defaults ---
NON_INTERACTIVE=0
SKIP_OLLAMA_INSTALL=0
SKIP_DOCKER_INSTALL_IF_MISSING=0
CHOSEN_MODEL_ARG=""   # Populated by --model flag
MODEL_FROM_ARG=""     # Parsed model ID from CHOSEN_MODEL_ARG
MODEL_RAM_FROM_ARG="" # Parsed RAM for model from CHOSEN_MODEL_ARG
NO_MODEL_DOWNLOAD=0
INSTALL_OPEN_WEBUI=1
INSTALL_PINOKIO=1
INSTALL_LOBEHUB=1
INSTALL_OLLAMA_GUI=1
INSTALL_ENCHANTED=1
NO_RUN_MODEL=0
ASSUME_YES_TO_FAIL_CONTINUE=0

# --- Model Definitions ---
# Format: "OllamaHubID;Description;RecommendedRAM_MB"
declare -A INTERACTIVE_MODEL_CHOICES=(
  # General Purpose / Chat Models (Small to Medium)
  ["1"]="llama3:8b;Meta - Excellent all-rounder (8B);8000"
  ["2"]="gemma:7b;Google - Strong general purpose model (7B);7000"
  ["3"]="mistral:7b;MistralAI - Popular, fast, and capable (7B);7000"
  ["4"]="phi3:medium;Microsoft - Very capable (14B, 4k context);14000"
  ["5"]="qwen:7b-chat;Alibaba - Strong multilingual chat model (7B);7000"
  ["6"]="llama3:8b-instruct;Meta - Llama 3 8B Instruct version;8000"
  ["7"]="nexral/devstral-7b;DevStrAl - Mistral fine-tune for dev/general;7000"

  # High Performance Chat Models (Larger, require more resources)
  ["10"]="mixtral:8x7b;MistralAI - MoE, very high performance (47B);48000"
  ["11"]="llama3:70b;Meta - Extremely powerful, general purpose (70B);70000"
  ["12"]="command-r:35b;Cohere - Enterprise grade, RAG optimized (35B);35000"
  ["13"]="command-r-plus:104b;Cohere - Flagship, RAG & Tool Use (104B);104000"
  ["14"]="huihui_ai/gpt-oss-abliterated:latest;OpenAI GPT-OSS - Reasoning & agentic tasks (20B);20000"
  ["15"]="huihui_ai/huihui-moe-abliterated:latest;Huihui MoE - Efficient MoE architecture (12B);12000"

  # Coding Models
  ["20"]="codellama:7b;Meta - Code generation (7B);7000"
  ["21"]="deepseek-coder:6.7b;DeepSeek - Strong coder (6.7B);7000"
  ["22"]="starcoder2:7b;HF/ServiceNow - Code generation (7B);7000"
  ["23"]="codellama:13b;Meta - Code generation (13B);13000"
  ["24"]="granite-code:8b;IBM - Granite Code Model (8B);8000"
  ["25"]="deepseek-coder:1.3b;DeepSeek - Small coder (1.3B);2000"

  # Small & Efficient Models (for lower resource systems)
  ["30"]="phi3:mini;Microsoft - Highly capable small model (3.8B, 4k context);4000"
  ["31"]="gemma:2b;Google - Small & efficient (2B);2500"
  ["32"]="tinyllama:1.1b;TinyLlama - Extremely small footprint (1.1B);1500"
  ["33"]="qwen:1.8b-chat;Alibaba - Very small multilingual chat (1.8B);2000"
  ["34"]="granite4:latest;IBM - Instruction following & tool-calling (3B);3000"

  # Multimodal Models (Vision + Text)
  ["M1"]="llava:7b;LLaVA - Vision and text model (7B);7500" # RAM includes vision components
  ["M2"]="huihui_ai/granite3.2-vision-abliterated:latest;IBM Granite Vision - Visual document understanding (2B);3000"

  # Multilingual Models
  ["L1"]="aya:8b;Cohere - Broad multilingual coverage (8B, 100+ lang);8000"
  # qwen models (e.g., 5, 33) also have strong multilingual capabilities.

  # Specific DeepSeek Models (from original script for reference)
  ["d1"]="deepseek-r1:1.5b;DeepSeek - Original Series 1.5B;2300"
  ["d2"]="deepseek-r1:7b;DeepSeek - Original Series 7B;4700"
)
# --- Helper Functions ---

fail() {
  echo -e "${RED}❌ ERROR: $1${NC}" | tee -a "$LOG_FILE"
  echo -e "${YELLOW}Check the log file for details: $LOG_FILE${NC}"
  if [ "$NON_INTERACTIVE" -eq 1 ]; then
    if [ "$ASSUME_YES_TO_FAIL_CONTINUE" -eq 1 ]; then
      warning "Non-interactive mode: Error occurred, but configured to attempt to continue."
      return 1
    else
      echo -e "${RED}Non-interactive mode: Aborting due to error.${NC}" | tee -a "$LOG_FILE"
      exit 1
    fi
  fi
  read -p "Do you want to continue with the rest of the installation? [Y/n] " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo -e "${RED}Installation aborted by user.${NC}" | tee -a "$LOG_FILE"
    exit 1
  fi
  return 1
}

info() { echo -e "${BLUE}ℹ️ $1${NC}" | tee -a "$LOG_FILE"; }
success() { echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"; }
warning() { echo -e "${YELLOW}⚠️ $1${NC}" | tee -a "$LOG_FILE"; }
section() { echo -e "\n${BOLD}${CYAN}=== $1 ===${NC}" | tee -a "$LOG_FILE"; }

display_banner() {
  echo -e "${BOLD}${BLUE}"
  echo '  ____  _ _                                 _____                _      _ _          '
  echo ' / __ \| | |                               |_   _|              | |    | | |         '
  echo '| |  | | | | __ _ _ __ ___   __ _    | |  _ __  ___| |_ __ _| | | ___ _ __ '
  echo '| |  | | | |/ _` | '\''_ ` _ \ / _` |   | | | '\''_ \/ __| __/ _` | | |/ _ \ '\''__|'
  echo '| |__| | | | (_| | | | | | | (_| |  _| |_| | | \__ \ || (_| | | |  __/ |   '
  echo ' \____/|_|_|\__,_|_| |_| |_|\__,_| |_____|_| |_|___/\__\__,_|_|_|\___|_|   '
  echo -e "${NC}"
  echo -e "${CYAN}A comprehensive installer for Ollama, UIs, and various Models${NC}\n"
}

init_log() {
  echo "=== Ollama Ecosystem Installation Log - $(date) ===" >"$LOG_FILE"
  echo "Script arguments: $SCRIPT_ARGS_LOG" >>"$LOG_FILE"
  echo "System: $(uname -a)" >>"$LOG_FILE"
  success "Log file initialized at $LOG_FILE"
}

user_confirm() {
  local prompt_message="$1"
  local default_yes=${2:-false}
  if [ "$NON_INTERACTIVE" -eq 1 ]; then
    if [ "$default_yes" = true ]; then
      info "Non-interactive: Auto-confirming '$prompt_message' as YES."
      return 0
    else
      info "Non-interactive: Auto-confirming '$prompt_message' as NO."
      return 1
    fi
  fi
  local yn_prompt=$([ "$default_yes" = true ] && echo "[Y/n]" || echo "[y/N]")
  read -p "$prompt_message $yn_prompt " -n 1 -r
  echo
  if [ "$default_yes" = true ]; then
    [[ $REPLY =~ ^[Nn]$ ]] && return 1 || return 0
  else [[ $REPLY =~ ^[Yy]$ ]] && return 0 || return 1; fi
}

display_help() {
  echo "Enhanced Ollama Ecosystem Installer"
  echo "Usage: $0 [options]"
  echo ""
  echo "General Options:"
  echo "  -h, --help                  Display this help message."
  echo "  -y, --yes                   Enable non-interactive mode. Assumes 'yes' or default for most prompts."
  echo "      --assume-yes-on-fail    In non-interactive mode (-y), if a component installation fails, attempt to continue."
  echo ""
  echo "Installation Skipping Options:"
  echo "      --skip-ollama           Skip Ollama installation."
  echo "      --skip-docker-install   Skip attempting to install Docker/Podman if no runtime is found."
  echo "      --no-model-download     Skip downloading any model (sets model to 'none')."
  echo "      --no-run-model          Skip the prompt to run the Ollama model after installation."
  echo ""
  echo "Component Installation Control (by default all are installed if applicable):"
  echo "      --no-open-webui         Skip Open WebUI installation."
  echo "      --no-pinokio            Skip Pinokio installation (Arch-based systems only)."
  echo "      --no-lobehub            Skip LobeHub installation."
  echo "      --no-ollama-gui         Skip Ollama Web UI (ollama/ollama-webui) installation."
  echo "      --no-enchanted          Skip Enchanted installation."
  echo ""
  echo "Model Selection:"
  echo "      --model MODEL_CHOICE    Select Ollama model. Provide choice key from interactive menu (e.g., 1, M1, d1),"
  echo "                              or full model ID (e.g., 'llama3:8b', 'nexral/devstral-7b')."
  echo "                              Default for non-interactive mode (if --model not used): phi3:mini (Choice 30)."
  echo "                              See interactive menu (run script without -y) for full list of choice keys."
  echo ""
  echo "Example: $0 -y --model 2 --no-pinokio"
  echo "  (Non-interactive, install model from choice #2 of interactive list, skip Pinokio)"
  echo "Example: $0 --model llava:7b"
  echo "  (Interactive, but pre-selects llava:7b model)"
}

# --- Argument Parsing & Initial Setup ---
SCRIPT_ARGS_LOG="$@"
while [[ "$#" -gt 0 ]]; do
  case $1 in
  -h | --help)
    display_help
    exit 0
    ;;
  -y | --yes)
    NON_INTERACTIVE=1
    shift
    ;;
  --assume-yes-on-fail)
    ASSUME_YES_TO_FAIL_CONTINUE=1
    shift
    ;;
  --skip-ollama)
    SKIP_OLLAMA_INSTALL=1
    shift
    ;;
  --skip-docker-install)
    SKIP_DOCKER_INSTALL_IF_MISSING=1
    shift
    ;;
  --model)
    CHOSEN_MODEL_ARG="$2"
    shift
    shift
    ;;
  --no-model-download)
    NO_MODEL_DOWNLOAD=1
    MODEL="none"
    shift
    ;;
  --no-open-webui)
    INSTALL_OPEN_WEBUI=0
    shift
    ;;
  --no-pinokio)
    INSTALL_PINOKIO=0
    shift
    ;;
  --no-lobehub)
    INSTALL_LOBEHUB=0
    shift
    ;;
  --no-ollama-gui)
    INSTALL_OLLAMA_GUI=0
    shift
    ;;
  --no-enchanted)
    INSTALL_ENCHANTED=0
    shift
    ;;
  --no-run-model)
    NO_RUN_MODEL=1
    shift
    ;;
  *)
    warning "Unknown parameter passed: $1"
    display_help
    exit 1
    ;;
  esac
done

# Pre-process CHOSEN_MODEL_ARG to populate MODEL_FROM_ARG and MODEL_RAM_FROM_ARG
if [ -n "$CHOSEN_MODEL_ARG" ]; then
  if [[ "$CHOSEN_MODEL_ARG" == *":"* ]] || [[ "$CHOSEN_MODEL_ARG" == *"/"* ]]; then # Full model_id (name:tag or user/model:tag)
    MODEL_FROM_ARG="$CHOSEN_MODEL_ARG"
    MODEL_RAM_FROM_ARG="UNKNOWN" # Default for direct names unless found in map
    for key_choice in "${!INTERACTIVE_MODEL_CHOICES[@]}"; do
      value_choice="${INTERACTIVE_MODEL_CHOICES[$key_choice]}"
      ollama_id_choice="${value_choice%%;*}"
      if [ "$ollama_id_choice" == "$MODEL_FROM_ARG" ]; then
        MODEL_RAM_FROM_ARG="${value_choice##*;}"
        break
      fi
    done
  elif [[ -v INTERACTIVE_MODEL_CHOICES["$CHOSEN_MODEL_ARG"] ]]; then # Key from interactive list
    model_data="${INTERACTIVE_MODEL_CHOICES[$CHOSEN_MODEL_ARG]}"
    MODEL_FROM_ARG="${model_data%%;*}"
    MODEL_RAM_FROM_ARG="${model_data##*;}"
  else
    warning "Value '$CHOSEN_MODEL_ARG' for --model is not a known choice key or a 'name:tag' (or 'user/name:tag') format."
    MODEL_FROM_ARG="" # Will fallback to interactive menu or default
    MODEL_RAM_FROM_ARG=""
  fi
fi

# --- Core Installation Functions ---
check_sudo() {
  section "Checking Permissions"
  if ! command -v sudo &>/dev/null; then
    warning "sudo is not installed."
    if [ "$EUID" -eq 0 ]; then
      info "Running as root, proceeding without explicit sudo command."
      sudo() { "$@"; }
    else fail "sudo is not installed and not running as root. Please install sudo or run as root."; fi
  else
    if ! sudo -n true 2>/dev/null; then
      info "Sudo requires a password. Validating sudo access..."
      if ! sudo -v; then fail "No sudo privileges or password not provided. Please ensure you have sudo access."; fi
    fi
    success "Sudo access verified."
  fi
}

detect_package_manager() {
  section "Detecting Package Manager"
  if command -v apt &>/dev/null; then
    PKG_MANAGER="apt"
    PKG_UPDATE="sudo apt update"
    PKG_INSTALL="sudo apt install -y"
    PKG_CHECK_INSTALLED="dpkg -s"
  elif command -v dnf &>/dev/null; then
    PKG_MANAGER="dnf"
    PKG_UPDATE="sudo dnf check-update || true"
    PKG_INSTALL="sudo dnf install -y"
    PKG_CHECK_INSTALLED="dnf list installed"
  elif command -v yum &>/dev/null; then
    PKG_MANAGER="yum"
    PKG_UPDATE="sudo yum check-update || true"
    PKG_INSTALL="sudo yum install -y"
    PKG_CHECK_INSTALLED="yum list installed"
  elif command -v pacman &>/dev/null; then
    PKG_MANAGER="pacman"
    PKG_UPDATE="sudo pacman -Sy"
    PKG_INSTALL="sudo pacman -S --needed --noconfirm"
    PKG_CHECK_INSTALLED="pacman -Q"
  elif command -v apk &>/dev/null; then
    PKG_MANAGER="apk"
    PKG_UPDATE="sudo apk update"
    PKG_INSTALL="sudo apk add"
    PKG_CHECK_INSTALLED="apk info -e"
  else
    fail "Unsupported package manager. Cannot proceed."
    exit 1
  fi
  success "Detected $PKG_MANAGER package manager."
}

is_arch() { [[ -f /etc/arch-release ]] || grep -qi "Arch Linux" /etc/os-release 2>/dev/null; }

install_yay() {
  info "Attempting to install yay AUR helper..."
  if [ "$EUID" -eq 0 ]; then
    warning "Running as root. Cannot build AUR packages like yay as root. Please install yay manually."
    return 1
  fi
  local missing_deps=""
  command -v git &>/dev/null || missing_deps+="git "
  local essential_bd_pkgs=("make" "gcc" "patch" "fakeroot" "binutils" "pkgconf")
  local install_base_devel_trigger=0
  for pkg_bd in "${essential_bd_pkgs[@]}"; do if ! pacman -Q "$pkg_bd" &>/dev/null; then
    install_base_devel_trigger=1
    break
  fi; done
  [ "$install_base_devel_trigger" -eq 1 ] && missing_deps+="base-devel "

  if [ -n "$missing_deps" ]; then
    info "Installing prerequisites for yay: $missing_deps"
    # shellcheck disable=SC2086
    if ! sudo pacman -S --needed --noconfirm $missing_deps 2>&1 | tee -a "$LOG_FILE"; then
      [ ${PIPESTATUS[0]} -ne 0 ] && warning "Failed to install prerequisites ($missing_deps) for yay." && return 1
    fi
    success "Prerequisites for yay installed."
  fi
  local build_dir
  build_dir=$(mktemp -d -p "$HOME" "yay_build_XXXXXX")
  if [ ! -d "$build_dir" ]; then
    warning "Failed to create temporary build directory for yay in $HOME."
    return 1
  fi
  info "Cloning yay into $build_dir/yay..."
  if ! git clone https://aur.archlinux.org/yay.git "$build_dir/yay" 2>&1 | tee -a "$LOG_FILE"; then
    [ ${PIPESTATUS[0]} -ne 0 ] && warning "Failed to clone yay repository." && rm -rf "$build_dir" && return 1
  fi
  pushd "$build_dir/yay" >/dev/null || {
    warning "Failed to enter yay build directory."
    rm -rf "$build_dir"
    return 1
  }
  info "Building and installing yay (makepkg -si)..."
  if ! makepkg -si --noconfirm 2>&1 | tee -a "$LOG_FILE"; then
    [ ${PIPESTATUS[0]} -ne 0 ] && warning "Failed to build or install yay with makepkg." && popd >/dev/null && rm -rf "$build_dir" && return 1
  fi
  popd >/dev/null
  rm -rf "$build_dir"
  if command -v yay &>/dev/null; then
    success "yay installed successfully."
    AUR_HELPER="yay"
    return 0
  else
    warning "yay installation command seemed to complete, but 'yay' command not found."
    return 1
  fi
}

check_aur_helper() {
  if is_arch; then
    section "Checking AUR Helper (for Pinokio)"
    if command -v yay &>/dev/null; then
      AUR_HELPER="yay"
      success "Found yay AUR helper."
    elif command -v paru &>/dev/null; then
      AUR_HELPER="paru"
      success "Found paru AUR helper."
    else
      warning "No AUR helper (yay or paru) found."
      if [ "$INSTALL_PINOKIO" -eq 1 ]; then
        if user_confirm "Do you want to attempt to install yay AUR helper?" true; then
          install_yay || warning "Failed to install yay. Pinokio installation will be skipped."
        else info "Skipping yay installation. Pinokio installation will be skipped."; fi
      else info "Pinokio installation is skipped by flag, so not attempting to install AUR helper."; fi
    fi
  fi
}

detect_container_runtime() {
  section "Detecting Container Runtime"
  if command -v podman &>/dev/null; then
    CONTAINER_CMD="podman"
    success "Using Podman as container runtime."
    podman info 2>/dev/null | grep -q "rootless: true" && info "Running Podman in rootless mode."
    return
  fi
  if command -v docker &>/dev/null; then
    if ! systemctl is-active --quiet docker 2>/dev/null; then
      info "Attempting to start Docker service..."
      if ! sudo systemctl start docker 2>&1 | tee -a "$LOG_FILE"; then
        [ ${PIPESTATUS[0]} -ne 0 ] && warning "Failed to start Docker service automatically." || success "Docker service started."
      else success "Docker service started."; fi
    else info "Docker service is already running."; fi
    if [ "$EUID" -ne 0 ] && ! groups "$USER" | grep -q '\bdocker\b'; then
      CONTAINER_CMD="sudo docker"
      warning "Current user '$USER' is not in 'docker' group. Using 'sudo docker'. Consider: sudo usermod -aG docker $USER && newgrp docker"
    else CONTAINER_CMD="docker"; fi
    success "Using Docker as container runtime."
    return
  fi
  warning "No compatible container runtime (Podman or Docker) found."
  if [ "$SKIP_DOCKER_INSTALL_IF_MISSING" -eq 1 ]; then
    warning "Skipping Docker installation as per --skip-docker-install flag."
    fail "No container runtime available and installation skipped. Cannot proceed with UI installations."
    CONTAINER_CMD=""
    return
  fi
  if user_confirm "Do you want to attempt to install Docker?" true; then
    install_docker
    if command -v docker &>/dev/null; then
      if [ "$EUID" -ne 0 ] && ! groups "$USER" | grep -q '\bdocker\b'; then CONTAINER_CMD="sudo docker"; else CONTAINER_CMD="docker"; fi
      success "Using newly installed Docker as container runtime."
    else
      fail "Docker installation attempted but failed to set up."
      CONTAINER_CMD=""
    fi
  else
    info "Skipping Docker installation by user choice."
    fail "No container runtime available and installation skipped."
    CONTAINER_CMD=""
  fi
}

install_docker() {
  section "Installing Docker"
  [ -z "$PKG_MANAGER" ] && detect_package_manager
  [ -z "$PKG_MANAGER" ] && fail "Package manager not detected." && return 1
  info "Attempting to install Docker using $PKG_MANAGER..."
  local status_install_docker=1 status_install_deps=0 # Default to failure for docker
  case $PKG_MANAGER in
  apt)
    info "Setting up Docker repository for apt..."
    eval "$PKG_UPDATE" | tee -a "$LOG_FILE"
    eval "$PKG_INSTALL ca-certificates curl gnupg" 2>&1 | tee -a "$LOG_FILE"
    status_install_deps=${PIPESTATUS[0]}
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    # shellcheck disable=SC2024
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$(. /etc/os-release && echo "$ID") $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
    eval "$PKG_UPDATE" | tee -a "$LOG_FILE"
    eval "$PKG_INSTALL docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin" 2>&1 | tee -a "$LOG_FILE"
    status_install_docker=${PIPESTATUS[0]}
    ;;
  dnf)
    info "Setting up Docker repository for dnf..."
    sudo dnf -y install dnf-plugins-core 2>&1 | tee -a "$LOG_FILE"
    sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo 2>&1 | tee -a "$LOG_FILE"
    eval "$PKG_INSTALL docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin" 2>&1 | tee -a "$LOG_FILE"
    status_install_docker=${PIPESTATUS[0]}
    ;;
  yum)
    info "Setting up Docker repository for yum..."
    sudo yum install -y yum-utils 2>&1 | tee -a "$LOG_FILE"
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo 2>&1 | tee -a "$LOG_FILE"
    eval "$PKG_INSTALL docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin" 2>&1 | tee -a "$LOG_FILE"
    status_install_docker=${PIPESTATUS[0]}
    ;;
  pacman)
    eval "$PKG_INSTALL docker docker-compose" 2>&1 | tee -a "$LOG_FILE"
    status_install_docker=${PIPESTATUS[0]}
    ;;
  apk)
    eval "$PKG_UPDATE" | tee -a "$LOG_FILE"
    eval "$PKG_INSTALL docker docker-cli docker-compose" 2>&1 | tee -a "$LOG_FILE"
    status_install_docker=${PIPESTATUS[0]}
    ;;
  *)
    fail "Docker installation for $PKG_MANAGER not implemented."
    return 1
    ;;
  esac
  if [ "$status_install_docker" -ne 0 ] || [ "$status_install_deps" -ne 0 ]; then
    fail "Docker package installation failed."
    return 1
  fi
  info "Enabling and starting Docker service..."
  local status_enable=0 status_start=0
  sudo systemctl enable docker 2>&1 | tee -a "$LOG_FILE" || status_enable=${PIPESTATUS[0]}
  sudo systemctl start docker 2>&1 | tee -a "$LOG_FILE" || status_start=${PIPESTATUS[0]}
  [ "$status_enable" -ne 0 ] && warning "Failed to enable Docker service."
  [ "$status_start" -ne 0 ] && warning "Failed to start Docker service."
  if ! command -v docker &>/dev/null; then
    fail "Docker command not found after installation."
    return 1
  fi
  if ! sudo systemctl is-active --quiet docker; then
    sleep 2
    sudo systemctl start docker
    if ! sudo systemctl is-active --quiet docker; then
      fail "Docker service not active."
      return 1
    fi
  fi
  success "Docker installed and service started."
  if ! groups "$USER" | grep -q '\bdocker\b' && [ "$EUID" -ne 0 ]; then
    if user_confirm "Add user $USER to docker group? (Requires logout/login or 'newgrp docker')" true; then
      sudo usermod -aG docker "$USER" 2>&1 | tee -a "$LOG_FILE"
      info "User $USER added to docker group. Please log out/in or run 'newgrp docker'. For this script, 'sudo docker' used if needed."
    fi
  fi
  return 0
}

install_dependencies() {
  section "Installing System Dependencies"
  info "Updating package lists (output in $LOG_FILE)..."
  eval "$PKG_UPDATE" 2>&1 | tee -a "$LOG_FILE"
  [ ${PIPESTATUS[0]} -ne 0 ] && warning "Package update failed. Continuing, but dependencies might fail."
  info "Installing required packages: curl, wget, git (output in $LOG_FILE)..."
  eval "$PKG_INSTALL curl wget git" 2>&1 | tee -a "$LOG_FILE"
  [ ${PIPESTATUS[0]} -ne 0 ] && fail "Failed to install core dependencies." || success "System dependencies installed/verified."
}

install_ollama() {
  if [ "$SKIP_OLLAMA_INSTALL" -eq 1 ]; then
    info "Skipping Ollama installation as per flag."
    ! command -v ollama &>/dev/null && warning "Ollama not installed & skipped. Subsequent steps may fail."
    return
  fi
  section "Installing Ollama"
  if command -v ollama &>/dev/null; then
    info "Ollama already installed. Version: $(ollama --version 2>/dev/null | awk '{print $2}')"
    if ! user_confirm "Reinstall/update Ollama?" false; then
      success "Skipping Ollama reinstallation."
      return
    fi
    info "Proceeding with Ollama reinstallation/update."
  fi
  info "Downloading Ollama installer script..."
  if ! curl -fsSL https://ollama.com/install.sh -o /tmp/ollama_install.sh; then
    fail "Failed to download Ollama installer."
    return 1
  fi
  chmod +x /tmp/ollama_install.sh
  info "Running Ollama installer (progress shown, full log in $LOG_FILE)..."
  sh /tmp/ollama_install.sh 2>&1 | tee -a "$LOG_FILE"
  local ollama_status=${PIPESTATUS[0]}
  rm -f /tmp/ollama_install.sh
  if [ "$ollama_status" -ne 0 ]; then
    fail "Ollama installation script failed (status $ollama_status)."
    return 1
  fi
  if ! command -v ollama &>/dev/null; then
    fail "Ollama command not found after installation."
    return 1
  fi
  success "Ollama installation script completed."
  if command -v systemctl &>/dev/null; then
    info "Ensuring Ollama systemd service is enabled and running..."
    sudo systemctl daemon-reload 2>&1 | tee -a "$LOG_FILE"
    sudo systemctl enable ollama.service 2>&1 | tee -a "$LOG_FILE"
    if ! sudo systemctl start ollama.service 2>&1 | tee -a "$LOG_FILE"; then
      sudo systemctl status ollama.service --no-pager >>"$LOG_FILE"
      warning "Ollama service failed to start initially."
    fi
    if sudo systemctl is-active --quiet ollama.service; then
      success "Ollama systemd service is active."
    else
      warning "Ollama systemd service not active. Trying again..."
      sleep 2
      sudo systemctl start ollama.service 2>&1 | tee -a "$LOG_FILE"
      if sudo systemctl is-active --quiet ollama.service; then
        success "Ollama systemd service now active."
      else
        sudo systemctl status ollama.service --no-pager >>"$LOG_FILE"
        fail "Ollama service failed to start."
        return 1
      fi
    fi
  else
    warning "systemd not detected. Attempting to start Ollama manually in background."
    ollama serve &>>"$LOG_FILE" &
    local ollama_pid=$! && sleep 5
    if ps -p "$ollama_pid" >/dev/null; then
      success "Ollama running (PID: $ollama_pid). Manage manually."
    else
      fail "Failed to start Ollama manually."
      return 1
    fi
  fi
  info "Waiting for Ollama API (up to 20s)..."
  for i in {1..10}; do
    if curl -s --head http://localhost:11434/ &>/dev/null; then
      success "Ollama API responsive."
      return 0
    fi
    info "Waiting... ($i/10)"
    sleep 2
  done
  warning "Ollama API not responsive in time. Continuing installation..."
  return 0
}

check_container() {
  local container_name=$1
  if [ -z "$CONTAINER_CMD" ]; then
    warning "No container command. Cannot check '$container_name'."
    return 1
  fi
  if $CONTAINER_CMD container inspect "$container_name" &>/dev/null; then
    warning "Container '$container_name' already exists."
    if user_confirm "Remove and replace existing '$container_name' container?" false; then
      info "Stopping/removing existing container '$container_name'..."
      $CONTAINER_CMD stop "$container_name" &>/dev/null || true
      $CONTAINER_CMD rm "$container_name" &>/dev/null || true
      success "Existing container '$container_name' removed."
      return 0
    else
      info "Skipping recreation of container '$container_name'."
      return 1
    fi
  fi
  return 0
}

choose_model() {
  if [ "$NO_MODEL_DOWNLOAD" -eq 1 ]; then
    MODEL="none"
    info "Skipping model selection/download: --no-model-download."
    return
  fi
  local selected_ollama_id="" selected_ram_mb="UNKNOWN"
  if [ -n "$MODEL_FROM_ARG" ]; then # MODEL_FROM_ARG is pre-processed from CHOSEN_MODEL_ARG
    selected_ollama_id="$MODEL_FROM_ARG"
    selected_ram_mb="$MODEL_RAM_FROM_ARG"
    info "Using model '$selected_ollama_id' from command line argument."
  else
    if [ "$NON_INTERACTIVE" -eq 1 ]; then
      local default_choice_key="30" # Default: phi3:mini
      if [[ -v INTERACTIVE_MODEL_CHOICES["$default_choice_key"] ]]; then
        local model_data="${INTERACTIVE_MODEL_CHOICES[$default_choice_key]}"
        selected_ollama_id="${model_data%%;*}"
        selected_ram_mb="${model_data##*;}"
        info "Non-interactive mode: Defaulting to model '$selected_ollama_id'."
      else # Fallback if default key somehow missing (should not happen)
        selected_ollama_id="phi3:mini"
        selected_ram_mb="4000" # Hardcoded fallback
        info "Non-interactive mode: Defaulting to model '$selected_ollama_id' (hardcoded fallback)."
      fi
    else
      section "Ollama Model Selection"
      echo -e "${CYAN}Choose model, or 'c' for custom, 's' to skip:${NC}"
      # Print categorized menu
      echo -e "\n${BOLD}General Purpose / Chat Models (Small to Medium):${NC}"
      for k in {"1","2","3","4","5","6","7"}; do [[ -v INTERACTIVE_MODEL_CHOICES["$k"] ]] && printf "  ${YELLOW}%2s)${NC} %-25s (%s; RAM: ~%sGB)\n" "$k" "${INTERACTIVE_MODEL_CHOICES[$k]%%;*}" "$(echo "${INTERACTIVE_MODEL_CHOICES[$k]}" | cut -d';' -f2)" "$((${INTERACTIVE_MODEL_CHOICES[$k]##*;} / 1000))"; done
      echo -e "\n${BOLD}High Performance Chat Models:${NC}"
      for k in {"10","11","12","13","14","15"}; do [[ -v INTERACTIVE_MODEL_CHOICES["$k"] ]] && printf "  ${YELLOW}%2s)${NC} %-25s (%s; RAM: ~%sGB)\n" "$k" "${INTERACTIVE_MODEL_CHOICES[$k]%%;*}" "$(echo "${INTERACTIVE_MODEL_CHOICES[$k]}" | cut -d';' -f2)" "$((${INTERACTIVE_MODEL_CHOICES[$k]##*;} / 1000))"; done
      echo -e "\n${BOLD}Coding Models:${NC}"
      for k in {"20","21","22","23","24","25"}; do [[ -v INTERACTIVE_MODEL_CHOICES["$k"] ]] && printf "  ${YELLOW}%2s)${NC} %-25s (%s; RAM: ~%sGB)\n" "$k" "${INTERACTIVE_MODEL_CHOICES[$k]%%;*}" "$(echo "${INTERACTIVE_MODEL_CHOICES[$k]}" | cut -d';' -f2)" "$((${INTERACTIVE_MODEL_CHOICES[$k]##*;} / 1000))"; done
      echo -e "\n${BOLD}Small & Efficient Models:${NC}"
      for k in {"30","31","32","33","34"}; do [[ -v INTERACTIVE_MODEL_CHOICES["$k"] ]] && printf "  ${YELLOW}%2s)${NC} %-25s (%s; RAM: ~%sGB)\\n" "$k" "${INTERACTIVE_MODEL_CHOICES[$k]%%;*}" "$(echo "${INTERACTIVE_MODEL_CHOICES[$k]}" | cut -d';' -f2)" "$((${INTERACTIVE_MODEL_CHOICES[$k]##*;} / 1000))"; done
      echo -e "\n${BOLD}Multimodal Models (Vision + Text):${NC}"
      for k in {"M1","M2"}; do [[ -v INTERACTIVE_MODEL_CHOICES["$k"] ]] && printf "  ${YELLOW}%2s)${NC} %-25s (%s; RAM: ~%sGB)\\n" "$k" "${INTERACTIVE_MODEL_CHOICES[$k]%%;*}" "$(echo "${INTERACTIVE_MODEL_CHOICES[$k]}" | cut -d';' -f2)" "$((${INTERACTIVE_MODEL_CHOICES[$k]##*;} / 1000))"; done
      echo -e "\n${BOLD}Multilingual Models:${NC}"
      for k in {"L1"}; do [[ -v INTERACTIVE_MODEL_CHOICES["$k"] ]] && printf "  ${YELLOW}%2s)${NC} %-25s (%s; RAM: ~%sGB)\n" "$k" "${INTERACTIVE_MODEL_CHOICES[$k]%%;*}" "$(echo "${INTERACTIVE_MODEL_CHOICES[$k]}" | cut -d';' -f2)" "$((${INTERACTIVE_MODEL_CHOICES[$k]##*;} / 1000))"; done
      echo -e "\n${BOLD}DeepSeek Original Series (for reference):${NC}"
      for k in {"d1","d2"}; do [[ -v INTERACTIVE_MODEL_CHOICES["$k"] ]] && printf "  ${YELLOW}%2s)${NC} %-25s (%s; RAM: ~%sGB)\n" "$k" "${INTERACTIVE_MODEL_CHOICES[$k]%%;*}" "$(echo "${INTERACTIVE_MODEL_CHOICES[$k]}" | cut -d';' -f2)" "$((${INTERACTIVE_MODEL_CHOICES[$k]##*;} / 1000))"; done
      echo -e "\n  ${YELLOW}c)${NC} Custom model (model_name:tag)"
      echo -e "  ${YELLOW}s)${NC} Skip model download"
      read -rp "Enter choice (default: 30 if empty): " uchoice
      uchoice=${uchoice:-30} # Default phi3:mini
      if [[ "$uchoice" =~ ^[Ss]$ ]]; then
        MODEL="none"
        info "Skipping model download."
        return
      elif [[ "$uchoice" =~ ^[Cc]$ ]]; then
        read -rp "Enter custom Ollama model ID (e.g., user/model:tag): " cmodel
        if [ -z "$cmodel" ] || [[ ! "$cmodel" == *":"* && ! "$cmodel" == *"/"* ]]; then
          warning "Invalid custom model ID format."
          MODEL="none"
          choose_model
          return
        fi
        selected_ollama_id="$cmodel"
        selected_ram_mb="UNKNOWN"
      elif [[ -v INTERACTIVE_MODEL_CHOICES["$uchoice"] ]]; then
        model_data="${INTERACTIVE_MODEL_CHOICES[$uchoice]}"
        selected_ollama_id="${model_data%%;*}"
        selected_ram_mb="${model_data##*;}"
      else
        warning "Invalid selection. Defaulting to phi3:mini (30)."
        local model_data_def="${INTERACTIVE_MODEL_CHOICES[30]}"
        selected_ollama_id="${model_data_def%%;*}"
        selected_ram_mb="${model_data_def##*;}"
      fi
    fi
  fi
  MODEL="$selected_ollama_id"
  if [ "$MODEL" != "none" ]; then
    if [ "$selected_ram_mb" == "UNKNOWN" ]; then
      warning "RAM for model '$MODEL' is unknown/not pre-defined. Ensure you have sufficient RAM."
      if ! user_confirm "Continue to download '$MODEL' without pre-defined RAM check?" true; then
        MODEL="none"
        info "Download cancelled."
        [ -z "$MODEL_FROM_ARG" ] && [ "$NON_INTERACTIVE" -eq 0 ] && choose_model
        return
      fi
    else
      total_ram_mb=$(free -m | awk '/^Mem:/{print $2}')
      recommended_ram_mb=$selected_ram_mb
      if [ "$total_ram_mb" -lt "$recommended_ram_mb" ]; then
        warning "System RAM ${total_ram_mb}MB. Model '$MODEL' recommends ${recommended_ram_mb}MB. May run slow/fail."
        if ! user_confirm "Continue download '$MODEL' anyway?" false; then
          MODEL="none"
          info "Download cancelled."
          [ -z "$MODEL_FROM_ARG" ] && [ "$NON_INTERACTIVE" -eq 0 ] && choose_model
          return
        fi
      fi
    fi
    success "Selected model for download: $MODEL"
  fi
}

download_model() {
  if [ "$MODEL" = "none" ] || [ "$NO_MODEL_DOWNLOAD" -eq 1 ]; then
    warning "Skipping model download."
    return
  fi
  if ! command -v ollama &>/dev/null; then
    warning "Ollama not found. Cannot download $MODEL."
    return 1
  fi
  section "Ollama Model Download: $MODEL"
  info "Checking if model $MODEL is already downloaded..."
  if ollama list | awk '{print $1}' | grep -Fxq "$MODEL"; then
    success "Model $MODEL already downloaded."
  else
    info "Downloading $MODEL (progress shown, full log in $LOG_FILE)..."
    echo -e "${YELLOW}This can take minutes to hours depending on size/speed.${NC}"
    ollama pull "$MODEL" 2>&1 | tee -a "$LOG_FILE"
    pull_status=${PIPESTATUS[0]}
    if [ "$pull_status" -ne 0 ]; then
      fail "Failed to download $MODEL (status: $pull_status). Try: ollama pull $MODEL"
      return 1
    fi
    success "Model $MODEL downloaded."
  fi
  return 0
}

run_model() {
  if [ "$MODEL" = "none" ] || [ "$NO_RUN_MODEL" -eq 1 ]; then
    info "Skipping interactive model run."
    [ "$MODEL" != "none" ] && info "Run later with: ollama run $MODEL"
    return
  fi
  if ! command -v ollama &>/dev/null; then
    warning "Ollama not found. Cannot run $MODEL."
    return
  fi
  if ! ollama list | awk '{print $1}' | grep -Fxq "$MODEL"; then
    warning "Model $MODEL not downloaded. Cannot run."
    return
  fi
  if user_confirm "Run $MODEL model now in terminal?" false; then
    info "Running $MODEL model..."
    echo -e "${YELLOW}Interactive session. Type prompts, /bye or Ctrl+D to exit. Ctrl+C to force exit.${NC}"
    sleep 1
    ollama run "$MODEL"
    success "Exited Ollama model run."
  else info "Skipping model execution. Run later: ollama run $MODEL"; fi
}

install_ui_component() {
  local ui_name="$1" container_name="$2" image_name="$3" port_map="$4" vol_map="$5" env_vars="$6" install_flag=${7}
  if [ "$install_flag" -eq 0 ]; then
    info "Skipping $ui_name: flag."
    return
  fi
  if [ -z "$CONTAINER_CMD" ]; then
    warning "No container runtime. Skipping $ui_name."
    return 1
  fi
  section "Installing $ui_name"
  if ! check_container "$container_name"; then
    success "Skipping $ui_name: user choice on existing container."
    return
  fi
  info "Pulling $ui_name image: $image_name (progress shown, full log in $LOG_FILE)..."
  $CONTAINER_CMD pull "$image_name" 2>&1 | tee -a "$LOG_FILE"
  pull_status=${PIPESTATUS[0]}
  if [ "$pull_status" -ne 0 ]; then
    fail "Failed to pull $ui_name image ($image_name)."
    return 1
  fi
  success "$ui_name image pulled."
  info "Creating $ui_name container '$container_name'..."
  local run_cmd="$CONTAINER_CMD run -d --name \"$container_name\" --restart always -p \"$port_map\""
  [ -n "$vol_map" ] && run_cmd+=" $vol_map"
  [ -n "$env_vars" ] && run_cmd+=" $env_vars"
  run_cmd+=" \"$image_name\""
  echo "Executing: $run_cmd" >>"$LOG_FILE"
  eval "$run_cmd" >>"$LOG_FILE" 2>&1
  run_status=$?
  if [ "$run_status" -ne 0 ]; then
    fail "Failed to create $ui_name container (status: $run_status)."
    $CONTAINER_CMD logs "$container_name" >>"$LOG_FILE" 2>&1
    return 1
  fi
  success "$ui_name installed and container '$container_name' started."
  return 0
}

install_open_webui() { install_ui_component "Open WebUI" "open-webui" "ghcr.io/open-webui/open-webui:main" "3000:8080" "-v open-webui_data:/app/backend/data" "" "$INSTALL_OPEN_WEBUI"; }
install_pinokio() {
  if [ "$INSTALL_PINOKIO" -eq 0 ]; then
    info "Skipping Pinokio: flag."
    return
  fi
  section "Installing Pinokio (Arch AUR)"
  if ! is_arch; then
    info "Not Arch. Skipping Pinokio."
    return
  fi
  if [ -z "$AUR_HELPER" ]; then
    warning "No AUR helper. Skipping Pinokio."
    return
  fi
  if command -v pinokio &>/dev/null; then
    info "Pinokio already installed."
    if ! user_confirm "Reinstall/update Pinokio?" false; then
      success "Skipping Pinokio reinstall."
      return
    fi
  fi
  info "Installing Pinokio from AUR using $AUR_HELPER (pinokio-bin)..."
  # shellcheck disable=SC2086
  if ! $AUR_HELPER -S --noconfirm pinokio-bin 2>&1 | tee -a "$LOG_FILE"; then
    [ ${PIPESTATUS[0]} -ne 0 ] && fail "Failed to install Pinokio."
    return 1
  fi
  success "Pinokio installed via $AUR_HELPER."
}
install_lobehub() {
  local ollama_api_url=""
  if [[ "$CONTAINER_CMD" == *"docker"* ]]; then
    ollama_api_url="http://host.docker.internal:11434"
  elif [[ "$CONTAINER_CMD" == *"podman"* ]]; then
    host_ip=$(hostname -I | awk '{print $1}')
    ollama_api_url="http://${host_ip:-127.0.0.1}:11434"
  fi
  [ -n "$ollama_api_url" ] && info "LobeHub ($CONTAINER_CMD) will try Ollama at $ollama_api_url. Ensure Ollama is accessible."
  install_ui_component "LobeHub" "lobehub" "ghcr.io/lobehub/lobe-chat:latest" "3210:3210" "" "-e OLLAMA_PROXY_URL=${ollama_api_url}" "$INSTALL_LOBEHUB"
}
install_ollama_gui() {
  install_ui_component "Ollama Web UI (ollama/webui)" "ollama-gui" "ollama/ollama-webui:latest" "4000:8080" "-v ollama_webui_data:/app/backend/data" "" "$INSTALL_OLLAMA_GUI"
  if [ "$INSTALL_OLLAMA_GUI" -eq 1 ] && [ "$?" -eq 0 ]; then
    info "For Ollama Web UI (localhost:4000): Configure Ollama API in UI settings (e.g. http://localhost:11434 or http://host.docker.internal:11434 if needed)."
    info "  Or run ollama-gui container with '--network host'."
  fi
}
install_enchanted() {
  install_ui_component "Enchanted" "enchanted" "ghcr.io/enchanted-ai/enchanted:latest" "9090:9090" "-v enchanted_data:/app/data" "" "$INSTALL_ENCHANTED"
  if [ "$INSTALL_ENCHANTED" -eq 1 ] && [ "$?" -eq 0 ]; then
    info "For Enchanted AI (localhost:9090): Configure LLM in settings (Ollama API: http://localhost:11434). May need '--network host'."
  fi
}

# --- Information Display Functions ---
show_system_info() {
  section "System Information"
  {
    echo "OS: $(cat /etc/os-release | grep "PRETTY_NAME" | cut -d= -f2 | tr -d '"')"
    [ -f /proc/cpuinfo ] && echo "CPU: $(grep "model name" /proc/cpuinfo | head -1 | cut -d ':' -f2 | sed 's/^[ \t]*//') ($(grep -c processor /proc/cpuinfo) cores)"
    command -v free &>/dev/null && echo "RAM: $(free -h | awk '/^Mem:/{print $4 " free of " $2}')"
    command -v df &>/dev/null && echo "Disk (.): $(df -h . | awk 'NR==2 {print $4 " free of " $2}')"
    if command -v nvidia-smi &>/dev/null; then
      echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -n 1) ($(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n 1)MiB)"
    elif command -v lspci &>/dev/null; then
      gpu_info=$(lspci 2>/dev/null | grep -i 'vga\|3d\|2d' | grep -Ei 'nvidia|amd|ati|intel' | head -1 | sed 's/.*controller: //; s/ (rev.*)//')
      [ -n "$gpu_info" ] && echo "GPU: $gpu_info" || echo "GPU: Not detected."
    else echo "GPU: Detection tools not found."; fi
    echo "Container Runtime: ${CONTAINER_CMD:-Not detected/installed}"
  } | tee -a "$LOG_FILE"
}

show_service_info() {
  section "Service Information & Access URLs"
  echo -e "${BOLD}Access your AI tools:${NC}" | tee -a "$LOG_FILE"
  ([ "$INSTALL_OPEN_WEBUI" -eq 1 ] && $CONTAINER_CMD container inspect "open-webui" &>/dev/null 2>&1) && echo -e "🔗 Open-WebUI      → ${CYAN}http://localhost:3000${NC}" | tee -a "$LOG_FILE"
  ([ "$INSTALL_PINOKIO" -eq 1 ] && command -v pinokio &>/dev/null) && echo -e "🔗 Pinokio         → Run ${CYAN}pinokio${NC} in terminal/menu" | tee -a "$LOG_FILE"
  ([ "$INSTALL_OLLAMA_GUI" -eq 1 ] && $CONTAINER_CMD container inspect "ollama-gui" &>/dev/null 2>&1) && echo -e "🔗 Ollama Web UI   → ${CYAN}http://localhost:4000${NC}" | tee -a "$LOG_FILE"
  ([ "$INSTALL_LOBEHUB" -eq 1 ] && $CONTAINER_CMD container inspect "lobehub" &>/dev/null 2>&1) && echo -e "🔗 LobeHub         → ${CYAN}http://localhost:3210${NC}" | tee -a "$LOG_FILE"
  ([ "$INSTALL_ENCHANTED" -eq 1 ] && $CONTAINER_CMD container inspect "enchanted" &>/dev/null 2>&1) && echo -e "🔗 Enchanted       → ${CYAN}http://localhost:9090${NC}" | tee -a "$LOG_FILE"
  if [ "$MODEL" != "none" ] && command -v ollama &>/dev/null && ollama list | awk '{print $1}' | grep -Fxq "$MODEL"; then
    echo -e "🤖 Installed model → ${CYAN}$MODEL${NC} (${CYAN}ollama run $MODEL${NC})" | tee -a "$LOG_FILE"
  elif [ "$MODEL" != "none" ]; then echo -e "❓ Model ${CYAN}$MODEL${NC} was selected but might not be installed. Check logs." | tee -a "$LOG_FILE"; fi
  echo -e "\n${BOLD}${GREEN}Installation process finished! Review warnings above.${NC}" | tee -a "$LOG_FILE"
  echo -e "Log: ${CYAN}$LOG_FILE${NC}" | tee -a "$LOG_FILE"
}

show_connection_instructions() {
  section "Connection & Usage Instructions"
  echo -e "${BOLD}${CYAN}How to use installed components:${NC}\n" | tee -a "$LOG_FILE"
  if ! [ "$SKIP_OLLAMA_INSTALL" -eq 1 ] && command -v ollama &>/dev/null; then
    echo -e "${BOLD}Ollama:${NC}" | tee -a "$LOG_FILE"
    [ -n "$MODEL" ] && [ "$MODEL" != "none" ] && echo -e "  • CLI access: ${CYAN}ollama run $MODEL${NC}" | tee -a "$LOG_FILE"
    echo -e "  • List models: ${CYAN}ollama list${NC}" | tee -a "$LOG_FILE"
    if command -v systemctl &>/dev/null; then
      echo -e "  • Start/Stop: ${CYAN}sudo systemctl start/stop ollama${NC}" | tee -a "$LOG_FILE"
      echo -e "  • Status: ${CYAN}systemctl status ollama${NC}" | tee -a "$LOG_FILE"
    else
      echo -e "  • Ollama (if started by script w/o systemd) runs in background. Start manually: ${CYAN}ollama serve${NC}" | tee -a "$LOG_FILE"
    fi
    echo "" | tee -a "$LOG_FILE"
  fi
  local ui_instr_gen=0
  ([ "$INSTALL_OPEN_WEBUI" -eq 1 ] && $CONTAINER_CMD container inspect "open-webui" &>/dev/null 2>&1) && ui_instr_gen=1 && echo -e "${BOLD}Open WebUI (http://localhost:3000):${NC}\n  Configure Ollama API if needed. Start/Stop: ${CYAN}$CONTAINER_CMD start/stop open-webui${NC}. Logs: ${CYAN}$CONTAINER_CMD logs open-webui${NC}\n" | tee -a "$LOG_FILE"
  ([ "$INSTALL_PINOKIO" -eq 1 ] && is_arch && command -v pinokio &>/dev/null) && ui_instr_gen=1 && echo -e "${BOLD}Pinokio:${NC}\n  Launch: ${CYAN}pinokio${NC}. Config Ollama API: ${CYAN}http://localhost:11434${NC}\n" | tee -a "$LOG_FILE"
  ([ "$INSTALL_OLLAMA_GUI" -eq 1 ] && $CONTAINER_CMD container inspect "ollama-gui" &>/dev/null 2>&1) && ui_instr_gen=1 && echo -e "${BOLD}Ollama WebUI (http://localhost:4000):${NC}\n  Configure Ollama API in UI (e.g. http://localhost:11434). Start/Stop: ${CYAN}$CONTAINER_CMD start/stop ollama-gui${NC}. Logs: ${CYAN}$CONTAINER_CMD logs ollama-gui${NC}\n" | tee -a "$LOG_FILE"
  ([ "$INSTALL_LOBEHUB" -eq 1 ] && $CONTAINER_CMD container inspect "lobehub" &>/dev/null 2>&1) && ui_instr_gen=1 && echo -e "${BOLD}LobeHub (http://localhost:3210):${NC}\n  Settings > Language Model > Ollama. Set Proxy URL if needed. Start/Stop: ${CYAN}$CONTAINER_CMD start/stop lobehub${NC}. Logs: ${CYAN}$CONTAINER_CMD logs lobehub${NC}\n" | tee -a "$LOG_FILE"
  ([ "$INSTALL_ENCHANTED" -eq 1 ] && $CONTAINER_CMD container inspect "enchanted" &>/dev/null 2>&1) && ui_instr_gen=1 && echo -e "${BOLD}Enchanted (http://localhost:9090):${NC}\n  Settings > LLM > Ollama. API: ${CYAN}http://localhost:11434${NC}. May need --network host. Start/Stop: ${CYAN}$CONTAINER_CMD start/stop enchanted${NC}. Logs: ${CYAN}$CONTAINER_CMD logs enchanted${NC}\n" | tee -a "$LOG_FILE"
  if [ "$ui_instr_gen" -eq 1 ]; then
    echo -e "${BOLD}Troubleshooting UI & Ollama Connection:${NC}" | tee -a "$LOG_FILE"
    echo -e "  • Ollama service running? (${CYAN}ollama list${NC} or ${CYAN}sudo systemctl status ollama${NC})" | tee -a "$LOG_FILE"
    echo -e "  • Ollama Host: Default ${CYAN}127.0.0.1:11434${NC}. For containers to access:" | tee -a "$LOG_FILE"
    echo -e "    - Docker: Use ${CYAN}http://host.docker.internal:11434${NC} in UI, or UI with ${CYAN}--network host${NC}." | tee -a "$LOG_FILE"
    echo -e "    - Podman: Use host IP (${CYAN}hostname -I${NC}) or UI with ${CYAN}--network host${NC}." | tee -a "$LOG_FILE"
    echo -e "    - Or, Ollama listen on all interfaces: ${CYAN}OLLAMA_HOST=0.0.0.0 ollama serve${NC} (or edit service)." | tee -a "$LOG_FILE"
    echo -e "  • Check container logs: ${CYAN}$CONTAINER_CMD logs [container-name]${NC}\n" | tee -a "$LOG_FILE"
  fi
}

# --- Main Function ---
main() {
  init_log
  display_banner
  show_system_info
  echo ""
  if ! user_confirm "Proceed with installation based on current settings/flags?" true; then
    info "Installation aborted by user."
    exit 0
  fi

  check_sudo || exit 1
  detect_package_manager || exit 1
  install_dependencies # Fails script if critical deps not installed

  check_aur_helper         # Arch specific, for Pinokio
  detect_container_runtime # Tries to install Docker if needed

  install_ollama || warning "Ollama installation/setup failed. Model/UI functionality might be affected."

  if ! [ "$NO_MODEL_DOWNLOAD" -eq 1 ]; then
    choose_model # Sets global $MODEL
    download_model || warning "Failed to download model $MODEL. Try manually later."
  else
    info "Model download skipped by flag."
    MODEL="none"
  fi

  # Install UI components (check their own flags and $CONTAINER_CMD)
  install_open_webui
  install_pinokio
  install_lobehub
  install_ollama_gui
  install_enchanted

  show_service_info
  show_connection_instructions

  if ! [ "$NO_RUN_MODEL" -eq 1 ] && [ "$MODEL" != "none" ]; then run_model; fi

  success "All selected installation tasks attempted."
  info "Review output and log file ($LOG_FILE) for errors/warnings."
}

# Run main function
main

