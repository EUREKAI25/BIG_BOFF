/**
 * Test JS natif - à exécuter avec Node.js
 * Compare les résultats avec la version API Python
 */

// === MOCK STORE (identique au serveur) ===
const Store = {
    _data: new Map(),
    get(key) { return this._data.get(key); },
    set(key, value) { this._data.set(key, value); },
    getAllLineages() { return Array.from(this._data.keys()); },
    clear() { this._data.clear(); }
};

// === CODE ORIGINAL traverse.js ===
function traverse(lineage, callback, options = {}) {
  const {
    direction = 'up',
    includeRoot = true,
    skipSelf = false
  } = options;

  const segments = lineage.split(':');
  const levels = [];
  
  for (let i = 1; i <= segments.length; i++) {
    levels.push(segments.slice(0, i).join(':'));
  }
  
  if (!includeRoot && levels[0] === 'Object') {
    levels.shift();
  }
  if (skipSelf && levels.length > 0) {
    levels.pop();
  }
  
  const orderedLevels = direction === 'up' ? levels.reverse() : levels;
  
  for (const level of orderedLevels) {
    const obj = Store.get(level);
    if (obj) {
      const result = callback(obj, level);
      if (result !== undefined && result !== null && result !== false) {
        return result;
      }
    }
  }
  
  return undefined;
}

function getAncestors(lineage) {
  const ancestors = [];
  traverse(lineage, (obj, level) => {
    ancestors.push(level);
    return undefined;
  }, { skipSelf: true });
  return ancestors;
}

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

function traverse_collect(lineage, options = {}) {
    const results = [];
    traverse(lineage, (obj, level) => { results.push({ obj, level }); }, options);
    return results;
}

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
    return undefined;
  }, { skipSelf: true });
  
  return Array.from(collected.values());
}

// === DONNÉES DE TEST ===
console.log("=== CHARGEMENT DES DONNÉES ===\n");

Store.set('Object', {
    name: 'Object',
    attributeBundle: {
        owned: [
            { name: 'id', type: 'string' },
            { name: 'createdAt', type: 'date' }
        ]
    }
});

Store.set('Object:Entity', {
    name: 'Entity',
    attributeBundle: {
        owned: [
            { name: 'label', type: 'string' },
            { name: 'description', type: 'text' }
        ]
    }
});

Store.set('Object:Entity:Agent', {
    name: 'Agent',
    attributeBundle: {
        owned: [
            { name: 'status', type: 'enum' },
            { name: 'capabilities', type: 'array' }
        ]
    }
});

Store.set('Object:Entity:Agent:AIAgent', {
    name: 'AIAgent',
    attributeBundle: {
        owned: [
            { name: 'model', type: 'string' },
            { name: 'temperature', type: 'number' }
        ]
    }
});

Store.set('Object:Entity:Agent:HumanAgent', {
    name: 'HumanAgent',
    attributeBundle: {
        owned: [
            { name: 'email', type: 'string' },
            { name: 'role', type: 'string' }
        ]
    }
});

console.log("Store keys:", Store.getAllLineages());
console.log("");

// === TESTS ===
console.log("=== TEST 1: getAncestors ===");
const ancestors = getAncestors('Object:Entity:Agent:AIAgent');
console.log("getAncestors('Object:Entity:Agent:AIAgent'):");
console.log(JSON.stringify(ancestors, null, 2));
console.log("");

console.log("=== TEST 2: getDescendants ===");
const descendants = getDescendants('Object:Entity:Agent');
console.log("getDescendants('Object:Entity:Agent'):");
console.log(JSON.stringify(descendants, null, 2));
console.log("");

console.log("=== TEST 3: traverse_collect (direction: up) ===");
const collectUp = traverse_collect('Object:Entity:Agent:AIAgent', { direction: 'up' });
console.log("traverse_collect('Object:Entity:Agent:AIAgent', {direction: 'up'}):");
console.log(JSON.stringify(collectUp, null, 2));
console.log("");

console.log("=== TEST 4: traverse_collect (direction: down) ===");
const collectDown = traverse_collect('Object:Entity:Agent:AIAgent', { direction: 'down' });
console.log("traverse_collect('Object:Entity:Agent:AIAgent', {direction: 'down'}):");
console.log(JSON.stringify(collectDown, null, 2));
console.log("");

console.log("=== TEST 5: collectInheritedElements ===");
const inherited = collectInheritedElements('Object:Entity:Agent:AIAgent', 'attributeBundle');
console.log("collectInheritedElements('Object:Entity:Agent:AIAgent', 'attributeBundle'):");
console.log(JSON.stringify(inherited, null, 2));
console.log("");

console.log("=== TEST 6: traverse avec skipSelf ===");
const skipSelf = traverse_collect('Object:Entity:Agent', { skipSelf: true });
console.log("traverse_collect('Object:Entity:Agent', {skipSelf: true}):");
console.log(JSON.stringify(skipSelf, null, 2));
console.log("");

console.log("=== TEST 7: traverse sans includeRoot ===");
const noRoot = traverse_collect('Object:Entity:Agent', { includeRoot: false });
console.log("traverse_collect('Object:Entity:Agent', {includeRoot: false}):");
console.log(JSON.stringify(noRoot, null, 2));

// === EXPORT POUR COMPARAISON ===
const results = {
    test1_ancestors: ancestors,
    test2_descendants: descendants,
    test3_collect_up: collectUp,
    test4_collect_down: collectDown,
    test5_inherited: inherited,
    test6_skipSelf: skipSelf,
    test7_noRoot: noRoot
};

// Sauvegarder pour comparaison
const fs = require('fs');
fs.writeFileSync('test_results_js.json', JSON.stringify(results, null, 2));
console.log("\n✅ Résultats sauvegardés dans test_results_js.json");
