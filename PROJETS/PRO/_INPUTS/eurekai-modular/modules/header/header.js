/* =============================================================================
   EUREKAI Module — Header
   En-tête avec logo, breadcrumb, lineage input et actions
   ============================================================================= */

const Module_header = {
  config: null,
  currentLineage: null,
  
  /**
   * Initialiser le module
   */
  init(config, template) {
    this.config = config;
    
    // Écouter les événements
    EventBus.on('object:select', (data) => this.updateBreadcrumb(data.lineage), 'header');
    EventBus.on('breadcrumb:update', (data) => this.updateBreadcrumb(data.lineage), 'header');
    
    console.log('[Module:header] Initialized');
  },
  
  /**
   * Rendre le HTML du module
   */
  render(config) {
    const c = config.config;
    
    return `
      <div class="header">
        <div class="header-left">
          <div class="logo">
            <span class="logo-icon">◈</span>
            ${c.logo} <span class="version">${c.version}</span>
          </div>
          <div class="breadcrumb" id="breadcrumb"></div>
        </div>
        
        ${c.showLineageInput ? `
          <div class="lineage-input-wrapper">
            <div class="lineage-input-container">
              <span class="lineage-input-icon">◈</span>
              <input type="text" 
                     class="lineage-input" 
                     id="lineageInput" 
                     placeholder="Object:Entity:Agent.attr=value depends_on Object:Target"
                     onkeydown="if(event.key==='Enter') Module_header.submitLineage()">
              <button class="lineage-submit" onclick="Module_header.submitLineage()" title="Créer">+</button>
            </div>
          </div>
        ` : ''}
        
        <div class="header-actions">
          ${c.actions.includes('import') ? `
            <button class="action-btn" onclick="Module_header.action('import')" title="Importer">📁</button>
          ` : ''}
          ${c.actions.includes('export') ? `
            <button class="action-btn" onclick="Module_header.action('export')" title="Exporter">💾</button>
          ` : ''}
          ${c.actions.includes('bootstrap') ? `
            <button class="action-btn primary" onclick="Module_header.action('bootstrap')" title="Bootstrap">▶</button>
          ` : ''}
        </div>
      </div>
    `;
  },
  
  /**
   * Soumettre le lineage input
   */
  submitLineage() {
    const input = document.getElementById('lineageInput');
    const value = input?.value?.trim();
    
    if (!value) return;
    
    EventBus.emit('lineage:submit', { lineage: value }, 'header');
    input.value = '';
  },
  
  /**
   * Déclencher une action
   */
  action(actionName) {
    EventBus.emit(`action:${actionName}`, {}, 'header');
  },
  
  /**
   * Mettre à jour le breadcrumb
   */
  updateBreadcrumb(lineage) {
    this.currentLineage = lineage;
    const container = document.getElementById('breadcrumb');
    if (!container) return;
    
    if (!lineage) {
      container.innerHTML = '';
      return;
    }
    
    const segments = lineage.split(':');
    const html = segments.map((segment, idx) => {
      const partialLineage = segments.slice(0, idx + 1).join(':');
      const isLast = idx === segments.length - 1;
      
      return `
        ${idx > 0 ? '<span class="breadcrumb-separator">:</span>' : ''}
        <span class="breadcrumb-item ${isLast ? 'active' : ''}" 
              onclick="Module_header.navigateTo('${partialLineage}')">
          ${segment}
        </span>
      `;
    }).join('');
    
    container.innerHTML = html;
  },
  
  /**
   * Naviguer vers un lineage
   */
  navigateTo(lineage) {
    EventBus.emit('object:select', { lineage, source: 'breadcrumb' }, 'header');
  }
};

window.Module_header = Module_header;
