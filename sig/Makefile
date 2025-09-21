.PHONY: all clean inplace clean-all test help conservative normal aggressive ultra

# Default: process files creating *_transparent.png (original behavior)
all:
	./run_clean.sh . 230 false

# In-place processing (no traces left behind) - default aggressiveness
inplace:
	./run_clean.sh . 230 true 1.5
	@echo "Files processed in-place. No traces left."

# Different aggressiveness levels for anti-aliasing
conservative:
	./run_clean.sh . 230 true 0.8
	@echo "Conservative processing (preserves more edge pixels)"

normal:
	./run_clean.sh . 230 true 1.0
	@echo "Normal processing"

aggressive:
	./run_clean.sh . 230 true 1.8
	@echo "Aggressive processing (removes more anti-aliasing)"

ultra:
	./run_clean.sh . 230 true 2.5
	@echo "Ultra aggressive processing (removes almost all light pixels)"

# Clean up any leftover files
clean:
	rm -f *_transparent.png *.tmp *.bak
	@echo "Cleaned up output files"

clean-all: clean
	rm -rf venv
	@echo "Cleaned up everything including old venv"

# Test with verbose output
test:
	@echo "Testing transparency processing..."
	./run_clean.sh . 230 true

help:
	@echo "Available targets:"
	@echo "  all         - Process PNGs creating *_transparent.png files (preserves output)"
	@echo "  inplace     - Process PNGs in-place, leave no traces (RECOMMENDED)"
	@echo ""
	@echo "Anti-aliasing modes (for text with white borders):"
	@echo "  conservative - Gentle processing (aggressiveness=0.8)"
	@echo "  normal      - Standard processing (aggressiveness=1.0)"
	@echo "  aggressive  - Strong processing (aggressiveness=1.8) - GOOD FOR TEXT"
	@echo "  ultra       - Very strong processing (aggressiveness=2.5)"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean       - Remove output files (*_transparent.png, *.tmp, *.bak)"
	@echo "  clean-all   - Remove all generated files including old venv"
	@echo "  test        - Test processing with current settings"
	@echo "  help        - Show this help message"
