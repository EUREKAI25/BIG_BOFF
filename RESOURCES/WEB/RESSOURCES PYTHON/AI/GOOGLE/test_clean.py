# testgemini_force.py
import os
import time

# Force la clé AVANT d'importer genai
os.environ['GOOGLE_API_KEY'] = 'AIzaSyBD764XQXso1vD1jZLNt6G4AP0nqkK5jCo'

# Maintenant importe
from google import genai

client = genai.Client()

print("Génération vidéo...")
try:
    op = client.models.generate_videos(
        model="veo-3.0-generate-001",
        prompt="8-second AI avatar, non-human appearance"
    )
    print(f"✅ Opération lancée: {op}")
    
    # Attendre
    while not op.done:
        print("En cours...")
        time.sleep(10)
        op = client.operations.get(op)
    
    # Télécharger
    vid = op.response.generated_videos[0]
    client.files.download(file=vid.video)
    vid.video.save("result.mp4")
    print("✅ Vidéo sauvegardée!")
    
except Exception as e:
    print(f"Erreur: {e}")