# testgemini_solution.py
from dotenv import load_dotenv
import os
import time

# Charge .env
load_dotenv('.venv/.env')

# Récupère la clé
API_KEY = os.getenv('GOOGLE_API_KEY')
if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY non trouvée dans .env")

print(f"Clé chargée depuis .env: {API_KEY[:10]}...{API_KEY[-4:]}")

# Importe genai APRÈS avoir chargé la clé
from google import genai

# Passe la clé EXPLICITEMENT au client
client = genai.Client(api_key=API_KEY)

print("Génération vidéo...")
op = client.models.generate_videos(
    model="veo-3.0-generate-001",
    prompt="8-second AI avatar, non-human appearance"
)

print(f"Opération: {op}")

while not op.done:
    print("En cours...")
    time.sleep(10)
    op = client.operations.get(op)

vid = op.response.generated_videos[0]
client.files.download(file=vid.video)
vid.video.save("result.mp4")
print("✅ Vidéo sauvegardée!")