# BIG_BOFF Search — Checklist Distribution

## 1. Configuration centralisée

### Créer `config.json` (avec valeurs par défaut)
```json
{
  "db_path": "~/.bigboff/catalogue.db",
  "dropbox_root": "~/Dropbox/____BIG_BOFF___",
  "export_dir": "/tmp/bigboff_export",
  "server_port": 7777,
  "thumbnails_dir": "~/.bigboff/thumbnails",
  "saved_images_dir": "~/.bigboff/saved_images"
}
```

### Créer `config_loader.py`
```python
import os
import json
from pathlib import Path

def load_config():
    config_path = Path.home() / '.bigboff' / 'config.json'
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
    else:
        config = get_default_config()

    # Expand ~ and env vars
    for key, value in config.items():
        if isinstance(value, str):
            config[key] = os.path.expanduser(value)

    return config
```

---

## 2. Scripts d'indexation avec CLI

### Transformer chaque script pour accepter des arguments

**Avant** :
```python
DB_PATH = "/Users/nathalie/Dropbox/..."
```

**Après** :
```python
import argparse
from config_loader import load_config

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-path', help='Path to catalogue.db')
    parser.add_argument('--source-dir', help='Source directory to index')
    args = parser.parse_args()

    config = load_config()
    db_path = args.db_path or config['db_path']
    source_dir = args.source_dir or config['dropbox_root']

    # ...
```

### Scripts à refactorer
- [x] ~~generate_tags.py~~ → Utilise déjà config.py
- [ ] index_notes.py → Accepter --export-dir, --db-path
- [ ] index_emails.py → Accepter --accounts-file, --db-path
- [ ] index_content.py → Accepter --source-dir, --db-path
- [ ] import_vault.py → Accepter --csv-file, --db-path
- [ ] server.py → Accepter --port, --db-path, --config

---

## 3. Installation automatisée

### Créer `install.sh`
```bash
#!/bin/bash
set -e

echo "=== BIG_BOFF Search — Installation ==="

# 1. Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 requis"
    exit 1
fi

# 2. Créer dossiers
mkdir -p ~/.bigboff/{thumbnails,saved_images}

# 3. Copier config par défaut
if [ ! -f ~/.bigboff/config.json ]; then
    cp config.default.json ~/.bigboff/config.json
    echo "✓ Config créée : ~/.bigboff/config.json"
fi

# 4. Installer dépendances Python
pip3 install -r requirements.txt

# 5. Initialiser la base
python3 src/setup_db.py

# 6. Vérifier dépendances optionnelles
if command -v ffmpeg &> /dev/null; then
    echo "✓ ffmpeg installé (miniatures vidéo)"
else
    echo "⚠️  ffmpeg manquant (miniatures vidéo désactivées)"
fi

# 7. Setup extension Chrome
echo "Extension Chrome : chargez 'extension/' en mode développeur"

echo ""
echo "✅ Installation terminée !"
echo "Lancez : python3 src/server.py"
```

### Créer `requirements.txt`
```txt
beautifulsoup4>=4.12.0
requests>=2.31.0
Pillow>=10.0.0
```

### Créer `setup_db.py`
```python
"""Initialise la base de données avec toutes les tables."""
import sqlite3
from config_loader import load_config

def setup_db():
    config = load_config()
    db_path = config['db_path']

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Tables principales
    c.execute("""CREATE TABLE IF NOT EXISTS items (...)""")
    c.execute("""CREATE TABLE IF NOT EXISTS tags (...)""")
    c.execute("""CREATE TABLE IF NOT EXISTS notes (...)""")
    c.execute("""CREATE TABLE IF NOT EXISTS emails (...)""")
    c.execute("""CREATE TABLE IF NOT EXISTS videos (...)""")
    c.execute("""CREATE TABLE IF NOT EXISTS events (...)""")
    c.execute("""CREATE TABLE IF NOT EXISTS contacts (...)""")
    c.execute("""CREATE TABLE IF NOT EXISTS lieux (...)""")
    c.execute("""CREATE TABLE IF NOT EXISTS vault (...)""")
    c.execute("""CREATE TABLE IF NOT EXISTS relations (...)""")
    c.execute("""CREATE TABLE IF NOT EXISTS url_metadata_cache (...)""")
    c.execute("""CREATE TABLE IF NOT EXISTS favorites (...)""")

    # Index
    # ...

    conn.commit()
    conn.close()
    print("✅ Base de données initialisée")

if __name__ == "__main__":
    setup_db()
```

---

## 4. Pipeline d'indexation

### Créer `index_all.py` (orchestrateur)
```python
"""Pipeline complet d'indexation."""
import subprocess
import sys

def run(script, description):
    print(f"\n▶ {description}...")
    result = subprocess.run([sys.executable, f"src/{script}"], capture_output=True)
    if result.returncode != 0:
        print(f"❌ Erreur : {result.stderr.decode()}")
        return False
    print("✅")
    return True

def main():
    steps = [
        ("generate_tags.py", "Génération tags fichiers"),
        ("index_content.py", "Indexation contenu code/texte"),
        ("index_notes.py", "Indexation Apple Notes"),
        ("index_emails.py", "Indexation emails IMAP"),
        ("import_vault.py --csv vault.csv", "Import coffre-fort"),
    ]

    for script, desc in steps:
        if not run(script, desc):
            print(f"\n⚠️  Erreur à l'étape : {desc}")
            choice = input("Continuer quand même ? [y/N] ")
            if choice.lower() != 'y':
                break

if __name__ == "__main__":
    main()
```

---

## 5. Documentation utilisateur

### Créer `INSTALL.md`
```markdown
# Installation BIG_BOFF Search

## Prérequis
- macOS 10.15+ (ou Windows/Linux avec adaptations)
- Python 3.9+
- Chrome ou Edge

## Installation rapide
\`\`\`bash
./install.sh
\`\`\`

## Configuration initiale
1. Éditer `~/.bigboff/config.json`
2. Configurer vos comptes email dans `~/.bigboff/email_accounts.json`
3. Lancer l'indexation : `python3 index_all.py`

## Lancement
\`\`\`bash
python3 src/server.py
\`\`\`

Ouvrir Chrome → charger extension depuis `extension/`
```

---

## 6. Tests d'installation

### Créer `test_install.py`
```python
"""Vérifie que l'installation est correcte."""
import os
import sqlite3
from pathlib import Path
from config_loader import load_config

def test_config():
    config = load_config()
    assert 'db_path' in config
    print("✓ Config chargée")

def test_database():
    config = load_config()
    db_path = config['db_path']
    assert Path(db_path).exists()

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in c.fetchall()]

    required = ['items', 'tags', 'notes', 'emails', 'events', 'contacts']
    for table in required:
        assert table in tables, f"Table manquante : {table}"

    print(f"✓ Base de données OK ({len(tables)} tables)")

def test_server():
    import requests
    try:
        resp = requests.get('http://127.0.0.1:7777/api/stats', timeout=2)
        assert resp.status_code == 200
        print("✓ Serveur répond")
    except:
        print("⚠️  Serveur non démarré (normal si pas encore lancé)")

if __name__ == "__main__":
    test_config()
    test_database()
    test_server()
    print("\n✅ Installation valide")
```

---

## 7. Adaptations plateforme

### Windows
- Remplacer AppleScript par alternatives (PowerShell pour Outlook ?)
- Adapter chemins (pas de ~, utiliser %USERPROFILE%)
- Tester corbeille (send2trash au lieu de AppleScript)

### Linux
- Alternative à Apple Notes (Markdown files ?)
- Tester avec Thunderbird pour emails
- Adapter ouverture fichiers (xdg-open)

---

## Priorités

| Priorité | Tâche | Effort |
|----------|-------|--------|
| 🔴 P0 | config_loader.py + config.json | 2h |
| 🔴 P0 | requirements.txt | 30min |
| 🔴 P0 | setup_db.py | 1h |
| 🟠 P1 | Refactor scripts avec argparse | 4h |
| 🟠 P1 | install.sh | 2h |
| 🟠 P1 | INSTALL.md | 1h |
| 🟡 P2 | index_all.py orchestrateur | 2h |
| 🟡 P2 | test_install.py | 1h |
| 🟢 P3 | Adaptations Windows/Linux | 8h+ |

**Temps total estimé : 15-20h**

---

## Prochaine étape

Commencer par **P0** : configuration centralisée pour découpler l'environnement utilisateur.
