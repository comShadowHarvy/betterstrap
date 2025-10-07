#!/bin/bash

# Docker GPU Helper Script
# Easily run Docker containers with dual GPU support (NVIDIA + Intel)
# Usage: ./docker-gpu.sh [OPTIONS] IMAGE [COMMAND]

set -e

# Configuration
ENABLE_NVIDIA=true
ENABLE_INTEL=true
CONTAINER_NAME=""
DETACHED=false
INTERACTIVE=false
TTY=false
REMOVE=false
EXTRA_ARGS=""

# Help function
show_help() {
    echo "Docker GPU Helper - Run containers with dual GPU support"
    echo ""
    echo "Usage: $0 [OPTIONS] IMAGE [COMMAND]"
    echo ""
    echo "GPU Options:"
    echo "  --nvidia-only      Enable only NVIDIA GPU"
    echo "  --intel-only       Enable only Intel GPU"
    echo "  --no-gpu           Disable all GPU access"
    echo ""
    echo "Docker Options:"
    echo "  --name NAME        Set container name"
    echo "  -d, --detach       Run in background"
    echo "  -i, --interactive  Keep STDIN open"
    echo "  -t, --tty          Allocate pseudo-TTY"
    echo "  --rm               Remove container when it exits"
    echo ""
    echo "Examples:"
    echo "  $0 ubuntu:20.04 nvidia-smi                    # Test NVIDIA GPU"
    echo "  $0 --intel-only ubuntu:20.04 vainfo           # Test Intel GPU"
    echo "  $0 --name jellyfin -d jellyfin:latest         # Run Jellyfin with both GPUs"
    echo "  $0 --rm -it ubuntu:20.04 /bin/bash            # Interactive shell with GPU access"
    echo ""
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --nvidia-only)
            ENABLE_NVIDIA=true
            ENABLE_INTEL=false
            shift
            ;;
        --intel-only)
            ENABLE_NVIDIA=false
            ENABLE_INTEL=true
            shift
            ;;
        --no-gpu)
            ENABLE_NVIDIA=false
            ENABLE_INTEL=false
            shift
            ;;
        --name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        -d|--detach)
            DETACHED=true
            shift
            ;;
        -i|--interactive)
            INTERACTIVE=true
            shift
            ;;
        -t|--tty)
            TTY=true
            shift
            ;;
        --rm)
            REMOVE=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        -*)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            # This is the image name, stop parsing options
            break
            ;;
    esac
done

# Check if image is provided
if [ $# -eq 0 ]; then
    echo "Error: Docker image not specified"
    echo "Use --help for usage information"
    exit 1
fi

IMAGE="$1"
shift

# Build Docker command
DOCKER_CMD="docker run"

# Add container name if specified
if [ -n "$CONTAINER_NAME" ]; then
    DOCKER_CMD="$DOCKER_CMD --name $CONTAINER_NAME"
fi

# Add run options
if [ "$DETACHED" = true ]; then
    DOCKER_CMD="$DOCKER_CMD -d"
fi

if [ "$INTERACTIVE" = true ]; then
    DOCKER_CMD="$DOCKER_CMD -i"
fi

if [ "$TTY" = true ]; then
    DOCKER_CMD="$DOCKER_CMD -t"
fi

if [ "$REMOVE" = true ]; then
    DOCKER_CMD="$DOCKER_CMD --rm"
fi

# Add GPU support
GPU_ENABLED=false

if [ "$ENABLE_NVIDIA" = true ]; then
    # Check if NVIDIA GPU is available
    if lspci | grep -i nvidia >/dev/null 2>&1; then
        if command -v nvidia-smi >/dev/null 2>&1; then
            DOCKER_CMD="$DOCKER_CMD --gpus all"
            GPU_ENABLED=true
            echo "🎮 NVIDIA GPU enabled"
        else
            echo "⚠️  NVIDIA GPU detected but drivers not available"
        fi
    elif [ "$ENABLE_INTEL" = false ]; then
        echo "⚠️  NVIDIA GPU not found"
    fi
fi

if [ "$ENABLE_INTEL" = true ]; then
    # Check if Intel GPU render devices exist
    if [ -d "/dev/dri" ] && [ -n "$(ls -A /dev/dri/render* 2>/dev/null)" ]; then
        DOCKER_CMD="$DOCKER_CMD --device /dev/dri:/dev/dri -e LIBVA_DRIVER_NAME=iHD"
        GPU_ENABLED=true
        echo "🔧 Intel GPU enabled"
    elif [ "$ENABLE_NVIDIA" = false ]; then
        echo "⚠️  Intel GPU render devices not found"
    fi
fi

if [ "$GPU_ENABLED" = false ] && ([ "$ENABLE_NVIDIA" = true ] || [ "$ENABLE_INTEL" = true ]); then
    echo "⚠️  No GPUs available - running without GPU acceleration"
fi

# Add image and command
DOCKER_CMD="$DOCKER_CMD $IMAGE"

# Add any remaining arguments as the command
if [ $# -gt 0 ]; then
    DOCKER_CMD="$DOCKER_CMD $*"
fi

# Show the command being executed (for debugging)
echo "🐳 Running: $DOCKER_CMD"
echo ""

# Execute the command
eval "$DOCKER_CMD"