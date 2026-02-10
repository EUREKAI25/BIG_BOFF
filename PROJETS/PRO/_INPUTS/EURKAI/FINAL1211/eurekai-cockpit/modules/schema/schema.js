/* =============================================================================
   EUREKAI — Schema Module
   Gère les schemas des types d'objets (Object:Schema:<TypeName>)
   
   Un Schema définit :
   - attributes[] : les attributs avec leurs contraintes
   - questions[] : les questions à poser dans le chat
   - readers{} : les méthodes de lecture par type de source
   - validators[] : les validations personnalisées
   ============================================================================= */

const SchemaModule = {
  
  // Cache des schemas chargés
  cache: {},
  
  /**
   * Obtenir le schema pour un lineage donné
   * @param {string} lineage - Le lineage de l'objet à créer
   * @returns {Object|null} - Le schema ou null si pas trouvé
   */
  get(lineage) {
    // Extraire le type (dernier segment avant une éventuelle instance #)
    const typeName = this.extractTypeName(lineage);
    
    // Vérifier le cache
    if (this.cache[typeName]) {
      return this.cache[typeName];
    }
    
    // Chercher le schema dans le Store
    const schemaLineage = `Object:Schema:${typeName}`;
    const schemaObj = Store.get(schemaLineage);
    
    if (schemaObj) {
      const schema = this.parseSchemaObject(schemaObj);
      this.cache[typeName] = schema;
      return schema;
    }
    
    // Chercher un schema parent (héritage)
    const parentSchema = this.findParentSchema(lineage);
    if (parentSchema) {
      this.cache[typeName] = parentSchema;
      return parentSchema;
    }
    
    // Schema par défaut
    return this.getDefaultSchema(typeName);
  },
  
  /**
   * Extraire le nom du type depuis un lineage
   */
  extractTypeName(lineage) {
    // Retirer l'instance si présente (après #)
    const withoutInstance = lineage.split('#')[0];
    // Prendre le dernier segment
    const segments = withoutInstance.split(':');
    return segments[segments.length - 1];
  },
  
  /**
   * Chercher un schema parent
   */
  findParentSchema(lineage) {
    const segments = lineage.split(':');
    
    // Remonter dans la hiérarchie
    for (let i = segments.length - 1; i > 0; i--) {
      const parentType = segments[i - 1];
      const schemaLineage = `Object:Schema:${parentType}`;
      const schemaObj = Store.get(schemaLineage);
      
      if (schemaObj) {
        return this.parseSchemaObject(schemaObj);
      }
    }
    
    return null;
  },
  
  /**
   * Parser un objet schema depuis le Store
   */
  parseSchemaObject(schemaObj) {
    const schema = {
      name: schemaObj.lineage,
      attributes: [],
      questions: [],
      readers: {},
      validators: []
    };
    
    // Extraire les attributs depuis attributeBundle
    for (const attr of (schemaObj.attributeBundle?.owned || [])) {
      if (attr.name === '_attributes' && attr.value) {
        // Format JSON des attributs
        try {
          schema.attributes = JSON.parse(attr.value);
        } catch (e) {
          console.warn('[Schema] Erreur parsing _attributes:', e);
        }
      }
      else if (attr.name === '_questions' && attr.value) {
        try {
          schema.questions = JSON.parse(attr.value);
        } catch (e) {
          console.warn('[Schema] Erreur parsing _questions:', e);
        }
      }
      else if (attr.name === '_readers' && attr.value) {
        try {
          schema.readers = JSON.parse(attr.value);
        } catch (e) {
          console.warn('[Schema] Erreur parsing _readers:', e);
        }
      }
      else if (attr.name === '_validators' && attr.value) {
        try {
          schema.validators = JSON.parse(attr.value);
        } catch (e) {
          console.warn('[Schema] Erreur parsing _validators:', e);
        }
      }
      // Sinon, c'est un attribut standard du schema
      else if (!attr.name.startsWith('_')) {
        schema.attributes.push(this.parseAttributeDefinition(attr));
      }
    }
    
    return schema;
  },
  
  /**
   * Parser une définition d'attribut
   */
  parseAttributeDefinition(attr) {
    return {
      name: attr.name,
      type: attr.type || attr.valueType || 'string',
      required: attr.required === true || attr.required === 'true',
      default: attr.default,
      label: attr.label || this.humanize(attr.name),
      description: attr.description,
      placeholder: attr.placeholder,
      
      // Contraintes
      min: attr.min,
      max: attr.max,
      minLength: attr.minLength,
      maxLength: attr.maxLength,
      pattern: attr.pattern,
      options: attr.options,
      multiple: attr.multiple,
      
      // Question associée pour le chat
      question: attr.question,
      
      // Section du formulaire
      section: attr.section || 'main'
    };
  },
  
  /**
   * Schema par défaut pour les types sans schema défini
   */
  getDefaultSchema(typeName) {
    return {
      name: typeName,
      attributes: [
        {
          name: 'name',
          type: 'string',
          required: true,
          label: 'Nom',
          description: `Nom du ${typeName}`,
          placeholder: `Mon ${typeName}`,
          section: 'identity',
          question: `Quel nom voulez-vous donner à ce ${typeName} ?`
        },
        {
          name: 'description',
          type: 'string',
          required: false,
          label: 'Description',
          description: 'Description optionnelle',
          multiline: true,
          section: 'identity',
          question: `Pouvez-vous décrire ce ${typeName} ?`
        }
      ],
      questions: [
        {
          id: 'intro',
          text: `Je vais vous aider à créer un ${typeName}. Commençons par le nom.`,
          field: 'name',
          type: 'open'
        }
      ],
      readers: {
        seed: 'defaultSeedReader',
        json: 'defaultJsonReader'
      },
      validators: []
    };
  },
  
  /**
   * Créer un nouveau schema
   */
  create(typeName, definition) {
    const schemaLineage = `Object:Schema:${typeName}`;
    
    // Créer l'objet schema
    createObjectType(schemaLineage, { source: 'schema-module' });
    
    // Ajouter les attributs de définition
    if (definition.attributes) {
      addAttribute(schemaLineage, {
        name: '_attributes',
        value: JSON.stringify(definition.attributes),
        type: 'json'
      });
    }
    
    if (definition.questions) {
      addAttribute(schemaLineage, {
        name: '_questions',
        value: JSON.stringify(definition.questions),
        type: 'json'
      });
    }
    
    if (definition.readers) {
      addAttribute(schemaLineage, {
        name: '_readers',
        value: JSON.stringify(definition.readers),
        type: 'json'
      });
    }
    
    // Vider le cache
    delete this.cache[typeName];
    
    return schemaLineage;
  },
  
  /**
   * Lister tous les schemas disponibles
   */
  list() {
    const allLineages = Store.getAllLineages ? Store.getAllLineages() : [];
    return allLineages
      .filter(l => l.startsWith('Object:Schema:'))
      .map(l => ({
        lineage: l,
        typeName: l.replace('Object:Schema:', ''),
        schema: this.get(l.replace('Object:Schema:', ''))
      }));
  },
  
  /**
   * Humanize un nom de champ
   */
  humanize(str) {
    return str
      .replace(/([A-Z])/g, ' $1')
      .replace(/_/g, ' ')
      .replace(/^\w/, c => c.toUpperCase())
      .trim();
  }
};

// ============================================================================
// Readers - Méthodes de lecture pour différents types de sources
// ============================================================================

const SchemaReaders = {
  
  /**
   * Reader par défaut pour les fichiers seed (.gev)
   */
  defaultSeedReader(content, schema) {
    const data = {};
    const lines = content.split('\n');
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('//') || trimmed.startsWith('#')) continue;
      
      // Format: .attributeName = value
      const match = trimmed.match(/^\.(\w+)\s*=\s*(.+)$/);
      if (match) {
        const [, name, value] = match;
        // Vérifier si l'attribut est dans le schema
        const attrDef = schema.attributes.find(a => a.name === name);
        if (attrDef) {
          data[name] = this.parseValue(value, attrDef.type);
        } else {
          // Attribut non défini dans le schema, on le garde quand même
          data[name] = value.trim();
        }
      }
    }
    
    return data;
  },
  
  /**
   * Reader pour JSON
   */
  defaultJsonReader(content, schema) {
    try {
      const json = JSON.parse(content);
      const data = {};
      
      for (const attr of schema.attributes) {
        if (json[attr.name] !== undefined) {
          data[attr.name] = json[attr.name];
        }
      }
      
      return data;
    } catch (e) {
      console.warn('[SchemaReaders] Erreur parsing JSON:', e);
      return {};
    }
  },
  
  /**
   * Reader pour notes libres (extraction par patterns)
   */
  noteReader(content, schema) {
    const data = {};
    const lower = content.toLowerCase();
    
    for (const attr of schema.attributes) {
      // Chercher des patterns comme "nom: xxx" ou "le nom est xxx"
      const patterns = [
        new RegExp(`${attr.name}\\s*[:=]\\s*["']?([^"'\\n]+)["']?`, 'i'),
        new RegExp(`(?:le|la|mon|ma)\\s+${attr.name}\\s+(?:est|:)\\s*["']?([^"'\\n]+)["']?`, 'i')
      ];
      
      for (const pattern of patterns) {
        const match = content.match(pattern);
        if (match) {
          data[attr.name] = match[1].trim();
          break;
        }
      }
    }
    
    return data;
  },
  
  /**
   * Reader pour cahier des charges (extraction structurée)
   */
  specReader(content, schema) {
    const data = {};
    const sections = content.split(/^#{1,3}\s+/m);
    
    // TODO: Implémentation plus sophistiquée avec NLP ou LLM
    // Pour l'instant, extraction basique
    
    for (const attr of schema.attributes) {
      const attrPattern = new RegExp(`${attr.label || attr.name}[:\\s]+([^\\n]+)`, 'i');
      const match = content.match(attrPattern);
      if (match) {
        data[attr.name] = match[1].trim();
      }
    }
    
    return data;
  },
  
  /**
   * Parser une valeur selon son type
   */
  parseValue(value, type) {
    const trimmed = value.trim().replace(/^["']|["']$/g, '');
    
    switch (type) {
      case 'number':
        return parseFloat(trimmed) || 0;
      case 'boolean':
        return ['true', '1', 'yes', 'oui'].includes(trimmed.toLowerCase());
      case 'array':
        return trimmed.split(',').map(s => s.trim());
      default:
        return trimmed;
    }
  },
  
  /**
   * Obtenir un reader par son nom
   */
  getReader(readerName) {
    return this[readerName] || this.defaultSeedReader;
  }
};

window.SchemaModule = SchemaModule;
window.SchemaReaders = SchemaReaders;
