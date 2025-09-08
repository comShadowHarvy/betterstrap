#!/bin/bash

# Simple Ollama Update Script
# Updates all models one by one with progress tracking

# Get list of installed models
echo "Getting list of installed models..."
models=($(ollama list | tail -n +2 | awk '{print $1}'))

if [ ${#models[@]} -eq 0 ]; then
    echo "No models found!"
    exit 1
fi

echo "Found ${#models[@]} models to update:"
for model in "${models[@]}"; do
    echo "  - $model"
done
echo

read -p "Continue with updates? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo "Starting updates..."
echo

updated=0
failed=0

for i in "${!models[@]}"; do
    model="${models[$i]}"
    echo "[$((i+1))/${#models[@]}] Updating: $model"
    
    if ollama pull "$model" >/dev/null 2>&1; then
        echo "✅ SUCCESS: $model"
        ((updated++))
    else
        echo "❌ FAILED: $model"
        ((failed++))
    fi
    echo
done

echo "=== FINAL SUMMARY ==="
echo "✅ Updated: $updated"
echo "❌ Failed: $failed"
echo "📋 Total: ${#models[@]}"
