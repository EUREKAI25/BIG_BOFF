/* =============================================================================
   EUREKAI — Task Generator
   Génère des tâches pour ressources manquantes + alertes
   ============================================================================= */

const TaskGenerator = {
  
  // Criticité des types de ressources
  criticality: {
    'schema': 'high',        // Bloque
    'parent': 'high',        // Bloque
    'permission': 'high',    // Bloque
    'api_external': 'high',  // Bloque validation
    'template': 'medium',    // Continue avec warning
    'example': 'low',        // Continue silencieusement
    'documentation': 'low'   // Continue silencieusement
  },
  
  // Configuration alertes
  alertConfig: {
    defaultAssignee: 'User:SuperAdmin',
    channels: {
      front: true,     // Alerte dans le cockpit
      email: false,    // Email (à configurer)
      sms: false       // SMS (à configurer)
    }
  },
  
  /**
   * Configurer les alertes
   */
  configure(config) {
    Object.assign(this.alertConfig, config);
  },
  
  /**
   * Créer une tâche pour ressource manquante
   * @param {string} targetLineage - Lineage de l'objet qui nécessite la ressource
   * @param {string} resourceType - Type de ressource (schema, template, api_external, etc.)
   * @param {Object} details - Détails additionnels
   * @returns {Object} - { task, blocked, alert }
   */
  createMissingResourceTask(targetLineage, resourceType, details = {}) {
    const criticality = this.criticality[resourceType] || 'medium';
    const blocked = criticality === 'high';
    
    // Générer lineage de la tâche
    const taskId = `Task_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
    const taskLineage = `Object:Task:CreateMissingResource:${taskId}`;
    
    // Créer l'objet tâche
    const task = {
      lineage: taskLineage,
      name: taskId,
      createdAt: new Date().toISOString(),
      
      // Attributs de la tâche
      attributeBundle: {
        owned: [
          { name: 'targetLineage', value: targetLineage, type: 'lineage' },
          { name: 'resourceType', value: resourceType, type: 'string' },
          { name: 'criticality', value: criticality, type: 'enum' },
          { name: 'status', value: 'pending', type: 'enum' },
          { name: 'assignedTo', value: this.alertConfig.defaultAssignee, type: 'lineage' },
          { name: 'description', value: details.description || `Créer ${resourceType} pour ${targetLineage}`, type: 'string' },
          { name: 'reason', value: details.reason || 'Ressource manquante détectée par GetCreate', type: 'string' }
        ],
        inherited: [],
        injected: []
      },
      
      // Relations
      relationBundle: {
        owned: [
          { type: 'targets', target: targetLineage },
          { type: 'assigned_to', target: this.alertConfig.defaultAssignee }
        ],
        inherited: [],
        injected: []
      },
      
      // Tags
      tags: ['task', 'missing-resource', criticality]
    };
    
    // Ajouter détails spécifiques
    if (details.apiType) {
      task.attributeBundle.owned.push({ name: 'apiType', value: details.apiType, type: 'string' });
    }
    if (details.providers) {
      task.attributeBundle.owned.push({ name: 'suggestedProviders', value: details.providers.join(','), type: 'string' });
    }
    
    // Stocker la tâche
    Store.set(taskLineage, task);
    
    // Logger
    HistoryLogger.logTask(taskLineage, details.reason || resourceType, this.alertConfig.defaultAssignee);
    
    // Créer alerte si critique
    let alert = null;
    if (blocked) {
      alert = this.createAlert(taskLineage, targetLineage, resourceType, details);
    }
    
    return {
      task: taskLineage,
      taskObject: task,
      blocked,
      criticality,
      alert
    };
  },
  
  /**
   * Créer une alerte
   */
  createAlert(taskLineage, targetLineage, resourceType, details) {
    const alertId = `Alert_${Date.now()}`;
    const alertLineage = `Object:Alert:${alertId}`;
    
    const alert = {
      lineage: alertLineage,
      name: alertId,
      createdAt: new Date().toISOString(),
      
      attributeBundle: {
        owned: [
          { name: 'type', value: 'missing_resource', type: 'string' },
          { name: 'severity', value: 'high', type: 'enum' },
          { name: 'message', value: `Ressource critique manquante: ${resourceType} pour ${targetLineage}`, type: 'string' },
          { name: 'taskLineage', value: taskLineage, type: 'lineage' },
          { name: 'targetLineage', value: targetLineage, type: 'lineage' },
          { name: 'status', value: 'active', type: 'enum' },
          { name: 'channels', value: Object.keys(this.alertConfig.channels).filter(c => this.alertConfig.channels[c]).join(','), type: 'string' }
        ],
        inherited: [],
        injected: []
      },
      
      tags: ['alert', 'high-severity']
    };
    
    Store.set(alertLineage, alert);
    
    // Déclencher les canaux d'alerte
    this._triggerAlertChannels(alert, details);
    
    return alertLineage;
  },
  
  /**
   * Déclencher les canaux d'alerte
   */
  _triggerAlertChannels(alert, details) {
    const channels = this.alertConfig.channels;
    
    // Front (toujours actif en dev)
    if (channels.front) {
      this._alertFront(alert);
    }
    
    // Email (si configuré)
    if (channels.email) {
      this._alertEmail(alert);
    }
    
    // SMS (si configuré)
    if (channels.sms) {
      this._alertSms(alert);
    }
  },
  
  /**
   * Alerte front-end
   */
  _alertFront(alert) {
    const message = alert.attributeBundle.owned.find(a => a.name === 'message')?.value;
    
    // Toast urgent
    if (typeof showToast === 'function') {
      showToast(`🚨 ${message}`, 'error', 10000);
    }
    
    // Ajouter à la liste des alertes actives
    if (!Store.gevrContext.activeAlerts) {
      Store.gevrContext.activeAlerts = [];
    }
    Store.gevrContext.activeAlerts.push(alert.lineage);
    
    // Event pour UI
    Store.emit('alert', { alert });
  },
  
  /**
   * Alerte email (placeholder)
   */
  _alertEmail(alert) {
    console.log('[Alert:Email] Would send email:', alert.lineage);
    // TODO: Implémenter avec API externe email
  },
  
  /**
   * Alerte SMS (placeholder)
   */
  _alertSms(alert) {
    console.log('[Alert:SMS] Would send SMS:', alert.lineage);
    // TODO: Implémenter avec API externe SMS
  },
  
  /**
   * Créer tâche pour API externe non configurée
   */
  createApiConfigTask(targetLineage, apiType, providers = []) {
    return this.createMissingResourceTask(targetLineage, 'api_external', {
      apiType,
      providers,
      description: `Configurer l'API externe "${apiType}" pour ${targetLineage}`,
      reason: `API externe requise mais non configurée`
    });
  },
  
  /**
   * Obtenir les tâches pending
   */
  getPendingTasks() {
    return Store.query('Object:Task:CreateMissingResource:*')
      .filter(t => {
        const status = t.attributeBundle?.owned?.find(a => a.name === 'status')?.value;
        return status === 'pending';
      });
  },
  
  /**
   * Marquer une tâche comme résolue
   */
  resolveTask(taskLineage) {
    const task = Store.get(taskLineage);
    if (!task) return false;
    
    const statusAttr = task.attributeBundle.owned.find(a => a.name === 'status');
    if (statusAttr) {
      statusAttr.value = 'resolved';
    }
    
    task.attributeBundle.owned.push({
      name: 'resolvedAt',
      value: new Date().toISOString(),
      type: 'datetime'
    });
    
    HistoryLogger.log({
      type: 'task_resolved',
      taskLineage,
      status: 'resolved'
    });
    
    return true;
  }
};

window.TaskGenerator = TaskGenerator;
