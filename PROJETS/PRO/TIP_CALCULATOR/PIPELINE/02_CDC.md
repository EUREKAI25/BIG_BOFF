# CAHIER DES CHARGES — TIP CALCULATOR

## 1. Contexte et objectifs

Application web statique de calcul de pourboire au restaurant avec répartition automatique par personne. Projet de test pour valider le workflow de création EURKAI (idée → artefacts → déploiement).

**Objectif** : produire une application web simple, rapide, mobile-first, utilisable immédiatement au restaurant sans installation.

## 2. Périmètre fonctionnel

### 2.1 Fonctionnalités principales

**F01 — Saisie montant addition**
- Champ numérique (décimales autorisées)
- Validation : montant > 0
- Symbole € affiché

**F02 — Saisie nombre de personnes**
- Champ numérique entier
- Validation : nombre >= 1
- Par défaut : 2

**F03 — Sélection pourcentage pourboire**
- Champ numérique ou slider
- Plage : 0% à 50%
- Par défaut : 15%
- Préréglages suggérés : 10%, 15%, 20%

**F04 — Calcul temps réel**
- Recalcul automatique à chaque modification de champ
- Pas de bouton "Calculer"
- Délai anti-rebond : 300ms

**F05 — Affichage résultats**
- Montant du pourboire (€)
- Total avec pourboire (€)
- Montant par personne (€)
- Affichage clair, hiérarchisé
- 2 décimales max

### 2.2 Fonctionnalités secondaires (v2)

Hors scope initial, à considérer ultérieurement :
- Sauvegarde historique (LocalStorage)
- Partage calcul (lien, QR code)
- Multi-devises
- Mode sombre
- PWA (installable)
- Répartition inégale

### 2.3 Hors périmètre

- Backend, API, base de données
- Authentification utilisateur
- Tracking analytics
- Publicité
- Logo, branding
- Framework JS (React, Vue, etc.)

## 3. Utilisateurs et parcours

**Utilisateur cible** : toute personne au restaurant souhaitant calculer rapidement le pourboire.

**Parcours principal** :
1. Ouvrir l'app sur mobile (lien direct ou favoris)
2. Entrer le montant de l'addition
3. Ajuster le nombre de personnes si nécessaire
4. Ajuster le % de pourboire si nécessaire (ou garder 15%)
5. Lire le résultat : montant par personne
6. Payer et fermer

**Durée estimée** : < 30 secondes

## 4. Contraintes

### 4.1 Techniques

**Stack** :
- HTML5 sémantique
- CSS3 (pas de préprocesseur, vanilla uniquement)
- JavaScript vanilla (ES6+)
- Aucune dépendance externe

**Performance** :
- Chargement page < 1 seconde
- Calcul instantané (< 100ms perçu)
- Poids total < 50 Ko

**Compatibilité** :
- Navigateurs modernes (Chrome, Safari, Firefox, Edge)
- iOS Safari 14+, Android Chrome 90+
- Responsive : 320px à 1920px

**Hébergement** :
- Statique (GitHub Pages, Netlify, Vercel)
- HTTPS obligatoire
- Pas de backend requis

### 4.2 Business

- Budget : 0€ (gratuit, open source)
- Délai : 1 journée max (proof of concept)
- Licence : MIT ou domaine public

### 4.3 Design

**Principes** :
- Mobile-first (écran 375px comme base)
- Minimaliste, épuré
- Couleurs douces (pas de rouge/vert agressifs)
- Typographie lisible (taille min 16px)
- Contraste WCAG AA minimum
- Pas de logo, pas d'illustrations

**Palette suggérée** :
- Fond : blanc cassé ou gris très clair
- Texte : gris foncé (pas noir pur)
- Accent : bleu/violet doux pour les champs actifs
- Résultats : vert doux pour mise en valeur

## 5. Livrables attendus

1. **Code source** :
   - `src/index.html` (page unique)
   - `src/style.css` (styles)
   - `src/script.js` (logique calcul)

2. **Documentation** :
   - `README.md` (installation, usage)
   - `PIPELINE/02_CDC.md` (ce fichier)
   - `PIPELINE/03_SPECS.md` (specs techniques)

3. **Déploiement** :
   - URL publique fonctionnelle
   - Repository GitHub

4. **Tests** :
   - Tests manuels sur mobile et desktop
   - Cas limites validés (0€, 1 personne, 50% tip, etc.)

## 6. Critères de succès

| Critère | Mesure | Cible |
|---|---|---|
| **Utilisabilité** | Temps pour 1 calcul | < 30s |
| **Performance** | Chargement initial | < 1s |
| **Responsive** | Utilisable sur mobile | 100% |
| **Fiabilité** | Calculs corrects | 100% |
| **Accessibilité** | Contraste WCAG AA | Pass |
| **Poids** | Taille totale | < 50 Ko |

**Validation finale** : une personne non-technique doit pouvoir utiliser l'app au restaurant sans explication.

## 7. Risques identifiés

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Calculs incorrects (arrondis) | Faible | Fort | Tests unitaires, validation manuelle |
| Non-responsive sur vieux mobiles | Moyenne | Faible | Tests multi-devices, fallback CSS |
| Chargement lent (3G) | Faible | Moyen | Minification, inline CSS critique |
| Pas d'adoption (trop simple) | Forte | Nul | C'est un projet test, pas un produit |

## 8. Points d'attention

- **Arrondis** : toujours arrondir à 2 décimales, arrondi supérieur pour éviter de sous-payer
- **Division** : gérer division par zéro (nombre de personnes)
- **UX mobile** : taille des zones de saisie suffisante pour les doigts (min 44px)
- **Focus** : auto-focus sur le champ montant au chargement
- **Validation** : feedback visuel immédiat si saisie invalide

## 9. Prochaine étape

Production des **spécifications techniques** (PIPELINE/03_SPECS.md) détaillant :
- Structure HTML exacte
- Classes CSS et architecture
- Fonctions JavaScript et algorithmes
- Plan de tests
