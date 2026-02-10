/* =============================================================================
   EUREKAI — Form Builder
   Génère des formulaires par sections depuis le schema
   Agnostique du rendu (le theme décide des contrôles)
   ============================================================================= */

const FormBuilder = {
  
  // Ordre des sections par défaut
  defaultSectionOrder: ['identity', 'core', 'options', 'relations', 'rules', 'preview'],
  
  // Seuil pour créer une section dédiée pour une liste
  listSectionThreshold: 8,
  
  /**
   * Générer la structure du formulaire depuis un schema
   * @param {string} lineage - Lineage de l'objet à créer
   * @param {Object} options - Options { sources, parentSchema }
   * @returns {Object} - Structure du formulaire
   */
  generate(lineage, options = {}) {
    const name = getLineageName(lineage);
    const parentLineage = getParentLineage(lineage);
    
    // Collecter les attributs depuis différentes sources
    const attributes = this._collectAttributes(lineage, options);
    
    // Organiser en sections
    const sections = this._organizeSections(attributes, options);
    
    // Pré-remplir depuis les sources
    const prefilled = this._prefillFromSources(sections, options.sources || {});
    
    return {
      lineage,
      name,
      parent: parentLineage,
      sections: prefilled,
      metadata: {
        generatedAt: new Date().toISOString(),
        attributeCount: attributes.length,
        sectionCount: prefilled.length,
        sources: Object.keys(options.sources || {})
      }
    };
  },
  
  /**
   * Collecter les attributs depuis le schema et les héritages
   */
  _collectAttributes(lineage, options) {
    const attributes = [];
    const seen = new Set();
    
    // 1. Attributs du schema parent
    const parentLineage = getParentLineage(lineage);
    if (parentLineage) {
      const parent = Store.get(parentLineage);
      if (parent) {
        for (const attr of (parent.attributeBundle?.owned || [])) {
          if (!seen.has(attr.name) && !attr.name.startsWith('_')) {
            seen.add(attr.name);
            attributes.push({
              ...attr,
              source: 'inherited',
              from: parentLineage
            });
          }
        }
      }
    }
    
    // 2. Attributs hérités via traverse
    traverse(lineage, (obj, level) => {
      for (const attr of (obj.attributeBundle?.owned || [])) {
        if (!seen.has(attr.name) && !attr.name.startsWith('_')) {
          seen.add(attr.name);
          attributes.push({
            ...attr,
            source: 'inherited',
            from: level
          });
        }
      }
    }, { skipSelf: true });
    
    // 3. Attributs injectés (comportements)
    const injected = options.injected || [];
    for (const attr of injected) {
      if (!seen.has(attr.name)) {
        seen.add(attr.name);
        attributes.push({
          ...attr,
          source: 'injected'
        });
      }
    }
    
    return attributes;
  },
  
  /**
   * Organiser les attributs en sections
   */
  _organizeSections(attributes, options) {
    const sections = {
      identity: {
        name: 'identity',
        title: 'Identité',
        description: 'Informations de base',
        fields: [
          // Champs système
          { 
            name: 'name', 
            valueType: 'string', 
            required: true,
            minLength: 2,
            maxLength: 50,
            placeholder: "Nom de l'objet",
            system: true
          }
        ]
      },
      core: {
        name: 'core',
        title: 'Attributs requis',
        description: 'Champs obligatoires',
        fields: []
      },
      options: {
        name: 'options',
        title: 'Options',
        description: 'Champs optionnels',
        fields: []
      },
      relations: {
        name: 'relations',
        title: 'Relations',
        description: 'Liens avec autres objets',
        fields: []
      }
    };
    
    // Sections dédiées pour grandes listes
    const dedicatedSections = {};
    
    // Trier les attributs
    for (const attr of attributes) {
      // Ignorer les attributs système internes
      if (attr.name.startsWith('_') || attr.system) continue;
      
      // Déterminer la section
      const field = this._attributeToField(attr);
      
      if (attr.valueType === 'lineage' || attr.type === 'lineage') {
        // Relation vers un autre objet
        sections.relations.fields.push(field);
      }
      else if (attr.valueType === 'enum' && attr.multiple && attr.options?.length >= this.listSectionThreshold) {
        // Grande liste → section dédiée
        const sectionName = `list_${attr.name}`;
        dedicatedSections[sectionName] = {
          name: sectionName,
          title: attr.label || this._humanize(attr.name),
          description: attr.description || `Sélectionnez les ${attr.name}`,
          fields: [field],
          isList: true
        };
      }
      else if (attr.required) {
        sections.core.fields.push(field);
      }
      else {
        sections.options.fields.push(field);
      }
    }
    
    // Construire l'ordre final des sections
    const orderedSections = [];
    
    for (const sectionName of this.defaultSectionOrder) {
      if (sections[sectionName] && sections[sectionName].fields.length > 0) {
        orderedSections.push(sections[sectionName]);
      }
    }
    
    // Ajouter les sections dédiées
    for (const section of Object.values(dedicatedSections)) {
      orderedSections.push(section);
    }
    
    // Section preview toujours à la fin
    orderedSections.push({
      name: 'preview',
      title: 'Aperçu',
      description: 'Vérifier avant création',
      fields: [],
      isPreview: true
    });
    
    return orderedSections;
  },
  
  /**
   * Convertir un attribut schema en définition de champ
   */
  _attributeToField(attr) {
    return {
      name: attr.name,
      label: attr.label || this._humanize(attr.name),
      description: attr.description || null,
      
      // Type et contraintes (pour le theme)
      valueType: attr.valueType || attr.type || 'string',
      required: attr.required || false,
      
      // Contraintes numériques
      min: attr.min,
      max: attr.max,
      step: attr.step,
      
      // Contraintes string
      minLength: attr.minLength,
      maxLength: attr.maxLength,
      pattern: attr.pattern,
      multiline: attr.multiline || false,
      
      // Enum
      options: attr.options ? this._parseOptions(attr.options) : null,
      multiple: attr.multiple || false,
      
      // Référence
      targetType: attr.targetType,
      
      // Valeurs
      default: attr.default,
      placeholder: attr.placeholder,
      
      // Métadonnées
      source: attr.source,
      from: attr.from,
      
      // API
      api: attr.api,
      apiProvider: attr.apiProvider,
      
      // État
      value: null,
      touched: false,
      valid: null,
      errors: []
    };
  },
  
  /**
   * Parser les options enum
   */
  _parseOptions(options) {
    if (typeof options === 'string') {
      return options.split('|').map(o => ({
        value: o.trim(),
        label: this._humanize(o.trim())
      }));
    }
    if (Array.isArray(options)) {
      return options.map(o => {
        if (typeof o === 'string') {
          return { value: o, label: this._humanize(o) };
        }
        return o;
      });
    }
    return [];
  },
  
  /**
   * Pré-remplir les champs depuis les sources
   */
  _prefillFromSources(sections, sources) {
    const { seed, catalog, instance, inherited, injected } = sources;
    
    for (const section of sections) {
      for (const field of section.fields) {
        // Priorité : instance > seed > catalog > inherited > injected > default
        
        if (instance && instance[field.name] !== undefined) {
          field.value = instance[field.name];
          field.prefillSource = 'instance';
        }
        else if (seed && seed[field.name] !== undefined) {
          field.value = seed[field.name];
          field.prefillSource = 'seed';
        }
        else if (catalog && catalog[field.name] !== undefined) {
          field.value = catalog[field.name];
          field.prefillSource = 'catalog';
        }
        else if (inherited && inherited[field.name] !== undefined) {
          field.value = inherited[field.name];
          field.prefillSource = 'inherited';
        }
        else if (injected && injected[field.name] !== undefined) {
          field.value = injected[field.name];
          field.prefillSource = 'injected';
        }
        else if (field.default !== undefined) {
          field.value = field.default;
          field.prefillSource = 'default';
        }
      }
    }
    
    return sections;
  },
  
  /**
   * Valider une section
   */
  validateSection(section) {
    const errors = [];
    
    for (const field of section.fields) {
      const fieldErrors = this.validateField(field);
      if (fieldErrors.length > 0) {
        errors.push({
          field: field.name,
          errors: fieldErrors
        });
        field.errors = fieldErrors;
        field.valid = false;
      } else {
        field.errors = [];
        field.valid = true;
      }
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  },
  
  /**
   * Valider un champ
   */
  validateField(field) {
    const errors = [];
    const value = field.value;
    
    // Required
    if (field.required && (value === null || value === undefined || value === '')) {
      errors.push({ type: 'required', message: 'Ce champ est requis' });
    }
    
    // Skip other validations if empty and not required
    if (value === null || value === undefined || value === '') {
      return errors;
    }
    
    // String constraints
    if (field.valueType === 'string') {
      if (field.minLength && value.length < field.minLength) {
        errors.push({ type: 'minLength', message: `Minimum ${field.minLength} caractères` });
      }
      if (field.maxLength && value.length > field.maxLength) {
        errors.push({ type: 'maxLength', message: `Maximum ${field.maxLength} caractères` });
      }
      if (field.pattern && !new RegExp(field.pattern).test(value)) {
        errors.push({ type: 'pattern', message: 'Format invalide' });
      }
    }
    
    // Number constraints
    if (field.valueType === 'number') {
      const num = parseFloat(value);
      if (isNaN(num)) {
        errors.push({ type: 'type', message: 'Doit être un nombre' });
      } else {
        if (field.min !== undefined && num < field.min) {
          errors.push({ type: 'min', message: `Minimum ${field.min}` });
        }
        if (field.max !== undefined && num > field.max) {
          errors.push({ type: 'max', message: `Maximum ${field.max}` });
        }
      }
    }
    
    // Enum constraints
    if (field.valueType === 'enum' && field.options) {
      const validValues = field.options.map(o => o.value);
      if (field.multiple) {
        const values = Array.isArray(value) ? value : [value];
        for (const v of values) {
          if (!validValues.includes(v)) {
            errors.push({ type: 'enum', message: `Valeur invalide: ${v}` });
          }
        }
      } else {
        if (!validValues.includes(value)) {
          errors.push({ type: 'enum', message: 'Valeur invalide' });
        }
      }
    }
    
    return errors;
  },
  
  /**
   * Valider tout le formulaire
   */
  validateAll(formData) {
    const results = [];
    
    for (const section of formData.sections) {
      if (section.isPreview) continue;
      
      const result = this.validateSection(section);
      results.push({
        section: section.name,
        ...result
      });
    }
    
    const allValid = results.every(r => r.valid);
    
    return {
      valid: allValid,
      sections: results
    };
  },
  
  /**
   * Extraire les valeurs du formulaire
   */
  extractValues(formData) {
    const values = {};
    
    for (const section of formData.sections) {
      if (section.isPreview) continue;
      
      for (const field of section.fields) {
        if (field.value !== null && field.value !== undefined) {
          values[field.name] = field.value;
        }
      }
    }
    
    return values;
  },
  
  /**
   * Humanize une string (camelCase → Title Case)
   */
  _humanize(str) {
    return str
      .replace(/([A-Z])/g, ' $1')
      .replace(/_/g, ' ')
      .replace(/^\w/, c => c.toUpperCase())
      .trim();
  }
};

window.FormBuilder = FormBuilder;
