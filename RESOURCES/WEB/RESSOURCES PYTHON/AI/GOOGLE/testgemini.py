# test_minimal.py
from dotenv import load_dotenv
import os

load_dotenv('.venv/.env')
key = os.getenv('GOOGLE_API_KEY')

# Nettoie la clé de tout caractère parasite
key = key.strip() if key else None

if not key:
    raise RuntimeError("Pas de clé")

from google import genai
client = genai.Client(api_key=key)

# Test simple
models = list(client.models.list())
print(f"✅ {len(models)} modèles trouvés")