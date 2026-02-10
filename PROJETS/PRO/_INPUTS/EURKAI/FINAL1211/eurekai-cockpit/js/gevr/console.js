/* =============================================================================
   EUREKAI Cockpit — GEVR Console
   ============================================================================= */

let gevrCommandHistory = [];
let gevrHistoryIndex = -1;

function gevrConsoleKeydown(event) {
  const input = document.getElementById('gevrConsoleInput');
  if (!input) return;
  
  if (event.key === 'Enter') {
    gevrExecuteCommand();
  } else if (event.key === 'ArrowUp') {
    if (gevrHistoryIndex < gevrCommandHistory.length - 1) {
      gevrHistoryIndex++;
      input.value = gevrCommandHistory[gevrCommandHistory.length - 1 - gevrHistoryIndex];
    }
    event.preventDefault();
  } else if (event.key === 'ArrowDown') {
    if (gevrHistoryIndex > 0) {
      gevrHistoryIndex--;
      input.value = gevrCommandHistory[gevrCommandHistory.length - 1 - gevrHistoryIndex];
    } else if (gevrHistoryIndex === 0) {
      gevrHistoryIndex = -1;
      input.value = '';
    }
    event.preventDefault();
  }
}

function gevrExecuteCommand() {
  const input = document.getElementById('gevrConsoleInput');
  if (!input) return;
  
  const cmd = input.value.trim();
  if (!cmd) return;
  
  // Add to history
  gevrCommandHistory.push(cmd);
  gevrHistoryIndex = -1;
  input.value = '';
  
  GEVRRuntime.log('info', `> ${cmd}`);
  
  // Parse and execute
  const parts = cmd.split(/\s+/);
  const action = parts[0].toLowerCase();
  const args = parts.slice(1);
  
  try {
    switch (action) {
      case 'help':
        gevrShowHelp();
        break;
        
      case 'bootstrap':
        gevrBootstrap();
        break;
        
      case 'scan':
        gevrScan();
        break;
        
      case 'run':
        if (args[0]) gevrRunScenario(args[0]);
        else GEVRRuntime.log('error', 'Usage: run <scenario_lineage>');
        break;
        
      case 'query':
      case 'read':
        const results = SuperTools.read(args.join(' ') || '*');
        GEVRRuntime.log('success', `${results.length} results`);
        results.slice(0, 10).forEach(r => {
          GEVRRuntime.log('info', `  • ${r.lineage}`);
        });
        if (results.length > 10) {
          GEVRRuntime.log('info', `  ... and ${results.length - 10} more`);
        }
        break;
        
      case 'create':
        if (args[0]) {
          SuperTools.create({ source: 'lineage', lineage: args[0] });
          buildLineageIndex();
          renderTree();
        } else {
          GEVRRuntime.log('error', 'Usage: create <lineage>');
        }
        break;
        
      case 'delete':
        if (args[0]) {
          const deleted = SuperTools.delete(args[0], true);
          GEVRRuntime.log('success', `Deleted ${deleted} object(s)`);
          buildLineageIndex();
          renderTree();
        } else {
          GEVRRuntime.log('error', 'Usage: delete <lineage>');
        }
        break;
        
      case 'status':
        GEVRRuntime.log('success', '=== EUREKAI Status ===');
        GEVRRuntime.log('info', `  Objects: ${Store.count()}`);
        GEVRRuntime.log('info', `  Scenarios: ${GEVRRuntime.findScenarios().length}`);
        GEVRRuntime.log('info', `  Files: ${Object.keys(Store.fileStore).length}`);
        GEVRRuntime.log('info', `  Status: ${Store.gevrContext['system.status'] || 'unknown'}`);
        break;
        
      case 'files':
        const files = GEVRRuntime.listFiles();
        GEVRRuntime.log('success', `${files.length} files`);
        files.forEach(f => GEVRRuntime.log('info', `  • ${f.name} (${f.size}B)`));
        break;
        
      case 'handlers':
        const handlers = GEVRRuntime.getHandlers();
        GEVRRuntime.log('success', `${handlers.length} handlers`);
        handlers.forEach(h => GEVRRuntime.log('info', `  • ${h}`));
        break;
        
      case 'ctx':
      case 'context':
        if (args.length === 0) {
          const ctx = GEVRRuntime.getContext();
          GEVRRuntime.log('success', `Context: ${Object.keys(ctx).length} keys`);
          Object.entries(ctx).forEach(([k, v]) => {
            GEVRRuntime.log('info', `  • ${k} = ${JSON.stringify(v).slice(0, 50)}`);
          });
        } else if (args.length === 1) {
          const value = GEVRRuntime.getContext(args[0]);
          GEVRRuntime.log('success', `${args[0]} = ${JSON.stringify(value)}`);
        } else {
          GEVRRuntime.setContext(args[0], args.slice(1).join(' '));
          GEVRRuntime.log('success', `Set ${args[0]}`);
        }
        break;
        
      case 'clear':
        gevrClear();
        break;
        
      case 'export':
        downloadJSON();
        break;
        
      default:
        GEVRRuntime.log('warn', `Unknown command: ${action}. Type 'help' for help.`);
    }
  } catch (err) {
    GEVRRuntime.log('error', err.message);
  }
}

function gevrShowHelp() {
  GEVRRuntime.log('info', '=== GEVR Console Help ===');
  GEVRRuntime.log('info', 'Commands:');
  GEVRRuntime.log('info', '  bootstrap     - Run bootstrap');
  GEVRRuntime.log('info', '  scan          - Find scenarios');
  GEVRRuntime.log('info', '  run <lineage> - Run scenario');
  GEVRRuntime.log('info', '  query <pat>   - Search objects');
  GEVRRuntime.log('info', '  create <lin>  - Create object');
  GEVRRuntime.log('info', '  delete <lin>  - Delete object');
  GEVRRuntime.log('info', '  status        - System status');
  GEVRRuntime.log('info', '  files         - List files');
  GEVRRuntime.log('info', '  handlers      - List handlers');
  GEVRRuntime.log('info', '  ctx [key] [v] - Get/set context');
  GEVRRuntime.log('info', '  clear         - Clear logs');
  GEVRRuntime.log('info', '  export        - Export JSON');
  GEVRRuntime.log('info', '  help          - Show this help');
}

window.gevrConsoleKeydown = gevrConsoleKeydown;
window.gevrExecuteCommand = gevrExecuteCommand;
window.gevrShowHelp = gevrShowHelp;
