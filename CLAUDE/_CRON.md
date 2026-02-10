# Cron — Tâches planifiées

> À consulter et exécuter à chaque début de session Claude.
> Chaque tâche a une fréquence. Si la date d'échéance est dépassée, l'exécuter.

**Dernière vérification** : 2026-02-08

---

## Tâches automatisées (LaunchAgent)

| Tâche | Fréquence | LaunchAgent | Script |
|---|---|---|---|
| **BIG_BOFF Pulse** — heartbeat système | **1 tick/seconde** (KeepAlive) | `com.bigboff.pulse` | `TOOLS/pulse.py` |
| BIG_BOFF Search — serveur | permanent (KeepAlive) | `com.bigboff.search` | `TOOLS/SEARCH/src/server.py` |

### Tâches gérées par le Pulse (`_PULSE.json`)

| Tâche | Intervalle | Action | Statut |
|---|---|---|---|
| Alertes / rappels | 1s | `check_alerts` → notification macOS | actif |
| Scan nouveaux fichiers | 60s | `scan_new_files` → catalogue + tags via Spotlight | actif |
| Pipeline agence | 60s | `pipeline_check` → dispatcher.py | actif |
| Sync emails IMAP | 6h | `sync_emails` | désactivé |
| Indexation contenu | 24h | `content_index` | désactivé |
| Nettoyage + VACUUM | 7 jours | `maintenance_cleanup` | actif |

## Tâches de maintenance

| Tâche | Fréquence | Prochaine échéance | Script/Action |
|---|---|---|---|
| Détecter les dossiers-projets sans `_SUIVI.md` | hebdo | 2026-02-14 | Scan `find` + création auto |
| Détecter les `_SUIVI.md` obsolètes (> 30j) | hebdo | 2026-02-14 | Scan dates + alerte |
| Nettoyer `_MOVES_LOG.md` (archiver les confirmés) | mensuel | 2026-03-07 | Manuel |
| Relancer `catalogue.py` (mise à jour base) | mensuel | 2026-03-07 | `python3 TOOLS/MAINTENANCE/catalogue.py` |
| Vérifier cohérence `_HUB.md` vs réalité | mensuel | 2026-03-07 | Comparer dossiers existants vs entrées hub |

## Tâches projet

| Tâche | Fréquence | Prochaine échéance | Détail |
|---|---|---|---|
| Lister les projets 🟣 (action requise Nathalie) | chaque session | **chaque session** | Lire `_HUB.md`, alerter en début de conversation |
| MAJ `_AUTO_BRIEF.md` | chaque session | **chaque session** | Après chaque action significative |
| Avancement ménage de printemps | chaque session | **chaque session** | Vérifier `EURKAI/_SUIVI.md` module ménage-local |

## Tâches ponctuelles (one-shot, à traiter dès que possible)

| Tâche | Priorité | Statut | Détail |
|---|---|---|---|
| ~~Consolidation SUBLYM~~ | haute | ✅ fait | Exécuté 2026-02-07 — 16 dossiers archivés, 7 modules migrés |
| ~~Consolidation EURKAI~~ | haute | ✅ fait | Exécuté 2026-02-07 — 4 dossiers archivés, 6 fragments copiés |
| ~~Consolider BBOFF/BIGBOFF~~ | moyenne | ✅ fait | BBOFF copie archivé, BBOFF et BIGBOFF qualifiés |
| ~~Trier NEW, RESTART, front24~~ | basse | ✅ fait | front24+NEW archivés, RESTART gardé |
| ~~Qualifier _INPUTS, _OUTPUTS, _RULES, _TESTS, _TODO~~ | basse | ✅ fait | Qualifiés comme référence/listes de tâches |
| Explorer Dropbox hors BIG_BOFF | basse | ⚪ à planifier | DOMAINES2, ENVIES, IMAGES, _INBOX, etc. |
| **Supprimer `_CORBEILLE_SECURITE/`** | **one-shot** | **2026-08-08** | Doublons vérifiés, 6 mois de sécurité écoulés → supprimer le dossier entièrement |
| Auto-triage ~/Downloads (module EURKAI) | basse | ⚪ idée | Script launchd + fswatch, classement après 30min d'inactivité |
| ~~Hash SHA256 (second pass)~~ | basse | ✅ fait | 13 959 hashés, 3 173 doublons exacts (~553 Mo). Script : `hash_secondpass.py` |
| Indexation full-text + moteur de recherche | basse | ⚪ à faire | Module EURKAI CATALOGS |

---

## Comment ça marche

1. En début de session, Claude lit ce fichier
2. Il vérifie les dates d'échéance
3. Il exécute les tâches échues
4. Il met à jour "Prochaine échéance" et "Dernière vérification"
5. Les tâches ponctuelles complétées sont déplacées en bas dans "Historique"

## Historique (tâches ponctuelles terminées)

_Vide pour le moment._
