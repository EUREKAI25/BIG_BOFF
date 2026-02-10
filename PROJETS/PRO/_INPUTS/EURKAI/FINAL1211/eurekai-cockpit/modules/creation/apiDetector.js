/* =============================================================================
   EUREKAI — API Detector
   Détecte les APIs requises (internes vs externes) pour un objet
   ============================================================================= */

const ApiDetector = {
  
  // APIs internes connues (gérées par EUREKAI)
  internalApis: {
    'date': { name: 'Date', type: 'internal', status: 'configured' },
    'time': { name: 'Time', type: 'internal', status: 'configured' },
    'datetime': { name: 'DateTime', type: 'internal', status: 'configured' },
    'uuid': { name: 'UUID', type: 'internal', status: 'configured' },
    'slug': { name: 'Slug', type: 'internal', status: 'configured' },
    'hash': { name: 'Hash', type: 'internal', status: 'configured' },
    'random': { name: 'Random', type: 'internal', status: 'configured' }
  },
  
  // APIs externes connues (requièrent configuration)
  externalApis: {
    'geo': { name: 'Geolocation', type: 'external', providers: ['google_maps', 'mapbox', 'openstreetmap'] },
    'weather': { name: 'Weather', type: 'external', providers: ['openweathermap', 'weatherapi'] },
    'currency': { name: 'Currency Exchange', type: 'external', providers: ['exchangerate', 'fixer'] },
    'translate': { name: 'Translation', type: 'external', providers: ['google_translate', 'deepl'] },
    'email': { name: 'Email Service', type: 'external', providers: ['sendgrid', 'mailgun', 'ses'] },
    'sms': { name: 'SMS Service', type: 'external', providers: ['twilio', 'vonage'] },
    'storage': { name: 'File Storage', type: 'external', providers: ['s3', 'gcs', 'azure_blob'] },
    'payment': { name: 'Payment', type: 'external', providers: ['stripe', 'paypal'] },
    'ai': { name: 'AI Model', type: 'external', providers: ['anthropic', 'openai', 'mistral'] },
    'search': { name: 'Search', type: 'external', providers: ['algolia', 'elasticsearch'] },
    'analytics': { name: 'Analytics', type: 'external', providers: ['google_analytics', 'mixpanel'] }
  },
  
  // Configuration des APIs externes (status par provider)
  _externalConfig: {},
  
  /**
   * Configurer une API externe
   * @param {string} apiType - Type d'API (geo, weather, etc.)
   * @param {string} provider - Provider choisi
   * @param {Object} config - Configuration (apiKey, etc.)
   */
  configureExternal(apiType, provider, config = {}) {
    this._externalConfig[apiType] = {
      provider,
      config,
      status: 'configured',
      configuredAt: new Date().toISOString()
    };
    
    HistoryLogger.log({
      type: 'api_config',
      apiType,
      provider,
      status: 'configured'
    });
  },
  
  /**
   * Obtenir le status d'une API externe
   */
  getExternalStatus(apiType) {
    return this._externalConfig[apiType]?.status || 'pending';
  },
  
  /**
   * Détecter les APIs requises pour un objet
   * @param {Object} obj - L'objet ou son schema
   * @returns {Array} - Liste des APIs { type, name, api, status, provider? }
   */
  detect(obj) {
    const apis = [];
    const schema = obj.attributeBundle?.owned || [];
    
    for (const attr of schema) {
      // Vérifier si l'attribut déclare une API explicitement
      if (attr.api) {
        apis.push(this._resolveApi(attr.name, attr.api, attr.apiProvider));
        continue;
      }
      
      // Inférer depuis le valueType
      const inferred = this._inferFromValueType(attr.name, attr.valueType || attr.type);
      if (inferred) {
        apis.push(inferred);
      }
    }
    
    // Dédupliquer par type d'API
    const unique = [];
    const seen = new Set();
    for (const api of apis) {
      if (!seen.has(api.api)) {
        seen.add(api.api);
        unique.push(api);
      }
    }
    
    return unique;
  },
  
  /**
   * Résoudre une API déclarée
   */
  _resolveApi(attrName, apiType, provider = null) {
    // API interne ?
    if (this.internalApis[apiType]) {
      return {
        attribute: attrName,
        ...this.internalApis[apiType],
        api: apiType
      };
    }
    
    // API externe ?
    if (this.externalApis[apiType]) {
      const external = this.externalApis[apiType];
      const config = this._externalConfig[apiType];
      
      return {
        attribute: attrName,
        api: apiType,
        name: external.name,
        type: 'external',
        providers: external.providers,
        provider: config?.provider || provider || null,
        status: config?.status || 'pending'
      };
    }
    
    // API inconnue
    return {
      attribute: attrName,
      api: apiType,
      name: apiType,
      type: 'unknown',
      status: 'unknown'
    };
  },
  
  /**
   * Inférer le type d'API depuis le valueType
   */
  _inferFromValueType(attrName, valueType) {
    if (!valueType) return null;
    
    const vt = valueType.toLowerCase();
    
    // Types internes évidents
    if (vt === 'date' || vt === 'datetime') {
      return { attribute: attrName, api: 'date', ...this.internalApis['date'] };
    }
    if (vt === 'time') {
      return { attribute: attrName, api: 'time', ...this.internalApis['time'] };
    }
    if (vt === 'uuid') {
      return { attribute: attrName, api: 'uuid', ...this.internalApis['uuid'] };
    }
    
    // Types qui suggèrent une API externe
    if (vt === 'geo' || vt === 'location' || vt === 'coordinates' || vt === 'address') {
      return this._resolveApi(attrName, 'geo');
    }
    if (vt === 'currency' || vt === 'money') {
      return this._resolveApi(attrName, 'currency');
    }
    if (vt === 'email' && attrName.includes('send')) {
      return this._resolveApi(attrName, 'email');
    }
    if (vt === 'phone' && attrName.includes('sms')) {
      return this._resolveApi(attrName, 'sms');
    }
    
    return null;
  },
  
  /**
   * Vérifier si toutes les APIs externes sont configurées
   * @param {Array} apis - Liste des APIs (from detect())
   * @returns {Object} - { valid, pending, missing }
   */
  validateApis(apis) {
    const external = apis.filter(a => a.type === 'external');
    const pending = external.filter(a => a.status === 'pending');
    const configured = external.filter(a => a.status === 'configured');
    
    return {
      valid: pending.length === 0,
      total: external.length,
      configured: configured.length,
      pending: pending.length,
      pendingList: pending.map(a => ({ api: a.api, name: a.name, providers: a.providers }))
    };
  },
  
  /**
   * Générer le message d'erreur pour APIs manquantes
   */
  getPendingMessage(validation) {
    if (validation.valid) return null;
    
    const list = validation.pendingList
      .map(a => `• ${a.name} (${a.providers.slice(0, 3).join(', ')})`)
      .join('\n');
    
    return `APIs externes requises (${validation.pending}/${validation.total} non configurées):\n${list}`;
  }
};

window.ApiDetector = ApiDetector;
