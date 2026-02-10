/* =============================================================================
   EUREKAI Cockpit — Configuration
   ============================================================================= */

const CONFIG = {
  version: 'v46',
  lineageRegex: /^([A-Z][A-Za-z0-9_]*)(:[A-Z][A-Za-z0-9_]*)*$/,
  
  // Relation types and aliases
  relationTypes: ['depends_on', 'related_to', 'inherits_from', 'scope_of', 'type_of', 'in'],
  relationAliases: {
    'scope_of': 'related_to',
    'type_of': 'inherits_from'
  },
  
  // Central methods (CRUDOE)
  centralMethods: ['Create', 'Read', 'Update', 'Delete', 'Orchestrate', 'Engage'],
  
  // Default settings
  defaults: {
    maxDepth: 5,
    maxSearchResults: 50
  }
};

// Freeze to prevent modifications
Object.freeze(CONFIG);
