# testgemini_final.py
import time
from google import genai

# Lit directement le fichier .env sans utiliser dotenv
with open('.venv/.env', 'r') as f:
    for line in f:
        if line.startswith('GOOGLE_API_KEY'):
            API_KEY = line.split('=', 1)[1].strip()
            break

print(f"Clé: {API_KEY[:10]}...{API_KEY[-6:]}")

# Crée le client avec la clé
client = genai.Client(api_key=API_KEY)

# Génération vidéo
print("Génération vidéo...")
op = client.models.generate_videos(
    model="veo-3.0-generate-001",
    prompt="8-second AI avatar, non-human appearance"
)

print(f"Opération: {op}")

# Attente
while not op.done:
    print("En cours...")
    time.sleep(10)
    op = client.operations.get(op)

# Téléchargement
vid = op.response.generated_videos[0]
client.files.download(file=vid.video)
vid.video.save("result.mp4")
print("✅ Vidéo sauvegardée!")