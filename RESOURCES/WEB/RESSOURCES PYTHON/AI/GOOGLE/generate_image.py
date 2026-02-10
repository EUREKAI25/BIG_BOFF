# generate_image.py
import json
from google import genai

def get_api_key():
    with open('.venv/.env', 'r') as f:
        for line in f:
            if line.startswith('GOOGLE_API_KEY'):
                return line.split('=', 1)[1].strip()

def generate_image(prompt_file=None, reference_image=None):
    """Génère une image avec Imagen"""
    
    # Charge le prompt
    prompt = "Ultra realistic AI humanoid avatar"
    if prompt_file:
        with open(prompt_file, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict):
                prompt = data.get('description', '') + ' ' + ' '.join(data.get('requirements', []))
            else:
                prompt = data
    
    client = genai.Client(api_key=get_api_key())
    
    # Génération d'image avec Imagen
    print(f"Génération d'image: {prompt[:50]}...")
    
    try:
        # Note: l'API exacte peut varier
        response = client.models.generate_images(
            model="imagen-3.0-generate-002",  # ou autre modèle d'image
            prompt=prompt,
            number_of_images=1
        )
        
        # Sauvegarde l'image
        output_path = "generated_avatar.png"
        with open(output_path, 'wb') as f:
            f.write(response.images[0])
        
        print(f"✅ Image générée: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Erreur génération image: {e}")
        return None

if __name__ == "__main__":
    import sys
    prompt_file = sys.argv[1] if len(sys.argv) > 1 else "prompt.json"
    generate_image(prompt_file)