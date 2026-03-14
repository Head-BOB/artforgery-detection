import cv2
import os
import numpy as np
import zipfile

def auto_canny(image, sigma=0.33):
    median = np.median(image)
    lower = int(max(0, (1.0 - sigma) * median))
    upper = int(min(255, (1.0 + sigma) * median))
    return cv2.Canny(image, lower, upper)

def create_patches(image, scale, output_dir, base_name):
    """
    Generate overlapping patches at the given scale (patch size).
    Save patches into the specified output directory.
    """
    h, w = image.shape[:2]
    step = scale // 2 
    count = 0

    for y in range(0, h - scale + 1, step):
        for x in range(0, w - scale + 1, step):
            patch = image[y:y+scale, x:x+scale]
            patch_filename = os.path.join(output_dir, f"{base_name}_scale{scale}_y{y}_x{x}.png")
            cv2.imwrite(patch_filename, patch)
            count += 1
    print(f"Created {count} patches for scale {scale} in {output_dir}")

def process_image():
    image_path = input("Enter the full path of the image: ").strip()

    if not os.path.isfile(image_path):
        print("Error: File not found.")
        return

    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not read the image.")
        return

    
    base_dir = os.path.join(os.path.dirname(__file__), "processed")
    os.makedirs(base_dir, exist_ok=True)

    
    base_name = os.path.basename(image_path)
    name, ext = os.path.splitext(base_name)
    original_path = os.path.join(base_dir, f"{name}_rgb{ext}")
    cv2.imwrite(original_path, img)

    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_path = os.path.join(base_dir, f"{name}_grayscale{ext}")
    cv2.imwrite(gray_path, gray)

    
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)

    
    edges = auto_canny(blurred)
    edges_path = os.path.join(base_dir, f"{name}_edges{ext}")
    cv2.imwrite(edges_path, edges)

    
    scales = [128, 256, 512]
    all_patches_dir = os.path.join(base_dir, "patches")
    os.makedirs(all_patches_dir, exist_ok=True)

    
    for version, image in [("original", img), ("gray", gray), ("edges", edges)]:
        version_dir = os.path.join(all_patches_dir, version)
        os.makedirs(version_dir, exist_ok=True)
        for scale in scales:
            create_patches(image, scale, version_dir, f"{name}_{version}")

    
    zip_path = os.path.join(base_dir, f"{name}_patches.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(all_patches_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, base_dir)
                zipf.write(file_path, arcname)

    print("\nProcessing complete. Patches and ZIP archive are ready.")
    print(f"Folder: {all_patches_dir}")
    print(f"ZIP: {zip_path}")

if __name__ == "__main__":
    process_image()