/* =============================================================================
   EUREKAI Module — Toast
   Notifications temporaires
   ============================================================================= */

const Module_toast = {
  config: null,
  container: null,
  
  /**
   * Initialiser le module
   */
  init(config) {
    this.config = config;
    
    // Écouter les événements
    EventBus.on('toast:show', (data) => this.show(data.message, data.type, data.duration), 'toast');
    
    // Créer le container si nécessaire
    this.container = document.getElementById('toast-container');
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      document.body.appendChild(this.container);
    }
    
    console.log('[Module:toast] Initialized');
  },
  
  /**
   * Afficher un toast
   */
  show(message, type = 'info', duration = null) {
    if (!this.container) return;
    
    const actualDuration = duration || this.config?.config?.duration || 3000;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    this.container.appendChild(toast);
    
    // Animation d'entrée
    requestAnimationFrame(() => {
      toast.classList.add('visible');
    });
    
    // Auto-dismiss
    setTimeout(() => {
      toast.classList.remove('visible');
      toast.classList.add('hiding');
      
      setTimeout(() => {
        toast.remove();
      }, 200);
    }, actualDuration);
  },
  
  /**
   * Raccourcis
   */
  success(message, duration) {
    this.show(message, 'success', duration);
  },
  
  error(message, duration) {
    this.show(message, 'error', duration);
  },
  
  warning(message, duration) {
    this.show(message, 'warning', duration);
  },
  
  info(message, duration) {
    this.show(message, 'info', duration);
  }
};

// Fonction globale de compatibilité
function showToast(message, type = 'info', duration = 3000) {
  Module_toast.show(message, type, duration);
}

window.Module_toast = Module_toast;
window.showToast = showToast;
