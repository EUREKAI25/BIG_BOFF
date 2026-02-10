/**
 * EUREKAI Code Service - Node.js Server
 * Auto-generated from: traverse.js
 * Generated: 2025-12-13T07:20:19.065638
 */
const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// ============================================================================
// DEPENDENCIES MOCK/INJECT
// ============================================================================
// TODO: Implement or inject Store
const Store = {
    _data: new Map(),
    get(key) { return this._data.get(key); },
    set(key, value) { this._data.set(key, value); },
    getAllLineages() { return Array.from(this._data.keys()); },
    clear() { this._data.clear(); }
};

// ============================================================================
// ORIGINAL SOURCE CODE
// ============================================================================
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

// ============================================================================
// CALLBACK VARIANTS (for functions with callbacks)
// ============================================================================
/**
 * Variant: Collect all results from traverse
 * @returns {Array} All collected results
 */
function traverse_collect(lineage, options = {}) {
    const results = [];
    traverse(lineage, (obj, level) => { results.push({ obj, level }); }, options);
    return results;
}

/**
 * Variant: Find first match in traverse
 * @param {string} field - Field to match
 * @param {*} value - Value to match
 * @returns {*} First matching result or undefined
 */
function traverse_find(lineage, options = {}, field, value) {
    return traverse(lineage, (obj, level) => { if (obj[field] === value) return { obj, level }; }, options);
}

/**
 * Variant: Check if any match exists in traverse
 * @param {string} field - Field to check
 * @param {*} value - Value to check
 * @returns {boolean} True if match found
 */
function traverse_exists(lineage, options = {}, field, value) {
    return traverse_find(lineage, options = {}, field, value) !== undefined;
}


// ============================================================================
// API DISPATCHER
// ============================================================================
const exposed = {
    traverse,
    resolveSecondaryMethod,
    collectInheritedElements,
    getAncestors,
    getDescendants,
    traverse_collect,
    traverse_find,
    traverse_exists,
};

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', functions: Object.keys(exposed) });
});

// List available functions
app.get('/functions', (req, res) => {
    const info = {};
    for (const [name, fn] of Object.entries(exposed)) {
        info[name] = {
            params: fn.length,
            isVariant: name.includes('_collect') || name.includes('_find') || name.includes('_exists')
        };
    }
    res.json(info);
});

// Call a function
app.post('/call', async (req, res) => {
    const { fn, args = [] } = req.body;
    
    if (!fn) {
        return res.status(400).json({ ok: false, error: 'Missing function name' });
    }
    
    if (!exposed[fn]) {
        return res.status(404).json({ 
            ok: false, 
            error: `Function '${fn}' not found`,
            available: Object.keys(exposed)
        });
    }
    
    try {
        const result = await exposed[fn](...args);
        res.json({ ok: true, result });
    } catch (error) {
        res.status(500).json({ 
            ok: false, 
            error: error.message,
            stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
        });
    }
});

// Batch call multiple functions
app.post('/batch', async (req, res) => {
    const { calls = [] } = req.body;
    const results = [];
    
    for (const { fn, args = [] } of calls) {
        try {
            if (!exposed[fn]) {
                results.push({ ok: false, error: `Function '${fn}' not found` });
            } else {
                const result = await exposed[fn](...args);
                results.push({ ok: true, result });
            }
        } catch (error) {
            results.push({ ok: false, error: error.message });
        }
    }
    
    res.json({ ok: true, results });
});

// Store management endpoints (if Store dependency exists)
app.post('/store/set', (req, res) => {
    const { key, value } = req.body;
    Store.set(key, value);
    res.json({ ok: true });
});

app.get('/store/get/:key', (req, res) => {
    const value = Store.get(req.params.key);
    res.json({ ok: true, value });
});

app.get('/store/keys', (req, res) => {
    res.json({ ok: true, keys: Store.getAllLineages() });
});

app.post('/store/clear', (req, res) => {
    Store.clear();
    res.json({ ok: true });
});

app.post('/store/bulk', (req, res) => {
    const { items = [] } = req.body;
    for (const { key, value } of items) {
        Store.set(key, value);
    }
    res.json({ ok: true, count: items.length });
});

// ============================================================================
// SERVER START
// ============================================================================
const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
    console.log(`🚀 EUREKAI Server running on http://localhost:${PORT}`);
    console.log(`📚 Available functions: ${Object.keys(exposed).join(', ')}`);
});

module.exports = { app, exposed, Store, };