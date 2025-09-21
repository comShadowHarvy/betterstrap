# 🖼️ PNG Transparency Tool

**Advanced PNG transparency processor with intelligent white pixel detection**

A powerful utility to make white pixels transparent in PNG images, specifically designed for:
- 🎯 **Text and logos** with white anti-aliasing borders
- 📄 **Documents** with white backgrounds  
- 🖼️ **Icons and graphics** that need clean transparency
- 🔄 **Batch processing** of multiple files
- ⚡ **Single-file processing** without touching other files

## Quick Start

**🎯 Single File Processing (NEW!):**
```bash
./transparent.sh filename.png        # Default processing (good for most cases)
./transparent.sh filename.png 1.8    # Aggressive (perfect for text/logos)
./transparent.sh filename.png 0.8    # Conservative (preserves more details)
```

**📁 Batch Processing (all files in folder):**
```bash
make aggressive    # Process all PNGs with aggressive settings
make inplace      # Process all PNGs with default settings
```

**📄 Traditional (creates output files):**
```bash
make all          # Creates *_transparent.png files
make clean        # Clean up afterward
```

## 🎆 Features

### ✅ **Trace-Free Processing**
- 🏠 **Ephemeral virtual environments** - Created in system temp, auto-deleted
- 📝 **In-place processing** - Overwrites original files safely
- 🚫 **Signal-safe cleanup** - Handles Ctrl+C gracefully
- 🧹 **No leftover files** - Everything cleaned automatically

### 🛠️ **Smart Processing**
- 🎯 **Anti-aliasing detection** - Removes white borders around text perfectly
- 📊 **Perceptual brightness** - Uses human vision weighting (not simple RGB)
- 🔄 **4 detection strategies** - Multiple algorithms for different pixel types
- ⚙️ **Aggressiveness levels** - From conservative (0.8) to ultra (2.5+)
- 🎨 **Threshold tuning** - Adjustable white-pixel detection

### 🛡️ **Safety & Reliability**
- 💾 **Backup support** - Optional `.bak` files when processing in-place
- ⚙️ **Atomic operations** - Temp files, rollback on failure
- ⚡ **Single-file mode** - Process specific files without affecting others
- 📋 **Batch processing** - Handle entire directories efficiently

## Usage

### Command Line

**Single File Processing:**
```bash
# Easy wrapper script
./transparent.sh image.png           # Default (aggressiveness=1.5)
./transparent.sh image.png 1.8       # Aggressive (good for text)
./transparent.sh image.png 0.8       # Conservative

# Direct Python usage
python3 png_to_transparent.py image.png --inplace --aggressiveness 1.8
python3 png_to_transparent.py image.png --inplace --backup  # With backups
python3 png_to_transparent.py image.png --threshold 200     # Custom threshold
```

**Batch Processing:**
```bash
# Process all PNGs in current directory
python3 png_to_transparent.py . --inplace --aggressiveness 1.8

# Clean launcher (handles venv automatically)
./run_clean.sh /path/to/pngs 230 true 1.8   # in-place mode
./run_clean.sh image.png 240 true 1.8       # single file
```

### Makefile Targets
```bash
make help        # Show all options

# Anti-aliasing modes (for text with white borders)
make conservative # Gentle processing (keeps more edge pixels)
make normal      # Standard processing  
make aggressive  # Strong processing - GOOD FOR TEXT
make ultra       # Very aggressive processing

# Standard processing
make inplace     # Process in-place (normal aggressiveness)
make all         # Create *_transparent.png files

# Maintenance
make clean       # Remove output files
make clean-all   # Remove everything including old venv
make test        # Test processing
```

## How It Works

1. **Dependency Check**: Uses system Python if Pillow is installed
2. **Temp Venv**: Creates ephemeral venv in system temp if needed
3. **Processing**: Makes white/light-gray pixels transparent
4. **Cleanup**: Removes venv and temp files automatically

## Migration from Old Version

**Old way (leaves traces):**
```bash
./run.sh        # Creates persistent venv/ directory
make all        # Creates *_transparent.png files
make clean      # Manual cleanup required
```

**New way (trace-free):**
```bash
make inplace    # Everything handled automatically
```

## Algorithm

The tool uses **perceptual brightness** and **multiple detection strategies**:

### Detection Methods:
1. **Perceptual Brightness**: Uses weighted RGB (0.299*R + 0.587*G + 0.114*B) not simple averages
2. **Color Similarity**: Measures how "gray" vs "colorful" pixels are
3. **Anti-aliasing Detection**: Catches light pixels around text borders
4. **Multi-threshold**: Different thresholds for different pixel types

### Aggressiveness Levels:
- **0.5-0.8**: Conservative (preserves more edge details)
- **1.0**: Normal processing
- **1.5-1.8**: Aggressive (good for text with white anti-aliasing)
- **2.0+**: Ultra aggressive (removes almost all light pixels)

Pixels matching any detection strategy become fully transparent while preserving colored content.

## Error Recovery

- **Atomic operations**: Uses temporary files, moves on success
- **Signal handling**: Ctrl+C triggers proper cleanup
- **Rollback on failure**: Original files preserved if processing fails
- **Temp cleanup**: All temporary files removed even on crash

## 📸 Examples

### Perfect for Text/Logos
```bash
# Outlook thumbnail with white background
./transparent.sh thumbnail_Outlook-jxlfr1jr.png 1.8

# Company logo with anti-aliasing
./transparent.sh company_logo.png 1.8

# Document screenshot
./transparent.sh document_screenshot.png 1.5
```

### Before & After
```bash
# Create test images to see results
python3 -c "
from PIL import Image, ImageDraw
img = Image.open('processed_image.png')

# Test on colored backgrounds
red_bg = Image.new('RGBA', img.size, (255, 0, 0, 255))
red_bg.paste(img, (0, 0), img)
red_bg.save('test_on_red.png')

blue_bg = Image.new('RGBA', img.size, (0, 100, 200, 255))
blue_bg.paste(img, (0, 0), img) 
blue_bg.save('test_on_blue.png')
"
```

### Batch Processing
```bash
# Process all company logos
make aggressive

# Process with custom settings
for file in *.png; do
    ./transparent.sh "$file" 1.8
done
```

## 🔧 Troubleshooting

### "Still seeing white pixels"
1. **Increase aggressiveness**: Try `2.0` or `2.5`
2. **Lower threshold**: Use `--threshold 200` instead of default `240`
3. **Check on colored background**: White might be your image viewer

```bash
# More aggressive processing
./transparent.sh image.png 2.5

# Custom threshold
python3 png_to_transparent.py image.png --threshold 200 --aggressiveness 2.0 --inplace
```

### "Removed too much"
1. **Decrease aggressiveness**: Try `0.8` or `1.0`
2. **Increase threshold**: Use `--threshold 250`
3. **Use backup**: Always use `--backup` for important files

```bash
# Conservative processing
./transparent.sh image.png 0.8

# With backup
python3 png_to_transparent.py image.png --inplace --backup --aggressiveness 0.8
```

### "Permission denied"
```bash
# Make scripts executable
chmod +x transparent.sh run_clean.sh png_smart_transparent.py
```

### "Pillow not found"
```bash
# Install Pillow globally
pip install Pillow

# Or use the auto-venv wrapper
./run_clean.sh image.png 240 true 1.8
```

## 📁 File Structure

```
sig/
├── transparent.sh              # 🎯 Easy single-file wrapper
├── png_to_transparent.py       # 🔧 Main processing script
├── png_smart_transparent.py    # 🧠 Smart processing (experimental)
├── run_clean.sh               # 🧹 Clean wrapper with auto-venv
├── Makefile                   # 📋 Batch processing targets
├── requirements.txt           # 📦 Python dependencies
└── README.md                  # 📚 This file
```

## 🚀 Installation

```bash
# Clone or download the files
git clone <repo> sig
cd sig

# Make scripts executable
chmod +x *.sh *.py

# Test with a PNG file
./transparent.sh your_image.png 1.8
```

## 📋 Requirements

- **Python 3.6+**
- **Pillow** (installed automatically in temp venv if needed)
- **Standard Unix tools** (bash, mktemp, find)
- **Linux/macOS** (tested on CachyOS Linux)

## 📝 License

MIT License - Feel free to use, modify, and distribute.

## 🤝 Contributing

Contributions welcome! This tool was built to solve real transparency issues with text and logos.

---

**⭐ Star this repo if it helped you clean up your PNG transparency issues!**
