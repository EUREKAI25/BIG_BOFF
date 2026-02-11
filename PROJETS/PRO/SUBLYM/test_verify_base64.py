"""
TEST VÉRIFICATION BASE64 — Vérifier que l'encodage/décodage est correct
"""

import base64
import os
from pathlib import Path

# PHOTO DE RÉFÉRENCE
REF_PHOTOS_DIR = "/Users/nathalie/Dropbox/____BIG_BOFF___/PROJETS/PRO/SUBLYM_APP_PUB/Avatars/Mickael/photos"
REF_PHOTO = sorted(Path(REF_PHOTOS_DIR).glob("*.png"))[0]

print("=" * 70)
print("TEST VÉRIFICATION BASE64")
print("=" * 70)

# 1. Charger l'image originale
print(f"\n📸 Image originale:")
print(f"   Chemin: {REF_PHOTO}")

with open(REF_PHOTO, "rb") as f:
    original_bytes = f.read()

print(f"   Taille: {len(original_bytes)} bytes")
print(f"   Premiers bytes: {original_bytes[:20].hex()}")

# 2. Encoder en base64
print(f"\n🔄 Encodage en base64...")
image_b64 = base64.b64encode(original_bytes).decode('utf-8')
print(f"   Longueur base64: {len(image_b64)} chars")
print(f"   Premiers chars: {image_b64[:100]}")

# 3. Construire data URI (comme dans l'appel API)
data_uri = f"data:image/png;base64,{image_b64}"
print(f"\n📦 Data URI:")
print(f"   Longueur totale: {len(data_uri)} chars")
print(f"   Préfixe: {data_uri[:50]}")

# 4. Extraire et décoder le base64 du data URI
print(f"\n🔄 Décodage du base64...")
if data_uri.startswith("data:image/png;base64,"):
    extracted_b64 = data_uri.split(",", 1)[1]
    decoded_bytes = base64.b64decode(extracted_b64)

    print(f"   Base64 extrait: {len(extracted_b64)} chars")
    print(f"   Bytes décodés: {len(decoded_bytes)} bytes")
    print(f"   Premiers bytes décodés: {decoded_bytes[:20].hex()}")

    # 5. Comparer avec l'original
    print(f"\n✅ Vérification:")
    if original_bytes == decoded_bytes:
        print(f"   ✅ IDENTIQUE - L'encodage/décodage fonctionne parfaitement")
    else:
        print(f"   ❌ DIFFÉRENT - Il y a un problème d'encodage/décodage!")
        print(f"   Taille originale: {len(original_bytes)}")
        print(f"   Taille décodée: {len(decoded_bytes)}")

    # 6. Sauvegarder l'image décodée pour vérification visuelle
    decoded_path = "test_decoded_image.png"
    with open(decoded_path, "wb") as f:
        f.write(decoded_bytes)
    print(f"   💾 Image décodée sauvegardée: {decoded_path}")
    print(f"   Ouvrir pour vérifier visuellement...")
    os.system(f"open {decoded_path}")

else:
    print(f"   ❌ Format data URI invalide")

print("\n" + "=" * 70)
