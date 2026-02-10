/* =============================================================================
   EUREKAI Cockpit — Resizers
   ============================================================================= */

function setupResizers() {
  setupResizer('resizerLeft', 'treePanel', 'left');
  setupResizer('resizerRight', 'tagsPanel', 'right');
}

function setupResizer(resizerId, panelId, side) {
  const resizer = document.getElementById(resizerId);
  const panel = document.getElementById(panelId);
  
  if (!resizer || !panel) return;
  
  let isResizing = false;
  let startX, startWidth;
  
  resizer.addEventListener('mousedown', (e) => {
    isResizing = true;
    startX = e.clientX;
    startWidth = panel.offsetWidth;
    resizer.classList.add('active');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  });
  
  document.addEventListener('mousemove', (e) => {
    if (!isResizing) return;
    
    const diff = side === 'left' ? e.clientX - startX : startX - e.clientX;
    const newWidth = Math.max(180, Math.min(600, startWidth + diff));
    panel.style.width = `${newWidth}px`;
  });
  
  document.addEventListener('mouseup', () => {
    if (isResizing) {
      isResizing = false;
      resizer.classList.remove('active');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }
  });
}

window.setupResizers = setupResizers;
