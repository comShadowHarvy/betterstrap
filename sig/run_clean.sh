#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*" >&2; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $*" >&2; }

# Cleanup function
cleanup() {
    local exit_code=$?
    
    if [[ -n "${TEMP_VENV:-}" && -d "$TEMP_VENV" ]]; then
        log "Cleaning up temporary venv: $TEMP_VENV"
        rm -rf "$TEMP_VENV" || warn "Failed to remove temp venv"
    fi
    
    if [[ "${CLEAN_OUTPUT:-true}" == "true" ]]; then
        log "Cleaning up output files (*_transparent.png)"
        find "${WORK_DIR}" -name "*_transparent.png" -delete 2>/dev/null || true
    fi
    
    exit $exit_code
}

# Set up signal handling
trap cleanup EXIT
trap 'exit 130' INT TERM

# Parse command line arguments
WORK_DIR="${1:-.}"
THRESHOLD="${2:-230}"
CLEAN_OUTPUT="${3:-true}"
AGGRESSIVENESS="${4:-1.5}"  # Default to more aggressive for better anti-aliasing

if [[ ! -f "$WORK_DIR" && ! -d "$WORK_DIR" ]]; then
    error "Path '$WORK_DIR' does not exist"
    exit 1
fi

# Check if we need to create a temporary venv
if python3 -c "import PIL" 2>/dev/null; then
    log "Using system Python (Pillow already installed)"
    PYTHON="python3"
else
    log "Pillow not found, creating temporary virtual environment"
    TEMP_VENV="$(mktemp -d -t betterstrap_venv_XXXXXX)"
    
    log "Creating venv in: $TEMP_VENV"
    python3 -m venv "$TEMP_VENV" >/dev/null
    
    log "Installing Pillow"
    "$TEMP_VENV/bin/pip" install --quiet Pillow
    
    PYTHON="$TEMP_VENV/bin/python"
fi

# Check if WORK_DIR is a single file or directory
if [[ -f "$WORK_DIR" ]]; then
    if [[ ! "$WORK_DIR" =~ \.png$ ]]; then
        error "File '$WORK_DIR' is not a PNG file"
        exit 1
    fi
    log "Processing single file: $WORK_DIR"
else
    # Check for PNG files in directory
    if ! find "$WORK_DIR" -maxdepth 1 -name "*.png" -type f | grep -q .; then
        warn "No PNG files found in '$WORK_DIR'"
        exit 0
    fi
    log "Processing directory: $WORK_DIR"
fi

# Run the processing
log "Processing '$WORK_DIR' with threshold $THRESHOLD, aggressiveness $AGGRESSIVENESS"
if [[ "$CLEAN_OUTPUT" == "true" ]]; then
    # Use in-place mode when cleaning output
    "$PYTHON" "$(dirname "$0")/png_to_transparent.py" "$WORK_DIR" --threshold "$THRESHOLD" --aggressiveness "$AGGRESSIVENESS" --inplace
else
    # Use original mode when preserving output
    "$PYTHON" "$(dirname "$0")/png_to_transparent.py" "$WORK_DIR" --threshold "$THRESHOLD" --aggressiveness "$AGGRESSIVENESS"
fi

if [[ "$CLEAN_OUTPUT" == "true" ]]; then
    success "Processing complete. Temporary files will be cleaned up."
else
    success "Processing complete. Output files (*_transparent.png) preserved."
fi