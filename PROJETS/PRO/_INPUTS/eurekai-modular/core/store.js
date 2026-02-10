/* =============================================================================
   EUREKAI Cockpit — Data Store
   ============================================================================= */

const Store = {
  // Object types storage
  objectTypes: {},
  
  // Tags storage
  tags: {},
  
  // Catalog
  catalog: { examples: [] },
  
  // Lineage index for fast lookups
  lineageIndex: { index: {}, roots: [] },
  
  // UI state
  ui: {
    selectedLineage: null,
    expandedNodes: new Set(),
    activeTags: [],
    maxDepth: 5
  },
  
  // File store for GEVR
  fileStore: {},
  
  // GEVR context
  gevrContext: {},
  
  // Event listeners
  _listeners: {},
  
  // Subscribe to store changes
  subscribe(event, callback) {
    if (!this._listeners[event]) this._listeners[event] = [];
    this._listeners[event].push(callback);
    return () => {
      this._listeners[event] = this._listeners[event].filter(cb => cb !== callback);
    };
  },
  
  // Emit event
  emit(event, data) {
    if (this._listeners[event]) {
      this._listeners[event].forEach(cb => cb(data));
    }
  },
  
  // Get object by lineage
  get(lineage) {
    return this.objectTypes[lineage] || null;
  },
  
  // Set object
  set(lineage, obj) {
    this.objectTypes[lineage] = obj;
    this.emit('change', { type: 'set', lineage, obj });
    return obj;
  },
  
  // Delete object
  delete(lineage) {
    const obj = this.objectTypes[lineage];
    if (obj) {
      delete this.objectTypes[lineage];
      this.emit('change', { type: 'delete', lineage });
      return true;
    }
    return false;
  },
  
  // Get all lineages
  getAllLineages() {
    return Object.keys(this.objectTypes);
  },
  
  // Get object count
  count() {
    return Object.keys(this.objectTypes).length;
  },
  
  // Query objects
  query(pattern) {
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
    return Object.entries(this.objectTypes)
      .filter(([lineage]) => regex.test(lineage))
      .map(([lineage, obj]) => ({ lineage, ...obj }));
  },
  
  // Reset store
  reset() {
    this.objectTypes = {};
    this.tags = {};
    this.lineageIndex = { index: {}, roots: [] };
    this.emit('reset');
  },
  
  // Export data
  export() {
    return {
      version: CONFIG.version,
      exportedAt: new Date().toISOString(),
      objectTypes: this.objectTypes,
      tags: this.tags,
      catalog: this.catalog
    };
  },
  
  // Import data
  import(data) {
    if (data.objectTypes) {
      Object.assign(this.objectTypes, data.objectTypes);
    }
    if (data.tags) {
      Object.assign(this.tags, data.tags);
    }
    if (data.catalog) {
      Object.assign(this.catalog, data.catalog);
    }
    this.emit('import', data);
    return true;
  }
};

// Global access
window.Store = Store;
