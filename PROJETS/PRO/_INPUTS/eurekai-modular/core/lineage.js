/* =============================================================================
   EUREKAI Cockpit — Lineage Utilities
   ============================================================================= */

/**
 * Valide un lineage
 * @param {string} lineage - Le lineage à valider
 * @returns {boolean}
 */
function validateLineage(lineage) {
  return CONFIG.lineageRegex.test(lineage);
}

/**
 * Parse un lineage en segments
 * @param {string} lineage - Le lineage
 * @returns {Array|null} - Les segments ou null si invalide
 */
function parseLineage(lineage) {
  if (!validateLineage(lineage)) return null;
  return lineage.split(':');
}

/**
 * Obtient le nom (dernier segment) d'un lineage
 * @param {string} lineage - Le lineage
 * @returns {string}
 */
function getLineageName(lineage) {
  const segments = lineage.split(':');
  return segments[segments.length - 1];
}

/**
 * Obtient le parent d'un lineage
 * @param {string} lineage - Le lineage
 * @returns {string|null} - Le lineage parent ou null si c'est une racine
 */
function getParentLineage(lineage) {
  const segments = lineage.split(':');
  if (segments.length <= 1) return null;
  return segments.slice(0, -1).join(':');
}

/**
 * Parse une syntaxe enhanced lineage
 * Supporte:
 * - Simple: "Object:Entity"
 * - Avec attributs: "Object:Entity.name:string.value=42"
 * - Avec relation: "Object:Entity depends_on Object:Target"
 * - Combiné: "Object:Entity.attr=val depends_on Object:Target"
 * 
 * @param {string} input - L'input à parser
 * @returns {Object} { lineage, attributes: [], relation: { type, target }, valid }
 */
function parseEnhancedLineage(input) {
  const result = {
    lineage: null,
    attributes: [],
    relation: null,
    valid: false
  };
  
  if (!input || typeof input !== 'string') return result;
  
  let remaining = input.trim();
  
  // Check for relation pattern
  let relationMatch = null;
  for (const relType of CONFIG.relationTypes) {
    const regex = new RegExp(`\\s+${relType}\\s+(.+)$`, 'i');
    const match = remaining.match(regex);
    if (match) {
      const actualType = CONFIG.relationAliases[relType] || relType;
      relationMatch = { type: actualType, target: match[1].trim(), originalType: relType };
      remaining = remaining.replace(regex, '');
      break;
    }
  }
  
  // Find where attributes start (first .lowercase)
  const dotIndex = remaining.search(/\.[a-z]/i);
  let lineagePart, attrPart;
  
  if (dotIndex > 0) {
    lineagePart = remaining.substring(0, dotIndex);
    attrPart = remaining.substring(dotIndex);
  } else {
    lineagePart = remaining;
    attrPart = '';
  }
  
  // Validate lineage
  if (!validateLineage(lineagePart)) {
    return result;
  }
  
  result.lineage = lineagePart;
  
  // Parse attributes
  if (attrPart) {
    const attrRegex = /\.([a-zA-Z_][a-zA-Z0-9_]*)(?::([a-zA-Z]+))?(?:=([^.]+))?/g;
    let match;
    while ((match = attrRegex.exec(attrPart)) !== null) {
      result.attributes.push({
        name: match[1],
        type: match[2] || 'string',
        value: match[3]?.trim()
      });
    }
  }
  
  // Validate relation target
  if (relationMatch) {
    if (validateLineage(relationMatch.target)) {
      result.relation = relationMatch;
    } else {
      return result; // Invalid relation target
    }
  }
  
  result.valid = true;
  return result;
}

/**
 * Build lineage index for fast tree rendering
 */
function buildLineageIndex() {
  const index = {};
  const roots = new Set();
  
  for (const lineage of Store.getAllLineages()) {
    const segments = lineage.split(':');
    
    // Track roots
    roots.add(segments[0]);
    
    // Build parent-child relationships
    if (segments.length > 1) {
      const parentLineage = segments.slice(0, -1).join(':');
      if (!index[parentLineage]) {
        index[parentLineage] = [];
      }
      if (!index[parentLineage].includes(lineage)) {
        index[parentLineage].push(lineage);
      }
    }
  }
  
  Store.lineageIndex = {
    index,
    roots: Array.from(roots).sort()
  };
  
  return Store.lineageIndex;
}

/**
 * Get children of a lineage from index
 * @param {string} lineage - The parent lineage
 * @returns {Array} - Children lineages
 */
function getChildren(lineage) {
  return Store.lineageIndex.index[lineage] || [];
}

// Global access
window.validateLineage = validateLineage;
window.parseLineage = parseLineage;
window.getLineageName = getLineageName;
window.getParentLineage = getParentLineage;
window.parseEnhancedLineage = parseEnhancedLineage;
window.buildLineageIndex = buildLineageIndex;
window.getChildren = getChildren;
