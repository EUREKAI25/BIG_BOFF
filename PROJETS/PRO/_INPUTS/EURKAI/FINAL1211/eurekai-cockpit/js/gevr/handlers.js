/* =============================================================================
   EUREKAI Cockpit — GEVR Handlers
   ============================================================================= */

// Register default handlers
(function() {
  // GET handlers
  GEVRRuntime.registerHandler('get:file', async (params) => {
    const content = GEVRRuntime.getFileContent(params.name);
    return { success: !!content, content };
  });
  
  GEVRRuntime.registerHandler('get:store', async (params) => {
    const results = Store.query(params.pattern || '*');
    return { success: true, data: results };
  });
  
  GEVRRuntime.registerHandler('get:context', async (params) => {
    const value = GEVRRuntime.getContext(params.key);
    return { success: true, value };
  });
  
  // EXECUTE handlers
  GEVRRuntime.registerHandler('execute:parse', async (params, input) => {
    const content = input?.content || '';
    const lines = content.split(/\r?\n/).filter(l => l.trim() && !l.trim().startsWith('#'));
    return { success: true, lines };
  });
  
  GEVRRuntime.registerHandler('execute:create', async (params, input) => {
    const lineage = input?.lineage || params.lineage;
    if (!lineage) return { success: false, error: 'No lineage' };
    const result = createLineageWithAncestors(lineage);
    return { success: !!result, ...result };
  });
  
  // VALIDATE handlers
  GEVRRuntime.registerHandler('validate:schema', async (params, input) => {
    const errors = [];
    const data = input?.data || input;
    
    if (params.schema === 'ObjectType') {
      if (Array.isArray(data)) {
        data.forEach((item, i) => {
          if (!item.lineage) errors.push(`Item ${i}: missing lineage`);
        });
      }
    }
    
    return { success: errors.length === 0, errors };
  });
  
  // RENDER handlers
  GEVRRuntime.registerHandler('render:json', async (params, input) => {
    const output = JSON.stringify(input, null, 2);
    return { success: true, output, format: 'json' };
  });
  
  GEVRRuntime.registerHandler('render:report', async (params, input) => {
    const report = {
      title: params.template || 'Report',
      generatedAt: new Date().toISOString(),
      summary: input
    };
    return { success: true, report };
  });
})();
