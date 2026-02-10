#!/usr/bin/env python3
"""
Test EUREKAI Modular
"""
import os
import sys

# 1. Créer un fichier JS de test
demo_js = '''
/**
 * Additionne deux nombres
 * @param {number} a
 * @param {number} b
 * @returns {number}
 */
function add(a, b) {
    return a + b;
}

/**
 * Salue quelqu'un
 * @param {string} name
 * @returns {string}
 */
function greet(name) {
    return "Hello, " + name + "!";
}

window.add = add;
window.greet = greet;
'''

print("=" * 50)
print("EUREKAI MODULAR - TEST")
print("=" * 50)

# Sauvegarder le JS
with open('./test.js', 'w') as f:
    f.write(demo_js)
print("\n1. Fichier JS créé: ./test.js")

# 2. Convertir
from convert import convert
manifest_path, backend_path = convert('./test.js')
print(f"\n2. Conversion:")
print(f"   Manifest: {manifest_path}")
print(f"   Backend:  {backend_path}")

# 3. Enregistrer
from register import register, list_modules
register(manifest_path)
print(f"\n3. Enregistré dans registry")
print(f"   Modules: {list_modules()}")

# 4. Afficher le manifest
import json
with open(manifest_path) as f:
    manifest = json.load(f)
print(f"\n4. Manifest généré:")
print(json.dumps(manifest, indent=2))

# 5. Instructions
print("\n" + "=" * 50)
print("POUR TESTER LE SERVEUR:")
print("=" * 50)
print("""
# Terminal 1 - Lancer le serveur:
pip install flask
python server.py

# Terminal 2 - Tester avec curl:
curl "http://localhost:5000/api/Test/Create/add?vec123&token123"
curl "http://localhost:5000/api/Test/Execute/greet?vec456&token123"

# Ou ouvrir dans le navigateur:
http://localhost:5000/static/demo.html
""")
