# debug_env.py
with open('.venv/.env', 'r') as f:
    content = f.read()
    print(f"Contenu brut du fichier: {repr(content)}")
    
    # Extrait juste la valeur après GOOGLE_API_KEY=
    for line in content.split('\n'):
        if line.startswith('GOOGLE_API_KEY'):
            key = line.split('=', 1)[1]
            print(f"Clé extraite: {repr(key)}")
            print(f"Longueur: {len(key)}")
            print(f"Commence par: {key[:15]}")
            print(f"Finit par: {key[-10:]}")