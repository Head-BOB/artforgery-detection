import os
import cv2
import numpy as np
import torch
import torchvision.transforms.functional as TF
from PIL import Image

# Exact parameters from your Colab training script
SCALES = [512, 256]
TARGET_SIZE = 256
STRIDE = 512

def auto_canny(image, sigma=0.33):
    median = np.median(image)
    lower = int(max(0, (1.0 - sigma) * median))
    upper = int(min(255, (1.0 + sigma) * median))
    return cv2.Canny(image, lower, upper)

def process_image(filepath):
    
    try:
        pil_img = Image.open(filepath)
    except Exception as e:
        raise ValueError(f"Cannot open image: {e}")

    w, h = pil_img.size
    
    if w < max(SCALES) or h < max(SCALES):
        pil_img = pil_img.resize((max(w, max(SCALES)), max(h, max(SCALES))), Image.BICUBIC)
        w, h = pil_img.size

    rgb_tensors, gray_tensors, edge_tensors = [], [], []

    for y in range(0, h - max(SCALES) + 1, STRIDE):
        for x in range(0, w - max(SCALES) + 1, STRIDE):
            for scale in SCALES:
              
                box = (x, y, x + scale, y + scale)
                patch_pil = pil_img.crop(box).convert('RGB')

                
                patch_rgb_cv = cv2.cvtColor(np.array(patch_pil), cv2.COLOR_RGB2BGR)
                patch_gray_cv = cv2.cvtColor(patch_rgb_cv, cv2.COLOR_BGR2GRAY)
                
               
                blurred = cv2.GaussianBlur(patch_gray_cv, (5, 5), 0)
                patch_edge_cv = auto_canny(blurred)

               
                if scale != TARGET_SIZE:
                    patch_rgb_cv = cv2.resize(patch_rgb_cv, (TARGET_SIZE, TARGET_SIZE))
                    patch_gray_cv = cv2.resize(patch_gray_cv, (TARGET_SIZE, TARGET_SIZE))
                    patch_edge_cv = cv2.resize(patch_edge_cv, (TARGET_SIZE, TARGET_SIZE))

                
                img_rgb = Image.fromarray(cv2.cvtColor(patch_rgb_cv, cv2.COLOR_BGR2RGB))
                img_gray = Image.fromarray(patch_gray_cv).convert('L')
                img_edge = Image.fromarray(patch_edge_cv).convert('L')

                
                img_rgb = TF.resize(img_rgb, (224, 224))
                img_gray = TF.resize(img_gray, (224, 224))
                img_edge = TF.resize(img_edge, (224, 224))

                
                t_rgb = TF.to_tensor(img_rgb)
                t_gray = TF.to_tensor(img_gray)
                t_edge = TF.to_tensor(img_edge)

                
                t_rgb = TF.normalize(t_rgb, [0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
                t_gray = TF.normalize(t_gray, [0.5], [0.5])
                t_edge = TF.normalize(t_edge, [0.5], [0.5])

                rgb_tensors.append(t_rgb)
                gray_tensors.append(t_gray)
                edge_tensors.append(t_edge)

   
    batch_rgb = torch.stack(rgb_tensors)
    batch_gray = torch.stack(gray_tensors)
    batch_edge = torch.stack(edge_tensors)
    
    print(f"Server Preprocessing Complete: Generated {len(rgb_tensors)} perfectly matched patches.")
    return batch_rgb, batch_gray, batch_edge
