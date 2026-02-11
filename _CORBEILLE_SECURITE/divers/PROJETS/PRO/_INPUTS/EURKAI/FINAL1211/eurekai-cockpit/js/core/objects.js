/* =============================================================================
   EUREKAI Cockpit — Object Management
   ============================================================================= */

/**
 * Create a new ObjectType
 * @param {string} lineage - The lineage
 * @param {Object} options - Creation options
 * @returns {Object} - The created object
 */
function createObjectType(lineage, options = {}) {
  if (!validateLineage(lineage)) {
    throw new Error(`Invalid lineage: ${lineage}`);
  }
  
  // Check if exists
  if (Store.get(lineage)) {
    return Store.get(lineage);
  }
  
  const name = getLineageName(lineage);
  const parentLineage = getParentLineage(lineage);
  
  // Collect inherited elements if parent exists
  const inheritedAttrs = parentLineage ? collectInheritedElements(parentLineage, 'attributeBundle') : [];
  const inheritedMethods = parentLineage ? collectInheritedElements(parentLineage, 'methodBundle') : [];
  const inheritedRules = parentLineage ? collectInheritedElements(parentLineage, 'ruleBundle') : [];
  const inheritedRelations = parentLineage ? collectInheritedElements(parentLineage, 'relationBundle') : [];
  
  const obj = {
    lineage,
    name,
    parent: parentLineage,
    createdAt: new Date().toISOString(),
    source: options.source || 'manual',
    
    // Bundles
    attributeBundle: {
      owned: [],
      inherited: inheritedAttrs,
      injected: []
    },
    methodBundle: {
      owned: [],
      inherited: inheritedMethods,
      injected: []
    },
    ruleBundle: {
      owned: [],
      inherited: inheritedRules,
      injected: []
    },
    relationBundle: {
      owned: [],
      inherited: inheritedRelations,
      injected: []
    },
    
    // Tags
    tags: options.tags || [],
    
    // Metadata
    isIntermediate: options.isIntermediate || false
  };
  
  // Store the object
  Store.set(lineage, obj);
  
  return obj;
}

/**
 * Create lineage with all ancestors (silent mode - no prompts)
 * @param {string} lineage - The full lineage
 * @returns {Object} { created: [], finalLineage }
 */
function createLineageWithAncestors(lineage) {
  if (!validateLineage(lineage)) return null;
  
  // Rule: Object is parent of all
  const segments = parseLineage(lineage);
  if (segments[0] !== 'Object') {
    const rootExists = Store.get(segments[0]);
    if (!rootExists) {
      lineage = 'Object:' + lineage;
    }
  }
  
  // Check if already exists
  if (Store.get(lineage)) {
    return { created: [], finalLineage: lineage };
  }
  
  const finalSegments = parseLineage(lineage);
  const created = [];
  let currentPath = [];
  
  // Create all levels
  for (let i = 0; i < finalSegments.length; i++) {
    currentPath.push(finalSegments[i]);
    const path = currentPath.join(':');
    
    if (!Store.get(path)) {
      const isIntermediate = i < finalSegments.length - 1;
      const obj = createObjectType(path, { isIntermediate, source: 'lineage' });
      created.push(obj);
    }
  }
  
  buildLineageIndex();
  return { created, finalLineage: lineage };
}

/**
 * Process enhanced lineage - create object with attributes and relations
 * @param {string} input - Enhanced lineage string
 * @returns {Object} { created, finalLineage }
 */
async function processEnhancedLineage(input) {
  const parsed = parseEnhancedLineage(input);
  
  if (!parsed.valid) {
    showToast('Syntaxe invalide', 'error');
    return null;
  }
  
  // Create the main lineage
  const result = createLineageWithAncestors(parsed.lineage);
  if (!result) return null;
  
  const finalLineage = result.finalLineage;
  const mainObj = Store.get(finalLineage);
  if (!mainObj) return result;
  
  // Add attributes
  for (const attr of parsed.attributes) {
    const exists = mainObj.attributeBundle.owned.find(a => a.name === attr.name);
    if (!exists) {
      mainObj.attributeBundle.owned.push({
        name: attr.name,
        type: attr.type,
        value: attr.value,
        source: 'owned'
      });
    } else if (attr.value !== undefined && exists.value === undefined) {
      exists.value = attr.value;
    }
  }
  
  // Add relation if present
  if (parsed.relation) {
    // Ensure target exists
    const targetResult = createLineageWithAncestors(parsed.relation.target);
    const targetLineage = targetResult?.finalLineage || parsed.relation.target;
    
    if (Store.get(targetLineage)) {
      const existingRel = mainObj.relationBundle.owned.find(
        r => r.type === parsed.relation.type && r.target === targetLineage
      );
      if (!existingRel) {
        mainObj.relationBundle.owned.push({
          type: parsed.relation.type,
          target: targetLineage,
          source: 'owned'
        });
      }
    }
  }
  
  Store.emit('change', { type: 'create', lineage: finalLineage });
  return result;
}

/**
 * Delete an object and optionally its descendants
 * @param {string} lineage - The lineage to delete
 * @param {boolean} cascade - Delete descendants too
 * @returns {number} - Number of deleted objects
 */
function deleteObjectType(lineage, cascade = false) {
  if (!Store.get(lineage)) return 0;
  
  let deleted = 0;
  
  // Delete descendants first if cascade
  if (cascade) {
    const descendants = getDescendants(lineage);
    for (const desc of descendants.reverse()) {
      if (Store.delete(desc)) deleted++;
    }
  }
  
  // Delete the object
  if (Store.delete(lineage)) deleted++;
  
  buildLineageIndex();
  return deleted;
}

/**
 * Add attribute to object
 * @param {string} lineage - Object lineage
 * @param {Object} attr - Attribute definition { name, type, value }
 */
function addAttribute(lineage, attr) {
  const obj = Store.get(lineage);
  if (!obj) return false;
  
  const exists = obj.attributeBundle.owned.find(a => a.name === attr.name);
  if (exists) {
    // Update existing
    Object.assign(exists, attr);
  } else {
    obj.attributeBundle.owned.push({
      ...attr,
      source: 'owned'
    });
  }
  
  Store.emit('change', { type: 'update', lineage });
  return true;
}

/**
 * Add method to object
 * @param {string} lineage - Object lineage
 * @param {Object} method - Method definition { name, params, returns }
 */
function addMethod(lineage, method) {
  const obj = Store.get(lineage);
  if (!obj) return false;
  
  const exists = obj.methodBundle.owned.find(m => m.name === method.name);
  if (!exists) {
    obj.methodBundle.owned.push({
      ...method,
      source: 'owned'
    });
  }
  
  Store.emit('change', { type: 'update', lineage });
  return true;
}

/**
 * Add relation to object
 * @param {string} lineage - Object lineage
 * @param {Object} relation - Relation definition { type, target }
 */
function addRelation(lineage, relation) {
  const obj = Store.get(lineage);
  if (!obj) return false;
  
  // Ensure target exists
  if (!Store.get(relation.target)) {
    createLineageWithAncestors(relation.target);
  }
  
  const exists = obj.relationBundle.owned.find(
    r => r.type === relation.type && r.target === relation.target
  );
  
  if (!exists) {
    obj.relationBundle.owned.push({
      ...relation,
      source: 'owned'
    });
  }
  
  Store.emit('change', { type: 'update', lineage });
  return true;
}

/**
 * Resolve all elements for an object (owned overrides inherited)
 * @param {Object} obj - The object
 * @returns {Object} - Resolved bundles
 */
function resolveElements(obj) {
  const resolved = {
    attributes: [],
    methods: [],
    relations: [],
    rules: []
  };
  
  const bundles = [
    { key: 'attributes', bundle: 'attributeBundle' },
    { key: 'methods', bundle: 'methodBundle' },
    { key: 'relations', bundle: 'relationBundle' },
    { key: 'rules', bundle: 'ruleBundle' }
  ];
  
  for (const { key, bundle } of bundles) {
    const map = new Map();
    
    // Inherited first (will be overridden)
    for (const elem of (obj[bundle]?.inherited || [])) {
      const name = elem.name || elem.type || JSON.stringify(elem);
      map.set(name, { ...elem, source: 'inherited' });
    }
    
    // Then injected
    for (const elem of (obj[bundle]?.injected || [])) {
      const name = elem.name || elem.type || JSON.stringify(elem);
      map.set(name, { ...elem, source: 'injected' });
    }
    
    // Finally owned (highest priority)
    for (const elem of (obj[bundle]?.owned || [])) {
      const name = elem.name || elem.type || JSON.stringify(elem);
      map.set(name, { ...elem, source: 'owned' });
    }
    
    resolved[key] = Array.from(map.values());
  }
  
  return resolved;
}

// Global access
window.createObjectType = createObjectType;
window.createLineageWithAncestors = createLineageWithAncestors;
window.processEnhancedLineage = processEnhancedLineage;
window.deleteObjectType = deleteObjectType;
window.addAttribute = addAttribute;
window.addMethod = addMethod;
window.addRelation = addRelation;
window.resolveElements = resolveElements;
