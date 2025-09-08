#!/bin/bash

# Ollama Model Management Script with Categories
# Supports selective installation by model size categories

# Exit immediately if a command exits with a non-zero status
set -euo pipefail

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Model categories organized by size and resource requirements
declare -A MODEL_CATEGORIES=(
    # Large models (>7GB) - High resource requirements
    [large]="wizardlm-uncensored:13b gpt-oss:20b huihui_ai/am-thinking-abliterate:latest"
    
    # Medium models (3-8GB) - Moderate resource requirements  
    [medium]="kiloxiix/evere.8b-u3-base:latest GandalfBaum/mistralDAN:latest qwen3:8b llama3:8b llama3:latest StormSplits/shira:latest huihui_ai/exaone-deep-abliterated:latest goekdenizguelmez/JOSIEFIED-Qwen3:latest goekdenizguelmez/JOSIEFIED-Qwen2.5:latest thirdeyeai/SmolLM2-1.7B-Instruct-Uncensored.gguf:F16"
    
    # Small models (<3GB) - Low resource requirements
    [small]="smollm2:1.7b smollm:1.7b demitrechee/undres-ai-remover:latest huihui_ai/jan-nano-abliterated:latest"
)

# Storage requirements by category (approximate)
declare -A STORAGE_REQUIREMENTS=(
    [large]="~39GB"
    [medium]="~47GB" 
    [small]="~7GB"
    [all]="~93GB"
)

# ==============================================================================
# FUNCTIONS
# ==============================================================================

show_help() {
    cat << EOF
Ollama Model Management Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help      Show this help message
    -l, --large     Install large models only (~39GB): wizardlm-uncensored:13b, gpt-oss:20b, am-thinking-abliterate
    -m, --medium    Install medium models only (~47GB): llama3, qwen3, various 8b models
    -s, --small     Install small models only (~7GB): smollm variants, nano models
    -a, --all       Install all models (~93GB) [DEFAULT]
    --list          Show available models by category without installing
    --dry-run       Show what would be installed without actually installing

EXAMPLES:
    $0                    # Install all models
    $0 -s                 # Install only small models
    $0 -m -s              # Install medium and small models
    $0 --list             # Show available models
    $0 --dry-run -l       # Show what large models would be installed

CATEGORIES:
    Large:  High-performance models requiring significant resources (13b-20b+ params)
    Medium: Balanced performance and resource usage (7b-8b params)
    Small:  Fast, lightweight models for basic tasks (1.7b params)

EOF
}

list_models() {
    echo "=== AVAILABLE MODEL CATEGORIES ==="
    echo
    for category in large medium small; do
        echo "${category^^} MODELS (Storage: ${STORAGE_REQUIREMENTS[$category]}):"
        for model in ${MODEL_CATEGORIES[$category]}; do
            echo "  - $model"
        done
        echo
    done
}

install_ollama() {
    if command -v ollama >/dev/null 2>&1; then
        echo "✓ Ollama is already installed"
    else
        echo "📥 Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
        echo "✓ Ollama installed successfully"
    fi
}

start_ollama_service() {
    if ! pgrep -x "ollama" > /dev/null; then
        echo "🚀 Starting Ollama service..."
        ollama serve &
        # Give the service a moment to start
        sleep 5
        echo "✓ Ollama service started"
    else
        echo "✓ Ollama service is already running"
    fi
}

stop_ollama_service() {
    if pgrep -x "ollama" > /dev/null; then
        echo "⏹️  Stopping Ollama service..."
        pkill -f "ollama serve" || true
        sleep 2
    fi
}

build_model_list() {
    local categories=("$@")
    local models=()
    local temp_file
    
    # If no categories specified, use all
    if [ ${#categories[@]} -eq 0 ]; then
        categories=("large" "medium" "small")
    fi
    
    # Collect all models from specified categories
    for category in "${categories[@]}"; do
        if [[ -n "${MODEL_CATEGORIES[$category]:-}" ]]; then
            for model in ${MODEL_CATEGORIES[$category]}; do
                models+=("$model")
            done
        fi
    done
    
    # Remove duplicates while preserving order
    temp_file=$(mktemp)
    printf '%s\n' "${models[@]}" | awk '!seen[$0]++' > "$temp_file"
    mapfile -t models < "$temp_file"
    rm "$temp_file"
    
    printf '%s\n' "${models[@]}"
}

calculate_storage() {
    local categories=("$@")
    local total_size="Combined storage from selected categories"
    
    if [ ${#categories[@]} -eq 0 ] || [[ " ${categories[*]} " =~ " large " ]] && [[ " ${categories[*]} " =~ " medium " ]] && [[ " ${categories[*]} " =~ " small " ]]; then
        echo "${STORAGE_REQUIREMENTS[all]}"
    else
        echo "$total_size"
    fi
}

pull_models() {
    local models=("$@")
    local failed_models=()
    local success_count=0
    
    if [ ${#models[@]} -eq 0 ]; then
        echo "❌ No models specified for installation"
        return 1
    fi
    
    echo "📊 Installing ${#models[@]} models..."
    echo "💾 Estimated storage required: $(calculate_storage)"
    echo
    
    for model in "${models[@]}"; do
        echo "📥 Pulling: $model"
        if ollama pull "$model"; then
            echo "✓ Successfully pulled: $model"
            ((success_count++))
        else
            echo "❌ Failed to pull: $model"
            failed_models+=("$model")
        fi
        echo
    done
    
    echo "=== INSTALLATION SUMMARY ==="
    echo "✅ Successful: $success_count/${#models[@]}"
    
    if [ ${#failed_models[@]} -gt 0 ]; then
        echo "❌ Failed models:"
        for model in "${failed_models[@]}"; do
            echo "  - $model"
        done
        return 1
    fi
    
    echo "🎉 All models installed successfully!"
}

# ==============================================================================
# MAIN SCRIPT
# ==============================================================================

main() {
    local categories=()
    local dry_run=false
    local list_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -l|--large)
                categories+=("large")
                shift
                ;;
            -m|--medium)
                categories+=("medium")
                shift
                ;;
            -s|--small)
                categories+=("small")
                shift
                ;;
            -a|--all)
                categories=("large" "medium" "small")
                shift
                ;;
            --list)
                list_only=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            *)
                echo "❌ Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Handle list-only mode
    if [ "$list_only" = true ]; then
        list_models
        exit 0
    fi
    
    # Default to all categories if none specified
    if [ ${#categories[@]} -eq 0 ]; then
        categories=("large" "medium" "small")
    fi
    
    # Build model list
    readarray -t models < <(build_model_list "${categories[@]}")
    
    # Handle dry-run mode
    if [ "$dry_run" = true ]; then
        echo "=== DRY RUN MODE ==="
        echo "Selected categories: ${categories[*]}"
        echo "Models that would be installed:"
        for model in "${models[@]}"; do
            echo "  - $model"
        done
        echo "Estimated storage: $(calculate_storage "${categories[@]}")"
        exit 0
    fi
    
    # Show selected configuration
    echo "=== OLLAMA SETUP ==="
    echo "Selected categories: ${categories[*]}"
    echo "Models to install: ${#models[@]}"
    echo "Estimated storage: $(calculate_storage "${categories[@]}")"
    echo
    
    # Install and configure Ollama
    install_ollama
    start_ollama_service
    
    # Install models
    echo "=== MODEL INSTALLATION ==="
    if ! pull_models "${models[@]}"; then
        echo "⚠️  Some models failed to install. Check the summary above."
        exit 1
    fi
    
    echo
    echo "🎉 Setup complete! Use 'ollama list' to verify installed models."
}

# Run main function with all arguments
main "$@"
