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
