import os
import argparse
from PIL import Image

def make_white_transparent(input_path, output_path, threshold=200):
    img = Image.open(input_path).convert("RGBA")
    datas = img.getdata()
    new_data = []
    for item in datas:
        if item[0] > threshold and item[1] > threshold and item[2] > threshold:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    img.save(output_path, "PNG")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make white pixels transparent in all PNG images in a folder.")
    parser.add_argument("folder", help="Path to the folder containing PNG images")
    parser.add_argument("--threshold", type=int, default=200, help="Threshold for white detection")
    args = parser.parse_args()

    for filename in os.listdir(args.folder):
        if filename.lower().endswith(".png"):
            input_path = os.path.join(args.folder, filename)
            # Save as <original>_transparent.png
            name, ext = os.path.splitext(filename)
            output_path = os.path.join(args.folder, f"{name}_transparent{ext}")
            print(f"Processing {input_path} -> {output_path}")
            make_white_transparent(input_path, output_path, threshold=args.threshold)
