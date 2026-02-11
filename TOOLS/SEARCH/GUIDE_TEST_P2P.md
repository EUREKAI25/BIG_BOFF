# Guide de test P2P — Phases 1-8

> **But :** Tester le système de partage décentralisé en conditions réelles
> **Durée :** 15-20 minutes
> **Prérequis :** Serveur local lancé (`python3 src/server.py`)

---

## 🎯 Scénario de test complet

**Personnages :**
- **Alice** (toi) : Propriétaire de données, va partager avec Bob
- **Bob** (simulé) : Destinataire du partage

**Ce qu'on va tester :**
1. ✅ Créer une identité décentralisée (Phase 1)
2. ✅ Lancer le relay server (Phase 2)
3. ✅ Générer un QR code de partage (Phase 4)
4. ✅ Scanner le QR et accepter le partage (Phase 4)
5. ✅ Cloner des données en mode partage (Phase 6)
6. ✅ Créer un groupe et partager (Phase 7)

---

## 📋 ÉTAPE 1 : Préparer l'environnement

### 1.1 Vérifier que tout est installé

```bash
cd /Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/SEARCH

# Vérifier dépendances
pip list | grep -E "PyJWT|qrcode|Pillow|requests"
# Si manquant : pip install -r requirements.txt
```

### 1.2 Lancer les serveurs (2 terminaux)

**Terminal 1 — Serveur local (port 7777) :**
```bash
cd /Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/SEARCH
python3 src/server.py
```

**Terminal 2 — Relay server (port 8888) :**
```bash
cd /Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/SEARCH
python3 src/relay_server.py
```

✅ **Validation :** Tu dois voir :
- Terminal 1 : `Serveur BIG_BOFF sur http://127.0.0.1:7777`
- Terminal 2 : `Relay server sur http://127.0.0.1:8888`

---

## 🆔 ÉTAPE 2 : Créer ton identité Alice (Phase 1)

### 2.1 Générer tes clés

**Terminal 3 (nouveau) :**
```bash
cd /Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/SEARCH/src

# Générer identité Alice
python3 identity.py generate --alias alice
```

✅ **Validation :** Tu dois voir :
```
✅ Identité générée avec succès !
   User ID : bigboff_a1b2c3d4e5f6...
   Alias : alice
   Fichier : ~/.bigboff/identity.json
```

### 2.2 Vérifier ton identité

```bash
python3 identity.py info
```

Tu dois voir tes clés RSA et Ed25519, ton User ID, etc.

---

## 🔄 ÉTAPE 3 : S'enregistrer sur le relay (Phase 2)

### 3.1 Enregistrer Alice sur le relay

```bash
python3 sync.py register
```

✅ **Validation :**
```
✅ Utilisateur enregistré sur le relay
   User ID : bigboff_a1b2c3d4...
```

### 3.2 Tester la connexion

```bash
python3 sync.py push
```

Si c'est vide (première fois), c'est normal. L'important est que ça ne donne pas d'erreur.

---

## 📱 ÉTAPE 4 : Générer un QR de partage (Phase 4)

### 4.1 Créer un QR pour partager le tag "test"

```bash
python3 qr_share.py generate \
  --scope-type tag \
  --scope-value test \
  --mode consultation
```

✅ **Validation :** Un fichier `qr_share_<timestamp>.png` est créé dans le dossier courant.

### 4.2 Voir le QR

```bash
open qr_share_*.png
```

Tu verras une image QR avec les infos :
- User ID Alice
- Scope : tag:test
- Mode : consultation
- Expiration : 24h
- Signature Ed25519

---

## 🧪 ÉTAPE 5 : Simuler Bob qui scanne le QR

### 5.1 Créer identité Bob (dans un autre dossier)

**Option A — Simuler avec une 2e identity :**
```bash
# Sauvegarder identité Alice
cp ~/.bigboff/identity.json ~/.bigboff/identity_alice.json

# Créer identité Bob
python3 identity.py generate --alias bob

# Bob s'enregistre
python3 sync.py register
```

### 5.2 Bob vérifie le QR (scanner simulé)

```bash
# Récupérer les données du QR (exemple si tu as le JSON)
python3 qr_share.py verify --qr-file qr_share_*.png
```

✅ **Validation :** Tu dois voir :
```
✅ QR valide
   Propriétaire : alice (bigboff_a1b2...)
   Scope : tag:test
   Mode : consultation
   Expiration : 2026-02-12 05:30
```

---

## 🎁 ÉTAPE 6 : Tester le partage permanent (Phase 6)

### 6.1 Alice crée des items avec tag "recettes"

**Via l'UI Chrome ou en SQL direct :**
```bash
sqlite3 /Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/MAINTENANCE/catalogue.db <<EOF
INSERT INTO items (nom, extension, chemin_relatif)
VALUES ('pizza.md', 'md', '/test/');
INSERT INTO item_tags (item_id, tag)
VALUES (last_insert_rowid(), 'recettes');
EOF
```

### 6.2 Alice génère QR mode "partage"

```bash
python3 qr_share.py generate \
  --scope-type tag \
  --scope-value recettes \
  --mode partage
```

### 6.3 Alice crée une permission partage pour Bob

```bash
python3 permissions.py grant bob tag recettes --mode partage
```

✅ **Validation :**
```
✅ Permission accordée
   À : bob
   Scope : tag:recettes
   Mode : partage (clone permanent)
```

### 6.4 Bob clone les recettes

```bash
# Restaurer identité Bob si tu avais changé
cp ~/.bigboff/identity_bob.json ~/.bigboff/identity.json

# Clone initial
python3 sync.py share clone alice tag recettes
```

✅ **Validation :**
```
✅ Clone réussi : 1 élément(s) partagé(s)
   Propriétaire : alice
   Scope : tag:recettes
   Mode : partage permanent (is_shared_copy=1)
```

### 6.5 Vérifier dans la base Bob

```bash
sqlite3 /Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/MAINTENANCE/catalogue.db \
  "SELECT id, nom, source_user_id, is_shared_copy FROM items WHERE is_shared_copy=1"
```

Tu dois voir `pizza.md` avec `source_user_id=alice` et `is_shared_copy=1`.

---

## 👥 ÉTAPE 7 : Tester les groupes (Phase 7)

### 7.1 Alice crée un groupe "Famille"

```bash
# Redevenir Alice
cp ~/.bigboff/identity_alice.json ~/.bigboff/identity.json

python3 groups.py create Famille
```

✅ **Validation :**
```
✅ Groupe créé
   ID : grp_123abc...
   Nom : Famille
   Propriétaire : alice
```

### 7.2 Alice invite Bob au groupe

```bash
python3 groups.py invite grp_123abc bob
```

✅ **Validation :**
```
✅ Invitation créée
   Groupe : Famille
   Invité : bob
   QR code : qr_group_invite_*.png
```

### 7.3 Bob accepte l'invitation (simulé)

```bash
# En tant que Bob
cp ~/.bigboff/identity_bob.json ~/.bigboff/identity.json

python3 groups.py join grp_123abc
```

✅ **Validation :**
```
✅ Rejoint le groupe
   Groupe : Famille
   Rôle : member
```

### 7.4 Alice partage tag "photos" au groupe

```bash
# Redevenir Alice
cp ~/.bigboff/identity_alice.json ~/.bigboff/identity.json

# Créer permission groupe (directement via relay)
# Commande à implémenter ou via SQL direct pour le test
```

---

## ✅ ÉTAPE 8 : Vérifier que tout fonctionne

### 8.1 Lancer le test d'intégration automatique

```bash
cd /Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/SEARCH
./test_integration_ph6_7_8.sh
```

✅ **Validation :**
```
=========================================
  ✅ INTÉGRATION PH6-7-8 RÉUSSIE !
=========================================
```

---

## 🎨 ÉTAPE 9 : Tester via l'UI Chrome

### 9.1 Ouvrir l'extension

1. Clique sur l'icône BIG_BOFF dans Chrome
2. Tu dois voir le bouton **"Partager"** (icône share-nodes)
3. Tu dois voir le bouton **"Groupes"** (icône users)

### 9.2 Tester le partage via UI

1. Cherche un tag (ex: "recettes")
2. Clique sur le bouton **Partager**
3. Tu vois un modal avec :
   - Radio buttons : ⚪ Consultation / ⚪ Partage
   - Bouton "Générer QR"
4. Sélectionne **Partage**
5. Clique **Générer QR**
6. Un QR code s'affiche avec les infos

### 9.3 Tester les groupes via UI

1. Clique sur le bouton **Groupes**
2. Tu vois la liste de tes groupes
3. Clique **Créer un groupe**
4. Entre un nom → Crée
5. Tu vois le groupe dans la liste

---

## 🐛 Dépannage

### Le relay server ne démarre pas

```bash
# Vérifier que le port 8888 est libre
lsof -i :8888

# Si occupé, kill le processus
kill -9 <PID>
```

### Erreur "identity.json not found"

```bash
# Régénérer l'identité
cd src
python3 identity.py generate --alias alice
```

### QR code invalide

```bash
# Vérifier que le QR n'est pas expiré (24h)
python3 qr_share.py verify --qr-file qr_share_*.png
```

### Permission denied

```bash
# Vérifier que la permission existe
sqlite3 ~/.bigboff/relay.db \
  "SELECT * FROM permissions WHERE owner_user_id LIKE '%alice%'"
```

---

## 📊 Métriques de succès

À la fin du test, tu dois avoir :

- [x] 2 identités créées (Alice + Bob)
- [x] 2 users enregistrés sur le relay
- [x] 1+ permissions créées (consultation ou partage)
- [x] 1+ items clonés (is_shared_copy=1)
- [x] 1 groupe créé avec 2+ membres
- [x] QR codes générés et vérifiés
- [x] UI extension fonctionnelle (boutons partage/groupes)

**Si tout est ✅ → Phases 1-8 validées en conditions réelles !** 🎉

---

## 📞 Prochaines étapes

1. **Tester avec un vrai 2e appareil** (smartphone, 2e laptop)
2. **Tester la révocation** (partage → révoque → vérifie snapshot figé)
3. **Tester le multi-device** (QR activation type WhatsApp Web)
4. **Stress test** (1000 items partagés, 10 groupes)

---

**Besoin d'aide ?** Vérifie les logs des serveurs (Terminal 1 et 2) pour voir les erreurs détaillées.
