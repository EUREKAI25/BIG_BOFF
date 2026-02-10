/* =============================================================================
   EUREKAI Cockpit — Import/Export
   ============================================================================= */

function importData() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.json,.gev';
  
  input.onchange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (evt) => {
      const content = evt.target.result;
      
      if (file.name.endsWith('.json')) {
        try {
          const data = JSON.parse(content);
          Store.import(data);
          buildLineageIndex();
          renderTree();
          renderTags();
          showToast(`Importé: ${Object.keys(data.objectTypes || {}).length} objets`, 'success');
        } catch (err) {
          showToast(`Erreur JSON: ${err.message}`, 'error');
        }
      } else if (file.name.endsWith('.gev')) {
        Store.fileStore[file.name] = content;
        try {
          const result = SuperTools.createFromSeed(content);
          buildLineageIndex();
          renderTree();
          showToast(`Importé: ${result.created?.length || 0} objets`, 'success');
        } catch (err) {
          showToast(`Erreur GEV: ${err.message}`, 'error');
        }
      }
    };
    reader.readAsText(file);
  };
  
  input.click();
}

function exportData() {
  downloadJSON();
}

function runBootstrap() {
  gevrBootstrap();
}

window.importData = importData;
window.exportData = exportData;
window.runBootstrap = runBootstrap;
