/* =============================================================================
   EUREKAI Cockpit — SuperTools (CRUDOE)
   ============================================================================= */

const SuperTools = {
  
  /**
   * SuperCreate - Création d'objets multi-sources
   */
  async create(params) {
    const { source = 'lineage', ...rest } = params;
    console.log(`[SuperCreate] source=${source}`, rest);
    
    const lineage = rest.lineage || rest.targetType || 'Object';
    const secondary = resolveSecondaryMethod(lineage, 'Create');
    if (secondary) {
      console.log(`  → Secondary: ${secondary.method?.name || secondary.method} from ${secondary.from}`);
    }
    
    switch (source) {
      case 'lineage': return this.createFromLineage(rest.lineage, rest.attributes);
      case 'schema': return this.createFromSchema(rest.schema, rest.name);
      case 'seed': return this.createFromSeed(rest.content);
      case 'instance': return this.createFromInstance(rest.sourceLineage, rest.name);
      case 'idea': return this.createFromIdea(rest.description, rest.targetType);
      default: throw new Error(`Unknown source: ${source}`);
    }
  },
  
  createFromLineage(lineage, attributes = {}) {
    const result = createLineageWithAncestors(lineage);
    if (!result) return null;
    const obj = Store.get(result.finalLineage);
    if (obj && attributes) {
      for (const [name, value] of Object.entries(attributes)) {
        addAttribute(result.finalLineage, { name, value, type: typeof value });
      }
    }
    return { success: true, lineage: result.finalLineage, created: result.created };
  },
  
  createFromSchema(schemaLineage, instanceName) {
    const schema = Store.get(schemaLineage);
    if (!schema) throw new Error(`Schema not found: ${schemaLineage}`);
    const parentLineage = getParentLineage(schemaLineage) || 'Object';
    const instanceLineage = `${parentLineage}:${instanceName}`;
    const attributes = {};
    for (const attr of (schema.attributeBundle?.owned || [])) {
      if (attr.default !== undefined) attributes[attr.name] = attr.default;
    }
    return this.createFromLineage(instanceLineage, attributes);
  },
  
  createFromSeed(seedContent) {
    const created = [];
    const lines = seedContent.split(/\r?\n/);
    let currentLineage = null;
    let currentAttrs = {};
    
    const saveCurrentObject = () => {
      if (currentLineage) {
        const result = this.createFromLineage(currentLineage, currentAttrs);
        if (result?.created) created.push(...result.created);
        currentAttrs = {};
      }
    };
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('//')) continue;
      
      if (trimmed.match(/^[A-Z][A-Za-z0-9_:]*:$/)) {
        saveCurrentObject();
        currentLineage = trimmed.slice(0, -1);
      } else if (trimmed.startsWith('.') && trimmed.includes('=')) {
        const match = trimmed.match(/^\.([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*)$/);
        if (match) {
          let value = match[2].trim();
          if (value === 'true') value = true;
          else if (value === 'false') value = false;
          else if (!isNaN(value) && value !== '') value = parseFloat(value);
          currentAttrs[match[1]] = value;
        }
      } else if (currentLineage && /\s+(IN|RELATED_TO|DEPENDS_ON)\s+/i.test(trimmed)) {
        const relMatch = trimmed.match(/^(\S+)\s+(IN|RELATED_TO|DEPENDS_ON|INHERITS_FROM)\s+(\S+)$/i);
        if (relMatch) {
          saveCurrentObject();
          const obj = Store.get(currentLineage);
          if (obj) addRelation(currentLineage, { type: relMatch[2].toLowerCase(), target: relMatch[3] });
        }
      }
    }
    saveCurrentObject();
    buildLineageIndex();
    console.log(`[SuperCreate:fromSeed] ${created.length} objects`);
    return { success: true, created };
  },
  
  createFromInstance(sourceLineage, newName) {
    const source = Store.get(sourceLineage);
    if (!source) throw new Error(`Source not found: ${sourceLineage}`);
    const segments = sourceLineage.split(':');
    segments[segments.length - 1] = newName;
    const newLineage = segments.join(':');
    const attributes = {};
    for (const attr of (source.attributeBundle?.owned || [])) attributes[attr.name] = attr.value;
    const result = this.createFromLineage(newLineage, attributes);
    if (!result) return null;
    const newObj = Store.get(newLineage);
    if (newObj) {
      newObj.methodBundle.owned = JSON.parse(JSON.stringify(source.methodBundle?.owned || []));
      newObj.relationBundle.owned = JSON.parse(JSON.stringify(source.relationBundle?.owned || []));
      newObj.tags = [...(source.tags || [])];
    }
    return result;
  },
  
  createFromIdea(description, targetType = 'Entity') {
    const words = description.split(/\s+/).slice(0, 3);
    const name = words.map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join('');
    return this.createFromLineage(`Object:${targetType}:${name}`, {
      description, generatedFrom: 'idea', createdAt: new Date().toISOString()
    });
  },
  
  /**
   * SuperRead - Lecture d'objets
   */
  read(query) {
    console.log(`[SuperRead] ${query}`);
    const parsed = this.parseQuery(query);
    let results = Object.values(Store.objectTypes);
    
    if (parsed.type && parsed.type !== '*') {
      results = results.filter(obj => {
        const name = getLineageName(obj.lineage);
        return name === parsed.type || obj.lineage.endsWith(`:${parsed.type}`);
      });
    }
    if (parsed.inList) {
      results = results.filter(obj => obj.lineage.includes(parsed.inList) || obj.tags?.includes(parsed.inList));
    }
    for (const cond of parsed.conditions) {
      results = results.filter(obj => {
        const attr = obj.attributeBundle?.owned?.find(a => a.name === cond.field);
        if (!attr) return false;
        switch (cond.op) {
          case '=': return attr.value == cond.value;
          case '!=': return attr.value != cond.value;
          case '>': return attr.value > cond.value;
          case '<': return attr.value < cond.value;
          default: return true;
        }
      });
    }
    if (parsed.limit) results = results.slice(0, parsed.limit);
    console.log(`  → ${results.length} / ${Store.count()} results`);
    return results;
  },
  
  /**
   * SuperUpdate
   */
  update(lineage, updates) {
    const obj = Store.get(lineage);
    if (!obj) throw new Error(`Not found: ${lineage}`);
    console.log(`[SuperUpdate] ${lineage}`, updates);
    for (const [key, value] of Object.entries(updates)) {
      addAttribute(lineage, { name: key, value, type: typeof value });
    }
    obj.updatedAt = new Date().toISOString();
    return obj;
  },
  
  /**
   * SuperDelete
   */
  delete(lineage, cascade = false) {
    console.log(`[SuperDelete] ${lineage} (cascade=${cascade})`);
    return deleteObjectType(lineage, cascade);
  },
  
  /**
   * SuperOrchestrate
   */
  async orchestrate(scenarioLineage, context = {}) {
    const scenario = Store.get(scenarioLineage);
    if (!scenario) throw new Error(`Scenario not found: ${scenarioLineage}`);
    console.log(`[SuperOrchestrate] === ${getLineageName(scenarioLineage)} ===`);
    const steps = this.findSteps(scenarioLineage);
    console.log(`  Steps: ${steps.length}`);
    const startTime = Date.now();
    for (const step of steps) {
      const stepName = getLineageName(step.lineage);
      console.log(`  Step: ${stepName}`);
      const result = await this.executeStep(step, context);
      if (result) context = { ...context, ...result };
    }
    const duration = Date.now() - startTime;
    console.log(`  === Completed: ${duration}ms ===`);
    return { scenario: scenarioLineage, duration, steps: steps.length };
  },
  
  /**
   * SuperEngage
   */
  engage(agentLineage, task) {
    const agent = Store.get(agentLineage);
    if (!agent) throw new Error(`Agent not found: ${agentLineage}`);
    console.log(`[SuperEngage] ${agentLineage}`, task);
    return { agent: agentLineage, task, status: 'engaged', timestamp: new Date().toISOString() };
  },
  
  // Helpers
  parseQuery(query) {
    const parsed = { type: '*', conditions: [], inList: null, limit: null };
    const inMatch = query.match(/^(\*|\w+)\s+IN\s+(\w+)$/i);
    if (inMatch) { parsed.type = inMatch[1]; parsed.inList = inMatch[2]; return parsed; }
    const whereMatch = query.match(/^(\*|\w+)(?:\s+WHERE\s+(.+))?(?:\s+LIMIT\s+(\d+))?$/i);
    if (whereMatch) {
      parsed.type = whereMatch[1];
      if (whereMatch[2]) {
        for (const part of whereMatch[2].split(/\s+AND\s+/i)) {
          const m = part.match(/(\w+)\s*(=|!=|>|<)\s*(.+)/);
          if (m) parsed.conditions.push({ field: m[1], op: m[2], value: m[3].replace(/^['"]|['"]$/g, '') });
        }
      }
      if (whereMatch[3]) parsed.limit = parseInt(whereMatch[3]);
    }
    return parsed;
  },
  
  findSteps(scenarioLineage) {
    const steps = [];
    for (const name of ['GetStep', 'ExecuteStep', 'ValidateStep', 'RenderStep']) {
      const step = Store.get(`${scenarioLineage}:${name}`);
      if (step) steps.push(step);
    }
    return steps;
  },
  
  async executeStep(step, context) {
    const stepType = step.attributeBundle?.owned?.find(a => a.name === 'type')?.value || getLineageName(step.lineage);
    switch (stepType) {
      case 'GetStep':
        const pattern = step.attributeBundle?.owned?.find(a => a.name === 'pattern')?.value || '*.gev';
        const files = Object.keys(Store.fileStore).filter(f => pattern === '*.gev' ? f.endsWith('.gev') : f.includes(pattern.replace('*', '')));
        return { files };
      case 'ExecuteStep':
        if (context.files?.length) for (const f of context.files) if (Store.fileStore[f]) this.createFromSeed(Store.fileStore[f]);
        return { parsed: true };
      case 'ValidateStep': return { valid: true };
      case 'RenderStep': return { output: JSON.stringify({ status: 'complete', objects: Store.count() }) };
      default: return {};
    }
  }
};

window.SuperTools = SuperTools;
