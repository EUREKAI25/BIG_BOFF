# STANDARDS — Règles techniques de génération de code

> Standards à respecter pour toute génération de code dans les projets BIG_BOFF/EURKAI.
> Ces règles garantissent qualité, maintenabilité, accessibilité et cohérence.

**Dernière MAJ** : 2026-02-10

---

## 1. Principes généraux

### 1.1 Qualité

- **Simplicité** > complexité — éviter la sur-ingénierie
- **Lisibilité** > concision — code clair, noms explicites
- **Maintenabilité** > performance prématurée — optimiser quand nécessaire
- **Standards** > préférences — suivre les conventions établies

### 1.2 Documentation

- Chaque fonction/classe complexe a un commentaire explicatif
- Les algorithmes non-triviaux sont commentés étape par étape
- Les TODO/FIXME sont horodatés et signés
- Le README.md explique comment lancer/utiliser le projet

### 1.3 Modularité

- Un fichier = une responsabilité
- Extraction en module dès qu'une logique est réutilisable
- Pas de duplication de code (DRY)
- Dépendances minimales

---

## 2. HTML

### 2.1 Structure

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Titre explicite</title>
  <meta name="description" content="Description SEO">
</head>
<body>
  <!-- Contenu -->
</body>
</html>
```

### 2.2 Règles

- **Sémantique** : utiliser les balises appropriées (`<main>`, `<article>`, `<section>`, `<nav>`, `<header>`, `<footer>`)
- **Accessibilité** :
  - Tous les `<img>` ont un attribut `alt`
  - Tous les `<input>` sont liés à un `<label>` (via `for` ou imbrication)
  - Ordre logique des titres (`<h1>` → `<h2>` → `<h3>`, pas de saut)
  - Attributs ARIA si nécessaire (`aria-label`, `aria-describedby`)
- **Formulaires** :
  - Attributs `type`, `name`, `id` corrects
  - Validation HTML5 (`required`, `min`, `max`, `pattern`)
  - Autocomplete approprié (`autocomplete="email"`, etc.)
- **Performance** :
  - CSS dans `<head>` ou inline si critique
  - JS en fin de `<body>` ou avec `defer`
  - Lazy loading pour images hors viewport (`loading="lazy"`)

### 2.3 À éviter

- Balises deprecated (`<center>`, `<font>`, `<marquee>`)
- Tables pour la mise en page (réservé aux données tabulaires)
- IDs dupliqués
- Inline styles (sauf cas exceptionnel)

---

## 3. CSS

### 3.1 Architecture

- **Mobile-first** : base 375px, media queries pour desktop
- **Variables CSS** : couleurs, espacements, typographie centralisés
- **BEM simplifié** : `.block`, `.block__element`, `.block--modifier`
- **Composants** : un fichier par composant si CSS modulaire

### 3.2 Nommage

```css
/* ✓ BON */
.calculator { }
.calculator__input { }
.calculator__button--primary { }

/* ✗ MAUVAIS */
.calc { } /* trop court */
.calculatorInputField { } /* camelCase */
.calculator_button_primary { } /* underscores mixtes */
```

### 3.3 Variables

```css
:root {
  /* Couleurs */
  --color-bg: #f8f9fa;
  --color-text: #2d3748;
  --color-accent: #667eea;

  /* Espacements */
  --spacing-xs: 0.5rem;
  --spacing-sm: 1rem;
  --spacing-md: 1.5rem;
  --spacing-lg: 2rem;

  /* Autres */
  --radius: 8px;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}
```

### 3.4 Règles

- **Reset** : inclure un reset minimal (`* { margin: 0; padding: 0; box-sizing: border-box; }`)
- **Accessibilité** :
  - Contraste minimum WCAG AA (4.5:1 texte, 3:1 UI)
  - Touch targets min 44x44px
  - Focus visible sur tous les éléments interactifs
- **Performance** :
  - Pas d'animations lourdes (prefer `transform`/`opacity` vs `width`/`height`)
  - Transitions courtes (< 300ms)
  - Éviter sélecteurs descendants profonds (`.a .b .c .d .e`)
- **Responsive** :
  - Unités relatives (`rem`, `em`, `%`, `vw`, `vh`)
  - Media queries standard : `768px` (tablet), `1024px` (desktop)

### 3.5 À éviter

- `!important` (sauf override externe inévitable)
- IDs pour le style (réservé à JS)
- Magic numbers (utiliser variables)
- Préfixes vendeurs manuels (utiliser autoprefixer si nécessaire)

---

## 4. JavaScript

### 4.1 Style

- **ES6+** : utiliser syntaxe moderne (`const`/`let`, arrow functions, destructuring, template strings)
- **Nommage** :
  - Variables/fonctions : `camelCase`
  - Constantes globales : `UPPER_SNAKE_CASE`
  - Classes : `PascalCase`
- **Fonctions** : préférer fonctions pures quand possible
- **Async** : `async/await` plutôt que `.then()` pour lisibilité

### 4.2 Structure

```javascript
// 1. Imports (si modules)
import { something } from './module.js';

// 2. Constantes
const API_URL = 'https://api.example.com';

// 3. State
const state = {
  user: null,
  items: []
};

// 4. DOM elements
const elements = {
  button: document.getElementById('btn'),
  input: document.querySelector('.input')
};

// 5. Utils
function formatDate(date) { }

// 6. Business logic
function processData(data) { }

// 7. Event handlers
function handleClick(e) { }

// 8. Init
function init() { }

// 9. Start
init();
```

### 4.3 Règles

- **Validation** : toujours valider inputs utilisateur
- **Erreurs** : gérer les cas d'erreur (`try/catch`, vérifications null)
- **Performance** :
  - Debounce sur inputs fréquents (scroll, resize, input)
  - Éviter manipulation DOM dans boucles
  - Event delegation si nombreux éléments
- **Sécurité** :
  - Jamais `eval()`
  - Échapper HTML si insertion contenu utilisateur
  - Validation côté serveur obligatoire (front = UX uniquement)
- **Accessibilité** :
  - Gestion clavier (Enter, Escape, Tab)
  - Focus management
  - ARIA live regions si contenu dynamique

### 4.4 Patterns

```javascript
// ✓ BON : destructuring
const { name, age } = user;

// ✓ BON : template strings
const message = `Hello ${name}, you are ${age} years old`;

// ✓ BON : arrow function
const double = x => x * 2;

// ✓ BON : default parameters
function greet(name = 'Guest') { }

// ✓ BON : optional chaining
const street = user?.address?.street;

// ✗ MAUVAIS : var
var x = 10; // utiliser const ou let

// ✗ MAUVAIS : string concatenation
const msg = 'Hello ' + name; // utiliser template string
```

### 4.5 À éviter

- Variables globales non nécessaires
- Code synchrone bloquant
- Console.log en production (utiliser logger ou supprimer)
- Callbacks imbriqués (callback hell)

---

## 5. Python

### 5.1 Style

- **PEP 8** : suivre les conventions Python
- **Nommage** :
  - Variables/fonctions : `snake_case`
  - Classes : `PascalCase`
  - Constantes : `UPPER_SNAKE_CASE`
  - Privé : préfixe `_`
- **Type hints** : utiliser si améliore lisibilité

### 5.2 Structure

```python
"""Module docstring."""

# 1. Imports standard library
import os
import json

# 2. Imports third-party
import requests

# 3. Imports locaux
from .utils import helper

# 4. Constantes
API_KEY = os.getenv('API_KEY')

# 5. Classes
class MyClass:
    """Class docstring."""
    pass

# 6. Fonctions
def my_function(arg: str) -> dict:
    """Function docstring."""
    pass

# 7. Main
if __name__ == '__main__':
    main()
```

### 5.3 Règles

- **Docstrings** : toutes les fonctions/classes publiques
- **Validation** : vérifier types, valeurs nulles
- **Erreurs** : lever exceptions appropriées, pas de `pass` silencieux
- **Logging** : utiliser `logging` module, pas `print()`
- **Sécurité** :
  - Pas de secrets hardcodés (env vars)
  - Validation inputs
  - SQL paramétré (jamais string interpolation)

### 5.4 À éviter

- `import *`
- Variables globales mutables
- Bare `except:` (toujours spécifier exception)
- Mutation arguments par défaut

---

## 6. Tests

### 6.1 Principes

- **Couverture** : minimum 80% pour logique métier
- **Isolation** : chaque test indépendant
- **Nomenclature** : `test_<fonction>_<cas>_<resultat_attendu>`
- **AAA** : Arrange, Act, Assert

### 6.2 Types

- **Unitaires** : fonctions pures, calculs, transformations
- **Intégration** : API, base de données, services externes
- **E2E** : parcours utilisateur complet
- **Manuels** : UX, responsive, accessibilité

### 6.3 Cas à tester

- Happy path (cas nominal)
- Edge cases (limites : 0, null, vide, max)
- Erreurs (inputs invalides, réseau down)
- Sécurité (injection, XSS si applicable)

---

## 7. Git

### 7.1 Commits

```
Type: Description courte (max 70 chars)

Corps optionnel avec détails.
- Point 1
- Point 2

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Types** : `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### 7.2 Règles

- Commits atomiques (1 changement = 1 commit)
- Messages clairs et explicites
- Pas de `WIP`, `temp`, `test` en production
- Branch pour features (sauf petits projets solo)

---

## 8. Sécurité

### 8.1 Checklist

- [ ] Pas de secrets dans le code (API keys, passwords)
- [ ] Validation tous inputs utilisateur
- [ ] HTTPS obligatoire en production
- [ ] Headers sécurité (CSP, X-Frame-Options, etc.)
- [ ] Dépendances à jour (pas de vulnérabilités connues)
- [ ] SQL paramétré, jamais string interpolation
- [ ] Échappement HTML si contenu utilisateur
- [ ] CORS configuré correctement
- [ ] Rate limiting sur APIs
- [ ] Logs ne contiennent pas de données sensibles

---

## 9. Performance

### 9.1 Web

- **Chargement** : < 3s sur 3G
- **Poids page** : < 500 Ko (idéal < 200 Ko)
- **Images** : WebP/AVIF, lazy loading, responsive
- **Fonts** : subset, preload, fallback
- **JS/CSS** : minification, tree-shaking, code-splitting

### 9.2 Backend

- **Temps réponse API** : < 200ms (p95)
- **Caching** : utiliser Redis/memcached si pertinent
- **Database** : indexes, requêtes optimisées
- **N+1** : éviter (eager loading)

---

## 10. Accessibilité (A11y)

### 10.1 Checklist WCAG AA

- [ ] Contraste texte minimum 4.5:1
- [ ] Contraste UI minimum 3:1
- [ ] Navigation clavier complète
- [ ] Focus visible
- [ ] Labels sur tous inputs
- [ ] Alt text sur images
- [ ] Titres hiérarchiques (`<h1>` → `<h2>` → `<h3>`)
- [ ] ARIA si éléments custom
- [ ] Pas de dépendance couleur seule (info + icône)
- [ ] Taille police min 16px

### 10.2 Tests

- Naviguer au clavier uniquement (Tab, Enter, Escape)
- Tester avec lecteur d'écran (VoiceOver, NVDA)
- Vérifier contraste (outil navigateur ou Contrast Checker)
- Zoom 200% (contenu reste utilisable)

---

## 11. Modules EURKAI

### 11.1 Structure standard

```
MODULES/<nom_module>/
├── MANIFEST.json      # Interface (inputs, outputs, config)
├── README.md          # Documentation complète
├── src/               # Code agnostique
│   └── index.js       # Point d'entrée
├── tests/             # Tests unitaires
├── examples/          # Exemples d'utilisation
└── .gitignore
```

### 11.2 MANIFEST.json

```json
{
  "name": "tip-calculator",
  "version": "1.0.0",
  "description": "Calculateur de pourboire réutilisable",
  "interface": {
    "inputs": {
      "bill": { "type": "number", "required": true },
      "people": { "type": "number", "default": 2 },
      "tipPercent": { "type": "number", "default": 15 }
    },
    "outputs": {
      "tipAmount": { "type": "number" },
      "total": { "type": "number" },
      "perPerson": { "type": "number" }
    }
  },
  "dependencies": [],
  "license": "MIT"
}
```

### 11.3 Règles

- **Agnostique** : pas de dépendance projet-spécifique
- **Testable** : tests unitaires fournis
- **Documenté** : README avec exemples
- **Versionné** : semver (1.0.0 → 1.0.1 → 1.1.0 → 2.0.0)

---

## 12. Application de ces standards

### 12.1 Avant de coder

1. Lire BRIEF + CDC + SPECS
2. Consulter ce fichier STANDARDS.md
3. Vérifier si modules réutilisables existent
4. Planifier structure fichiers

### 12.2 Pendant le dev

- Appliquer standards au fur et à mesure
- Commenter code complexe
- Tester régulièrement

### 12.3 Avant validation

- [ ] Code respecte tous les standards applicables
- [ ] Tests passent
- [ ] README à jour
- [ ] Commit propre avec message clair
- [ ] Pas de console.log / print / TODO oubliés

---

## 13. Évolutions

Ce fichier évolue avec l'expérience. Ajouter/modifier standards au fil des projets.

**Historique** :
- 2026-02-10 : Création initiale (TIP_CALCULATOR comme référence)
