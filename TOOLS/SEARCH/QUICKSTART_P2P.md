# Quickstart P2P — 5 minutes chrono

> **Test ultra-rapide du système de partage P2P**

## 🚀 Démarrage en 3 commandes

### 1️⃣ Lancer les serveurs (2 terminaux)

**Terminal 1 :**
```bash
cd /Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/SEARCH
python3 src/server.py
# → http://127.0.0.1:7777
```

**Terminal 2 :**
```bash
cd /Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/SEARCH
python3 src/relay_server.py
# → http://127.0.0.1:8888
```

### 2️⃣ Créer ton identité

**Terminal 3 :**
```bash
cd /Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/SEARCH/src
python3 identity.py generate --alias alice
python3 sync.py register
```

✅ Tu dois voir : `✅ Identité générée` et `✅ Utilisateur enregistré`

### 3️⃣ Générer un QR de partage

```bash
python3 qr_share.py generate --scope-type tag --scope-value test --mode consultation
open qr_share_*.png
```

✅ Un QR code s'affiche avec tes infos de partage !

---

## 🧪 Test automatique complet

**Pour valider que tout marche :**

```bash
cd /Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/SEARCH
./test_integration_ph6_7_8.sh
```

✅ **Si tu vois :**
```
=========================================
  ✅ INTÉGRATION PH6-7-8 RÉUSSIE !
=========================================
```

**→ Tout fonctionne ! 🎉**

---

## 🎨 Test via l'UI Chrome

1. **Ouvre l'extension** BIG_BOFF dans Chrome
2. Tu dois voir **2 nouveaux boutons** :
   - 🔗 **Partager** (share-nodes icon)
   - 👥 **Groupes** (users icon)

3. **Tester le partage :**
   - Cherche un tag
   - Clique **Partager**
   - Sélectionne mode (Consultation / Partage)
   - Génère le QR
   - ✅ QR affiché !

4. **Tester les groupes :**
   - Clique **Groupes**
   - Clique **Créer un groupe**
   - Entre un nom
   - ✅ Groupe créé !

---

## ❓ Problème ?

### Les serveurs ne démarrent pas

```bash
# Vérifier les ports
lsof -i :7777
lsof -i :8888

# Si occupé, kill
kill -9 <PID>
```

### Erreur identity.json

```bash
cd src
python3 identity.py generate --alias alice
```

### Voir les logs détaillés

Regarde les terminaux 1 et 2 où tournent les serveurs.

---

## 📖 Pour aller plus loin

**Guide complet :** `GUIDE_TEST_P2P.md`
- Scénarios Alice/Bob détaillés
- Tests partage permanent (Phase 6)
- Tests groupes (Phase 7)
- Tests multi-device (Phase 8)

**Documentation phases :** `README.md`

---

**C'est prêt !** Les Phases 1-8 P2P sont opérationnelles 🚀
