# Idées — TIP_CALCULATOR

> Idées d'améliorations futures (hors scope initial)

---

## IDÉES NATHALIE

_Section réservée à tes idées — ajoute-les ici_

- [ ]

---

## IDÉES CLAUDE

### Fonctionnalités v2

- [ ] **Historique** : Sauvegarde des 10 derniers calculs (LocalStorage)
- [ ] **Partage** : Générer un lien court ou QR code pour partager le calcul
- [ ] **Multi-devises** : Support $, £, CHF avec conversion temps réel
- [ ] **Partage inégal** : Mode "qui paye quoi" avec montants individuels
- [ ] **Pourboire suggéré** : Recommandation basée sur la qualité du service (emoji slider : 😞 → 😐 → 😊 → 🤩)
- [ ] **Arrondi intelligent** : Option "arrondir au 5€ supérieur" pour simplifier

### Optimisations

- [ ] **PWA** : Installable sur mobile, fonctionne offline
- [ ] **Mode sombre** : Détection auto système + toggle manuel
- [ ] **Animations** : Transition douce sur changement de résultat
- [ ] **Raccourcis clavier** : Tab entre champs, Enter pour recalculer
- [ ] **Gesture** : Swipe pour reset, shake pour randomiser le tip (fun)

### Design

- [ ] **Thèmes** : 3-4 palettes de couleurs (pastel, dark, contrast)
- [ ] **Icônes** : Ajouter des icônes FA pour les champs (💶 👥 💯)
- [ ] **Micro-interactions** : Boutons tip avec effet ripple
- [ ] **Tips éducatifs** : Afficher des infos sur les coutumes de pourboire par pays
- [ ] **Confetti** : Animation fun si le pourboire > 25% (généreux !)

### Technique

- [ ] **Tests unitaires** : Jest pour les fonctions de calcul
- [ ] **A11y avancée** : Support lecteur d'écran complet, mode high contrast
- [ ] **Analytics** : Tracker usage (montant moyen, % tip favori) — privacy-friendly
- [ ] **Presets personnalisables** : Configurer ses propres boutons (12%, 18%, 22%)
- [ ] **Export données** : Télécharger l'historique en CSV/JSON

### Module réutilisable

- [ ] **Extraire en module EURKAI** : `MODULES/TIP_CALCULATOR/`
  - Widget embeddable dans d'autres apps
  - API JavaScript : `TipCalculator.calculate(bill, people, percent)`
  - MANIFEST.json définissant l'interface
  - Utilisable dans app resto, app comptabilité, etc.
