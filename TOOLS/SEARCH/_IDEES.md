# Idées de Nathalie à étudier plus tard
# MENU CONTEXTUEL
- sur claude ou chatgpt -> récupère la conversation - option formater / partager

---

# Suggestions Claude — Phases 6-7-8 P2P (2026-02-11)

## Optimisations techniques avant tests utilisateurs

### 1. Performance & UX
- [ ] **Indicateur progression sync** : Barre de progression lors du clone initial (50+ items)
- [ ] **Notification fin de sync** : Toast "X nouveaux éléments synchronisés"
- [ ] **Cache local QR** : Mémoriser derniers QR générés (éviter re-génération)
- [ ] **Compression sync** : Gzip payload JSON pour partages volumineux (>1000 items)
- [ ] **Pagination sync** : Limiter à 100 items par batch (éviter timeout)

### 2. Sécurité & robustesse
- [ ] **Rate limiting relay** : Max 10 requêtes/min par user (anti-spam)
- [ ] **Validation taille payload** : Max 10 Mo par push (éviter DOS)
- [ ] **Expiration tokens JWT** : Cleanup automatique tokens expirés (>24h)
- [ ] **Révocation QR usagés** : Marquer QR comme "used" après accept
- [ ] **Log audit relay** : Tracer qui partage quoi à qui (RGPD compliance)

### 3. Amélioration UX partage
- [ ] **Preview contenu QR** : Modal "X va partager Y éléments (tag:recettes)" avant scan
- [ ] **Historique partages** : Vue "Mes partages" (actifs/révoqués) dans UI
- [ ] **Notifications partage** : "Alice a partagé 12 recettes avec toi" (push optionnel)
- [ ] **Recherche dans groupes** : Autocomplete groupes existants lors création permission
- [ ] **Icônes groupes** : Avatar généré automatiquement (initiales + couleur)

### 4. Debug & monitoring (dev)
- [ ] **Dashboard relay** : Page admin /admin (stats users, partages actifs, erreurs)
- [ ] **Logs structurés** : JSON logging avec niveaux (DEBUG/INFO/ERROR)
- [ ] **Health check** : Endpoint /health (relay + DB accessible)
- [ ] **Metrics Prometheus** : Exporter nb users, partages, sync/min (pour scalabilité)

### 5. Documentation utilisateur
- [ ] **Tutorial onboarding** : 3 slides explicatives au 1er lancement
- [ ] **FAQ intégrée** : Bouton "?" dans UI → popup aide contextuelle
- [ ] **Vidéo démo 30s** : Générer QR → scanner → sync (screencast)
- [ ] **Guide troubleshooting** : Que faire si sync échoue / QR invalide

### 6. Préparation Phase 9 (Freemium)
- [ ] **Compteur usage gratuit** : Tracker nb partages/groupes/devices (limite à définir)
- [ ] **Modal upgrade premium** : "Limite atteinte, passer premium ?" (non bloquant pour MVP)
- [ ] **Feature flags** : Table relay pour activer/désactiver fonctions par user

### 7. Mobile first (avant responsive)
- [ ] **PWA manifest.json** : Icône, nom, couleurs (installable sur mobile)
- [ ] **Service worker** : Cache offline basique (UI fonctionne sans relay)
- [ ] **Touch gestures** : Swipe left sur résultat = révéler bouton partage
- [ ] **Camera permission** : Demander accès caméra uniquement au scan QR (pas au load)

### 8. Tests automatisés à ajouter
- [ ] **Test charge relay** : 100 users simultanés, 1000 items chacun (Apache Bench)
- [ ] **Test révocation cascade** : Supprimer groupe → vérifier permissions supprimées
- [ ] **Test offline** : Sync échoue → retry auto après reconnexion
- [ ] **Test corruption DB** : Relay DB corrompue → fallback gracieux
- [ ] **Test multi-device race** : Desktop + Mobile sync simultané → pas de conflit

### 9. Quick wins (2-3h chacun)
- [ ] **Bouton "Copier lien QR"** : Partage via SMS/WhatsApp (fallback si scan échoue)
- [ ] **Dark mode** : CSS prefers-color-scheme (extension + fullpage)
- [ ] **Shortcut clavier** : Ctrl+K = focus recherche, Ctrl+Q = scanner QR
- [ ] **Export permissions CSV** : Backup liste partages pour migration
- [ ] **Import groupes JSON** : Créer groupe en masse depuis fichier

### 10. Idées long terme (post-MVP)
- [ ] **Sync intelligent** : Détecter conflits (2 users modifient même item) → merge auto
- [ ] **Historique versions** : Garder 5 versions d'un item partagé (undo)
- [ ] **Permissions temporaires** : "Partager pendant 7 jours" (auto-révocation)
- [ ] **Groupes hiérarchiques** : Sous-groupes (Famille > Parents > Maman)
- [ ] **Marketplace tags** : Découvrir tags populaires partagés publiquement (opt-in)

---

## Priorisation recommandée (pré-tests utilisateurs)

**🔴 Critique (faire avant tests) :**
1. Rate limiting relay (sécurité)
2. Indicateur progression sync (UX)
3. Health check endpoint (monitoring)

**🟡 Important (faire pendant bêta) :**
4. Historique partages (transparence)
5. Tutorial onboarding (adoption)
6. Test charge relay (scalabilité)

**🟢 Nice to have (post-bêta) :**
7. Dark mode
8. Export/import permissions
9. Sync intelligent conflits

