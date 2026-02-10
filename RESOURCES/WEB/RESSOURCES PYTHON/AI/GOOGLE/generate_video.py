# generate_video.py
import time
import json
from google import genai

def get_api_key():
    with open('.venv/.env', 'r') as f:
        for line in f:
            if line.startswith('GOOGLE_API_KEY'):
                return line.split('=', 1)[1].strip()

def generate_video(prompt_file=None, image_file=None, output_name="output.mp4"):
    """Génère une vidéo avec Veo"""
    
    # Charge le prompt
    prompt = "8 second video"
    if prompt_file:
        with open(prompt_file, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict):
                prompt = data.get('description', '') + ' ' + ' '.join(data.get('requirements', []))
            else:
                prompt = str(data)
            prompt += " 8 second video."
    
    # Charge l'image si fournie
    image_data = None
    if image_file:
        if image_file.endswith('.json'):
            # Image déjà encodée
            with open(image_file, 'r') as f:
                image_info = json.load(f)
                image_data = image_info['data']
        else:
            # Image brute à encoder
            import base64
            with open(image_file, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
    
    client = genai.Client(api_key=get_api_key())
    
    print(f"Génération vidéo: {prompt[:50]}...")
    if image_data:
        print("Avec image de référence")
    
    # Lance la génération
    op = client.models.generate_videos(
        model="veo-3.0-generate-001",
        prompt=prompt
    )
    
    # Attente
    timeout = time.time() + 15 * 60
    while not op.done:
        if time.time() > timeout:
            print("Timeout")
            return None
        print("En cours...")
        time.sleep(10)
        op = client.operations.get(op)
    
    # Téléchargement
    vid = op.response.generated_videos[0]
    client.files.download(file=vid.video)
    vid.video.save(output_name)
    print(f"✅ Vidéo sauvegardée: {output_name}")
    return output_name

if __name__ == "__main__":
    import sys
    prompt_file = sys.argv[1] if len(sys.argv) > 1 else "prompt.json"
    image_file = sys.argv[2] if len(sys.argv) > 2 else None
    generate_video(prompt_file, image_file)