/* =============================================================================
   EUREKAI Cockpit — GEVR Runtime
   ============================================================================= */

const GEVRRuntime = {
  logs: [],
  handlers: {},
  
  // Logging
  log(level, message, data = null) {
    const time = new Date().toLocaleTimeString('fr-FR', { hour12: false });
    const entry = { time, level, message, data };
    this.logs.push(entry);
    
    const logEl = document.getElementById('gevrLog');
    if (logEl) {
      const entryEl = document.createElement('div');
      entryEl.className = 'gevr-log-entry';
      entryEl.innerHTML = `
        <span class="gevr-log-time">${time}</span>
        <span class="gevr-log-level ${level}">${level}</span>
        <span class="gevr-log-message">${message}${data ? ' ' + JSON.stringify(data) : ''}</span>
      `;
      logEl.appendChild(entryEl);
      logEl.scrollTop = logEl.scrollHeight;
      
      // Update count
      const countEl = document.getElementById('gevrLogCount');
      if (countEl) countEl.textContent = `${this.logs.length} entries`;
    }
    
    console.log(`[GEVR:${level}] ${message}`, data || '');
  },
  
  // Clear logs
  clearLogs() {
    this.logs = [];
    const logEl = document.getElementById('gevrLog');
    if (logEl) logEl.innerHTML = '';
  },
  
  // File management
  uploadFile(name, content) {
    Store.fileStore[name] = content;
    this.log('success', `File uploaded: ${name}`, { size: content.length });
    gevrRefreshFileList();
  },
  
  deleteFile(name) {
    delete Store.fileStore[name];
    this.log('info', `File deleted: ${name}`);
  },
  
  listFiles() {
    return Object.entries(Store.fileStore).map(([name, content]) => ({
      name,
      size: content.length
    }));
  },
  
  clearFiles() {
    const count = Object.keys(Store.fileStore).length;
    Store.fileStore = {};
    return { count };
  },
  
  getFileContent(name) {
    return Store.fileStore[name] || null;
  },
  
  // Context
  getContext(key) {
    return key ? Store.gevrContext[key] : Store.gevrContext;
  },
  
  setContext(key, value) {
    Store.gevrContext[key] = value;
  },
  
  // Handlers
  registerHandler(name, fn) {
    this.handlers[name] = fn;
  },
  
  getHandlers() {
    return Object.keys(this.handlers);
  },
  
  // Find scenarios
  findScenarios() {
    return Store.getAllLineages()
      .filter(l => l.includes(':Scenario:') || l.endsWith(':Scenario'))
      .map(lineage => ({
        lineage,
        name: getLineageName(lineage),
        obj: Store.get(lineage)
      }));
  },
  
  // Execute scenario
  async executeScenario(lineage) {
    return await SuperTools.orchestrate(lineage, Store.gevrContext);
  },
  
  // Bootstrap
  async bootstrap() {
    this.log('info', '########## EUREKAI BOOTSTRAP ##########');
    
    // Phase 0: Import files
    const gevFiles = Object.keys(Store.fileStore).filter(f => f.endsWith('.gev'));
    this.log('info', `=== Phase 0: Auto-Import (${gevFiles.length} files) ===`);
    
    let totalCreated = 0;
    for (const fileName of gevFiles) {
      this.log('info', `Importing: ${fileName}...`);
      try {
        const content = Store.fileStore[fileName];
        const result = SuperTools.createFromSeed(content);
        totalCreated += result.created?.length || 0;
        this.log('success', `→ ${fileName}: ${result.created?.length || 0} objects`);
      } catch (err) {
        this.log('error', `→ ${fileName}: ${err.message}`);
      }
    }
    
    buildLineageIndex();
    
    // Find and run bootstrap scenarios
    const scenarios = this.findScenarios();
    const bootstrapScenarios = scenarios.filter(s => 
      s.lineage.includes(':Bootstrap:') || s.name === 'InitSystem'
    );
    
    this.log('info', `Bootstrap scenarios: ${bootstrapScenarios.length}`);
    
    for (const scenario of bootstrapScenarios) {
      this.log('info', `=== Running: ${scenario.name} ===`);
      try {
        const result = await this.executeScenario(scenario.lineage);
        this.log('success', `=== Completed: ${scenario.name} ===`, { duration: result.duration });
      } catch (err) {
        this.log('error', `Scenario failed: ${err.message}`);
      }
    }
    
    // Update status
    Store.gevrContext['system.status'] = 'ready';
    Store.gevrContext['system.readyAt'] = new Date().toISOString();
    
    this.log('success', `Bootstrap complete: ${Store.count()} objects`);
    
    renderTree();
    gevrRefreshStatus();
    
    return { success: true, objects: Store.count() };
  }
};

// UI functions
function gevrBootstrap() {
  GEVRRuntime.bootstrap();
}

function gevrScan() {
  const scenarios = GEVRRuntime.findScenarios();
  GEVRRuntime.log('success', `Found ${scenarios.length} scenarios`);
  
  const listEl = document.getElementById('gevrScenarioList');
  if (listEl) {
    if (scenarios.length === 0) {
      listEl.innerHTML = '<div class="gevr-empty">Aucun scénario trouvé</div>';
    } else {
      listEl.innerHTML = scenarios.map(s => `
        <div class="gevr-scenario-item" onclick="gevrRunScenario('${s.lineage}')">
          <span class="gevr-scenario-name">${s.name}</span>
        </div>
      `).join('');
    }
  }
  
  gevrRefreshStatus();
}

function gevrRunScenario(lineage) {
  GEVRRuntime.log('info', `Running scenario: ${lineage}`);
  GEVRRuntime.executeScenario(lineage);
}

function gevrClear() {
  GEVRRuntime.clearLogs();
}

function gevrCopyLogs() {
  const text = GEVRRuntime.logs.map(l => 
    `${l.time} [${l.level}] ${l.message}${l.data ? ' ' + JSON.stringify(l.data) : ''}`
  ).join('\n');
  
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand('copy');
  document.body.removeChild(textarea);
  
  showToast('Logs copiés', 'success');
}

function gevrUpload() {
  document.getElementById('gevrFileInput')?.click();
}

function gevrProcessUpload(input) {
  const files = input.files;
  if (!files || files.length === 0) return;
  
  Array.from(files).forEach(file => {
    const reader = new FileReader();
    reader.onload = (e) => {
      GEVRRuntime.uploadFile(file.name, e.target.result);
    };
    reader.readAsText(file);
  });
  
  input.value = '';
}

function gevrRefreshFileList() {
  const files = GEVRRuntime.listFiles();
  const listEl = document.getElementById('gevrFileList');
  if (!listEl) return;
  
  if (files.length === 0) {
    listEl.innerHTML = '<div class="gevr-empty">Aucun fichier</div>';
  } else {
    listEl.innerHTML = files.map(f => `
      <div class="gevr-file-item">
        <span class="gevr-file-name">${f.name}</span>
        <span class="gevr-file-size">${f.size > 1024 ? (f.size/1024).toFixed(1) + 'KB' : f.size + 'B'}</span>
        <span class="gevr-file-delete" onclick="GEVRRuntime.deleteFile('${f.name}'); gevrRefreshFileList();">×</span>
      </div>
    `).join('');
  }
}

function gevrClearFiles() {
  const result = GEVRRuntime.clearFiles();
  gevrRefreshFileList();
  showToast(`${result.count} fichiers supprimés`, 'info');
}

function gevrRefreshStatus() {
  const objCount = document.getElementById('gevrObjectCount');
  const scenCount = document.getElementById('gevrScenarioCount');
  
  if (objCount) objCount.textContent = Store.count();
  if (scenCount) scenCount.textContent = GEVRRuntime.findScenarios().length;
}

window.GEVRRuntime = GEVRRuntime;
window.gevrBootstrap = gevrBootstrap;
window.gevrScan = gevrScan;
window.gevrRunScenario = gevrRunScenario;
window.gevrClear = gevrClear;
window.gevrCopyLogs = gevrCopyLogs;
window.gevrUpload = gevrUpload;
window.gevrProcessUpload = gevrProcessUpload;
window.gevrRefreshFileList = gevrRefreshFileList;
window.gevrClearFiles = gevrClearFiles;
window.gevrRefreshStatus = gevrRefreshStatus;
