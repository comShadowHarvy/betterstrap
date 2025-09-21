#!/usr/bin/env python3
"""
Smart PNG transparency tool that preserves white text while removing white artifacts.
Specifically designed for images with white letters that need to keep their white color.
"""

import os
import argparse
import shutil
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

def analyze_white_pixels(img):
    """Analyze the white pixels to understand the image structure."""
    data = np.array(img)
    height, width = data.shape[:2]
    
    # Find white pixels
    white_mask = (data[:,:,0] > 240) & (data[:,:,1] > 240) & (data[:,:,2] > 240)
    
    # Separate by alpha channel
    if data.shape[2] == 4:  # RGBA
        opaque_white = white_mask & (data[:,:,3] > 200)
        transparent_white = white_mask & (data[:,:,3] < 50)
        semi_transparent_white = white_mask & (data[:,:,3] >= 50) & (data[:,:,3] <= 200)
    else:  # RGB
        opaque_white = white_mask
        transparent_white = np.zeros_like(white_mask)
        semi_transparent_white = np.zeros_like(white_mask)
    
    return {
        'opaque_white': np.sum(opaque_white),
        'transparent_white': np.sum(transparent_white), 
        'semi_transparent_white': np.sum(semi_transparent_white),
        'total_pixels': width * height
    }

def smart_white_cleanup(input_path, output_path, mode='artifacts', preserve_text=True):
    """
    Smart white pixel processing that can preserve white text.
    
    Args:
        input_path: Input PNG file
        output_path: Output PNG file
        mode: 'artifacts' (remove only artifacts), 'edges' (remove edge artifacts), 'aggressive' (remove most white)
        preserve_text: Whether to try to preserve solid white text
    """
    img = Image.open(input_path).convert("RGBA")
    data = np.array(img)
    
    print(f"Image size: {img.size}")
    
    # Analyze current state
    analysis = analyze_white_pixels(img)
    print(f"Analysis: {analysis}")
    
    height, width = data.shape[:2]
    result = data.copy()
    
    if mode == 'artifacts':
        # Remove only already-transparent white pixels and semi-transparent ones
        for y in range(height):
            for x in range(width):
                r, g, b, a = data[y, x]
                
                # Remove white pixels that are already transparent or semi-transparent
                if r > 240 and g > 240 and b > 240 and a < 200:
                    result[y, x] = [255, 255, 255, 0]
                    
    elif mode == 'edges':
        # More sophisticated: remove white pixels that look like anti-aliasing
        for y in range(1, height-1):
            for x in range(1, width-1):
                r, g, b, a = data[y, x]
                
                if r > 230 and g > 230 and b > 230:
                    # Check surrounding pixels
                    surrounding = data[y-1:y+2, x-1:x+2]
                    
                    # Count colored (non-white) neighbors
                    colored_neighbors = 0
                    for sy in range(3):
                        for sx in range(3):
                            if sy == 1 and sx == 1:  # Skip center pixel
                                continue
                            sr, sg, sb, sa = surrounding[sy, sx]
                            if not (sr > 220 and sg > 220 and sb > 220):  # Not white
                                colored_neighbors += 1
                    
                    # If this white pixel has many colored neighbors, it might be anti-aliasing
                    if colored_neighbors >= 3 and a < 255:
                        result[y, x] = [255, 255, 255, 0]
                    # If it's very transparent, remove it regardless
                    elif a < 100:
                        result[y, x] = [255, 255, 255, 0]
                        
    elif mode == 'aggressive':
        # Remove most white pixels except very solid ones
        for y in range(height):
            for x in range(width):
                r, g, b, a = data[y, x]
                
                # Only keep white pixels that are very opaque and very white
                if r > 240 and g > 240 and b > 240:
                    if a < 240 or (r < 250 or g < 250 or b < 250):
                        result[y, x] = [255, 255, 255, 0]
    
    # Convert back to PIL Image
    result_img = Image.fromarray(result, 'RGBA')
    result_img.save(output_path, "PNG")
    
    # Analyze result
    result_analysis = analyze_white_pixels(result_img)
    print(f"Result: {result_analysis}")
    
    removed = analysis['opaque_white'] + analysis['semi_transparent_white'] - result_analysis['opaque_white'] - result_analysis['semi_transparent_white']
    print(f"Removed {removed} white pixels")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart transparency tool for images with white text")
    parser.add_argument("target", help="Path to a specific PNG file OR folder containing PNG images")
    parser.add_argument("--mode", choices=['artifacts', 'edges', 'aggressive'], default='edges',
                        help="Processing mode: artifacts=remove transparent whites, edges=remove anti-aliasing, aggressive=remove most whites")
    parser.add_argument("--inplace", action="store_true", help="Modify files in-place")
    parser.add_argument("--backup", action="store_true", help="Create .bak backup when using --inplace")
    args = parser.parse_args()

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
                          if not f.name.endswith(("_transparent.png", "_original.png", "_test.png", "_smart.png"))]
        if not files_to_process:
            print(f"No PNG files found in {target_path}")
            exit(0)
    else:
        print(f"Error: {target_path} does not exist")
        exit(1)
    
    # Process all files
    for png_file in files_to_process:
        input_path = str(png_file)
        
        if args.inplace:
            if args.backup:
                backup_path = str(png_file.with_suffix(".png.bak"))
                shutil.copy2(input_path, backup_path)
                print(f"Backup created: {backup_path}")
            
            temp_path = str(png_file.with_suffix(".tmp"))
            try:
                print(f"Processing {input_path} (mode: {args.mode})...")
                smart_white_cleanup(input_path, temp_path, mode=args.mode)
                shutil.move(temp_path, input_path)
                processed_count += 1
            except Exception as e:
                print(f"Error processing {input_path}: {e}")
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        else:
            output_path = str(png_file.with_name(f"{png_file.stem}_smart.png"))
            print(f"Processing {input_path} -> {output_path} (mode: {args.mode})")
            try:
                smart_white_cleanup(input_path, output_path, mode=args.mode)
                processed_count += 1
            except Exception as e:
                print(f"Error processing {input_path}: {e}")
    
    print(f"\nProcessed {processed_count} files.")
