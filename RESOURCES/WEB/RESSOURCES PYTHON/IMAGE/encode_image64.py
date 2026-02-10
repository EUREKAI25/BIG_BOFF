# test_encode_decode.py
import base64
import os

# Trouve d'abord le fichier
possible_paths = [
    "AI/GOOGLE/avatar_reference.png",
    "/Users/nathalie/Dropbox/CODESPYTHONUTILES/AI/GOOGLE/avatar_reference.png",
    "avatar_reference.png"
]

image_path = None
for path in possible_paths:
    if os.path.exists(path):
        image_path = path
        print(f"Fichier trouvé: {path}")
        break

if not image_path:
    print("Fichier non trouvé. Contenu du répertoire actuel:")
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.png'):
                print(f"  {os.path.join(root, file)}")
    exit(1)

# Encode
with open(image_path, 'rb') as f:
    raw_bytes = f.read()
    print(f"Taille originale: {len(raw_bytes)} bytes")

encoded = base64.b64encode(raw_bytes).decode('utf-8')
print(f"Encodé: {len(encoded)} caractères")
print(f"Début: {encoded[:100]}")

# Test décodage immédiat
decoded = base64.b64decode(encoded)
if decoded == raw_bytes:
    print("✓ Encodage/décodage OK")
else:
    print("✗ Problème encodage/décodage")

# Sauve le base64 pur (sans JSON)
with open('test_base64.txt', 'w') as f:
    f.write(encoded)
print("\nBase64 pur sauvé dans test_base64.txt")
print("Copie le contenu de ce fichier dans un décodeur en ligne")

# Sauve aussi l'image décodée pour vérifier
with open('test_verified.png', 'wb') as f:
    f.write(decoded)
print("Image décodée sauvée dans test_verified.png")