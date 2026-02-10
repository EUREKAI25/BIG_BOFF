/* =============================================================================
   EUREKAI Cockpit — Creation Tab
   Utilise Picker pour la sélection de type et Schema pour la génération
   ============================================================================= */

// État de la création
let createState = {
  files: [],
  parsedData: {},
  schema: null,
  initialized: false,
  typePicker: null
};

// =============================================================================
// Initialisation
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
  initTypePicker();
  initUploadZone();
});

/**
 * Initialiser le Picker de types
 */
function initTypePicker() {
  const container = document.getElementById('typePicker');
  if (!container) return;
  
  createState.typePicker = new Picker({
    // Query : tous les types uniques (2ème niveau des lineages), sauf Object et Schema
    query: (store) => {
      const allLineages = store.getAllLineages ? store.getAllLineages() : [];
      const typeSet = new Set();
      
      for (const lineage of allLineages) {
        const segments = lineage.split(':');
        // Prendre le type (niveau 2) s'il existe
        if (segments.length >= 2 && segments[1] !== 'Schema') {
          typeSet.add(segments.slice(0, 2).join(':'));
        }
        // Aussi ajouter le niveau 3 pour plus de granularité
        if (segments.length >= 3 && segments[1] !== 'Schema') {
          typeSet.add(segments.slice(0, 3).join(':'));
        }
      }
      
      return Array.from(typeSet);
    },
    
    // Affichage
    display: (item) => ({
      label: getLineageName(item),
      sublabel: item,
      value: item
    }),
    
    limit: 10,
    sort: 'frequency',
    showSearch: true,
    showFrequency: true,
    placeholder: 'Rechercher un type...',
    emptyMessage: 'Aucun type trouvé',
    
    // Sélection
    onSelect: (lineage) => {
      document.getElementById('createTypeInput').value = lineage + ':';
      // Focus sur l'input pour ajouter le nom
      document.getElementById('createTypeInput').focus();
    },
    
    // Voir tout
    onViewAll: (items) => {
      showAllTypesModal(items);
    }
  });
  
  createState.typePicker.render(container);
}

/**
 * Modal pour voir tous les types
 */
function showAllTypesModal(items) {
  const modal = document.getElementById('modalOverlay');
  const title = document.getElementById('modalTitle');
  const body = document.getElementById('modalBody');
  
  title.textContent = 'Tous les types';
  
  let html = '<div class="modal-types-list">';
  html += items.map(item => `
    <div class="modal-type-item" onclick="selectTypeFromModal('${item.value}')">
      <span class="modal-type-label">${item.label}</span>
      <span class="modal-type-lineage">${item.sublabel}</span>
      ${item._frequency > 1 ? `<span class="modal-type-count">${item._frequency}</span>` : ''}
    </div>
  `).join('');
  html += '</div>';
  
  body.innerHTML = html;
  modal.classList.add('active');
  
  // Fermer au clic sur le bouton
  document.getElementById('modalCancel').onclick = () => modal.classList.remove('active');
  document.getElementById('modalConfirm').style.display = 'none';
}

function selectTypeFromModal(lineage) {
  document.getElementById('createTypeInput').value = lineage + ':';
  document.getElementById('modalOverlay').classList.remove('active');
  document.getElementById('modalConfirm').style.display = '';
  document.getElementById('createTypeInput').focus();
}

/**
 * Initialiser la zone d'upload
 */
function initUploadZone() {
  const uploadZone = document.getElementById('createUploadZone');
  if (!uploadZone) return;
  
  uploadZone.addEventListener('click', () => {
    document.getElementById('createFileInput').click();
  });
  
  uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
  });
  
  uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
  });
  
  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    handleDroppedFiles(e.dataTransfer.files);
  });
}

// =============================================================================
// Création
// =============================================================================

/**
 * Démarrer la création
 */
async function startCreation() {
  const input = document.getElementById('createTypeInput');
  let lineage = input.value.trim();
  
  if (!lineage) {
    showToast('Entrez un type à créer', 'warning');
    return;
  }
  
  // Normaliser le lineage
  if (!lineage.startsWith('Object:')) {
    lineage = 'Object:' + lineage;
    input.value = lineage;
  }
  
  // Récupérer le schema
  const schema = SchemaModule.get(lineage);
  if (!schema) {
    showToast('Impossible de trouver le schema', 'error');
    return;
  }
  
  createState.schema = schema;
  console.log('[Creation] Schema chargé:', schema);
  
  // Détecter les sources
  const sources = await detectSources(lineage);
  updateSourceIndicators(sources);
  
  // Générer le formulaire depuis le schema
  const formData = generateFormFromSchema(schema, sources);
  
  // Initialiser ViewManager
  ViewManager.state.lineage = lineage;
  ViewManager.state.formData = formData;
  ViewManager.state.sources = sources;
  ViewManager.state.conversation = [];
  ViewManager.state.currentSection = 0;
  
  // Message initial du chat basé sur le schema
  if (schema.questions && schema.questions.length > 0) {
    const intro = schema.questions.find(q => q.id === 'intro');
    ViewManager.state.conversation.push({
      role: 'agent',
      content: intro ? intro.text : `Je vais vous aider à créer un ${schema.name}.`,
      timestamp: new Date().toISOString()
    });
  }
  
  createState.initialized = true;
  
  // Activer les boutons
  document.getElementById('btnNextSection').disabled = false;
  document.getElementById('btnFinalize').disabled = false;
  
  // Rafraîchir les vues
  refreshFormView();
  refreshChatView();
  refreshRecapView();
  
  showToast(`Création de "${getLineageName(lineage)}" initialisée`, 'success');
}

/**
 * Détecter les sources disponibles
 */
async function detectSources(lineage) {
  const sources = {
    inherited: null,
    catalog: null,
    seed: null
  };
  
  // 1. Hérité (parent)
  const parentLineage = getParentLineage(lineage);
  if (parentLineage) {
    const parent = Store.get(parentLineage);
    if (parent) {
      sources.inherited = {};
      for (const attr of (parent.attributeBundle?.owned || [])) {
        if (attr.default !== undefined) {
          sources.inherited[attr.name] = attr.default;
        }
      }
    }
  }
  
  // 2. Catalog
  const typeName = lineage.split(':').slice(-1)[0];
  const examples = Store.query ? Store.query(`Object:Example:${typeName}*`) : [];
  if (examples.length > 0) {
    const example = Store.get(examples[0]);
    if (example) {
      sources.catalog = {};
      for (const attr of (example.attributeBundle?.owned || [])) {
        sources.catalog[attr.name] = attr.value;
      }
    }
  }
  
  // 3. Fichiers uploadés
  if (Object.keys(createState.parsedData).length > 0) {
    sources.seed = createState.parsedData;
  }
  
  return sources;
}

/**
 * Mettre à jour les indicateurs de sources
 */
function updateSourceIndicators(sources) {
  const indicators = document.querySelectorAll('.source-indicator');
  indicators.forEach(ind => {
    const source = ind.dataset.source;
    const hasSource = sources[source] && Object.keys(sources[source]).length > 0;
    ind.classList.toggle('active', hasSource);
  });
}

/**
 * Générer le formulaire depuis le schema
 */
function generateFormFromSchema(schema, sources) {
  const sections = {};
  
  // Organiser les attributs par section
  for (const attr of schema.attributes) {
    const sectionName = attr.section || 'main';
    if (!sections[sectionName]) {
      sections[sectionName] = {
        name: sectionName,
        title: humanizeSection(sectionName),
        fields: []
      };
    }
    
    // Créer le champ
    const field = {
      name: attr.name,
      label: attr.label || humanize(attr.name),
      description: attr.description,
      valueType: attr.type || 'string',
      required: attr.required || false,
      default: attr.default,
      placeholder: attr.placeholder,
      options: attr.options,
      multiple: attr.multiple,
      min: attr.min,
      max: attr.max,
      minLength: attr.minLength,
      maxLength: attr.maxLength,
      multiline: attr.multiline,
      question: attr.question,
      value: null,
      prefillSource: null,
      valid: null,
      errors: []
    };
    
    // Pré-remplir depuis les sources (priorité: seed > catalog > inherited > default)
    if (sources.seed && sources.seed[attr.name] !== undefined) {
      field.value = sources.seed[attr.name];
      field.prefillSource = 'seed';
    } else if (sources.catalog && sources.catalog[attr.name] !== undefined) {
      field.value = sources.catalog[attr.name];
      field.prefillSource = 'catalog';
    } else if (sources.inherited && sources.inherited[attr.name] !== undefined) {
      field.value = sources.inherited[attr.name];
      field.prefillSource = 'inherited';
    } else if (attr.default !== undefined) {
      field.value = attr.default;
      field.prefillSource = 'default';
    }
    
    sections[sectionName].fields.push(field);
  }
  
  // Convertir en tableau ordonné
  const orderedSections = [];
  const order = ['identity', 'main', 'options', 'relations', 'advanced'];
  
  for (const name of order) {
    if (sections[name]) {
      orderedSections.push(sections[name]);
      delete sections[name];
    }
  }
  
  // Ajouter les sections restantes
  for (const section of Object.values(sections)) {
    orderedSections.push(section);
  }
  
  // Section preview à la fin
  orderedSections.push({
    name: 'preview',
    title: 'Aperçu',
    fields: [],
    isPreview: true
  });
  
  return {
    lineage: ViewManager.state?.lineage,
    name: schema.name,
    sections: orderedSections
  };
}

function humanizeSection(name) {
  const map = {
    identity: 'Identité',
    main: 'Informations principales',
    options: 'Options',
    relations: 'Relations',
    advanced: 'Avancé',
    preview: 'Aperçu'
  };
  return map[name] || humanize(name);
}

function humanize(str) {
  return str
    .replace(/([A-Z])/g, ' $1')
    .replace(/_/g, ' ')
    .replace(/^\w/, c => c.toUpperCase())
    .trim();
}

// =============================================================================
// Gestion des fichiers
// =============================================================================

function handleCreateUpload(input) {
  handleDroppedFiles(input.files);
  input.value = '';
}

function handleDroppedFiles(files) {
  Array.from(files).forEach(file => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      const content = e.target.result;
      createState.files.push({ name: file.name, content, size: file.size });
      
      // Parser selon le type et le schema
      const parsed = parseFile(file.name, content);
      if (parsed && Object.keys(parsed).length > 0) {
        Object.assign(createState.parsedData, parsed);
        showToast(`"${file.name}": ${Object.keys(parsed).length} champs`, 'success');
        
        // Réinjecter si création en cours
        if (createState.initialized) {
          reinjectParsedData();
        }
      } else {
        showToast(`Fichier "${file.name}" ajouté`, 'info');
      }
      
      refreshFilesList();
    };
    
    reader.readAsText(file);
  });
}

/**
 * Parser un fichier selon son type et le schema actif
 */
function parseFile(filename, content) {
  const schema = createState.schema || SchemaModule.getDefaultSchema('Object');
  
  // Déterminer le reader à utiliser
  let readerName = 'defaultSeedReader';
  
  if (filename.endsWith('.json')) {
    readerName = schema.readers?.json || 'defaultJsonReader';
  } else if (filename.endsWith('.gev')) {
    readerName = schema.readers?.seed || 'defaultSeedReader';
  } else if (filename.endsWith('.md') || filename.endsWith('.txt')) {
    // Détecter si c'est une note ou un cahier des charges
    if (content.includes('# Cahier') || content.includes('# Spec') || content.includes('## Objectif')) {
      readerName = schema.readers?.spec || 'specReader';
    } else {
      readerName = schema.readers?.note || 'noteReader';
    }
  }
  
  const reader = SchemaReaders.getReader(readerName);
  return reader.call(SchemaReaders, content, schema);
}

function reinjectParsedData() {
  if (!ViewManager.state.formData) return;
  
  for (const section of ViewManager.state.formData.sections) {
    for (const field of section.fields) {
      if (createState.parsedData[field.name] !== undefined && !field.value) {
        field.value = createState.parsedData[field.name];
        field.prefillSource = 'seed';
      }
    }
  }
  
  refreshFormView();
}

function refreshFilesList() {
  const container = document.getElementById('createFilesList');
  if (!container) return;
  
  if (createState.files.length === 0) {
    container.innerHTML = '';
    return;
  }
  
  container.innerHTML = createState.files.map((file, idx) => `
    <div class="create-file-item">
      <span class="create-file-icon">${getFileIcon(file.name)}</span>
      <span class="create-file-name">${file.name}</span>
      <span class="create-file-remove" onclick="removeCreateFile(${idx})">×</span>
    </div>
  `).join('');
}

function getFileIcon(filename) {
  if (filename.endsWith('.json')) return '📋';
  if (filename.endsWith('.gev')) return '⚡';
  if (filename.endsWith('.md')) return '📝';
  return '📄';
}

function removeCreateFile(index) {
  createState.files.splice(index, 1);
  refreshFilesList();
}

// =============================================================================
// Vues
// =============================================================================

function switchCreateView(viewName) {
  document.querySelectorAll('.view-tab').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.view === viewName);
  });
  
  document.querySelectorAll('.create-view').forEach(view => {
    view.classList.toggle('active', view.id === `createView${viewName.charAt(0).toUpperCase() + viewName.slice(1)}`);
  });
  
  if (createState.initialized && ViewManager.switchView) {
    ViewManager.switchView(viewName);
  }
}

function refreshFormView() {
  const container = document.getElementById('formSections');
  const state = ViewManager.state;
  
  if (!state.formData || !state.formData.sections) {
    container.innerHTML = '<div class="create-empty">Sélectionnez un type et cliquez sur "Démarrer"</div>';
    return;
  }
  
  let html = '';
  
  state.formData.sections.forEach((section, idx) => {
    const isCurrent = idx === state.currentSection;
    const validation = validateSection(section);
    const statusClass = validation.valid ? 'complete' : (validation.filled > 0 ? 'partial' : 'incomplete');
    const statusText = validation.valid ? '✓' : `${validation.filled}/${section.fields.length}`;
    
    html += `
      <div class="form-section ${isCurrent ? 'current' : ''} ${statusClass}" data-section="${idx}">
        <div class="form-section-header" onclick="goToSection(${idx})">
          <span class="form-section-title">${section.title}</span>
          <span class="form-section-status">${statusText}</span>
        </div>
        ${isCurrent ? `<div class="form-section-content">${renderSectionFields(section)}</div>` : ''}
      </div>
    `;
  });
  
  container.innerHTML = html;
  
  const indicator = document.getElementById('sectionIndicator');
  if (indicator) {
    indicator.textContent = `${state.currentSection + 1} / ${state.formData.sections.length}`;
  }
  
  document.getElementById('btnPrevSection').disabled = state.currentSection === 0;
  document.getElementById('btnNextSection').disabled = state.currentSection >= state.formData.sections.length - 1;
}

function validateSection(section) {
  if (section.isPreview) return { valid: true, filled: 0 };
  
  let filled = 0;
  let valid = true;
  
  for (const field of section.fields) {
    if (field.value !== null && field.value !== undefined && field.value !== '') {
      filled++;
    }
    if (field.required && (field.value === null || field.value === undefined || field.value === '')) {
      valid = false;
    }
  }
  
  return { valid, filled };
}

function renderSectionFields(section) {
  if (section.isPreview) {
    return renderPreviewSection();
  }
  
  if (!section.fields || section.fields.length === 0) {
    return '<div class="create-empty">Aucun champ dans cette section</div>';
  }
  
  return section.fields.map(field => {
    const errorHtml = field.errors?.length > 0 
      ? `<div class="form-field-error">${field.errors.map(e => e.message).join(', ')}</div>` 
      : '';
    
    const sourceHtml = field.prefillSource 
      ? `<span class="form-field-source">${field.prefillSource}</span>` 
      : '';
    
    return `
      <div class="form-field ${field.valid === false ? 'invalid' : ''}">
        <label class="form-field-label">
          ${field.label}
          ${field.required ? '<span class="form-field-required">*</span>' : ''}
          ${sourceHtml}
        </label>
        <div class="form-field-input">
          ${renderFieldInput(field)}
        </div>
        ${errorHtml}
        ${field.description ? `<div class="form-field-description">${field.description}</div>` : ''}
      </div>
    `;
  }).join('');
}

function renderFieldInput(field) {
  const value = field.value ?? '';
  const name = field.name;
  
  // Enum
  if (field.valueType === 'enum' && field.options) {
    if (field.options.length <= 5 && !field.multiple) {
      return `
        <div class="form-field-options">
          ${field.options.map(opt => {
            const optValue = typeof opt === 'string' ? opt : opt.value;
            const optLabel = typeof opt === 'string' ? opt : opt.label;
            return `
              <label class="form-field-option ${value === optValue ? 'selected' : ''}">
                <input type="radio" name="${name}" value="${optValue}" 
                       ${value === optValue ? 'checked' : ''}
                       onchange="handleFieldChange('${name}', this)">
                ${optLabel}
              </label>
            `;
          }).join('')}
        </div>
      `;
    } else {
      return `
        <select name="${name}" onchange="handleFieldChange('${name}', this)">
          <option value="">Sélectionner...</option>
          ${field.options.map(opt => {
            const optValue = typeof opt === 'string' ? opt : opt.value;
            const optLabel = typeof opt === 'string' ? opt : opt.label;
            return `<option value="${optValue}" ${value === optValue ? 'selected' : ''}>${optLabel}</option>`;
          }).join('')}
        </select>
      `;
    }
  }
  
  // Boolean
  if (field.valueType === 'boolean') {
    return `
      <label class="form-field-toggle">
        <input type="checkbox" name="${name}" ${value ? 'checked' : ''} onchange="handleFieldChange('${name}', this)">
        <span>${value ? 'Oui' : 'Non'}</span>
      </label>
    `;
  }
  
  // Number
  if (field.valueType === 'number') {
    return `<input type="number" name="${name}" value="${value}" 
                   ${field.min !== undefined ? `min="${field.min}"` : ''} 
                   ${field.max !== undefined ? `max="${field.max}"` : ''}
                   placeholder="${field.placeholder || ''}"
                   oninput="handleFieldChange('${name}', this)">`;
  }
  
  // Textarea
  if (field.multiline) {
    return `<textarea name="${name}" rows="4" placeholder="${field.placeholder || ''}"
                      oninput="handleFieldChange('${name}', this)">${value}</textarea>`;
  }
  
  // Default text
  return `<input type="text" name="${name}" value="${value}" 
                 placeholder="${field.placeholder || ''}"
                 oninput="handleFieldChange('${name}', this)">`;
}

function renderPreviewSection() {
  const state = ViewManager.state;
  if (!state.formData) return '<div class="create-empty">Aucune donnée</div>';
  
  let html = `<div class="preview-lineage">${state.lineage}</div>`;
  
  for (const section of state.formData.sections) {
    if (section.isPreview) continue;
    
    const filledFields = section.fields.filter(f => f.value !== null && f.value !== undefined && f.value !== '');
    if (filledFields.length === 0) continue;
    
    html += `
      <div class="preview-section">
        <div class="preview-section-title">${section.title}</div>
        ${filledFields.map(f => `
          <div class="preview-field">
            <span class="preview-label">${f.label}</span>
            <span class="preview-value">${f.value}</span>
          </div>
        `).join('')}
      </div>
    `;
  }
  
  return html;
}

function handleFieldChange(fieldName, element) {
  let value;
  
  if (element.type === 'checkbox') {
    value = element.checked;
  } else if (element.type === 'number') {
    value = element.value ? parseFloat(element.value) : null;
  } else {
    value = element.value;
  }
  
  // Mettre à jour le champ
  if (ViewManager.state.formData) {
    for (const section of ViewManager.state.formData.sections) {
      const field = section.fields.find(f => f.name === fieldName);
      if (field) {
        field.value = value;
        field.touched = true;
        break;
      }
    }
  }
  
  // Valider
  if (ViewManager.updateField) {
    ViewManager.updateField(fieldName, value);
  }
}

function goToSection(index) {
  ViewManager.state.currentSection = index;
  refreshFormView();
}

function nextSection() {
  const state = ViewManager.state;
  if (state.currentSection < state.formData.sections.length - 1) {
    state.currentSection++;
    refreshFormView();
  }
}

function previousSection() {
  if (ViewManager.state.currentSection > 0) {
    ViewManager.state.currentSection--;
    refreshFormView();
  }
}

// =============================================================================
// Chat
// =============================================================================

function refreshChatView() {
  const container = document.getElementById('chatMessages');
  const state = ViewManager.state;
  
  if (!state.conversation || state.conversation.length === 0) {
    container.innerHTML = '<div class="chat-empty">Démarrez une création pour utiliser le chat</div>';
    return;
  }
  
  container.innerHTML = state.conversation.map(msg => `
    <div class="chat-message ${msg.role}">
      <div class="chat-avatar">${msg.role === 'user' ? '👤' : '🤖'}</div>
      <div class="chat-bubble">${msg.content}</div>
    </div>
  `).join('');
  
  container.scrollTop = container.scrollHeight;
}

async function sendChatMessage() {
  const input = document.getElementById('chatInput');
  const message = input.value.trim();
  
  if (!message) return;
  if (!createState.initialized) {
    showToast('Démarrez une création d\'abord', 'warning');
    return;
  }
  
  input.value = '';
  
  // Ajouter message utilisateur
  ViewManager.state.conversation.push({
    role: 'user',
    content: message,
    timestamp: new Date().toISOString()
  });
  
  // Traiter le message selon le schema
  const response = processChatMessage(message);
  
  ViewManager.state.conversation.push({
    role: 'agent',
    content: response,
    timestamp: new Date().toISOString()
  });
  
  refreshChatView();
  refreshFormView();
}

/**
 * Traiter un message chat en utilisant les questions du schema
 */
function processChatMessage(message) {
  const schema = createState.schema;
  const state = ViewManager.state;
  
  // Extraire des valeurs depuis le message
  let extracted = 0;
  
  for (const attr of schema.attributes) {
    // Patterns de détection
    const patterns = [
      new RegExp(`(?:${attr.name}|${attr.label})\\s*[:=]\\s*["']?([^"'\\n]+)["']?`, 'i'),
      new RegExp(`(?:mon|ma|le|la)\\s+${attr.name}\\s+(?:est|sera|:)\\s*["']?([^"'\\n]+)["']?`, 'i')
    ];
    
    for (const pattern of patterns) {
      const match = message.match(pattern);
      if (match) {
        // Mettre à jour le champ
        for (const section of state.formData.sections) {
          const field = section.fields.find(f => f.name === attr.name);
          if (field && !field.value) {
            field.value = match[1].trim();
            field.prefillSource = 'chat';
            extracted++;
          }
        }
        break;
      }
    }
  }
  
  if (extracted > 0) {
    // Chercher le prochain champ vide requis
    for (const section of state.formData.sections) {
      const emptyRequired = section.fields.find(f => f.required && !f.value);
      if (emptyRequired && emptyRequired.question) {
        return `J'ai noté ${extracted} information(s). ${emptyRequired.question}`;
      }
    }
    return `J'ai noté ${extracted} information(s). Vous pouvez continuer ou passer à l'aperçu.`;
  }
  
  // Pas d'extraction, poser la prochaine question
  for (const section of state.formData.sections) {
    const emptyRequired = section.fields.find(f => f.required && !f.value);
    if (emptyRequired) {
      const question = emptyRequired.question || `Quelle est la valeur pour "${emptyRequired.label}" ?`;
      return question;
    }
  }
  
  return "Tous les champs requis sont remplis. Vous pouvez vérifier l'aperçu et créer l'objet.";
}

// =============================================================================
// Recap
// =============================================================================

function refreshRecapView() {
  const container = document.getElementById('recapContent');
  
  if (!createState.initialized) {
    container.innerHTML = '<div class="create-empty">Démarrez une création pour voir le récapitulatif</div>';
    return;
  }
  
  const state = ViewManager.state;
  let html = `<div class="recap-lineage">${state.lineage}</div>`;
  
  for (const section of state.formData.sections) {
    if (section.isPreview) continue;
    
    const filledFields = section.fields.filter(f => f.value !== null && f.value !== undefined && f.value !== '');
    if (filledFields.length === 0) continue;
    
    html += `
      <div class="recap-section">
        <div class="recap-section-title">${section.title}</div>
        <div class="recap-fields">
          ${filledFields.map(f => `
            <div class="recap-field">
              <span class="recap-field-label">${f.label}</span>
              <span class="recap-field-value">${f.value}</span>
              ${f.prefillSource ? `<span class="recap-field-source">(${f.prefillSource})</span>` : ''}
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }
  
  container.innerHTML = html;
}

// =============================================================================
// Actions
// =============================================================================

function updateAutonomy(value) {
  const level = parseInt(value) / 100;
  const label = document.getElementById('autonomyLabel');
  
  if (level < 0.3) {
    label.textContent = 'Manuel';
  } else if (level < 0.7) {
    label.textContent = 'Assisté';
  } else {
    label.textContent = 'Automatique';
  }
  
  if (ViewManager.setAutonomy) {
    ViewManager.setAutonomy(level);
  }
}

function cancelCreation() {
  createState = {
    files: [],
    parsedData: {},
    schema: null,
    initialized: false,
    typePicker: createState.typePicker
  };
  
  ViewManager.state = {
    lineage: null,
    formData: null,
    conversation: [],
    currentSection: 0,
    autonomyLevel: 0.5,
    activeView: 'form',
    sources: {}
  };
  
  document.getElementById('createTypeInput').value = '';
  document.getElementById('btnNextSection').disabled = true;
  document.getElementById('btnPrevSection').disabled = true;
  document.getElementById('btnFinalize').disabled = true;
  
  // Reset indicateurs
  document.querySelectorAll('.source-indicator').forEach(ind => ind.classList.remove('active'));
  
  refreshFormView();
  refreshChatView();
  refreshRecapView();
  refreshFilesList();
  
  // Rafraîchir le picker
  if (createState.typePicker) {
    createState.typePicker.refresh();
  }
  
  showToast('Création annulée', 'info');
}

async function finalizeCreation() {
  if (!createState.initialized) {
    showToast('Aucune création en cours', 'warning');
    return;
  }
  
  const state = ViewManager.state;
  
  // Valider tous les champs requis
  for (const section of state.formData.sections) {
    if (section.isPreview) continue;
    for (const field of section.fields) {
      if (field.required && !field.value) {
        showToast(`Champ requis manquant: ${field.label}`, 'error');
        return;
      }
    }
  }
  
  // Créer l'objet
  const lineage = state.lineage;
  createObjectType(lineage, { source: 'creation-form' });
  
  // Ajouter les attributs
  for (const section of state.formData.sections) {
    if (section.isPreview) continue;
    for (const field of section.fields) {
      if (field.value !== null && field.value !== undefined && field.value !== '') {
        addAttribute(lineage, {
          name: field.name,
          value: field.value,
          type: field.valueType
        });
      }
    }
  }
  
  // Rafraîchir l'index
  if (window.buildLineageIndex) buildLineageIndex();
  if (window.renderTree) renderTree();
  
  showToast(`Objet créé: ${lineage}`, 'success');
  
  // Sélectionner et basculer
  if (window.selectNode) selectNode(lineage);
  switchTab('explorer');
  
  cancelCreation();
}

// =============================================================================
// Exports
// =============================================================================

window.startCreation = startCreation;
window.switchCreateView = switchCreateView;
window.handleFieldChange = handleFieldChange;
window.goToSection = goToSection;
window.nextSection = nextSection;
window.previousSection = previousSection;
window.sendChatMessage = sendChatMessage;
window.updateAutonomy = updateAutonomy;
window.handleCreateUpload = handleCreateUpload;
window.removeCreateFile = removeCreateFile;
window.cancelCreation = cancelCreation;
window.finalizeCreation = finalizeCreation;
window.selectTypeFromModal = selectTypeFromModal;
