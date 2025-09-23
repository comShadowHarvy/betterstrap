# Qwen3-Omni AI Installer

## Overview

Professional installer for Qwen3-Omni multimodal AI models using pipx for isolated environments. Supports audio, video, and text inputs with audio and text outputs.

## Quick Start

```bash
# Basic installation (instruct model)
./qwen3omni.installer.sh

# Non-interactive with all models
./qwen3omni.installer.sh -y --models all

# Install specific models
./qwen3omni.installer.sh --models instruct,captioner

# Uninstall everything
./qwen3omni.installer.sh --uninstall
```

## Models Available

- **instruct**: Qwen3-Omni-30B-A3B-Instruct - Full multimodal capabilities
- **thinking**: Qwen3-Omni-30B-A3B-Thinking - Chain-of-thought reasoning  
- **captioner**: Qwen3-Omni-30B-A3B-Captioner - Detailed audio captioning

## System Requirements

- **Python**: 3.10+ with pipx
- **RAM**: 16GB+ recommended
- **Disk Space**: 20GB+ free
- **GPU**: CUDA 11.8+ with 10GB+ VRAM (optional, CPU works but slower)

## Features

- ✅ **Isolated environments** using pipx (no dependency conflicts)
- ✅ **Automatic dependency management** (transformers, torch, accelerate, etc.)
- ✅ **GPU detection and optimization** (FlashAttention when available)
- ✅ **System requirements check** (RAM, disk, CUDA)
- ✅ **Resume-safe downloads** with Hugging Face Hub
- ✅ **Post-install testing** with smoke tests
- ✅ **Professional error handling** with cleanup on failure
- ✅ **Non-interactive mode** for automation
- ✅ **Complete uninstall option**

## Advanced Usage

```bash
# Skip GPU checks (for CPU-only systems)
./qwen3omni.installer.sh --skip-gpu-check

# Skip downloads (use cached models)
./qwen3omni.installer.sh --skip-download

# Use custom models directory
./qwen3omni.installer.sh --models-dir /custom/path

# Force reinstall existing environments
./qwen3omni.installer.sh --force

# Use Hugging Face token for private models
./qwen3omni.installer.sh --hf-token your_token_here
```

## Using Installed Models

```bash
# Start interactive Python session with Qwen3-Omni
pipx run --spec transformers-qwen python

# Run a quick test
pipx run --spec transformers-qwen python -c "from transformers import AutoProcessor; print('Ready!')"

# Update installation
pipx upgrade transformers-qwen
```

## Python Example

```python
from transformers import AutoProcessor, AutoModelForTextToWaveform

# Load model and processor
processor = AutoProcessor.from_pretrained("Qwen/Qwen3-Omni-30B-A3B-Instruct")
model = AutoModelForTextToWaveform.from_pretrained("Qwen/Qwen3-Omni-30B-A3B-Instruct")

# Process input
inputs = processor("Hello, this is a test of Qwen3-Omni", return_tensors="pt")

# Generate output
with torch.no_grad():
    outputs = model.generate(**inputs)
```

## Troubleshooting

- **pipx not found**: Script will automatically install it
- **CUDA not detected**: Install NVIDIA drivers and CUDA toolkit
- **Out of memory**: Use `--skip-gpu-check` for CPU-only mode
- **Download fails**: Check internet connection and use `--hf-token` if needed
- **Permission errors**: Ensure you have write access to `~/.cache/huggingface/`

## Links

- [Qwen3-Omni Documentation](https://huggingface.co/Qwen/Qwen3-Omni-30B-A3B-Instruct)
- [Cookbooks & Examples](https://github.com/QwenLM/Qwen3-Omni/tree/main/cookbooks)
- [Qwen Community](https://github.com/QwenLM/Qwen)

---

**Created**: 2025-09-23  
**Version**: 1.0.0  
**Author**: Betterstrap Project