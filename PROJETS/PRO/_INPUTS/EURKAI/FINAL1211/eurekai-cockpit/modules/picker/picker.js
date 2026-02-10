/* =============================================================================
   EUREKAI — Picker Module
   Module réutilisable pour sélectionner des éléments avec présélection
   
   Usage:
   const picker = new Picker({
     query: (store) => store.getAllLineages().filter(l => !l.startsWith('Object:Schema')),
     display: (item) => ({ label: getLineageName(item), sublabel: item, value: item }),
     limit: 10,
     sort: 'frequency', // 'frequency' | 'alpha' | 'recent' | custom function
     onSelect: (item) => console.log('Selected:', item),
     onViewAll: () => showAllModal(),
     placeholder: 'Rechercher...',
     emptyMessage: 'Aucun élément trouvé'
   });
   
   picker.render(containerElement);
   picker.refresh();
   ============================================================================= */

class Picker {
  constructor(options = {}) {
    this.options = {
      query: options.query || (() => []),
      display: options.display || ((item) => ({ label: String(item), value: item })),
      limit: options.limit || 10,
      sort: options.sort || 'frequency',
      onSelect: options.onSelect || (() => {}),
      onViewAll: options.onViewAll || null,
      placeholder: options.placeholder || 'Rechercher...',
      emptyMessage: options.emptyMessage || 'Aucun élément',
      showSearch: options.showSearch !== false,
      showFrequency: options.showFrequency !== false,
      className: options.className || ''
    };
    
    this.container = null;
    this.items = [];
    this.filteredItems = [];
    this.searchQuery = '';
    this.frequencyMap = {};
  }
  
  /**
   * Rendre le picker dans un container
   */
  render(container) {
    this.container = container;
    this.container.innerHTML = '';
    this.container.className = `picker ${this.options.className}`;
    
    // Search input
    if (this.options.showSearch) {
      const searchWrapper = document.createElement('div');
      searchWrapper.className = 'picker-search';
      searchWrapper.innerHTML = `
        <input type="text" 
               class="picker-search-input" 
               placeholder="${this.options.placeholder}"
               oninput="this.pickerInstance.search(this.value)">
      `;
      searchWrapper.querySelector('input').pickerInstance = this;
      this.container.appendChild(searchWrapper);
    }
    
    // Items list
    const list = document.createElement('div');
    list.className = 'picker-list';
    this.listElement = list;
    this.container.appendChild(list);
    
    // View all link
    if (this.options.onViewAll) {
      const viewAll = document.createElement('div');
      viewAll.className = 'picker-view-all';
      viewAll.innerHTML = '<a href="#">Voir tout →</a>';
      viewAll.querySelector('a').addEventListener('click', (e) => {
        e.preventDefault();
        this.options.onViewAll(this.items);
      });
      this.container.appendChild(viewAll);
    }
    
    this.refresh();
    return this;
  }
  
  /**
   * Rafraîchir les données
   */
  refresh() {
    // Exécuter la query
    const rawItems = this.options.query(window.Store || {});
    
    // Calculer les fréquences si nécessaire
    if (this.options.sort === 'frequency') {
      this.calculateFrequency(rawItems);
    }
    
    // Transformer en objets display
    this.items = rawItems.map(item => {
      const display = this.options.display(item);
      return {
        ...display,
        _raw: item,
        _frequency: this.frequencyMap[this.getFrequencyKey(item)] || 0
      };
    });
    
    // Trier
    this.sortItems();
    
    // Filtrer si recherche active
    this.applyFilter();
    
    // Rendre
    this.renderItems();
  }
  
  /**
   * Calculer la fréquence des éléments (basé sur les segments de lineage)
   */
  calculateFrequency(items) {
    this.frequencyMap = {};
    
    for (const item of items) {
      const key = this.getFrequencyKey(item);
      this.frequencyMap[key] = (this.frequencyMap[key] || 0) + 1;
    }
    
    // Pour les lineages, compter aussi les parents
    if (items.length > 0 && typeof items[0] === 'string' && items[0].includes(':')) {
      const allLineages = items;
      
      for (const lineage of allLineages) {
        const segments = lineage.split(':');
        // Compter chaque segment intermédiaire
        for (let i = 1; i < segments.length; i++) {
          const partial = segments.slice(0, i + 1).join(':');
          this.frequencyMap[partial] = (this.frequencyMap[partial] || 0) + 1;
        }
      }
    }
  }
  
  /**
   * Obtenir la clé de fréquence pour un item
   */
  getFrequencyKey(item) {
    if (typeof item === 'string') {
      // Pour un lineage, prendre le type (sans l'instance)
      const parts = item.split(':');
      // Retourner le 2ème niveau si existe (ex: Object:Entity → Entity)
      return parts.length > 1 ? parts[1] : parts[0];
    }
    return String(item);
  }
  
  /**
   * Trier les items
   */
  sortItems() {
    const sortFn = this.options.sort;
    
    if (sortFn === 'frequency') {
      this.items.sort((a, b) => b._frequency - a._frequency);
    } else if (sortFn === 'alpha') {
      this.items.sort((a, b) => a.label.localeCompare(b.label));
    } else if (sortFn === 'recent') {
      // TODO: implémenter avec timestamps
      this.items.reverse();
    } else if (typeof sortFn === 'function') {
      this.items.sort(sortFn);
    }
  }
  
  /**
   * Rechercher
   */
  search(query) {
    this.searchQuery = query.toLowerCase().trim();
    this.applyFilter();
    this.renderItems();
  }
  
  /**
   * Appliquer le filtre de recherche
   */
  applyFilter() {
    if (!this.searchQuery) {
      this.filteredItems = this.items.slice(0, this.options.limit);
    } else {
      this.filteredItems = this.items
        .filter(item => {
          const searchIn = `${item.label} ${item.sublabel || ''} ${item.value}`.toLowerCase();
          return searchIn.includes(this.searchQuery);
        })
        .slice(0, this.options.limit);
    }
  }
  
  /**
   * Rendre la liste d'items
   */
  renderItems() {
    if (!this.listElement) return;
    
    if (this.filteredItems.length === 0) {
      this.listElement.innerHTML = `<div class="picker-empty">${this.options.emptyMessage}</div>`;
      return;
    }
    
    this.listElement.innerHTML = this.filteredItems.map((item, idx) => `
      <div class="picker-item" data-index="${idx}" onclick="this.closest('.picker').pickerInstance.selectItem(${idx})">
        <div class="picker-item-content">
          <span class="picker-item-label">${item.label}</span>
          ${item.sublabel ? `<span class="picker-item-sublabel">${item.sublabel}</span>` : ''}
        </div>
        ${this.options.showFrequency && item._frequency > 1 ? 
          `<span class="picker-item-frequency">${item._frequency}</span>` : ''}
      </div>
    `).join('');
    
    // Stocker la référence pour les event handlers
    this.container.pickerInstance = this;
  }
  
  /**
   * Sélectionner un item
   */
  selectItem(index) {
    const item = this.filteredItems[index];
    if (item) {
      this.options.onSelect(item._raw, item);
    }
  }
  
  /**
   * Obtenir tous les items (pour "Voir tout")
   */
  getAllItems() {
    return this.items;
  }
  
  /**
   * Obtenir les items filtrés actuels
   */
  getFilteredItems() {
    return this.filteredItems;
  }
}

// Styles par défaut (injectés une seule fois)
if (!document.getElementById('picker-styles')) {
  const style = document.createElement('style');
  style.id = 'picker-styles';
  style.textContent = `
    .picker {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    
    .picker-search {
      position: relative;
    }
    
    .picker-search-input {
      width: 100%;
      padding: 10px 12px;
      border: 1px solid var(--border-subtle, #333);
      border-radius: var(--radius-md, 6px);
      background: var(--bg-tertiary, #1a1a2e);
      color: var(--text-primary, #e6e6e6);
      font-size: 13px;
    }
    
    .picker-search-input:focus {
      outline: none;
      border-color: var(--accent-owned, #2ed573);
    }
    
    .picker-list {
      display: flex;
      flex-direction: column;
      gap: 4px;
      max-height: 300px;
      overflow-y: auto;
    }
    
    .picker-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 12px;
      background: var(--bg-tertiary, #1a1a2e);
      border-radius: var(--radius-sm, 4px);
      cursor: pointer;
      transition: all 0.15s;
    }
    
    .picker-item:hover {
      background: var(--glow-owned, rgba(46, 213, 115, 0.15));
      border-left: 2px solid var(--accent-owned, #2ed573);
    }
    
    .picker-item-content {
      display: flex;
      flex-direction: column;
      gap: 2px;
      overflow: hidden;
    }
    
    .picker-item-label {
      font-size: 13px;
      font-weight: 500;
      color: var(--text-primary, #e6e6e6);
    }
    
    .picker-item-sublabel {
      font-size: 11px;
      color: var(--text-muted, #666);
      font-family: var(--font-mono, monospace);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .picker-item-frequency {
      font-size: 11px;
      padding: 2px 8px;
      background: var(--bg-secondary, #16213e);
      border-radius: 10px;
      color: var(--text-muted, #666);
    }
    
    .picker-empty {
      padding: 20px;
      text-align: center;
      color: var(--text-muted, #666);
      font-style: italic;
    }
    
    .picker-view-all {
      text-align: center;
      padding: 8px;
    }
    
    .picker-view-all a {
      color: var(--accent-owned, #2ed573);
      text-decoration: none;
      font-size: 12px;
    }
    
    .picker-view-all a:hover {
      text-decoration: underline;
    }
  `;
  document.head.appendChild(style);
}

window.Picker = Picker;
