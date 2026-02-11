"""
TEST GEMINI SIMPLE — Données hardcodées pour debug
"""

import json
import os
import base64
import urllib.request
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# CONFIG
FAL_KEY = os.getenv("FAL_KEY")
ENDPOINT = "https://queue.fal.run/fal-ai/gemini-3-pro-image-preview"

# PHOTO DE RÉFÉRENCE (hardcodé)
REF_PHOTOS_DIR = "/Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PRO/SUBLYM_APP_PUB/Avatars/Mickael/photos"
REF_PHOTO = sorted(Path(REF_PHOTOS_DIR).glob("*.png"))[0]  # Première photo

# PROMPT SIMPLE (hardcodé)
PROMPT = """Based on the reference image provided, use the exact facial features, skin tone, and appearance of this person.

Put this man standing on a beach in the Maldives. He wears a white shirt and beige shorts.

Photo-realistic, cinematic quality, professional photography. Face clearly visible."""

# OUTPUT
OUTPUT_FILE = "test_gemini_simple_output.png"

def main():
    print("=" * 70)
    print("TEST GEMINI SIMPLE — Données hardcodées")
    print("=" * 70)

    # 1. Charger et encoder la photo
    print(f"\n📸 Chargement photo de référence...")
    print(f"   Chemin: {REF_PHOTO}")
    print(f"   Existe: {Path(REF_PHOTO).exists()}")

    with open(REF_PHOTO, "rb") as f:
        img_bytes = f.read()
        print(f"   Taille: {len(img_bytes)} bytes ({len(img_bytes)/1024/1024:.2f} MB)")

    image_b64 = base64.b64encode(img_bytes).decode('utf-8')
    image_url = f"data:image/png;base64,{image_b64}"
    print(f"   Base64: {len(image_b64)} chars")

    # 2. Construire le payload
    payload = {
        "prompt": PROMPT,
        "image_size": "landscape_4_3",
        "num_inference_steps": 4,
        "num_images": 1,
        "enable_safety_checker": False,
        "image_urls": [image_url]
    }

    print(f"\n📝 Prompt envoyé:")
    print("-" * 70)
    print(PROMPT)
    print("-" * 70)

    print(f"\n🔍 Payload:")
    debug_payload = payload.copy()
    debug_payload["image_urls"] = [f"<base64 {len(image_b64)} chars>"]
    print(json.dumps(debug_payload, indent=2))

    # 3. Appel API
    print(f"\n🚀 Appel API Fal.ai...")
    print(f"   Endpoint: {ENDPOINT}")

    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Key {FAL_KEY}",
            "Content-Type": "application/json"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        queue_result = json.loads(response.read().decode("utf-8"))

    status_url = queue_result.get("status_url")
    response_url = queue_result.get("response_url")

    print(f"   Status URL: {status_url}")
    print(f"   Response URL: {response_url}")

    # 4. Polling
    print(f"\n⏳ Attente génération...")
    max_wait = 120
    elapsed = 0

    while elapsed < max_wait:
        status_req = urllib.request.Request(
            status_url,
            headers={"Authorization": f"Key {FAL_KEY}"}
        )

        with urllib.request.urlopen(status_req, timeout=10) as status_resp:
            status_data = json.loads(status_resp.read().decode("utf-8"))

        status = status_data.get("status")
        print(f"   Status: {status}")

        if status == "COMPLETED":
            result_req = urllib.request.Request(
                response_url,
                headers={"Authorization": f"Key {FAL_KEY}"}
            )

            with urllib.request.urlopen(result_req, timeout=10) as result_resp:
                result = json.loads(result_resp.read().decode("utf-8"))

            print(f"\n🔍 RÉPONSE COMPLÈTE DE L'API:")
            print(json.dumps(result, indent=2))

            image_url = result.get("images", [{}])[0].get("url")
            if not image_url:
                print(f"\n❌ Pas d'URL d'image dans le résultat")
                print(json.dumps(result, indent=2))
                return

            print(f"\n✅ Génération terminée!")
            print(f"   URL: {image_url}")

            # Télécharger
            urllib.request.urlretrieve(image_url, OUTPUT_FILE)
            print(f"   Sauvegardé: {OUTPUT_FILE}")

            # Ouvrir
            os.system(f"open {OUTPUT_FILE}")

            return

        elif status == "FAILED":
            error = status_data.get("error", "Unknown error")
            print(f"\n❌ Échec: {error}")
            return

        time.sleep(2)
        elapsed += 2

    print(f"\n❌ Timeout après {max_wait}s")

if __name__ == "__main__":
    main()
