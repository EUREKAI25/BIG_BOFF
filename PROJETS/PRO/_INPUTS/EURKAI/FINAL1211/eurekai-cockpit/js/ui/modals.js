/* =============================================================================
   EUREKAI Cockpit — Modals
   ============================================================================= */

let modalResolve = null;

function showModal(title, body, options = {}) {
  const overlay = document.getElementById('modalOverlay');
  const titleEl = document.getElementById('modalTitle');
  const bodyEl = document.getElementById('modalBody');
  const confirmBtn = document.getElementById('modalConfirm');
  const cancelBtn = document.getElementById('modalCancel');
  
  if (!overlay) return Promise.resolve(false);
  
  titleEl.textContent = title;
  bodyEl.innerHTML = body;
  
  if (options.confirmText) confirmBtn.textContent = options.confirmText;
  if (options.cancelText) cancelBtn.textContent = options.cancelText;
  
  overlay.classList.add('active');
  
  return new Promise((resolve) => {
    modalResolve = resolve;
    
    confirmBtn.onclick = () => {
      closeModal();
      resolve(true);
    };
    
    cancelBtn.onclick = () => {
      closeModal();
      resolve(false);
    };
    
    overlay.onclick = (e) => {
      if (e.target === overlay) {
        closeModal();
        resolve(false);
      }
    };
  });
}

function closeModal() {
  const overlay = document.getElementById('modalOverlay');
  if (overlay) {
    overlay.classList.remove('active');
  }
}

async function confirmDelete(lineage) {
  const result = await showModal(
    'Confirmer la suppression',
    `<p>Voulez-vous supprimer <strong>${lineage}</strong> ?</p>
     <p style="color: var(--accent-warning); font-size: 12px;">
       Les enfants seront également supprimés.
     </p>`,
    { confirmText: 'Supprimer', cancelText: 'Annuler' }
  );
  
  if (result) {
    const deleted = deleteObjectType(lineage, true);
    showToast(`${deleted} objet(s) supprimé(s)`, 'success');
    buildLineageIndex();
    renderTree();
    renderFractal(null);
  }
}

window.showModal = showModal;
window.closeModal = closeModal;
window.confirmDelete = confirmDelete;
