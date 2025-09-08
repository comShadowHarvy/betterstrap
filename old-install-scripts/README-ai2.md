# Ollama Model Management Script (ai2.sh)

An enhanced script for managing Ollama AI models with categorization by size and resource requirements.

## Features

- 🏷️ **Model Categorization**: Models organized by size (large, medium, small)
- 🎯 **Selective Installation**: Install specific categories based on your needs
- 📊 **Storage Estimation**: Shows approximate disk space requirements
- 🔍 **Dry Run Mode**: Preview what would be installed without actually installing
- 📋 **Model Listing**: View available models by category
- ✅ **Installation Tracking**: Shows success/failure status for each model
- 🚀 **Service Management**: Automatically manages Ollama service

## Usage

```bash
# Install all models (default behavior)
./ai2.sh

# Install only small models (recommended for limited storage)
./ai2.sh -s

# Install medium and small models
./ai2.sh -m -s

# Install only large models (requires significant storage)
./ai2.sh -l

# Preview what would be installed (dry run)
./ai2.sh --dry-run -m

# List available models by category
./ai2.sh --list

# Show help
./ai2.sh --help
```

## Model Categories

### Large Models (~39GB)
High-performance models requiring significant resources:
- `wizardlm-uncensored:13b` (7.4 GB)
- `gpt-oss:20b` (13 GB)  
- `huihui_ai/am-thinking-abliterate:latest` (19 GB)

### Medium Models (~47GB)
Balanced performance and resource usage:
- `kiloxiix/evere.8b-u3-base:latest` (4.9 GB)
- `GandalfBaum/mistralDAN:latest` (4.4 GB)
- `qwen3:8b` (5.2 GB)
- `llama3:8b` (4.7 GB)
- `llama3:latest` (4.7 GB)
- `StormSplits/shira:latest` (4.7 GB)
- `huihui_ai/exaone-deep-abliterated:latest` (4.8 GB)
- `goekdenizguelmez/JOSIEFIED-Qwen3:latest` (5.0 GB)
- `goekdenizguelmez/JOSIEFIED-Qwen2.5:latest` (4.7 GB)
- `thirdeyeai/SmolLM2-1.7B-Instruct-Uncensored.gguf:F16` (3.6 GB)

### Small Models (~7GB)
Fast, lightweight models for basic tasks:
- `smollm2:1.7b` (1.8 GB)
- `smollm:1.7b` (990 MB)
- `demitrechee/undres-ai-remover:latest` (2.0 GB)
- `huihui_ai/jan-nano-abliterated:latest` (2.5 GB)

## Command Line Options

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help message |
| `-l, --large` | Install large models only |
| `-m, --medium` | Install medium models only |
| `-s, --small` | Install small models only |
| `-a, --all` | Install all models (default) |
| `--list` | Show available models by category |
| `--dry-run` | Show what would be installed without installing |

## Storage Requirements

- **Small only**: ~7GB
- **Medium only**: ~47GB  
- **Large only**: ~39GB
- **All models**: ~93GB

## Examples

### Common Use Cases

```bash
# For systems with limited storage (< 10GB available)
./ai2.sh -s

# For development/testing with moderate storage (< 50GB available)  
./ai2.sh -m

# For production with ample storage (> 100GB available)
./ai2.sh

# Check what small + medium models would require
./ai2.sh --dry-run -s -m

# See all available models organized by category
./ai2.sh --list
```

### Advanced Usage

```bash
# Install specific combinations
./ai2.sh -l -s          # Large and small models only
./ai2.sh -m -s          # Medium and small models only

# Preview installations
./ai2.sh --dry-run -l   # Preview large models
./ai2.sh --dry-run      # Preview all models
```

## Requirements

- **Operating System**: Linux/macOS/WSL
- **Shell**: Bash 4.0+ (uses associative arrays)
- **Network**: Internet connection for downloading models
- **Storage**: Variable based on selected categories

## Installation Status

The script provides detailed feedback during installation:

- ✅ **Success indicators**: Green checkmarks for completed installations
- ❌ **Failure indicators**: Red X marks for failed installations  
- 📊 **Progress tracking**: Shows current model being installed
- 📋 **Summary report**: Final count of successful/failed installations

## Troubleshooting

### Common Issues

1. **Service not starting**: The script automatically manages Ollama service startup
2. **Insufficient storage**: Use `--dry-run` to check storage requirements first
3. **Network issues**: Failed downloads will be reported in the summary
4. **Permission issues**: Run with appropriate permissions for Ollama installation

### Verification

After installation, verify models are available:

```bash
ollama list
```

This should show all successfully installed models.

## Customization

To add new models or modify categories, edit the `MODEL_CATEGORIES` associative array in the script:

```bash
declare -A MODEL_CATEGORIES=(
    [large]="your-large-model:latest"
    [medium]="your-medium-model:8b" 
    [small]="your-small-model:1.7b"
)
```

Update the `STORAGE_REQUIREMENTS` array accordingly to reflect storage estimates.
