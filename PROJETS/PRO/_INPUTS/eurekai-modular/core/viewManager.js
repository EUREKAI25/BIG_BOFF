/* =============================================================================
   EUREKAI — View Manager
   Gère les 3 vues unifiées (chat, form, recap) sur les mêmes données
   ============================================================================= */

const ViewManager = {
  
  // État partagé entre les vues
  state: {
    lineage: null,
    formData: null,
    conversation: [],
    currentSection: 0,
    autonomyLevel: 0.5, // 0 = manuel, 1 = auto
    activeView: 'form', // 'chat' | 'form' | 'recap'
    sources: {}
  },
  
  // Callbacks des vues
  views: {
    chat: null,
    form: null,
    recap: null
  },
  
  /**
   * Initialiser une session de création
   */
  async init(lineage, options = {}) {
    this.state.lineage = lineage;
    this.state.sources = options.sources || {};
    this.state.conversation = [];
    this.state.currentSection = 0;
    
    // Générer le formulaire
    this.state.formData = FormBuilder.generate(lineage, {
      sources: this.state.sources
    });
    
    // Ajouter message initial à la conversation
    this._addMessage('agent', `Je vais vous aider à créer un objet de type "${getLineageName(lineage)}".`);
    
    // Si des champs sont pré-remplis, le mentionner
    const prefilled = this._countPrefilled();
    if (prefilled > 0) {
      this._addMessage('agent', `J'ai pré-rempli ${prefilled} champ(s) depuis les sources disponibles.`);
    }
    
    // Log
    HistoryLogger.log({
      type: 'creation_init',
      lineage,
      sections: this.state.formData.sections.length,
      prefilled
    });
    
    // Rafraîchir les vues
    this._refreshViews();
    
    return this.state;
  },
  
  /**
   * Enregistrer une vue
   */
  registerView(name, callbacks) {
    this.views[name] = callbacks;
  },
  
  /**
   * Changer de vue active
   */
  switchView(viewName) {
    if (!['chat', 'form', 'recap'].includes(viewName)) return;
    
    this.state.activeView = viewName;
    this._refreshViews();
    
    HistoryLogger.log({
      type: 'view_switch',
      view: viewName,
      lineage: this.state.lineage
    });
  },
  
  /**
   * Définir le niveau d'autonomie
   */
  setAutonomy(level) {
    this.state.autonomyLevel = Math.max(0, Math.min(1, level));
    
    if (level > 0.7) {
      this._addMessage('agent', "Mode automatique activé. Je vais compléter les champs avec les valeurs par défaut.");
      this._autoFillDefaults();
    }
  },
  
  /**
   * Traiter un message utilisateur (chat)
   */
  async processUserMessage(message) {
    this._addMessage('user', message);
    
    // Analyser le message pour extraire des valeurs
    const extracted = await this._extractFromMessage(message);
    
    if (extracted.length > 0) {
      for (const { field, value } of extracted) {
        this._setFieldValue(field, value);
        this._addMessage('agent', `J'ai noté: ${field} = "${value}"`);
      }
    }
    
    // Répondre selon le contexte
    const response = this._generateResponse(message, extracted);
    this._addMessage('agent', response);
    
    this._refreshViews();
  },
  
  /**
   * Mettre à jour un champ (form)
   */
  updateField(fieldName, value) {
    this._setFieldValue(fieldName, value);
    
    // Ajouter à la conversation si significatif
    if (this.state.autonomyLevel < 0.5) {
      this._addMessage('system', `${fieldName} = "${value}"`);
    }
    
    // Valider le champ
    const field = this._findField(fieldName);
    if (field) {
      FormBuilder.validateField(field);
    }
    
    this._refreshViews();
  },
  
  /**
   * Passer à la section suivante
   */
  nextSection() {
    const sections = this.state.formData.sections;
    const currentSection = sections[this.state.currentSection];
    
    // Valider la section actuelle
    const validation = FormBuilder.validateSection(currentSection);
    
    if (!validation.valid) {
      this._addMessage('agent', `Certains champs requis ne sont pas remplis dans "${currentSection.title}".`);
      this._refreshViews();
      return { success: false, errors: validation.errors };
    }
    
    // Log section complète
    const values = {};
    for (const field of currentSection.fields) {
      if (field.value !== null && field.value !== undefined) {
        values[field.name] = field.value;
      }
    }
    HistoryLogger.logSectionComplete(this.state.lineage, currentSection.name, values);
    
    // Avancer
    if (this.state.currentSection < sections.length - 1) {
      this.state.currentSection++;
      const nextSection = sections[this.state.currentSection];
      this._addMessage('agent', `Passons à la section "${nextSection.title}".`);
    }
    
    this._refreshViews();
    return { success: true };
  },
  
  /**
   * Revenir à la section précédente
   */
  previousSection() {
    if (this.state.currentSection > 0) {
      this.state.currentSection--;
      this._refreshViews();
    }
  },
  
  /**
   * Aller à une section spécifique
   */
  goToSection(index) {
    if (index >= 0 && index < this.state.formData.sections.length) {
      this.state.currentSection = index;
      this._refreshViews();
    }
  },
  
  /**
   * Finaliser et créer l'objet
   */
  async finalize() {
    // Valider tout
    const validation = FormBuilder.validateAll(this.state.formData);
    
    if (!validation.valid) {
      this._addMessage('agent', "Il reste des champs invalides ou manquants.");
      return { success: false, validation };
    }
    
    // Vérifier les APIs
    const canValidate = GetCreate.canValidate(this.state.lineage);
    if (!canValidate.valid) {
      this._addMessage('agent', canValidate.reason);
      return { success: false, reason: canValidate.reason };
    }
    
    // Extraire les valeurs
    const values = FormBuilder.extractValues(this.state.formData);
    
    // Créer l'objet
    const result = await GetCreate.execute(this.state.lineage, {
      source: 'form',
      attributes: values
    });
    
    if (result.success) {
      // Appliquer les valeurs du formulaire
      for (const [name, value] of Object.entries(values)) {
        addAttribute(this.state.lineage, { name, value, type: typeof value });
      }
      
      this._addMessage('agent', `L'objet "${getLineageName(this.state.lineage)}" a été créé avec succès.`);
      
      HistoryLogger.log({
        type: 'creation_complete',
        lineage: this.state.lineage,
        fieldCount: Object.keys(values).length
      });
    } else {
      this._addMessage('agent', `Erreur lors de la création: ${result.error || result.reason}`);
    }
    
    this._refreshViews();
    return result;
  },
  
  /**
   * Obtenir le résumé pour la vue recap
   */
  getRecap() {
    const values = FormBuilder.extractValues(this.state.formData);
    const sections = [];
    
    for (const section of this.state.formData.sections) {
      if (section.isPreview) continue;
      
      const fields = section.fields
        .filter(f => f.value !== null && f.value !== undefined)
        .map(f => ({
          name: f.name,
          label: f.label,
          value: f.value,
          source: f.prefillSource
        }));
      
      if (fields.length > 0) {
        sections.push({
          title: section.title,
          fields
        });
      }
    }
    
    return {
      lineage: this.state.lineage,
      name: this.state.formData.name,
      sections,
      totalFields: Object.keys(values).length,
      validation: FormBuilder.validateAll(this.state.formData)
    };
  },
  
  // ============ Méthodes privées ============
  
  _addMessage(role, content) {
    this.state.conversation.push({
      role, // 'user' | 'agent' | 'system'
      content,
      timestamp: new Date().toISOString()
    });
  },
  
  _findField(name) {
    for (const section of this.state.formData.sections) {
      const field = section.fields.find(f => f.name === name);
      if (field) return field;
    }
    return null;
  },
  
  _setFieldValue(name, value) {
    const field = this._findField(name);
    if (field) {
      field.value = value;
      field.touched = true;
    }
  },
  
  _countPrefilled() {
    let count = 0;
    for (const section of this.state.formData.sections) {
      for (const field of section.fields) {
        if (field.prefillSource && field.value !== null) {
          count++;
        }
      }
    }
    return count;
  },
  
  _autoFillDefaults() {
    for (const section of this.state.formData.sections) {
      for (const field of section.fields) {
        if (field.value === null && field.default !== undefined) {
          field.value = field.default;
          field.prefillSource = 'auto';
        }
      }
    }
  },
  
  async _extractFromMessage(message) {
    // Simple extraction basée sur patterns
    // TODO: Améliorer avec NLP / LLM
    const extracted = [];
    const lower = message.toLowerCase();
    
    for (const section of this.state.formData.sections) {
      for (const field of section.fields) {
        // Pattern: "nom est X" ou "nom: X" ou "nom = X"
        const patterns = [
          new RegExp(`${field.name}\\s*(?:est|:|=)\\s*[""']?([^""']+)[""']?`, 'i'),
          new RegExp(`(?:mon|ma|le|la)\\s+${field.name}\\s+(?:est|:)\\s*[""']?([^""']+)[""']?`, 'i')
        ];
        
        for (const pattern of patterns) {
          const match = message.match(pattern);
          if (match) {
            extracted.push({ field: field.name, value: match[1].trim() });
            break;
          }
        }
      }
    }
    
    return extracted;
  },
  
  _generateResponse(message, extracted) {
    const currentSection = this.state.formData.sections[this.state.currentSection];
    
    if (extracted.length > 0) {
      // Des valeurs ont été extraites
      const remaining = currentSection.fields.filter(f => 
        f.required && (f.value === null || f.value === undefined)
      );
      
      if (remaining.length > 0) {
        return `Très bien. Il me faut encore: ${remaining.map(f => f.label).join(', ')}.`;
      } else {
        return "Parfait, cette section est complète. Voulez-vous passer à la suivante ?";
      }
    }
    
    // Pas de valeur extraite → poser une question
    const emptyRequired = currentSection.fields.find(f => 
      f.required && (f.value === null || f.value === undefined)
    );
    
    if (emptyRequired) {
      return `Quelle valeur souhaitez-vous pour "${emptyRequired.label}" ?`;
    }
    
    return "Je suis prêt à continuer. Que souhaitez-vous faire ?";
  },
  
  _refreshViews() {
    for (const [name, callbacks] of Object.entries(this.views)) {
      if (callbacks && callbacks.refresh) {
        callbacks.refresh(this.state);
      }
    }
  }
};

window.ViewManager = ViewManager;
