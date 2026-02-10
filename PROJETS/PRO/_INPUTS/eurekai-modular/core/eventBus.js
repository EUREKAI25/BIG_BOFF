/* =============================================================================
   EUREKAI Modular — Event Bus
   Communication inter-modules par événements
   ============================================================================= */

const EventBus = {
  _listeners: {},
  _history: [],
  _maxHistory: 100,
  
  /**
   * S'abonner à un événement
   * @param {string} event - Nom de l'événement (ex: "tab:switch")
   * @param {Function} callback - Fonction à appeler
   * @param {string} [moduleId] - ID du module (pour debug)
   * @returns {Function} - Fonction de désabonnement
   */
  on(event, callback, moduleId = 'anonymous') {
    if (!this._listeners[event]) {
      this._listeners[event] = [];
    }
    
    const listener = { callback, moduleId, addedAt: Date.now() };
    this._listeners[event].push(listener);
    
    // Retourne une fonction pour se désabonner
    return () => this.off(event, callback);
  },
  
  /**
   * S'abonner une seule fois
   */
  once(event, callback, moduleId = 'anonymous') {
    const unsubscribe = this.on(event, (...args) => {
      unsubscribe();
      callback(...args);
    }, moduleId);
    return unsubscribe;
  },
  
  /**
   * Se désabonner d'un événement
   */
  off(event, callback) {
    if (!this._listeners[event]) return;
    
    this._listeners[event] = this._listeners[event].filter(
      listener => listener.callback !== callback
    );
  },
  
  /**
   * Émettre un événement
   * @param {string} event - Nom de l'événement
   * @param {*} data - Données à transmettre
   * @param {string} [sourceModule] - Module émetteur
   */
  emit(event, data = null, sourceModule = 'system') {
    const entry = {
      event,
      data,
      source: sourceModule,
      timestamp: new Date().toISOString(),
      listeners: 0
    };
    
    // Historique
    this._history.push(entry);
    if (this._history.length > this._maxHistory) {
      this._history.shift();
    }
    
    // Notifier les listeners
    if (this._listeners[event]) {
      entry.listeners = this._listeners[event].length;
      
      for (const listener of this._listeners[event]) {
        try {
          listener.callback(data, { event, source: sourceModule });
        } catch (err) {
          console.error(`[EventBus] Error in listener for "${event}" (${listener.moduleId}):`, err);
        }
      }
    }
    
    // Debug
    console.log(`[EventBus] ${sourceModule} → ${event}`, data || '');
    
    return entry.listeners;
  },
  
  /**
   * Obtenir l'historique des événements
   */
  getHistory(filter = {}) {
    let history = [...this._history];
    
    if (filter.event) {
      history = history.filter(e => e.event === filter.event);
    }
    if (filter.source) {
      history = history.filter(e => e.source === filter.source);
    }
    if (filter.after) {
      history = history.filter(e => e.timestamp > filter.after);
    }
    
    return history;
  },
  
  /**
   * Lister tous les événements enregistrés
   */
  getRegisteredEvents() {
    return Object.keys(this._listeners).map(event => ({
      event,
      listeners: this._listeners[event].length,
      modules: this._listeners[event].map(l => l.moduleId)
    }));
  },
  
  /**
   * Nettoyer tous les listeners d'un module
   */
  clearModule(moduleId) {
    for (const event of Object.keys(this._listeners)) {
      this._listeners[event] = this._listeners[event].filter(
        listener => listener.moduleId !== moduleId
      );
    }
  },
  
  /**
   * Reset complet
   */
  reset() {
    this._listeners = {};
    this._history = [];
  }
};

// Export global
window.EventBus = EventBus;
