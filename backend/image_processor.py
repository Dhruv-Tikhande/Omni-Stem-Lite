from PIL import Image
import os

# 🎯 OBJECTIVE 3: Check resolution and upscale if needed
def enhance_and_prepare_image(image_path, target_width=1500):
    print(f"Loading direct image: {image_path}")
    img = Image.open(image_path)
    
    # Check if image is low resolution (smaller than our target width)
    if img.width < target_width:
        print(f"Image is low resolution ({img.width}x{img.height}). Upscaling...")
        
        # Calculate new height while keeping the exact same aspect ratio
        aspect_ratio = img.height / img.width
        new_height = int(target_width * aspect_ratio)
        
        # Upscale using LANCZOS (a high-quality resampling filter)
        img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
        print(f"Upscaled to High-Res: {img.width}x{img.height}")
    else:
        print(f"Image resolution is sufficient ({img.width}x{img.height}). No upscale needed.")
        
    return img

# 🎯 OBJECTIVE 4: Dynamic Tiling Protocol (448x448 patches)
def slice_into_tiles(img, output_folder, tile_size=448):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    img_width, img_height = img.size
    print(f"Executing Dynamic Tiling Protocol ({tile_size}x{tile_size})...")

    tile_count = 0
    # Loop through the image grid
    for y in range(0, img_height, tile_size):
        for x in range(0, img_width, tile_size):
            # Define the bounding box for the crop (handling the edges so it doesn't crash)
            box = (x, y, min(x + tile_size, img_width), min(y + tile_size, img_height))
            tile = img.crop(box)
            
            # Save the tile with its exact X and Y coordinates in the filename
            tile_path = f"{output_folder}/patch_x{x}_y{y}.png"
            tile.save(tile_path)
            tile_count += 1
            
    print(f"Success! Generated {tile_count} patches for the AI model.")

# --- The Master Pipeline ---
def process_direct_image(image_path, output_folder):
    # Step 1: Upscale
    high_res_img = enhance_and_prepare_image(image_path)
    # Step 2: Slice
    slice_into_tiles(high_res_img, output_folder)

# Uncomment the line below and change the filename to test it!
process_direct_image("line.png", "ai_ready_tiles")