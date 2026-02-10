/* =============================================================================
   EUREKAI Cockpit — Tabs UI
   ============================================================================= */

function switchTab(tabId) {
  // Update nav tabs
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.tab === tabId);
  });
  
  // Update content
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.toggle('active', content.id === `tab-${tabId}`);
  });
  
  // Refresh specific tabs
  if (tabId === 'json') {
    updateJSON();
  } else if (tabId === 'gevr') {
    gevrRefreshStatus();
  }
}

function updateJSON() {
  const container = document.getElementById('jsonContent');
  if (!container) return;
  
  const data = Store.export();
  container.textContent = JSON.stringify(data, null, 2);
}

function copyJSON() {
  const container = document.getElementById('jsonContent');
  if (!container) return;
  
  const text = container.textContent;
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand('copy');
  document.body.removeChild(textarea);
  
  showToast('JSON copié', 'success');
}

function downloadJSON() {
  const data = Store.export();
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `eurekai_export_${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Export téléchargé', 'success');
}

window.switchTab = switchTab;
window.updateJSON = updateJSON;
window.copyJSON = copyJSON;
window.downloadJSON = downloadJSON;
