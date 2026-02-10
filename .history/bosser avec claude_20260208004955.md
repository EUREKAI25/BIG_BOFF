# ORGANISATION

## CLI — COMMANDES ESSENTIELLES

### Reprendre une session après plantage ou fermeture

| Quoi | Commande |
|------|----------|
| Reprendre la dernière session | `claude --continue` ou `claude -c` |
| Choisir parmi les sessions passées | `claude --resume` ou `claude -r` |
| Reprendre une session nommée | `claude --resume nom-de-session` |
| Forker (repartir sans modifier l'original) | `claude --continue --fork-session` |
| Depuis une session en cours | `/resume` ou `/resume nom` |
| Nommer sa session (pour la retrouver) | `/rename mon-nom` |
| Compacter le contexte (session longue) | `/compact` |

**À retenir** :
- Les sessions sont **sauvegardées automatiquement** en local, même en cas de crash
- Toujours nommer ses sessions avec `/rename` dès le début d'un travail important
- Les permissions de session ne sont pas héritées à la reprise → il faut les ré-approuver
- Ne pas reprendre la même session dans 2 terminaux (messages mélangés) → utiliser `--fork-session`

### Autres commandes utiles

| Quoi | Commande |
|------|----------|
| Voir le contexte consommé | `/context` |
| Aide générale | `/help` |

---

## RESSOURCES DISPONIBLES HORS CONNEXION / EN CAS DE PLANTAGE

### 1. Fichiers de pilotage (toujours accessibles en local)
Ces fichiers Dropbox sont lisibles même sans Claude, avec n'importe quel éditeur texte :

| Fichier | Rôle |
|---------|------|
| [_AUTO_BRIEF.md](file:///Users/nathalie/Dropbox/____BIG_BOFF___/CLAUDE/_AUTO_BRIEF.md) | État complet des travaux (fait / à faire) |
| [Claude.md](file:///Users/nathalie/Dropbox/____BIG_BOFF___/CLAUDE/Claude.md) | Contrat, règles permanentes, conventions |
| [_CRON.md](file:///Users/nathalie/Dropbox/____BIG_BOFF___/CLAUDE/_CRON.md) | Tâches planifiées |
| [_MOVES_LOG.md](file:///Users/nathalie/Dropbox/____BIG_BOFF___/CLAUDE/_MOVES_LOG.md) | Journal des déplacements/renommages |
| [_HUB.md](file:///Users/nathalie/Dropbox/____BIG_BOFF___/_HUB.md) | Carte centrale de tous les projets |
| Chaque projet : `_SUIVI.md` | Suivi détaillé par projet |

> **En cas de plantage** : relire [_AUTO_BRIEF.md](file:///Users/nathalie/Dropbox/____BIG_BOFF___/CLAUDE/_AUTO_BRIEF.md) pour savoir exactement où on en était.

### 2. Mémoire persistante de Claude
Claude stocke ses notes dans :
```
~/.claude/projects/.../memory/MEMORY.md
```
Ce fichier est rechargé automatiquement à chaque nouvelle session. Il contient le protocole de session et les chemins vers tous les fichiers de pilotage.

### 3. Historique des conversations
- Les sessions Claude Code sont stockées localement sur la machine
- Accessibles via `claude --resume` (sélecteur interactif avec recherche)
- Les conversations GPT sont dans le répertoire dédié de chaque projet

### 4. Git / GitHub
- Chaque commit = un point de restauration du code
- `git log` pour voir l'historique
- `git diff` pour voir ce qui a changé depuis le dernier commit
- `git stash` pour sauvegarder du travail en cours sans commiter
- GitHub = backup distant, accessible depuis n'importe quel poste

### 5. Stratégie de résilience — checklist

- [ ] Nommer chaque session Claude (`/rename`)
- [ ] Commiter régulièrement sur git avec messages clairs
- [ ] Garder `_AUTO_BRIEF.md` à jour après chaque action significative
- [ ] Garder `_SUIVI.md` à jour dans chaque projet actif
- [ ] Pousser sur GitHub régulièrement (`git push`)

---

## RÈGLES DE TRAVAIL AVEC CLAUDE

Lui mettre à disposition pour chaque projet les ressources, les règles, l'objectif etc (cahier des charges)
- La pipeline à respecter
- Mettre à jour à mesure et prévoir le prompt avec path à lui donner systématiquement
- J'enregistre à mesure les conversations GPT dans un répertoire dédié pour chaque projet — Claude peut puiser dedans, le prompt lui indique sa présence
- Backup GitHub systématique avec état des lieux avancement, tâches pour la suite

