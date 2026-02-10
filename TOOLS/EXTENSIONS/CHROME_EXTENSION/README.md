# Extension Chrome - Éditeur Accordéons

Extension Chrome pour accès rapide à l'éditeur d'accordéons avec capture de contenu depuis n'importe quelle page web.

## Installation

1. Ouvrez Chrome et allez à `chrome://extensions/`

2. Activez le **Mode développeur** (coin supérieur droit)

3. Cliquez sur **"Charger l'extension non empaquetée"**

4. Sélectionnez le dossier `CHROME_EXTENSION` de ce projet

5. L'extension devrait apparaître dans votre barre d'extensions

6. **Important** : Épinglez l'icône pour un accès rapide (cliquez sur l'icône puzzle 🧩 puis sur la punaise 📌 à côté de "Éditeur Accordéons")

## Utilisation

### Ouvrir l'éditeur

**Méthode 1 : Clic sur l'icône**
- Cliquez sur l'icône de l'extension dans la barre d'outils
- L'éditeur s'ouvre dans un nouvel onglet

**Méthode 2 : Menu contextuel**
- Faites un clic droit n'importe où dans Chrome
- (Le menu "Ouvrir l'Éditeur" sera disponible dans une version future)

### Capturer du contenu depuis une page web

1. **Sélectionnez du texte** sur n'importe quelle page web

2. **Clic droit** sur la sélection

3. Choisissez **"Ajouter à l'Éditeur Accordéons"**

4. L'éditeur s'ouvre automatiquement avec une modale de collage pré-remplie contenant :
   - Le titre de la page comme section H1
   - Le texte sélectionné
   - Le lien source

5. Cliquez sur **"Insérer"** pour ajouter le contenu à votre éditeur

### Capturer un lien

1. **Clic droit sur un lien** (sans sélectionner de texte)

2. Choisissez **"Ajouter à l'Éditeur Accordéons"**

3. Le lien et le titre de la page sont capturés

### Capturer la page entière

1. **Clic droit** n'importe où sur la page (sans sélection de texte)

2. Choisissez **"Ajouter à l'Éditeur Accordéons"**

3. Le titre et l'URL de la page sont capturés

## Fonctionnalités

- ✅ **Bouton dans la barre d'outils** : Accès rapide à l'éditeur
- ✅ **Menu contextuel** : Capture de contenu depuis n'importe quelle page
- ✅ **Capture de texte sélectionné** : Le texte que vous sélectionnez est automatiquement inclus
- ✅ **Capture de liens** : URL et titre de page automatiquement ajoutés
- ✅ **Format Markdown** : Le contenu capturé est formaté en Markdown avec titre H1
- ✅ **Notifications** : Confirmation visuelle de l'ajout

## Prérequis

L'éditeur doit être en cours d'exécution sur `http://localhost:5173`

Pour lancer l'éditeur :
```bash
cd /path/to/accordion-editor
sh deploy.sh
```

## Permissions

L'extension demande les permissions suivantes :

- **contextMenus** : Pour créer le menu contextuel "Ajouter à l'Éditeur"
- **tabs** : Pour récupérer le titre et l'URL de la page active
- **notifications** : Pour afficher des confirmations
- **storage** : Pour transmettre les données capturées à l'éditeur
- **host_permissions (localhost:5173)** : Pour communiquer avec l'éditeur local

## Sécurité

- ✅ Fonctionne uniquement en local (localhost)
- ✅ Aucune donnée envoyée sur Internet
- ✅ Aucun tracking ou analytics
- ✅ Code source ouvert et auditable

## Dépannage

### L'extension ne s'affiche pas
- Vérifiez que le mode développeur est activé
- Rechargez l'extension depuis `chrome://extensions/`

### "Erreur lors de l'ajout du contenu"
- Vérifiez que l'éditeur est bien lancé sur `http://localhost:5173`
- Testez l'accès à `http://localhost:5173` dans un onglet

### Le contenu capturé n'apparaît pas
- Actualisez la page de l'éditeur
- Vérifiez les permissions de l'extension
- Consultez la console Chrome (F12) pour les erreurs

### Le menu contextuel ne s'affiche pas
- Rechargez l'extension
- Redémarrez Chrome si nécessaire

## Structure des fichiers

```
CHROME_EXTENSION/
├── manifest.json          # Configuration de l'extension
├── service_worker.js      # Logic de fond (menus, capture)
├── icons/
│   ├── icon-16.png       # Icône 16x16
│   ├── icon-48.png       # Icône 48x48
│   └── icon-128.png      # Icône 128x128
└── README.md             # Cette documentation
```

## Développement

Pour modifier l'extension :

1. Modifiez les fichiers sources
2. Allez à `chrome://extensions/`
3. Cliquez sur l'icône ⟳ (recharger) de l'extension
4. Testez vos modifications

## Limitations connues (V1)

- L'extension ne fonctionne qu'avec un éditeur en local
- Pas de synchronisation cloud
- Nécessite que l'éditeur soit lancé manuellement

## Améliorations futures

- [ ] Détection automatique si l'éditeur est lancé
- [ ] Options de configuration (port, format de capture)
- [ ] Raccourcis clavier personnalisables
- [ ] Capture d'images (avec conversion en markdown)
- [ ] Mode hors ligne avec queue de synchronisation
