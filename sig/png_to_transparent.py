import os
import argparse
import shutil
from pathlib import Path
from PIL import Image

def make_white_transparent(input_path, output_path, threshold=230, aggressiveness=1.0):
    """Make white/light pixels transparent with anti-aliasing support.
    
    Args:
        input_path: Input PNG file
        output_path: Output PNG file  
        threshold: Base threshold for white detection (0-255)
        aggressiveness: How aggressive to be (0.5=conservative, 2.0=very aggressive)
    """
    img = Image.open(input_path).convert("RGBA")
    datas = img.getdata()
    new_data = []
    
    # Adjust thresholds based on aggressiveness
    main_threshold = max(180, threshold - (aggressiveness - 1.0) * 30)
    gray_threshold = max(160, 220 - (aggressiveness - 1.0) * 40)
    similarity_tolerance = min(25, 10 + (aggressiveness - 1.0) * 15)
    
    for item in datas:
        r, g, b = item[0], item[1], item[2]
        
        # Calculate perceptual brightness (weighted RGB)
        brightness = (0.299 * r + 0.587 * g + 0.114 * b)
        
        # Calculate color similarity (how "gray" vs "colorful")
        max_diff = max(abs(r - g), abs(g - b), abs(r - b))
        
        # Multiple detection strategies:
        should_be_transparent = False
        
        # Strategy 1: Very bright pixels (near white)
        if brightness > main_threshold and max_diff < similarity_tolerance:
            should_be_transparent = True
            
        # Strategy 2: Light gray pixels (anti-aliasing)
        elif brightness > gray_threshold and max_diff < similarity_tolerance * 0.7:
            should_be_transparent = True
            
        # Strategy 3: High individual channel values (catch RGB-biased whites)
        elif (r > main_threshold or g > main_threshold or b > main_threshold) and \
             min(r, g, b) > gray_threshold * 0.8 and max_diff < similarity_tolerance:
            should_be_transparent = True
            
        # Strategy 4: Very aggressive mode - catch light pixels with slight tint
        elif aggressiveness > 1.5 and brightness > (gray_threshold - 20) and \
             max_diff < similarity_tolerance * 1.2:
            should_be_transparent = True
        
        if should_be_transparent:
            # Make completely transparent
            new_data.append((255, 255, 255, 0))
        else:
            # Keep original pixel
            new_data.append(item)
    
    img.putdata(new_data)
    img.save(output_path, "PNG")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make white pixels transparent in PNG images.")
    parser.add_argument("target", help="Path to a specific PNG file OR folder containing PNG images")
    parser.add_argument("--threshold", type=int, default=230, help="Threshold for white detection (0-255)")
    parser.add_argument("--aggressiveness", type=float, default=1.0, 
                        help="How aggressive to be with transparency: 0.5=conservative, 1.0=normal, 1.8=good for text, 2.5=ultra aggressive")
    parser.add_argument("--text-mode", action="store_true", help="Optimized for text with white anti-aliasing (sets aggressiveness=1.8)")
    parser.add_argument("--inplace", action="store_true", help="Modify files in-place instead of creating *_transparent.png")
    parser.add_argument("--backup", action="store_true", help="Create .bak backup when using --inplace")
    args = parser.parse_args()
    
    # Handle text-mode flag
    if args.text_mode:
        args.aggressiveness = 1.8
        print(f"Text mode enabled: using aggressiveness={args.aggressiveness}")

    target_path = Path(args.target)
    processed_count = 0
    
    # Determine if target is a file or directory
    if target_path.is_file():
        # Single file processing
        if not target_path.name.lower().endswith('.png'):
            print(f"Error: {target_path} is not a PNG file")
            exit(1)
        
        files_to_process = [target_path]
    elif target_path.is_dir():
        # Directory processing (original behavior)
        files_to_process = [f for f in target_path.glob("*.png") 
                          if not f.name.endswith("_transparent.png")]
        if not files_to_process:
            print(f"No PNG files found in {target_path}")
            exit(0)
    else:
        print(f"Error: {target_path} does not exist")
        exit(1)
    
    def process_file(png_file):
        """Process a single PNG file"""
        input_path = str(png_file)
        
        if args.inplace:
            # Create backup if requested
            if args.backup:
                backup_path = str(png_file.with_suffix(".png.bak"))
                shutil.copy2(input_path, backup_path)
                print(f"Backup created: {backup_path}")
            
            # Process in-place using a temporary file for safety
            temp_path = str(png_file.with_suffix(".tmp"))
            try:
                print(f"Processing {input_path} (in-place, aggressiveness={args.aggressiveness})...")
                make_white_transparent(input_path, temp_path, threshold=args.threshold, aggressiveness=args.aggressiveness)
                # Atomic replace
                shutil.move(temp_path, input_path)
                return True
            except Exception as e:
                print(f"Error processing {input_path}: {e}")
                # Clean up temp file if it exists
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                return False
        else:
            # Original behavior - create *_transparent.png
            name = png_file.stem
            output_path = str(png_file.with_name(f"{name}_transparent.png"))
            print(f"Processing {input_path} -> {output_path} (aggressiveness={args.aggressiveness})")
            try:
                make_white_transparent(input_path, output_path, threshold=args.threshold, aggressiveness=args.aggressiveness)
                return True
            except Exception as e:
                print(f"Error processing {input_path}: {e}")
                return False
    
    # Process all files
    for png_file in files_to_process:
        if process_file(png_file):
            processed_count += 1
    
    print(f"\nProcessed {processed_count} files.")
