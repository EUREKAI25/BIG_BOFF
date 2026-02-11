# Corbeille de sécurité — Auto-destruction

> **Date de création** : 2026-02-08
> **Date de destruction** : 2026-08-08 (6 mois)
> **Statut** : En attente de destruction

---

## Contenu

Doublons exacts (SHA256 identique) déplacés depuis l'ensemble du Dropbox BIG_BOFF.
Pour chaque groupe de doublons, **un seul exemplaire a été conservé à son emplacement d'origine**.
Les copies en surplus sont ici, classées par catégorie.

## Règle

- Passé le 2026-08-08, ce dossier peut être supprimé intégralement.
- Avant cette date, tout fichier peut être restauré à son emplacement d'origine (voir `_INVENTAIRE.csv`).
- En cas de doute sur un fichier, le chercher dans BIG_BOFF Search (l'original y est toujours indexé).

## Structure

```
_CORBEILLE_SECURITE/
├── _MANIFESTE.md          ← ce fichier
├── _INVENTAIRE.csv        ← chemin original, hash, taille, date de déplacement
├── avatars_sublym/        ← doublons SUBLYM_APP_PUB/Avatars
├── motionarray/           ← doublons MOTIONARRAY
├── formations/            ← doublons formations
├── copies_conflit/        ← fichiers "(1)", "(2)"...
└── divers/                ← autres doublons
```
