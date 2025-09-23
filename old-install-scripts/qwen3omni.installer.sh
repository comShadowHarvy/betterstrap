#!/usr/bin/env bash

# =============================================================================
# Qwen3-Omni AI Model Installer with pipx
# 
# A comprehensive installer for Qwen3-Omni multimodal foundation models using
# pipx for isolated Python environments. Supports audio, video, and text inputs
# with audio and text outputs.
#
# Models:
# - Qwen3-Omni-30B-A3B-Instruct: Full multimodal capabilities
# - Qwen3-Omni-30B-A3B-Thinking: Chain-of-thought reasoning
# - Qwen3-Omni-30B-A3B-Captioner: Detailed audio captioning
#
# Requirements: 16GB+ RAM, 20GB+ disk space, optional CUDA GPU
# =============================================================================

set -euo pipefail

# Script metadata
SCRIPT_VERSION="1.0.0"
SCRIPT_NAME="Qwen3-Omni Installer"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration defaults
LOG_DIR="$HOME/.betterstrap/logs"
LOG_FILE="$LOG_DIR/qwen3omni-$(date +%Y%m%d_%H%M%S).log"
MODELS_DIR="$HOME/.cache/huggingface/hub"
MIN_RAM_GB=16
MIN_DISK_GB=20
MIN_CUDA_VERSION="11.8"
MIN_VRAM_GB=10

# Colors for output (matching betterstrap style)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Command line options
NON_INTERACTIVE=0
SKIP_GPU_CHECK=0
SKIP_DOWNLOAD=0
SKIP_TEST=0
FORCE=0
UNINSTALL=0
MODELS_SELECTION=""
HF_TOKEN=""

# Available models
declare -A QWEN_MODELS=(
    ["instruct"]="Qwen/Qwen3-Omni-30B-A3B-Instruct;Full multimodal capabilities with audio/video/text input and audio/text output"
    ["thinking"]="Qwen/Qwen3-Omni-30B-A3B-Thinking;Chain-of-thought reasoning with thinker component"
    ["captioner"]="Qwen/Qwen3-Omni-30B-A3B-Captioner;Detailed audio captioning model"
)

# =============================================================================
# Utility Functions
# =============================================================================

# Logging functions matching betterstrap style
info() {
    echo -e "${BLUE}ℹ️  $*${NC}" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $*${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠️  $*${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ ERROR: $*${NC}" | tee -a "$LOG_FILE"
}

section() {
    echo -e "\n${BOLD}${CYAN}=== $* ===${NC}" | tee -a "$LOG_FILE"
}

# Enhanced fail function with cleanup
fail() {
    error "$*"
    echo -e "${YELLOW}Check the log file for details: $LOG_FILE${NC}"
    
    if [[ "$NON_INTERACTIVE" -eq 1 ]]; then
        echo -e "${RED}Non-interactive mode: Aborting due to error.${NC}" | tee -a "$LOG_FILE"
        cleanup_on_failure
        exit 1
    fi
    
    echo -e "${YELLOW}Last 10 lines from log file:${NC}"
    tail -n 10 "$LOG_FILE" 2>/dev/null || echo "Could not read log file"
    
    local reply
    read -p "Do you want to continue with the rest of the installation? [y/N] " -r reply
    echo
    if [[ ! "$reply" =~ ^[Yy]$ ]]; then
        echo -e "${RED}Installation aborted by user.${NC}" | tee -a "$LOG_FILE"
        cleanup_on_failure
        exit 1
    fi
    return 1
}

# User confirmation with non-interactive support
user_confirm() {
    local prompt="$1"
    local default_yes=${2:-false}
    
    if [[ "$NON_INTERACTIVE" -eq 1 ]]; then
        if [[ "$default_yes" == "true" ]]; then
            info "Non-interactive: Auto-confirming '$prompt' as YES."
            return 0
        else
            info "Non-interactive: Auto-confirming '$prompt' as NO."
            return 1
        fi
    fi
    
    local yn_prompt
    if [[ "$default_yes" == "true" ]]; then
        yn_prompt="[Y/n]"
    else
        yn_prompt="[y/N]"
    fi
    
    local reply
    read -p "$prompt $yn_prompt " -r reply
    echo
    
    if [[ "$default_yes" == "true" ]]; then
        [[ ! "$reply" =~ ^[Nn]$ ]] && return 0 || return 1
    else
        [[ "$reply" =~ ^[Yy]$ ]] && return 0 || return 1
    fi
}

# Display banner
display_banner() {
    echo -e "${BOLD}${BLUE}"
    cat << 'EOF'
  ____                  _____            ____                   _
 / __ \                |___ /           / __ \                 (_)
| |  | |_      _____ _ __ |_ \ ______   | |  | |_ __ ___  _ __  _
| |  | \ \ /\ / / _ \ '_ \__ \|______|  | |  | | '_ ` _ \| '_ \| |
| |__| |\ V  V /  __/ | | |__/          | |__| | | | | | | | | | |
 \____/  \_/\_/ \___|_| |_|____/          \____/|_| |_| |_|_| |_|_|

EOF
    echo -e "${NC}${CYAN}Professional Qwen3-Omni Multimodal AI Model Installer${NC}"
    echo -e "${CYAN}Isolated environments using pipx for better dependency management${NC}\n"
}

# Initialize logging
init_log() {
    mkdir -p "$LOG_DIR"
    cat > "$LOG_FILE" << EOF
=== Qwen3-Omni Installation Log - $(date) ===
Script: $0
Arguments: $*
System: $(uname -a)
User: $(whoami)
Python: $(python3 --version 2>/dev/null || echo "Not found")
EOF
    success "Log file initialized at $LOG_FILE"
}

# Cleanup function for failed installations
cleanup_on_failure() {
    warning "Cleaning up partially installed environments..."
    
    # Remove pipx environments
    for model in "${!QWEN_MODELS[@]}"; do
        local env_name="qwen3-$model"
        if pipx list 2>/dev/null | grep -q "$env_name"; then
            warning "Removing pipx environment: $env_name"
            pipx uninstall "$env_name" 2>/dev/null || true
        fi
    done
    
    # Remove transformers environment
    if pipx list 2>/dev/null | grep -q "transformersqwen"; then
        warning "Removing transformers environment"
        pipx uninstall "transformersqwen" 2>/dev/null || true
    fi
}

# =============================================================================
# Help and Usage
# =============================================================================

show_help() {
    cat << EOF
${BOLD}$SCRIPT_NAME v$SCRIPT_VERSION${NC}

${CYAN}USAGE:${NC}
    $0 [options]

${CYAN}OPTIONS:${NC}
    ${GREEN}General:${NC}
        -h, --help              Show this help message
        -y, --non-interactive   Enable non-interactive mode (auto-confirm)
        --force                 Force reinstallation of existing environments
        --uninstall             Uninstall all Qwen3-Omni environments

    ${GREEN}System:${NC}
        --skip-gpu-check        Skip GPU requirements check
        --models <list>         Comma-separated list of models to install
                               Options: instruct,thinking,captioner
                               Default: instruct

    ${GREEN}Installation:${NC}
        --skip-download         Skip model weight downloads
        --skip-test             Skip post-installation tests
        --hf-token <token>      Hugging Face authentication token
        --models-dir <path>     Custom models directory (default: ~/.cache/huggingface/hub)

${CYAN}EXAMPLES:${NC}
    $0                          # Interactive installation (instruct model)
    $0 -y --models instruct     # Non-interactive, instruct model only
    $0 --models all             # Install all available models
    $0 --uninstall              # Remove all Qwen3-Omni installations

${CYAN}MODELS:${NC}
EOF

    for model in "${!QWEN_MODELS[@]}"; do
        local model_info="${QWEN_MODELS[$model]}"
        local model_id="${model_info%;*}"
        local description="${model_info#*;}"
        printf "    ${YELLOW}%-12s${NC} %s\n" "$model" "$description"
    done

    echo -e "\n${CYAN}REQUIREMENTS:${NC}"
    echo -e "    RAM: ${MIN_RAM_GB}GB+ recommended"
    echo -e "    Disk: ${MIN_DISK_GB}GB+ free space"
    echo -e "    GPU: CUDA ${MIN_CUDA_VERSION}+ with ${MIN_VRAM_GB}GB+ VRAM (optional)"
    echo -e "    Python: 3.10+ with pipx"
}

# =============================================================================
# System Requirements Check
# =============================================================================

check_python() {
    section "Checking Python Requirements"
    
    if ! command -v python3 &> /dev/null; then
        fail "Python 3 is not installed. Please install Python 3.10+ first."
    fi
    
    local python_version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local python_major=$(echo "$python_version" | cut -d. -f1)
    local python_minor=$(echo "$python_version" | cut -d. -f2)
    
    if [[ "$python_major" -lt 3 ]] || [[ "$python_major" -eq 3 && "$python_minor" -lt 10 ]]; then
        fail "Python 3.10+ is required. Found: Python $python_version"
    fi
    
    success "Python $python_version detected"
}

check_pipx() {
    section "Checking pipx Installation"
    
    if ! command -v pipx &> /dev/null; then
        warning "pipx is not installed"
        
        if user_confirm "Install pipx now?" true; then
            info "Installing pipx..."
            python3 -m pip install --user pipx || fail "Failed to install pipx"
            python3 -m pipx ensurepath || warning "Failed to add pipx to PATH - you may need to restart your shell"
            
            # Try to add to current session PATH
            export PATH="$HOME/.local/bin:$PATH"
            
            if ! command -v pipx &> /dev/null; then
                fail "pipx installation failed or not in PATH. Please restart your shell and try again."
            fi
        else
            fail "pipx is required for isolated environment installation"
        fi
    fi
    
    success "pipx is available"
}

check_system_resources() {
    section "Checking System Resources"
    
    # Check RAM
    if [[ -f /proc/meminfo ]]; then
        local total_ram_kb
        total_ram_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        local total_ram_gb=$((total_ram_kb / 1024 / 1024))
        
        if [[ "$total_ram_gb" -lt "$MIN_RAM_GB" ]]; then
            warning "System has ${total_ram_gb}GB RAM, ${MIN_RAM_GB}GB+ recommended"
        else
            success "RAM: ${total_ram_gb}GB (sufficient)"
        fi
    else
        warning "Cannot check system RAM (not on Linux)"
    fi
    
    # Check disk space - create parent directories if they don't exist
    local models_parent_dir
    models_parent_dir="$(dirname "$MODELS_DIR")"
    
    # Create the directory structure if it doesn't exist
    if [[ ! -d "$models_parent_dir" ]]; then
        info "Creating models directory structure: $models_parent_dir"
        if ! mkdir -p "$models_parent_dir"; then
            warning "Could not create models directory: $models_parent_dir"
        fi
    fi
    
    local disk_space_gb
    if [[ -d "$models_parent_dir" ]]; then
        # Use error handling for df command
        if ! disk_space_gb="$(df -BG "$models_parent_dir" 2>/dev/null | awk 'NR==2 {print $4}' | sed 's/G//')"; then
            warning "Could not check disk space for $models_parent_dir, using home directory"
            disk_space_gb="$(df -BG "$HOME" 2>/dev/null | awk 'NR==2 {print $4}' | sed 's/G//' || echo '0')"
        fi
    else
        # Fallback to home directory if models dir creation failed
        disk_space_gb="$(df -BG "$HOME" 2>/dev/null | awk 'NR==2 {print $4}' | sed 's/G//' || echo '0')"
        warning "Using home directory for disk space check"
    fi
    
    # Validate disk_space_gb is a number
    if ! [[ "$disk_space_gb" =~ ^[0-9]+$ ]]; then
        warning "Could not determine disk space (got: '$disk_space_gb'), assuming 0GB"
        disk_space_gb=0
    fi
    
    if [[ "$disk_space_gb" -lt "$MIN_DISK_GB" ]]; then
        warning "Available disk space: ${disk_space_gb}GB, ${MIN_DISK_GB}GB+ recommended"
        if ! user_confirm "Continue with limited disk space?" false; then
            fail "Insufficient disk space"
        fi
    else
        success "Disk space: ${disk_space_gb}GB available"
    fi
}

check_gpu() {
    if [[ "$SKIP_GPU_CHECK" -eq 1 ]]; then
        info "Skipping GPU check as requested"
        return 0
    fi
    
    section "Checking GPU Requirements (Optional)"
    
    if ! command -v nvidia-smi &> /dev/null; then
        warning "nvidia-smi not found - CUDA GPU not detected"
        warning "CPU-only mode will be slower but functional"
        return 0
    fi
    
    # Check CUDA version
    local cuda_version
    if cuda_version=$(nvidia-smi | grep -oP "CUDA Version: \K[\d.]+"); then
        info "CUDA Version: $cuda_version"
        
        # Simple version comparison
        if python3 -c "import sys; sys.exit(0 if float('$cuda_version') >= float('$MIN_CUDA_VERSION') else 1)"; then
            success "CUDA version is sufficient"
        else
            warning "CUDA $cuda_version < $MIN_CUDA_VERSION (recommended)"
        fi
    fi
    
    # Check GPU memory
    local gpu_memory_mb
    if gpu_memory_mb=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1); then
        local gpu_memory_gb=$((gpu_memory_mb / 1024))
        
        if [[ "$gpu_memory_gb" -ge "$MIN_VRAM_GB" ]]; then
            success "GPU Memory: ${gpu_memory_gb}GB available"
        else
            warning "GPU Memory: ${gpu_memory_gb}GB < ${MIN_VRAM_GB}GB (recommended)"
        fi
    fi
}

# =============================================================================
# Installation Functions
# =============================================================================

install_transformers_environment() {
    section "Installing Transformers Environment"
    
    local env_name="transformersqwen"  # pipx suffix creates transformers+qwen = transformersqwen
    
    # Check if environment already exists
    if pipx list 2>/dev/null | grep -q "$env_name"; then
        if [[ "$FORCE" -eq 1 ]]; then
            warning "Removing existing $env_name environment"
            pipx uninstall "$env_name" || warning "Failed to remove existing environment"
        else
            success "$env_name environment already exists (use --force to reinstall)"
            return 0
        fi
    fi
    
    info "Installing transformers from source..."
    
    # Install transformers from Git
    if ! pipx install "git+https://github.com/huggingface/transformers.git" --suffix="qwen"; then
        fail "Failed to install transformers from source"
    fi
    
    # Inject common dependencies
    local deps=(
        "accelerate"
        "qwen-omni-utils"
        "torch"
        "torchaudio"
        "torchvision"
        "einops"
        "protobuf"
        "sentencepiece"
        "pillow"
        "numpy"
    )
    
    info "Injecting common dependencies..."
    for dep in "${deps[@]}"; do
        info "  Adding $dep..."
        pipx inject "$env_name" "$dep" || warning "Failed to inject $dep"
    done
    
    # Add FlashAttention if GPU is available
    if command -v nvidia-smi &> /dev/null && [[ "$SKIP_GPU_CHECK" -eq 0 ]]; then
        info "Adding FlashAttention for GPU acceleration..."
        pipx inject "$env_name" "flash-attn" --pip-args="--no-build-isolation" || warning "Failed to install FlashAttention"
    fi
    
    success "Transformers environment installed"
}

download_model() {
    local model_id="$1"
    local model_name="$2"
    
    section "Downloading Model: $model_name"
    
    if [[ "$SKIP_DOWNLOAD" -eq 1 ]]; then
        info "Skipping model download as requested"
        return 0
    fi
    
    local model_dir="$MODELS_DIR/models--${model_id//\/+/_}"
    
    # Check if model already exists
    if [[ -d "$model_dir" ]] && [[ -f "$model_dir/config.json" ]]; then
        success "Model $model_name already exists"
        return 0
    fi
    
    info "Downloading $model_name (this may take a while)..."
    
    # Use transformersqwen environment for huggingface-cli
    local hf_cmd="pipx run --spec transformersqwen huggingface-cli"
    
    # Prepare download command
    local download_cmd="$hf_cmd download --resume-download --local-dir-use-symlinks"
    
    if [[ -n "$HF_TOKEN" ]]; then
        download_cmd="$download_cmd --token '$HF_TOKEN'"
    fi
    
    download_cmd="$download_cmd '$model_id'"
    
    if ! eval "$download_cmd"; then
        fail "Failed to download $model_name. Check your internet connection and HF token."
    fi
    
    success "Model $model_name downloaded successfully"
}

run_model_test() {
    local model_name="$1"
    local model_id="$2"
    
    if [[ "$SKIP_TEST" -eq 1 ]]; then
        info "Skipping tests as requested"
        return 0
    fi
    
    section "Testing Model: $model_name"
    
    # Create a simple test script
    local test_script="/tmp/qwen_test_$model_name.py"
    cat > "$test_script" << 'EOF'
import sys
import time
from transformers import AutoProcessor, AutoModelForTextToWaveform

def test_model(model_id):
    try:
        print(f"Loading model: {model_id}")
        start_time = time.time()
        
        # Load processor and model
        processor = AutoProcessor.from_pretrained(model_id)
        model = AutoModelForTextToWaveform.from_pretrained(model_id)
        
        load_time = time.time() - start_time
        print(f"Model loaded successfully in {load_time:.2f}s")
        
        # Simple test prompt
        test_prompt = "Hello, this is a test."
        print(f"Testing with prompt: '{test_prompt}'")
        
        inputs = processor(test_prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model.generate(**inputs, max_length=50)
        
        print("✅ Model test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

if __name__ == "__main__":
    model_id = sys.argv[1] if len(sys.argv) > 1 else "Qwen/Qwen3-Omni-30B-A3B-Instruct"
    success = test_model(model_id)
    sys.exit(0 if success else 1)
EOF
    
    info "Running smoke test for $model_name..."
    
    if pipx run --spec transformersqwen python "$test_script" "$model_id"; then
        success "Model $model_name test passed"
    else
        warning "Model $model_name test failed - model may still work"
    fi
    
    rm -f "$test_script"
}

# =============================================================================
# Main Installation Logic
# =============================================================================

install_models() {
    local models_to_install=()
    
    if [[ "$MODELS_SELECTION" == "all" ]]; then
        models_to_install=("${!QWEN_MODELS[@]}")
    elif [[ -n "$MODELS_SELECTION" ]]; then
        IFS=',' read -ra models_to_install <<< "$MODELS_SELECTION"
    else
        models_to_install=("instruct")  # Default
    fi
    
    info "Installing models: ${models_to_install[*]}"
    
    for model in "${models_to_install[@]}"; do
        if [[ -z "${QWEN_MODELS[$model]:-}" ]]; then
            warning "Unknown model: $model (skipping)"
            continue
        fi
        
        local model_info="${QWEN_MODELS[$model]}"
        local model_id="${model_info%;*}"
        local description="${model_info#*;}"
        
        info "Processing model: $model ($description)"
        
        # Download model
        download_model "$model_id" "$model"
        
        # Test model
        run_model_test "$model" "$model_id"
    done
}

show_usage_examples() {
    section "Installation Complete!"
    
    success "Qwen3-Omni has been installed successfully"
    
    echo -e "\n${BOLD}${CYAN}Usage Examples:${NC}"
    echo -e "${YELLOW}Basic usage with pipx:${NC}"
    echo -e "  pipx run --spec transformersqwen python -c \"from transformers import AutoProcessor; print('Ready!')\""
    
    echo -e "\n${YELLOW}Interactive Python session:${NC}"
    echo -e "  pipx run --spec transformersqwen python"
    
    echo -e "\n${YELLOW}Update installation:${NC}"
    echo -e "  pipx upgrade transformersqwen"
    
    echo -e "\n${YELLOW}Uninstall:${NC}"
    echo -e "  $0 --uninstall"
    
    echo -e "\n${BOLD}${CYAN}Next Steps:${NC}"
    echo -e "1. Check the cookbooks at: ${BLUE}https://github.com/QwenLM/Qwen3-Omni/tree/main/cookbooks${NC}"
    echo -e "2. Read the documentation: ${BLUE}https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct${NC}"
    echo -e "3. Join the community: ${BLUE}https://github.com/QwenLM/Qwen${NC}"
    
    echo -e "\n${GREEN}Happy experimenting with Qwen3-Omni! 🚀${NC}"
}

uninstall_all() {
    section "Uninstalling Qwen3-Omni"
    
    warning "This will remove all Qwen3-Omni installations"
    
    if ! user_confirm "Are you sure you want to uninstall everything?" false; then
        info "Uninstall cancelled"
        return 0
    fi
    
    # Remove transformers environment
    if pipx list 2>/dev/null | grep -q "transformersqwen"; then
        info "Removing transformersqwen environment..."
        pipx uninstall "transformersqwen" || warning "Failed to remove transformersqwen"
    fi
    
    # Remove model-specific environments
    for model in "${!QWEN_MODELS[@]}"; do
        local env_name="qwen3-$model"
        if pipx list 2>/dev/null | grep -q "$env_name"; then
            info "Removing $env_name environment..."
            pipx uninstall "$env_name" || warning "Failed to remove $env_name"
        fi
    done
    
    success "Qwen3-Omni uninstalled successfully"
}

# =============================================================================
# Argument Parsing
# =============================================================================

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -y|--non-interactive)
                NON_INTERACTIVE=1
                shift
                ;;
            --skip-gpu-check)
                SKIP_GPU_CHECK=1
                shift
                ;;
            --skip-download)
                SKIP_DOWNLOAD=1
                shift
                ;;
            --skip-test)
                SKIP_TEST=1
                shift
                ;;
            --force)
                FORCE=1
                shift
                ;;
            --uninstall)
                UNINSTALL=1
                shift
                ;;
            --models)
                MODELS_SELECTION="$2"
                shift 2
                ;;
            --hf-token)
                HF_TOKEN="$2"
                shift 2
                ;;
            --models-dir)
                MODELS_DIR="$2"
                shift 2
                ;;
            *)
                error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# =============================================================================
# Main Function
# =============================================================================

main() {
    # Initialize logging
    init_log
    
    # Parse command line arguments
    parse_arguments "$@"
    
    # Show banner
    display_banner
    
    # Handle uninstall
    if [[ "$UNINSTALL" -eq 1 ]]; then
        uninstall_all
        exit 0
    fi
    
    # Check system requirements
    check_python
    check_pipx
    check_system_resources
    check_gpu
    
    # Confirm installation
    if [[ "$NON_INTERACTIVE" -eq 0 ]]; then
        echo -e "\n${CYAN}Ready to install Qwen3-Omni with the following configuration:${NC}"
        echo -e "Models: ${MODELS_SELECTION:-instruct}"
        echo -e "Models directory: $MODELS_DIR"
        echo -e "Skip GPU check: $([[ $SKIP_GPU_CHECK -eq 1 ]] && echo "Yes" || echo "No")"
        echo -e "Skip download: $([[ $SKIP_DOWNLOAD -eq 1 ]] && echo "Yes" || echo "No")"
        echo -e "Skip tests: $([[ $SKIP_TEST -eq 1 ]] && echo "Yes" || echo "No")"
        
        if ! user_confirm "\nProceed with installation?" true; then
            info "Installation cancelled by user"
            exit 0
        fi
    fi
    
    # Set up error handling
    trap 'fail "Installation failed unexpectedly"' ERR
    
    # Main installation steps
    install_transformers_environment
    install_models
    
    # Show usage examples
    show_usage_examples
    
    success "Installation completed successfully!"
}

# =============================================================================
# Script Entry Point
# =============================================================================

# Only run main if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi