/* =============================================================================
   EUREKAI Cockpit — Traverse avec Early-Exit
   ============================================================================= */

/**
 * Traverse le lineage d'un objet du plus spécifique au plus générique (ou inverse)
 * Supporte l'early-exit : si callback retourne une valeur truthy, arrête la traversée
 * 
 * @param {string} lineage - Le lineage à traverser
 * @param {Function} callback - Fonction appelée pour chaque niveau (obj, lineage) => result
 * @param {Object} options - Options de traversée
 * @returns {*} - La première valeur truthy retournée par callback, ou undefined
 * 
 * @example
 * // Trouver le premier objet avec un attribut 'temperature'
 * const result = traverse('Object:Entity:Agent:AIAgent', (obj, lineage) => {
 *   const attr = obj.attributeBundle?.owned?.find(a => a.name === 'temperature');
 *   if (attr) return { attr, from: lineage };
 * });
 */
function traverse(lineage, callback, options = {}) {
  const {
    direction = 'up',      // 'up' (spécifique→générique) ou 'down' (générique→spécifique)
    includeRoot = true,    // Inclure Object dans la traversée
    skipSelf = false       // Sauter l'objet lui-même
  } = options;

  const segments = lineage.split(':');
  const levels = [];
  
  // Construire les niveaux de lineage
  for (let i = 1; i <= segments.length; i++) {
    levels.push(segments.slice(0, i).join(':'));
  }
  
  // Filtrer selon les options
  if (!includeRoot && levels[0] === 'Object') {
    levels.shift();
  }
  if (skipSelf && levels.length > 0) {
    levels.pop();
  }
  
  // Ordre selon direction
  const orderedLevels = direction === 'up' ? levels.reverse() : levels;
  
  // Traverser avec early-exit
  for (const level of orderedLevels) {
    const obj = Store.get(level);
    if (obj) {
      const result = callback(obj, level);
      // Early exit si valeur truthy (mais pas false explicitement qui continue)
      if (result !== undefined && result !== null && result !== false) {
        return result;
      }
    }
  }
  
  return undefined;
}

/**
 * Résout une méthode secondaire pour un lineage donné
 * Traverse du plus spécifique au plus générique et retourne la première trouvée
 * 
 * @param {string} lineage - Le lineage de l'objet
 * @param {string} centralMethod - La méthode centrale (Create, Read, etc.)
 * @returns {Object|undefined} - { method, from } ou undefined
 */
function resolveSecondaryMethod(lineage, centralMethod) {
  return traverse(lineage, (obj, level) => {
    // Chercher dans methodBundle.owned
    const methods = obj.methodBundle?.owned || [];
    for (const method of methods) {
      // Format: methodName.secondary = centralMethod
      if (method.name === `${centralMethod.toLowerCase()}.secondary` || 
          method.secondary === centralMethod) {
        return { method, from: level };
      }
    }
    
    // Chercher dans attributeBundle.owned (format .create.secondary = methodName)
    const attrs = obj.attributeBundle?.owned || [];
    for (const attr of attrs) {
      if (attr.name === `${centralMethod.toLowerCase()}.secondary`) {
        return { method: attr.value, from: level };
      }
    }
    
    return undefined; // Continuer la traversée
  });
}

/**
 * Collecte tous les éléments hérités pour un lineage
 * @param {string} lineage - Le lineage de l'objet
 * @param {string} bundleType - Le type de bundle ('attributeBundle', 'methodBundle', etc.)
 * @returns {Array} - Les éléments hérités avec leur source
 */
function collectInheritedElements(lineage, bundleType) {
  const collected = new Map();
  
  traverse(lineage, (obj, level) => {
    const bundle = obj[bundleType];
    if (bundle && bundle.owned) {
      for (const elem of bundle.owned) {
        const name = elem.name || JSON.stringify(elem);
        if (!collected.has(name)) {
          collected.set(name, {
            ...elem,
            source: 'inherited',
            from: level
          });
        }
      }
    }
    return undefined; // Continuer la traversée complète
  }, { skipSelf: true });
  
  return Array.from(collected.values());
}

/**
 * Trouve tous les ancêtres d'un lineage
 * @param {string} lineage - Le lineage
 * @returns {Array} - Liste des lineages ancêtres (du plus proche au plus éloigné)
 */
function getAncestors(lineage) {
  const ancestors = [];
  traverse(lineage, (obj, level) => {
    ancestors.push(level);
    return undefined; // Continuer
  }, { skipSelf: true });
  return ancestors;
}

/**
 * Trouve tous les descendants d'un lineage
 * @param {string} lineage - Le lineage
 * @returns {Array} - Liste des lineages descendants
 */
function getDescendants(lineage) {
  const descendants = [];
  const prefix = lineage + ':';
  
  for (const key of Store.getAllLineages()) {
    if (key.startsWith(prefix)) {
      descendants.push(key);
    }
  }
  
  return descendants;
}

// Global access
window.traverse = traverse;
window.resolveSecondaryMethod = resolveSecondaryMethod;
window.collectInheritedElements = collectInheritedElements;
window.getAncestors = getAncestors;
window.getDescendants = getDescendants;
