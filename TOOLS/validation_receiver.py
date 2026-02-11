#!/usr/bin/env python3
"""
Serveur temporaire pour recevoir les validations de formulaires HTML.
Lance sur le port 9999, reçoit les validations et les écrit dans validation.json
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Permettre les requêtes depuis les fichiers HTML locaux

VALIDATION_FILE = "/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/validation.json"

@app.route('/api/validate', methods=['POST', 'OPTIONS'])
def receive_validation():
    """Reçoit une validation de formulaire et l'écrit dans validation.json"""

    if request.method == 'OPTIONS':
        # Gestion CORS preflight
        return '', 204

    try:
        data = request.json

        # Ajouter timestamp
        data['timestamp'] = datetime.now().isoformat()

        # Écrire dans le fichier
        with open(VALIDATION_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Validation reçue et sauvegardée !")
        print(f"Type: {data.get('type', 'unknown')}")
        print(f"Décision: {data.get('decision', 'unknown')}")
        print(f"Fichier: {VALIDATION_FILE}")

        return jsonify({
            "status": "success",
            "message": "Validation reçue et sauvegardée",
            "file": VALIDATION_FILE
        })

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def status():
    """Endpoint de test pour vérifier que le serveur tourne"""
    return jsonify({
        "status": "running",
        "message": "Serveur de validation opérationnel",
        "port": 9999
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Serveur de validation démarré sur http://localhost:9999")
    print("="*60)
    print(f"📁 Les validations seront sauvegardées dans:")
    print(f"   {VALIDATION_FILE}")
    print("\nEn attente de validations...")
    print("="*60 + "\n")

    app.run(host='127.0.0.1', port=9999, debug=False)
