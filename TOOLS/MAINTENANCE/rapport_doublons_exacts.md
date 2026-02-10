# Rapport doublons exacts (SHA256) — 2026-02-08

> Généré automatiquement par `hash_secondpass.py`
> Base : `catalogue.db` — 13 959 fichiers hashés

## Résumé

| Métrique | Valeur |
|---|---|
| Fichiers hashés | 13 959 |
| Fichiers cloud-only (non hashables) | 25 782 |
| Fichiers > 50 Mo (exclus) | 213 |
| **Paires de doublons exacts** | **3 173** |
| **Espace récupérable** | **~553 Mo** |

## Répartition par domaine

| Domaine | Paires | Espace (Mo) | Nature |
|---|---|---|---|
| SUBLYM_APP_PUB | 403 | ~370 Mo | Vidéos mp4, templates MotionArray en double |
| MEDIAS/PORTFOLIO | 81 | ~142 Mo | Images peinture numérique dupliquées entre sous-dossiers |
| MEDIAS/FORMATIONS | 9 | ~56 Mo | PDFs/vidéos formations dupliquées |
| MEDIAS/VIDEOS | 17 | ~41 Mo | Photos Rome triées dans 2 dossiers |
| BIGBOFF | 1410 | ~13 Mo | Zips de chantiers en double (CHANTIERS/ vs CHANTIERS/CHANTIERS/) |
| EURKAI | 811 | ~4 Mo | Petits fichiers code/config en double entre incarnations |
| INTERAGENTS | 330 | ~0,5 Mo | Fichiers dupliqués entre _OLD/ et TOOL/ |
| MEDIAS/PHOTOS | 30 | ~9 Mo | Photos en double |
| Autre | 82 | ~13 Mo | Divers |

## Actions recommandées (en attente validation Nathalie)

### Priorité 1 — Zips SUBLYM redondants (~350 Mo)
10 zips dans `ARCHIVES/SUBLYM_HISTORIQUE/_ZIPS/` ont un dossier décompressé identique à côté :
- SUBLYM24.zip, SUBLYM24 2.zip, SUBLYM24 3.zip → dossier SUBLYM24/ existe
- SUBLYM241.zip → dossier SUBLYM241/ existe
- SUBLYM72.zip, SUBLYM72 2.zip → dossier SUBLYM72/ existe
- SUBLYM_APP copie.zip → dossier SUBLYM_APP copie/ existe
- SUBLYM_MVP.zip, SUBLYM_MVP 2.zip → dossier SUBLYM_MVP/ existe
- front24.zip → dossier front24/ existe

**Recommandation** : supprimer ces 10 zips (le contenu est déjà dans les dossiers à côté)

### Priorité 2 — SUBLYM_APP_PUB (~370 Mo récupérables)
Nombreuses vidéos mp4 en double :
- `Living in a moment/` existe en 3 copies (racine + MOTIONARRAY/ × 2)
- Avatars Julien : même `final.mp4` copié sous 4-5 noms différents
- SublymTest.mp4 en double (racine + michael/)

**Recommandation** : dédupliquer les templates MotionArray et les vidéos avatar

### Priorité 3 — BIGBOFF/CHANTIERS (~13 Mo, mais 1410 paires)
Structure `CHANTIERS/CHANTIERS/` imbriquée = chaque fichier existe en double :
- `CHANTIERS-2/CHANTIERS/CHANTIERS/` est une copie de `CHANTIERS-2/CHANTIERS/`

**Recommandation** : supprimer le sous-dossier CHANTIERS/CHANTIERS/ imbriqué

### Priorité 4 — Photos/Vidéos Rome (~41 Mo)
Photos du vendredi 25 octobre dupliquées entre :
- `25_Vendredi/rome/` et `23_Mercredi/Rome, 25 octobre 2024/`

**Recommandation** : fusionner les deux dossiers

### À ne PAS toucher (pour le moment)
- MEDIAS/PORTFOLIO : même image classée dans plusieurs catégories = intentionnel ?
- EURKAI : doublons entre incarnations historiques (archivées)
