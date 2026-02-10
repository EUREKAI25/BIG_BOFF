/* =============================================================================
   EUREKAI — History Logger
   Log systématique pour audit d'exécution
   Format: dict { timestamp: eventData }
   ============================================================================= */

const HistoryLogger = {
  
  // Contexte actif (projet ou global)
  _activeContext: null,
  
  /**
   * Définir le contexte actif (projet)
   * @param {string} projectLineage - Lineage du projet ou null pour global
   */
  setContext(projectLineage) {
    this._activeContext = projectLineage;
  },
  
  /**
   * Obtenir l'objet history actif
   * @returns {Object} - Le dict history
   */
  getHistory() {
    if (this._activeContext) {
      const project = Store.get(this._activeContext);
      if (project) {
        if (!project.history) project.history = {};
        return project.history;
      }
    }
    // Fallback : history global dans le contexte GEVR
    if (!Store.gevrContext.history) Store.gevrContext.history = {};
    return Store.gevrContext.history;
  },
  
  /**
   * Log un événement
   * @param {Object} event - Données de l'événement
   * @returns {string} - Timestamp utilisé comme clé
   */
  log(event) {
    const timestamp = new Date().toISOString();
    const history = this.getHistory();
    
    const entry = {
      ...event,
      _logged: timestamp,
      _context: this._activeContext || 'global'
    };
    
    history[timestamp] = entry;
    
    // Aussi log en console pour debug
    console.log(`[History] ${timestamp}`, entry);
    
    return timestamp;
  },
  
  /**
   * Log un hook de scénario
   * @param {string} scenario - Nom du scénario (ex: "GetCreate")
   * @param {string} step - Étape (ex: "Get", "Create")
   * @param {string} hook - Type de hook (before, after, failure)
   * @param {Object} data - Données additionnelles
   */
  logHook(scenario, step, hook, data = {}) {
    return this.log({
      type: 'hook',
      scenario,
      step,
      hook: `${step.toLowerCase()}.${hook}`,
      ...data
    });
  },
  
  /**
   * Log début d'opération
   */
  logStart(scenario, lineage, input = {}) {
    return this.log({
      type: 'start',
      scenario,
      lineage,
      input,
      status: 'started'
    });
  },
  
  /**
   * Log fin d'opération réussie
   */
  logSuccess(scenario, lineage, output = {}, duration = null) {
    return this.log({
      type: 'end',
      scenario,
      lineage,
      output,
      duration,
      status: 'success'
    });
  },
  
  /**
   * Log échec d'opération
   */
  logFailure(scenario, lineage, error, triggeredAction = null) {
    return this.log({
      type: 'end',
      scenario,
      lineage,
      error: typeof error === 'string' ? error : error.message,
      triggeredAction,
      status: 'failure'
    });
  },
  
  /**
   * Log création de tâche
   */
  logTask(taskLineage, reason, assignedTo) {
    return this.log({
      type: 'task',
      taskLineage,
      reason,
      assignedTo,
      status: 'created'
    });
  },
  
  /**
   * Log détection API
   */
  logApiDetection(lineage, apis) {
    return this.log({
      type: 'api_detection',
      lineage,
      apis,
      internalCount: apis.filter(a => a.type === 'internal').length,
      externalCount: apis.filter(a => a.type === 'external').length,
      pendingCount: apis.filter(a => a.status === 'pending').length
    });
  },
  
  /**
   * Log validation de section formulaire
   */
  logSectionComplete(lineage, sectionName, data) {
    return this.log({
      type: 'section_complete',
      lineage,
      section: sectionName,
      fieldsCount: Object.keys(data).length
    });
  },
  
  /**
   * Obtenir les entrées filtrées
   * @param {Object} filters - { scenario, status, after, before }
   * @returns {Array} - Entrées filtrées, triées par date
   */
  query(filters = {}) {
    const history = this.getHistory();
    let entries = Object.entries(history).map(([ts, data]) => ({ timestamp: ts, ...data }));
    
    if (filters.scenario) {
      entries = entries.filter(e => e.scenario === filters.scenario);
    }
    if (filters.status) {
      entries = entries.filter(e => e.status === filters.status);
    }
    if (filters.type) {
      entries = entries.filter(e => e.type === filters.type);
    }
    if (filters.after) {
      entries = entries.filter(e => e.timestamp > filters.after);
    }
    if (filters.before) {
      entries = entries.filter(e => e.timestamp < filters.before);
    }
    if (filters.lineage) {
      entries = entries.filter(e => e.lineage === filters.lineage);
    }
    
    // Tri chronologique
    entries.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
    
    return entries;
  },
  
  /**
   * Exporter l'history pour audit
   */
  export() {
    return {
      context: this._activeContext || 'global',
      exportedAt: new Date().toISOString(),
      entries: this.getHistory()
    };
  },
  
  /**
   * Nettoyer les anciennes entrées
   * @param {number} retentionDays - Nombre de jours à conserver
   */
  cleanup(retentionDays = 90) {
    const history = this.getHistory();
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - retentionDays);
    const cutoffStr = cutoff.toISOString();
    
    let removed = 0;
    for (const ts of Object.keys(history)) {
      if (ts < cutoffStr) {
        delete history[ts];
        removed++;
      }
    }
    
    console.log(`[History] Cleanup: ${removed} entries removed (retention: ${retentionDays}d)`);
    return removed;
  }
};

window.HistoryLogger = HistoryLogger;
