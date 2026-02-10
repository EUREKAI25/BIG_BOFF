/* =============================================================================
   EUREKAI Cockpit — Initialization
   ============================================================================= */

function initialize() {
  console.log(`EUREKAI Cockpit ${CONFIG.version} initializing...`);
  
  // Setup UI
  setupResizers();
  setupDepthControl();
  setupLineageInput();
  
  // Build index and render
  buildLineageIndex();
  renderTree();
  renderTags();
  updateBreadcrumb();
  
  // Setup GEVR
  gevrRefreshFileList();
  gevrRefreshStatus();
  
  console.log(`EUREKAI Cockpit ${CONFIG.version} ready`);
  showToast(`Cockpit ${CONFIG.version} prêt`, 'success');
}

function setupLineageInput() {
  const input = document.getElementById('lineageInput');
  const submitBtn = document.getElementById('lineageSubmit');
  
  if (input) {
    input.addEventListener('keydown', async (e) => {
      if (e.key === 'Enter') {
        await handleLineageSubmit();
      }
    });
    
    input.addEventListener('input', () => {
      const value = input.value.trim();
      if (value) {
        const parsed = parseEnhancedLineage(value);
        input.classList.toggle('invalid', !parsed.valid && value.length > 0);
      } else {
        input.classList.remove('invalid');
      }
    });
  }
  
  if (submitBtn) {
    submitBtn.addEventListener('click', handleLineageSubmit);
  }
}

async function handleLineageSubmit() {
  const input = document.getElementById('lineageInput');
  if (!input) return;
  
  const value = input.value.trim();
  if (!value) return;
  
  try {
    const result = await processEnhancedLineage(value);
    if (result) {
      buildLineageIndex();
      renderTree();
      
      // Select the created object
      const lineage = result.finalLineage || result.created?.[0]?.lineage;
      if (lineage) {
        selectNode(lineage);
        // Expand ancestors
        const ancestors = getAncestors(lineage);
        ancestors.forEach(a => Store.ui.expandedNodes.add(a));
        renderTree();
      }
      
      showToast(`Créé: ${lineage || value}`, 'success');
      input.value = '';
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Console command
let lastConsoleResult = null;

function runConsoleCommand() {
  const input = document.getElementById('consoleInput');
  const output = document.getElementById('consoleOutput');
  
  if (!input || !output) return;
  
  const cmd = input.value.trim();
  if (!cmd) return;
  
  try {
    const result = eval(cmd);
    lastConsoleResult = result;
    output.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
  } catch (err) {
    lastConsoleResult = { error: err.message };
    output.innerHTML = `<pre style="color: var(--accent-error)">Error: ${err.message}</pre>`;
  }
}

function copyConsoleOutput() {
  if (lastConsoleResult !== null) {
    const text = JSON.stringify(lastConsoleResult, null, 2);
    
    // Méthode fallback pour HTTP
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    
    showToast('Copié !', 'success');
  }
}

function downloadConsoleOutput() {
  if (lastConsoleResult !== null) {
    const blob = new Blob([JSON.stringify(lastConsoleResult, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `console_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
}

function clearConsoleOutput() {
  const output = document.getElementById('consoleOutput');
  if (output) output.innerHTML = '<pre>// Effacé</pre>';
  lastConsoleResult = null;
}

window.runConsoleCommand = runConsoleCommand;
window.copyConsoleOutput = copyConsoleOutput;
window.downloadConsoleOutput = downloadConsoleOutput;
window.clearConsoleOutput = clearConsoleOutput;

// Expose main functions
window.OFT = {
  Store,
  SuperTools,
  GEVRRuntime,
  traverse,
  resolveSecondaryMethod,
  createObjectType,
  processEnhancedLineage,
  selectNode,
  renderTree,
  renderFractal
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', initialize);
