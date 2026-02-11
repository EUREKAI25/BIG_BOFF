/* =============================================================================
   EUREKAI — GetCreate Pattern
   Cherche un objet, si pas trouvé → crée via hookFailure
   Récursif pour les parents
   ============================================================================= */

const GetCreate = {
  
  // Mode dev = bypass permissions
  DEV_MODE: true,
  
  /**
   * Point d'entrée principal
   * @param {string} lineage - Lineage de l'objet à obtenir/créer
   * @param {Object} context - Contexte d'exécution
   * @returns {Object} - { success, object, created, blocked, task }
   */
  async execute(lineage, context = {}) {
    const startTime = Date.now();
    
    // Log start
    HistoryLogger.logStart('GetCreate', lineage, context);
    
    try {
      // Phase GET
      const getResult = await this._get(lineage, context);
      
      if (getResult.found) {
        // Objet trouvé
        const duration = Date.now() - startTime;
        HistoryLogger.logSuccess('GetCreate', lineage, { phase: 'get', found: true }, duration);
        
        return {
          success: true,
          object: getResult.object,
          created: false,
          source: 'existing'
        };
      }
      
      // Pas trouvé → hookFailure → CREATE
      HistoryLogger.logHook('GetCreate', 'Get', 'failure', { lineage, triggeredAction: 'Create' });
      
      // Phase CREATE
      const createResult = await this._create(lineage, context);
      
      const duration = Date.now() - startTime;
      
      if (createResult.blocked) {
        HistoryLogger.logFailure('GetCreate', lineage, createResult.reason, 'blocked');
        return createResult;
      }
      
      HistoryLogger.logSuccess('GetCreate', lineage, { phase: 'create', created: true }, duration);
      
      return {
        success: true,
        object: createResult.object,
        created: true,
        source: 'created',
        parentCreated: createResult.parentCreated || false
      };
      
    } catch (error) {
      HistoryLogger.logFailure('GetCreate', lineage, error);
      return {
        success: false,
        error: error.message,
        blocked: true
      };
    }
  },
  
  /**
   * Phase GET - Cherche l'objet
   */
  async _get(lineage, context) {
    HistoryLogger.logHook('GetCreate', 'Get', 'before', { lineage });
    
    const object = Store.get(lineage);
    
    if (object) {
      HistoryLogger.logHook('GetCreate', 'Get', 'after', { lineage, found: true });
      return { found: true, object };
    }
    
    return { found: false };
  },
  
  /**
   * Phase CREATE - Crée l'objet
   */
  async _create(lineage, context) {
    HistoryLogger.logHook('GetCreate', 'Create', 'before', { lineage });
    
    // 1. Obtenir le parent (récursif)
    const parentLineage = getParentLineage(lineage);
    let parentCreated = false;
    
    if (parentLineage) {
      const parentResult = await this.execute(parentLineage, { ...context, _isParentCall: true });
      
      if (!parentResult.success) {
        return {
          success: false,
          blocked: true,
          reason: `Parent creation failed: ${parentLineage}`,
          parentError: parentResult.error
        };
      }
      
      parentCreated = parentResult.created;
    }
    
    // 2. Vérifier permissions (bypass en DEV_MODE)
    if (!this.DEV_MODE) {
      const permitted = await this._checkPermissions(lineage, 'create', context);
      if (!permitted.allowed) {
        HistoryLogger.logHook('GetCreate', 'Create', 'failure', { 
          lineage, 
          reason: 'permission_denied',
          permission: permitted.reason 
        });
        
        // Créer tâche
        const taskResult = TaskGenerator.createMissingResourceTask(lineage, 'permission', {
          reason: permitted.reason
        });
        
        return {
          success: false,
          blocked: true,
          reason: 'Permission denied',
          task: taskResult.task
        };
      }
    }
    
    // 3. Collecter ressources
    const resources = await this._collectResources(lineage, parentLineage, context);
    HistoryLogger.log({
      type: 'resources_collected',
      lineage,
      schema: !!resources.schema,
      template: !!resources.template,
      examples: resources.examples?.length || 0
    });
    
    // 4. Vérifier ressources critiques
    if (!resources.schema && !parentLineage) {
      // Pas de schema et pas de parent = impossible
      const taskResult = TaskGenerator.createMissingResourceTask(lineage, 'schema', {
        reason: 'No schema available and no parent to inherit from'
      });
      
      return {
        success: false,
        blocked: true,
        reason: 'No schema available',
        task: taskResult.task
      };
    }
    
    // 5. Détecter APIs requises
    const apis = ApiDetector.detect(resources.schema || { attributeBundle: { owned: [] } });
    if (apis.length > 0) {
      HistoryLogger.logApiDetection(lineage, apis);
      
      const validation = ApiDetector.validateApis(apis);
      if (!validation.valid) {
        // Créer tâches pour chaque API externe non configurée
        for (const pending of validation.pendingList) {
          TaskGenerator.createApiConfigTask(lineage, pending.api, pending.providers);
        }
        
        // Ne bloque pas la création, mais bloquera la validation finale
        context._pendingApis = validation.pendingList;
      }
    }
    
    // 6. Créer l'objet
    const object = createObjectType(lineage, {
      source: context.source || 'getCreate',
      isIntermediate: context._isParentCall || false
    });
    
    if (!object) {
      HistoryLogger.logHook('GetCreate', 'Create', 'failure', { 
        lineage, 
        reason: 'creation_failed' 
      });
      
      return {
        success: false,
        blocked: true,
        reason: 'Object creation failed'
      };
    }
    
    // 7. Appliquer le schema hérité
    if (parentLineage && resources.parentSchema) {
      // Les éléments inherited sont déjà gérés par createObjectType via collectInheritedElements
      // Mais on peut ajouter des attributs par défaut du schema
      this._applySchemaDefaults(object, resources.parentSchema);
    }
    
    // 8. Marquer les APIs pendantes si nécessaire
    if (context._pendingApis?.length > 0) {
      object.attributeBundle.owned.push({
        name: '_pendingApis',
        value: context._pendingApis.map(a => a.api).join(','),
        type: 'internal'
      });
    }
    
    HistoryLogger.logHook('GetCreate', 'Create', 'after', { 
      lineage, 
      created: true,
      parentCreated 
    });
    
    buildLineageIndex();
    
    return {
      success: true,
      object,
      created: true,
      parentCreated,
      resources,
      apis
    };
  },
  
  /**
   * Vérifier les permissions
   */
  async _checkPermissions(lineage, action, context) {
    // Chercher permission dans le schema du type
    const permission = traverse(lineage, (obj, level) => {
      const permAttr = obj.attributeBundle?.owned?.find(
        a => a.name === `permission.${action}` || a.name === 'permission.create'
      );
      if (permAttr) {
        return { value: permAttr.value, from: level };
      }
    });
    
    if (permission && permission.value === false) {
      return { allowed: false, reason: `permission.${action} = false on ${permission.from}` };
    }
    
    // Par défaut, autorisé
    return { allowed: true };
  },
  
  /**
   * Collecter les ressources disponibles
   */
  async _collectResources(lineage, parentLineage, context) {
    const resources = {
      schema: null,
      parentSchema: null,
      template: null,
      examples: [],
      documentation: null
    };
    
    // Schema du parent
    if (parentLineage) {
      const parent = Store.get(parentLineage);
      if (parent) {
        resources.parentSchema = parent;
        resources.schema = parent; // Hérite du schema parent
      }
    }
    
    // Chercher un template spécifique
    const templateLineage = `Object:Template:${getLineageName(lineage)}`;
    resources.template = Store.get(templateLineage);
    
    // Chercher des exemples dans le catalog
    const examplePattern = `Object:Example:${getLineageName(lineage)}`;
    resources.examples = Store.query(examplePattern + '*');
    
    // Documentation
    const docLineage = `Object:Documentation:${getLineageName(lineage)}`;
    resources.documentation = Store.get(docLineage);
    
    return resources;
  },
  
  /**
   * Appliquer les valeurs par défaut du schema
   */
  _applySchemaDefaults(object, schema) {
    const schemaAttrs = schema.attributeBundle?.owned || [];
    
    for (const attr of schemaAttrs) {
      if (attr.default !== undefined) {
        // Vérifier si pas déjà défini
        const exists = object.attributeBundle.owned.find(a => a.name === attr.name);
        if (!exists) {
          object.attributeBundle.owned.push({
            name: attr.name,
            value: attr.default,
            type: attr.valueType || attr.type || 'string',
            source: 'owned'
          });
        }
      }
    }
  },
  
  /**
   * Vérifier si un objet peut être validé (APIs configurées, etc.)
   */
  canValidate(lineage) {
    const object = Store.get(lineage);
    if (!object) return { valid: false, reason: 'Object not found' };
    
    // Vérifier APIs pendantes
    const pendingApis = object.attributeBundle?.owned?.find(a => a.name === '_pendingApis');
    if (pendingApis && pendingApis.value) {
      const apis = pendingApis.value.split(',');
      const stillPending = apis.filter(api => ApiDetector.getExternalStatus(api) !== 'configured');
      
      if (stillPending.length > 0) {
        return {
          valid: false,
          reason: `APIs externes non configurées: ${stillPending.join(', ')}`,
          pendingApis: stillPending
        };
      }
    }
    
    // Vérifier champs required (à implémenter avec schema)
    
    return { valid: true };
  }
};

window.GetCreate = GetCreate;
