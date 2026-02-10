/* =============================================================================
   EUREKAI Module — Tree
   Arbre hiérarchique des objets
   ============================================================================= */

const Module_tree = {
  config: null,
  
  /**
   * Initialiser le module
   */
  init(config, template) {
    this.config = config;
    
    // Écouter les événements
    EventBus.on('store:change', () => this.refresh(), 'tree');
    EventBus.on('filter:tags', (data) => this.applyTagFilter(data.tags), 'tree');
    
    console.log('[Module:tree] Initialized');
  },
  
  /**
   * Rendre le HTML du module
   */
  render(config) {
    return `
      <div class="tree-module">
        <div class="panel-header">
          <span class="panel-title">Objects</span>
          <span class="object-count" id="objectCount">0</span>
        </div>
        ${config.config.searchable ? `
          <div class="tree-search">
            <input type="text" id="treeSearchInput" placeholder="🔍 Rechercher..." 
                   oninput="Module_tree.search(this.value)">
          </div>
        ` : ''}
        <div class="panel-content tree-container" id="treeContainer"></div>
      </div>
    `;
  },
  
  /**
   * Rafraîchir l'arbre
   */
  refresh() {
    const container = document.getElementById('treeContainer');
    if (!container || !window.Store) return;
    
    const roots = Store.lineageIndex?.roots || [];
    
    if (roots.length === 0) {
      container.innerHTML = '<div class="empty-state">Aucun objet</div>';
      this.updateCount(0);
      return;
    }
    
    let html = '';
    for (const root of roots) {
      html += this.renderNode(root, 0);
    }
    
    container.innerHTML = html;
    this.updateCount(Store.count ? Store.count() : Object.keys(Store.objectTypes || {}).length);
  },
  
  /**
   * Rendre un noeud de l'arbre
   */
  renderNode(lineage, depth) {
    const obj = Store.get(lineage);
    if (!obj) return '';
    
    const children = this.getChildren(lineage);
    const hasChildren = children.length > 0;
    const isExpanded = Store.ui?.expandedNodes?.has(lineage);
    const isSelected = Store.ui?.selectedLineage === lineage;
    const name = lineage.split(':').pop();
    
    let html = `
      <div class="tree-node" data-lineage="${lineage}">
        <div class="tree-node-header ${isSelected ? 'selected' : ''}" 
             onclick="Module_tree.selectNode('${lineage}')">
          <span class="tree-toggle ${hasChildren ? 'has-children' : ''}" 
                onclick="event.stopPropagation(); Module_tree.toggleNode('${lineage}')">
            ${hasChildren ? (isExpanded ? '▼' : '▶') : '·'}
          </span>
          <span class="tree-label">${name}</span>
        </div>
    `;
    
    if (hasChildren && isExpanded) {
      html += '<div class="tree-children expanded">';
      for (const child of children) {
        html += this.renderNode(child, depth + 1);
      }
      html += '</div>';
    }
    
    html += '</div>';
    return html;
  },
  
  /**
   * Obtenir les enfants d'un lineage
   */
  getChildren(lineage) {
    if (!Store.lineageIndex?.index) return [];
    return Store.lineageIndex.index[lineage] || [];
  },
  
  /**
   * Sélectionner un noeud
   */
  selectNode(lineage) {
    if (Store.ui) Store.ui.selectedLineage = lineage;
    
    EventBus.emit('object:select', { lineage }, 'tree');
    this.refresh();
  },
  
  /**
   * Toggler expand/collapse
   */
  toggleNode(lineage) {
    if (!Store.ui) return;
    
    if (Store.ui.expandedNodes.has(lineage)) {
      Store.ui.expandedNodes.delete(lineage);
      EventBus.emit('object:collapse', { lineage }, 'tree');
    } else {
      Store.ui.expandedNodes.add(lineage);
      EventBus.emit('object:expand', { lineage }, 'tree');
    }
    
    this.refresh();
  },
  
  /**
   * Rechercher
   */
  search(query) {
    if (!query.trim()) {
      this.refresh();
      return;
    }
    
    const container = document.getElementById('treeContainer');
    if (!container) return;
    
    const lowerQuery = query.toLowerCase();
    const allLineages = Object.keys(Store.objectTypes || {});
    const matches = allLineages.filter(l => l.toLowerCase().includes(lowerQuery));
    
    if (matches.length === 0) {
      container.innerHTML = '<div class="empty-state">Aucun résultat</div>';
      return;
    }
    
    // Expand ancestors of matches
    for (const match of matches) {
      const segments = match.split(':');
      for (let i = 1; i < segments.length; i++) {
        const ancestor = segments.slice(0, i).join(':');
        Store.ui?.expandedNodes?.add(ancestor);
      }
    }
    
    this.refresh();
    
    // Highlight matches
    for (const match of matches) {
      const node = container.querySelector(`[data-lineage="${match}"]`);
      if (node) {
        node.querySelector('.tree-node-header')?.classList.add('search-match');
      }
    }
  },
  
  /**
   * Appliquer le filtre par tags
   */
  applyTagFilter(tags) {
    // TODO: Implémenter le filtrage par tags
    this.refresh();
  },
  
  /**
   * Mettre à jour le compteur
   */
  updateCount(count) {
    const el = document.getElementById('objectCount');
    if (el) el.textContent = count;
  }
};

window.Module_tree = Module_tree;
