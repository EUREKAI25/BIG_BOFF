# pipeline.py
import sys
import os
import json
import base64
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from AI.GOOGLE.generate_image import generate_image
from AI.GOOGLE.generate_video import generate_video

def encode_image(image_path):
    """Encode une image en base64 (format qui fonctionne)"""
    if not image_path or not Path(image_path).exists():
        return None
    
    with open(image_path, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
    
    # Sauvegarde en TXT (format qui marche)
    output_txt = Path(image_path).stem + '_base64.txt'
    with open(output_txt, 'w') as f:
        f.write(encoded)
    
    # Sauvegarde aussi en JSON pour compatibilité
    output_json = Path(image_path).stem + '_encoded.json'
    with open(output_json, 'w') as f:
        json.dump({
            "mime_type": "image/png",
            "data": encoded
        }, f)
    
    print(f"✅ Image encodée: {output_txt}")
    return output_txt

def run_pipeline(
    image_prompt_file=None,
    video_prompt_file="video_prompt.json", 
    reference_image=None,
    generate_image_first=False
):
    print("🚀 Début du pipeline")
    
    # Validation
    if not Path(video_prompt_file).exists():
        print(f"❌ Prompt vidéo manquant: {video_prompt_file}")
        return None
    
    if reference_image and not Path(reference_image).exists():
        print(f"❌ Image référence manquante: {reference_image}")