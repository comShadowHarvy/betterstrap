#!/bin/bash

# Ollama Model Update Script
# Updates all currently installed models to their latest versions

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    cat << EOF
Ollama Model Update Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help      Show this help message
    -l, --list      List currently installed models without updating
    -y, --yes       Skip confirmation prompt and update all models
    --dry-run       Show what would be updated without actually updating

EXAMPLES:
    $0              # List models and prompt for confirmation
    $0 -y           # Update all models without confirmation
    $0 --list       # Just show installed models
    $0 --dry-run    # Show what would be updated

EOF
}

list_models() {
    echo -e "${BLUE}=== CURRENTLY INSTALLED MODELS ===${NC}"
    echo
    
    if ! command -v ollama >/dev/null 2>&1; then
        echo -e "${RED}❌ Ollama is not installed${NC}"
        return 1
    fi
    
    # Get model list
    local models
    if ! models=$(ollama list 2>/dev/null); then
        echo -e "${RED}❌ Failed to get model list. Is Ollama running?${NC}"
        return 1
    fi
    
    # Check if any models are installed
    local model_count
    model_count=$(echo "$models" | tail -n +2 | wc -l)
    
    if [ "$model_count" -eq 0 ]; then
        echo -e "${YELLOW}⚠️  No models are currently installed${NC}"
        return 0
    fi
    
    echo "$models"
    echo
    echo -e "${GREEN}Total models: $model_count${NC}"
}

get_installed_models() {
    # Get list of installed model names (first column, skip header)
    ollama list 2>/dev/null | tail -n +2 | awk '{print $1}' | grep -v '^$' || true
}

update_models() {
    local skip_confirm=$1
    local dry_run=$2
    
    echo -e "${BLUE}=== MODEL UPDATE PROCESS ===${NC}"
    echo
    
    # Get installed models
    local models
    readarray -t models < <(get_installed_models)
    
    if [ ${#models[@]} -eq 0 ]; then
        echo -e "${YELLOW}⚠️  No models found to update${NC}"
        return 0
    fi
    
    if [ "$dry_run" = true ]; then
        echo -e "${YELLOW}=== DRY RUN MODE ===${NC}"
        echo "The following models would be updated:"
        for model in "${models[@]}"; do
            echo "  - $model"
        done
        echo
        echo -e "${BLUE}Total models that would be updated: ${#models[@]}${NC}"
        return 0
    fi
    
    echo "Found ${#models[@]} models to update:"
    for model in "${models[@]}"; do
        echo "  - $model"
    done
    echo
    
    if [ "$skip_confirm" = false ]; then
        echo -e "${YELLOW}⚠️  This will download the latest versions of all models.${NC}"
        echo -e "${YELLOW}   Large models may take significant time and bandwidth.${NC}"
        echo
        read -p "Do you want to proceed? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}❌ Update cancelled${NC}"
            return 0
        fi
        echo
    fi
    
    # Update each model
    local updated=0
    local failed=0
    local failed_models=()
    
    echo -e "${BLUE}🚀 Starting model updates...${NC}"
    echo
    
    for model in "${models[@]}"; do
        echo -e "${BLUE}📥 Updating: $model${NC}"
        
        # Disable exit-on-error temporarily for this command
        set +e
        local pull_output
        pull_output=$(ollama pull "$model" 2>&1)
        local exit_code=$?
        set -e
        
        if [ $exit_code -eq 0 ]; then
            echo -e "${GREEN}✅ Successfully updated: $model${NC}"
            ((updated++))
        else
            echo -e "${RED}❌ Failed to update: $model${NC}"
            echo -e "${RED}   Error: $pull_output${NC}"
            ((failed++))
            failed_models+=("$model")
        fi
        echo
    done
    
    # Summary
    echo -e "${BLUE}=== UPDATE SUMMARY ===${NC}"
    echo -e "${GREEN}✅ Successfully updated: $updated/${#models[@]}${NC}"
    
    if [ $failed -gt 0 ]; then
        echo -e "${RED}❌ Failed updates: $failed${NC}"
        echo "Failed models:"
        for model in "${failed_models[@]}"; do
            echo "  - $model"
        done
        echo -e "${YELLOW}Note: Script will continue with remaining updates even if some fail.${NC}"
        # Don't exit with error code - we want to show the summary
        # return 1
    else
        echo -e "${GREEN}🎉 All models updated successfully!${NC}"
    fi
}

ensure_ollama_running() {
    if ! pgrep -x "ollama" > /dev/null; then
        echo -e "${YELLOW}🚀 Starting Ollama service...${NC}"
        ollama serve &
        sleep 3
        echo -e "${GREEN}✅ Ollama service started${NC}"
        echo
    fi
}

main() {
    local list_only=false
    local skip_confirm=false
    local dry_run=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -l|--list)
                list_only=true
                shift
                ;;
            -y|--yes)
                skip_confirm=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            *)
                echo -e "${RED}❌ Unknown option: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo -e "${BLUE}=== OLLAMA MODEL UPDATER ===${NC}"
    echo
    
    # Ensure Ollama is running
    ensure_ollama_running
    
    # List models
    if ! list_models; then
        exit 1
    fi
    
    # If list-only mode, exit here
    if [ "$list_only" = true ]; then
        exit 0
    fi
    
    echo
    
    # Update models
    update_models "$skip_confirm" "$dry_run"
}

# Run main function with all arguments
main "$@"
