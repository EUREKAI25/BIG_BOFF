/* =============================================================================
   EUREKAI Cockpit — Fractal View
   ============================================================================= */

/**
 * Render fractal view for an object
 */
function renderFractal(lineage) {
  const container = document.getElementById('fractalContent');
  const titleEl = document.getElementById('fractalTitle');
  
  if (!container) return;
  
  const obj = Store.get(lineage);
  
  if (!obj) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">◇</div>
        <div>Sélectionnez un objet dans l'arbre</div>
      </div>
    `;
    if (titleEl) titleEl.textContent = 'Sélectionner un objet';
    return;
  }
  
  if (titleEl) titleEl.textContent = lineage;
  
  // Resolve elements with priority
  const resolved = resolveElements(obj);
  
  container.innerHTML = '';
  
  // Attributes card
  if (resolved.attributes.length > 0) {
    container.appendChild(renderFractalCard('Attributs', resolved.attributes, 'attribute'));
  }
  
  // Methods card
  if (resolved.methods.length > 0) {
    container.appendChild(renderFractalCard('Méthodes', resolved.methods, 'method'));
  }
  
  // Relations card
  if (resolved.relations.length > 0) {
    container.appendChild(renderFractalCard('Relations', resolved.relations, 'relation'));
  }
  
  // Rules card
  if (resolved.rules.length > 0) {
    container.appendChild(renderFractalCard('Règles', resolved.rules, 'rule'));
  }
  
  // Children card
  const children = getChildren(lineage);
  if (children.length > 0) {
    container.appendChild(renderChildrenCard(children));
  }
  
  // Tags
  if (obj.tags && obj.tags.length > 0) {
    container.appendChild(renderTagsCard(obj.tags, lineage));
  }
  
  // If nothing to show
  if (container.children.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">◇</div>
        <div>Objet vide - ajoutez des attributs ou relations</div>
      </div>
    `;
  }
}

/**
 * Render a fractal card
 */
function renderFractalCard(title, items, type) {
  const card = document.createElement('div');
  card.className = 'fractal-card';
  
  const header = document.createElement('div');
  header.className = 'fractal-card-header';
  header.innerHTML = `
    <span class="fractal-card-title">${title}</span>
    <span class="fractal-card-count">${items.length}</span>
  `;
  
  const content = document.createElement('div');
  content.className = 'fractal-card-content';
  
  for (const item of items) {
    const el = document.createElement('div');
    el.className = `element-item ${item.source || 'owned'}`;
    
    if (type === 'attribute') {
      el.innerHTML = `
        <span class="element-name">${item.name}</span>
        <span class="element-type">${item.type || 'any'}</span>
        ${item.value !== undefined ? `<span class="element-value">${String(item.value).substring(0, 50)}</span>` : ''}
        <span class="element-source ${item.source}">${item.source}${item.from ? ` (${getLineageName(item.from)})` : ''}</span>
      `;
    } else if (type === 'method') {
      el.innerHTML = `
        <span class="element-name">${item.name}</span>
        <span class="element-type">${item.returns || 'void'}</span>
        <span class="element-source ${item.source}">${item.source}</span>
      `;
    } else if (type === 'relation') {
      el.innerHTML = `
        <span class="element-name">${item.type}</span>
        <span class="element-value">${item.target}</span>
        <span class="element-source ${item.source}">${item.source}</span>
      `;
    } else if (type === 'rule') {
      el.innerHTML = `
        <span class="element-name">${item.name || item.type}</span>
        <span class="element-source ${item.source}">${item.source}</span>
      `;
    }
    
    content.appendChild(el);
  }
  
  card.appendChild(header);
  card.appendChild(content);
  return card;
}

/**
 * Render children card
 */
function renderChildrenCard(children) {
  const card = document.createElement('div');
  card.className = 'fractal-card';
  
  const header = document.createElement('div');
  header.className = 'fractal-card-header';
  header.innerHTML = `
    <span class="fractal-card-title">Enfants</span>
    <span class="fractal-card-count">${children.length}</span>
  `;
  
  const content = document.createElement('div');
  content.className = 'fractal-card-content';
  
  for (const childLineage of children) {
    const el = document.createElement('div');
    el.className = 'element-item';
    el.style.cursor = 'pointer';
    el.innerHTML = `
      <span class="element-name">${getLineageName(childLineage)}</span>
      <span class="element-value" style="color: var(--text-muted)">${childLineage}</span>
    `;
    el.onclick = () => selectNode(childLineage);
    content.appendChild(el);
  }
  
  card.appendChild(header);
  card.appendChild(content);
  return card;
}

/**
 * Render tags card
 */
function renderTagsCard(tags, lineage) {
  const card = document.createElement('div');
  card.className = 'fractal-card';
  
  const header = document.createElement('div');
  header.className = 'fractal-card-header';
  header.innerHTML = `
    <span class="fractal-card-title">Tags</span>
    <span class="fractal-card-count">${tags.length}</span>
  `;
  
  const content = document.createElement('div');
  content.className = 'fractal-card-content';
  content.style.display = 'flex';
  content.style.flexWrap = 'wrap';
  content.style.gap = '6px';
  
  for (const tag of tags) {
    const tagEl = document.createElement('span');
    tagEl.className = 'tag-item';
    tagEl.style.marginBottom = '0';
    tagEl.innerHTML = `<span class="tag-name">${tag}</span>`;
    tagEl.onclick = () => toggleTagFilter(tag);
    content.appendChild(tagEl);
  }
  
  card.appendChild(header);
  card.appendChild(content);
  return card;
}

/**
 * Setup depth control
 */
function setupDepthControl() {
  const slider = document.getElementById('depthSlider');
  const valueEl = document.getElementById('depthValue');
  
  if (slider && valueEl) {
    slider.value = Store.ui.maxDepth;
    valueEl.textContent = Store.ui.maxDepth;
    
    slider.oninput = () => {
      Store.ui.maxDepth = parseInt(slider.value);
      valueEl.textContent = slider.value;
      if (Store.ui.selectedLineage) {
        renderFractal(Store.ui.selectedLineage);
      }
    };
  }
}

// Global access
window.renderFractal = renderFractal;
window.setupDepthControl = setupDepthControl;
