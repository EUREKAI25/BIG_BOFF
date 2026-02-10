# testgemini_avatar.py
import time
import json
from google import genai

# Lit la clé depuis .env
with open('.venv/.env', 'r') as f:
    for line in f:
        if line.startswith('GOOGLE_API_KEY'):
            API_KEY = line.split('=', 1)[1].strip()
            break

# Charge le prompt depuis le JSON
with open('/Users/nathalie/Dropbox/CODES PYTHON UTILES/AI/GOOGLE/prompt.json', 'r') as f:
    prompt_data = json.load(f)

# Construit le prompt détaillé
prompt = f"{prompt_data['description']} "
prompt += " ".join(prompt_data['requirements'])
# Ajoute la durée dans le prompt lui-même
prompt += " 8 second video."

print(f"Prompt: {prompt[:100]}...")

# Crée le client
client = genai.Client(api_key=API_KEY)

# Génération vidéo (sans config)
print("Génération de l'avatar...")
op = client.models.generate_videos(
    model="veo-3.0-generate-001",
    prompt=prompt
)

print(f"Opération lancée: {op}")

# Attente avec timeout
timeout = time.time() + 15 * 60  # 15 minutes max
while not op.done:
    if time.time() > timeout:
        print("Timeout atteint")
        break
    print("Génération en cours...")
    time.sleep(10)
    op = client.operations.get(op)

# Téléchargement
if op.done:
    vid = op.response.generated_videos[0]
    output_name = "avatar_green_screen.mp4"
    client.files.download(file=vid.video)
    vid.video.save(output_name)
    print(f"✅ Avatar sauvegardé: {output_name}")
else:
    print("❌ Génération incomplète")