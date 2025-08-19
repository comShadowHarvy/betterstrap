#!/bin/sh


# Exit immediately if a command exits with a non-zero status.
set -e

# --- Install Ollama ---
echo "--- Installing Ollama ---"
curl -fsSL https://ollama.com/install.sh | sh

# --- Check if Ollama is running ---
if ! pgrep -x "ollama" > /dev/null
then
    echo "--- Starting Ollama service ---"
    ollama serve &
    # Give the service a moment to start
    sleep 5
fi

# --- Model List ---
# Add or remove models from this list as needed
models=(
    "huihui_ai/am-thinking-abliterate:latest"
    "goekdenizguelmez/JOSIEFIED-Qwen2.5:latest"
    "goekdenizguelmez/JOSIEFIED-Qwen3:latest"
    "huihui_ai/exaone-deep-abliterated:latest"
    "huihui_ai/jan-nano-abliterated:latest"
    "StormSplits/shira:latest"
    "thirdeyeai/SmolLM2-1.7B-Instruct-Uncensored.gguf:F16"
    "llama3:latest"
    "qwen3:8b"
    "llama3:8b"
)

# --- Pull Models ---
echo "--- Pulling Ollama models ---"
for model in "${models[@]}"
do
    echo "--- Pulling ${model} ---"
    ollama pull "${model}"
done

echo "--- All models have been pulled successfully! ---"

# Optional: stop the ollama service if you started it in the background
# pkill -f "ollama serve"
