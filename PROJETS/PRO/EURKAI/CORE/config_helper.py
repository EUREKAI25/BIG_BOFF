#!/usr/bin/env python3
"""
EURKAI — Config Helper
Gestion centralisée de la configuration (.env)
"""

import os
import sys
from pathlib import Path

MASTER_ENV = Path.home() / ".bigboff" / "secrets.env"
BIG_BOFF_ROOT = Path("/Users/nathalie/Dropbox/____BIG_BOFF___")

def ensure_master_exists():
    """Vérifie que le fichier maître existe."""
    if not MASTER_ENV.exists():
        print(f"❌ Fichier maître introuvable : {MASTER_ENV}")
        print(f"📝 Copie le template depuis EURKAI/CORE/env.template vers {MASTER_ENV}")
        sys.exit(1)
    print(f"✅ Fichier maître trouvé : {MASTER_ENV}")

def create_symlink(project_path: Path):
    """Crée un symlink .env dans le projet pointant vers le maître."""
    project_env = project_path / ".env"

    # Supprimer ancien .env s'il existe et n'est pas déjà un symlink correct
    if project_env.exists() or project_env.is_symlink():
        if project_env.is_symlink() and project_env.resolve() == MASTER_ENV:
            print(f"  ✓ Symlink déjà correct : {project_path.name}")
            return
        else:
            print(f"  🗑️  Suppression ancien .env : {project_path.name}")
            project_env.unlink()

    # Créer symlink
    try:
        project_env.symlink_to(MASTER_ENV)
        print(f"  ✅ Symlink créé : {project_path.name}")
    except Exception as e:
        print(f"  ❌ Erreur : {project_path.name} — {e}")

def find_projects():
    """Trouve tous les dossiers projet potentiels."""
    projects = []

    # Projets PRO
    pro_dir = BIG_BOFF_ROOT / "PROJETS" / "PRO"
    if pro_dir.exists():
        for item in pro_dir.iterdir():
            if item.is_dir() and item.name not in ["ARCHIVES", "_INPUTS", "_OUTPUTS", "_RULES", "_TESTS", "_TODO"]:
                projects.append(item)

                # Sous-projets (ex: CLAUDE/backend, CLAUDE/frontend)
                for subitem in item.iterdir():
                    if subitem.is_dir() and (subitem / "package.json").exists() or (subitem / "requirements.txt").exists():
                        projects.append(subitem)

    # Projets PERSO
    perso_dir = BIG_BOFF_ROOT / "PROJETS" / "PERSO"
    if perso_dir.exists():
        for item in perso_dir.iterdir():
            if item.is_dir():
                projects.append(item)

    return projects

def sync_all():
    """Synchronise tous les projets."""
    ensure_master_exists()

    print("\n🔄 Synchronisation des symlinks .env...\n")

    projects = find_projects()
    print(f"📦 {len(projects)} projets détectés\n")

    for project in projects:
        create_symlink(project)

    print(f"\n✅ Synchronisation terminée !")
    print(f"📍 Maître : {MASTER_ENV}")
    print(f"📝 Template : {BIG_BOFF_ROOT / 'PROJETS/PRO/EURKAI/CORE/env.template'}")

def clean_old_envs():
    """Nettoie les anciens .env (non-symlinks)."""
    print("\n🧹 Recherche des anciens .env à nettoyer...\n")

    old_envs = []

    for root, dirs, files in os.walk(BIG_BOFF_ROOT):
        # Ignorer ARCHIVES, node_modules, .git, etc.
        dirs[:] = [d for d in dirs if d not in ["ARCHIVES", "node_modules", ".git", "dist", "build", "__pycache__"]]

        for file in files:
            if file in [".env", "env.txt"] or file.startswith(".env."):
                filepath = Path(root) / file

                # Ignorer .env.example, .env.template
                if "example" in file or "template" in file:
                    continue

                # Ignorer symlinks corrects
                if filepath.is_symlink() and filepath.resolve() == MASTER_ENV:
                    continue

                old_envs.append(filepath)

    if not old_envs:
        print("✅ Aucun ancien .env trouvé")
        return

    print(f"⚠️  {len(old_envs)} anciens fichiers .env trouvés :\n")
    for env in old_envs:
        print(f"  • {env.relative_to(BIG_BOFF_ROOT)}")

    response = input(f"\n❓ Supprimer ces {len(old_envs)} fichiers ? (o/N) : ")
    if response.lower() == "o":
        for env in old_envs:
            try:
                env.unlink()
                print(f"  🗑️  Supprimé : {env.relative_to(BIG_BOFF_ROOT)}")
            except Exception as e:
                print(f"  ❌ Erreur : {env.relative_to(BIG_BOFF_ROOT)} — {e}")
        print("\n✅ Nettoyage terminé !")
    else:
        print("\n⏭️  Nettoyage annulé")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="EURKAI Config Helper")
    parser.add_argument("action", choices=["sync", "clean"],
                        help="sync: créer symlinks | clean: supprimer anciens .env")

    args = parser.parse_args()

    if args.action == "sync":
        sync_all()
    elif args.action == "clean":
        clean_old_envs()
