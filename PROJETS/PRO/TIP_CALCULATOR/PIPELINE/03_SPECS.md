# SPÉCIFICATIONS TECHNIQUES — TIP CALCULATOR

## 1. Architecture globale

Application web statique mono-fichier avec séparation stricte structure/présentation/comportement.

```
src/
├── index.html    # Structure sémantique
├── style.css     # Présentation mobile-first
└── script.js     # Logique calcul + interactions
```

**Poids cible** :
- HTML : ~2 Ko
- CSS : ~3 Ko
- JS : ~2 Ko
- **Total** : ~7 Ko (largement < 50 Ko)

## 2. Spécifications HTML

### 2.1 Structure

```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Calculatrice de Pourboire</title>
  <meta name="description" content="Calculez rapidement le pourboire et le montant par personne au restaurant">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <main class="calculator">
    <h1>Calculatrice de Pourboire</h1>

    <form class="inputs" id="tipForm">
      <div class="input-group">
        <label for="bill">Montant de l'addition (€)</label>
        <input type="number" id="bill" step="0.01" min="0" required autofocus>
      </div>

      <div class="input-group">
        <label for="people">Nombre de personnes</label>
        <input type="number" id="people" min="1" value="2" required>
      </div>

      <div class="input-group">
        <label for="tipPercent">Pourboire (%)</label>
        <div class="tip-input-wrapper">
          <input type="number" id="tipPercent" min="0" max="50" value="15" required>
          <div class="tip-presets">
            <button type="button" data-tip="10">10%</button>
            <button type="button" data-tip="15">15%</button>
            <button type="button" data-tip="20">20%</button>
          </div>
        </div>
      </div>
    </form>

    <section class="results" id="results">
      <div class="result-item">
        <span class="result-label">Pourboire</span>
        <span class="result-value" id="tipAmount">0,00 €</span>
      </div>
      <div class="result-item">
        <span class="result-label">Total</span>
        <span class="result-value" id="totalAmount">0,00 €</span>
      </div>
      <div class="result-item result-highlight">
        <span class="result-label">Par personne</span>
        <span class="result-value" id="perPerson">0,00 €</span>
      </div>
    </section>
  </main>

  <script src="script.js"></script>
</body>
</html>
```

### 2.2 Critères HTML

- **Sémantique** : `<main>`, `<form>`, `<section>`, `<label>`
- **Accessibilité** : labels explicites, attributs ARIA si nécessaire
- **Performance** : inline critique ou CSS/JS en fin de body
- **SEO** : meta description, lang, title

## 3. Spécifications CSS

### 3.1 Approche

- **Mobile-first** : base 375px, media queries pour desktop
- **Architecture** : par composant (inputs, results)
- **Nommage** : BEM simplifié (`.calculator`, `.input-group`, `.result-item`)
- **Variables CSS** : couleurs, espacements, typographie

### 3.2 Code CSS

```css
/* Variables */
:root {
  --color-bg: #f8f9fa;
  --color-text: #2d3748;
  --color-text-light: #718096;
  --color-accent: #667eea;
  --color-accent-light: #7f9cf5;
  --color-success: #48bb78;
  --color-border: #e2e8f0;

  --spacing-xs: 0.5rem;
  --spacing-sm: 1rem;
  --spacing-md: 1.5rem;
  --spacing-lg: 2rem;

  --radius: 8px;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* Reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* Base */
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 16px;
  line-height: 1.5;
  color: var(--color-text);
  background: var(--color-bg);
  padding: var(--spacing-md);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Calculator */
.calculator {
  background: white;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: var(--spacing-lg);
  max-width: 480px;
  width: 100%;
}

.calculator h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: var(--spacing-lg);
  text-align: center;
  color: var(--color-text);
}

/* Inputs */
.inputs {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.input-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-light);
}

.input-group input {
  font-size: 1rem;
  padding: 0.75rem;
  border: 2px solid var(--color-border);
  border-radius: var(--radius);
  transition: border-color 0.2s;
  min-height: 44px; /* Touch target */
}

.input-group input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.input-group input:invalid {
  border-color: #fc8181;
}

/* Tip presets */
.tip-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.tip-presets {
  display: flex;
  gap: var(--spacing-xs);
}

.tip-presets button {
  flex: 1;
  padding: 0.5rem;
  font-size: 0.875rem;
  background: var(--color-bg);
  border: 2px solid var(--color-border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
  min-height: 44px;
}

.tip-presets button:hover {
  background: var(--color-accent-light);
  color: white;
  border-color: var(--color-accent-light);
}

.tip-presets button:active {
  transform: scale(0.98);
}

/* Results */
.results {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-md);
  border-top: 2px solid var(--color-border);
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm);
}

.result-label {
  font-size: 0.875rem;
  color: var(--color-text-light);
}

.result-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
}

.result-highlight {
  background: var(--color-bg);
  border-radius: var(--radius);
  margin-top: var(--spacing-xs);
}

.result-highlight .result-label {
  font-size: 1rem;
  font-weight: 500;
  color: var(--color-text);
}

.result-highlight .result-value {
  font-size: 1.75rem;
  color: var(--color-success);
}

/* Desktop */
@media (min-width: 768px) {
  .calculator h1 {
    font-size: 2rem;
  }

  .calculator {
    padding: var(--spacing-lg) calc(var(--spacing-lg) * 1.5);
  }
}
```

### 3.3 Critères CSS

- **Contraste** : ratio min 4.5:1 (WCAG AA)
- **Touch targets** : min 44x44px
- **Responsive** : fluide 320px → 1920px
- **Performance** : pas d'animations lourdes, transitions simples

## 4. Spécifications JavaScript

### 4.1 Architecture

```javascript
// State
const state = {
  bill: 0,
  people: 2,
  tipPercent: 15
};

// Elements
const elements = {
  billInput: document.getElementById('bill'),
  peopleInput: document.getElementById('people'),
  tipInput: document.getElementById('tipPercent'),
  tipButtons: document.querySelectorAll('[data-tip]'),
  tipAmount: document.getElementById('tipAmount'),
  totalAmount: document.getElementById('totalAmount'),
  perPerson: document.getElementById('perPerson')
};

// Utils
function formatCurrency(amount) {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR'
  }).format(amount);
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

// Calculations
function calculate() {
  const { bill, people, tipPercent } = state;

  // Validation
  if (bill <= 0 || people <= 0) {
    updateDisplay(0, 0, 0);
    return;
  }

  // Calculs
  const tipAmount = bill * (tipPercent / 100);
  const total = bill + tipAmount;
  const perPersonAmount = total / people;

  updateDisplay(tipAmount, total, perPersonAmount);
}

function updateDisplay(tip, total, perPerson) {
  elements.tipAmount.textContent = formatCurrency(tip);
  elements.totalAmount.textContent = formatCurrency(total);
  elements.perPerson.textContent = formatCurrency(perPerson);
}

// Event handlers
const debouncedCalculate = debounce(calculate, 300);

function handleBillInput(e) {
  state.bill = parseFloat(e.target.value) || 0;
  debouncedCalculate();
}

function handlePeopleInput(e) {
  state.people = parseInt(e.target.value) || 1;
  debouncedCalculate();
}

function handleTipInput(e) {
  state.tipPercent = parseFloat(e.target.value) || 0;
  debouncedCalculate();
}

function handleTipPreset(e) {
  const tip = parseFloat(e.target.dataset.tip);
  state.tipPercent = tip;
  elements.tipInput.value = tip;
  calculate();
}

// Init
function init() {
  // Event listeners
  elements.billInput.addEventListener('input', handleBillInput);
  elements.peopleInput.addEventListener('input', handlePeopleInput);
  elements.tipInput.addEventListener('input', handleTipInput);

  elements.tipButtons.forEach(btn => {
    btn.addEventListener('click', handleTipPreset);
  });

  // Initial calculation
  calculate();
}

// Start
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
```

### 4.2 Critères JavaScript

- **Debounce** : 300ms sur les inputs pour éviter recalcul constant
- **Validation** : montant > 0, personnes >= 1
- **Formatage** : `Intl.NumberFormat` pour €
- **Arrondis** : gérés automatiquement par le formateur
- **Erreurs** : affichage 0,00 € si données invalides

## 5. Tests

### 5.1 Tests fonctionnels

| Test | Input | Output attendu |
|---|---|---|
| Calcul simple | 100€, 2p, 15% | Tip: 15€, Total: 115€, PP: 57.50€ |
| Arrondis | 33.33€, 3p, 10% | Tip: 3.33€, Total: 36.66€, PP: 12.22€ |
| 1 personne | 50€, 1p, 20% | Tip: 10€, Total: 60€, PP: 60€ |
| 0% tip | 100€, 2p, 0% | Tip: 0€, Total: 100€, PP: 50€ |
| 50% tip max | 100€, 2p, 50% | Tip: 50€, Total: 150€, PP: 75€ |
| Montant invalide | 0€ ou vide | Tous à 0€ |

### 5.2 Tests responsive

- iPhone SE (375px)
- iPhone 12 (390px)
- iPad (768px)
- Desktop (1280px)

### 5.3 Tests navigateurs

- Chrome 120+
- Safari 16+
- Firefox 120+
- Edge 120+

## 6. Déploiement

### 6.1 Build

Aucun build nécessaire — fichiers statiques prêts à déployer.

**Optimisations optionnelles** :
- Minification CSS/JS (gain ~30%)
- Inline CSS critique (gain FCP)

### 6.2 Hébergement

**Option 1 : GitHub Pages**
```bash
# Push dans branch gh-pages
git subtree push --prefix PROJETS/PRO/TIP_CALCULATOR/src origin gh-pages
```

**Option 2 : Netlify**
- Drag & drop du dossier `src/`
- URL auto-générée

**Option 3 : Vercel**
- Import repo GitHub
- Build command : aucune
- Output directory : `PROJETS/PRO/TIP_CALCULATOR/src`

### 6.3 Configuration

**Fichier `netlify.toml`** (optionnel) :
```toml
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

## 7. Points d'attention

1. **Arrondis** : Le `Intl.NumberFormat` gère automatiquement l'arrondi à 2 décimales
2. **Performance** : Debounce critique pour éviter recalculs excessifs
3. **Accessibilité** : Labels liés aux inputs, contraste validé
4. **Touch** : Zones de 44px min pour mobile
5. **Validation** : Feedback visuel immédiat (bordure rouge si invalide)

## 8. Prochaine étape

**Développement** — création des 3 fichiers (`index.html`, `style.css`, `script.js`) dans `src/`.
