/* =============================================================================
   EUREKAI Module — NavMenu
   Navigation par onglets
   ============================================================================= */

const Module_navmenu = {
  config: null,
  activeTab: null,
  
  /**
   * Initialiser le module
   */
  init(config, template) {
    this.config = config;
    
    // Tab par défaut
    const defaultTab = config.config.tabs.find(t => t.default);
    this.activeTab = defaultTab?.id || config.config.tabs[0]?.id;
    
    // Écouter les événements
    EventBus.on('tab:activate', (data) => this.setActiveTab(data.tabId), 'navmenu');
    
    console.log('[Module:navmenu] Initialized');
  },
  
  /**
   * Rendre le HTML du module
   */
  render(config) {
    const tabs = config.config.tabs;
    
    const tabsHtml = tabs.map(tab => `
      <button class="nav-tab ${tab.id === this.activeTab ? 'active' : ''}" 
              data-tab="${tab.id}" 
              onclick="Module_navmenu.switchTab('${tab.id}')">
        <span class="tab-icon">${tab.icon}</span>${tab.label}
      </button>
    `).join('');
    
    return `<nav class="nav-tabs">${tabsHtml}</nav>`;
  },
  
  /**
   * Changer d'onglet
   */
  switchTab(tabId) {
    if (this.activeTab === tabId) return;
    
    const previousTab = this.activeTab;
    this.activeTab = tabId;
    
    // Mettre à jour l'UI
    this.updateUI();
    
    // Émettre l'événement
    EventBus.emit('tab:switch', { 
      tabId, 
      previousTab 
    }, 'navmenu');
  },
  
  /**
   * Définir l'onglet actif (depuis l'extérieur)
   */
  setActiveTab(tabId) {
    if (this.activeTab === tabId) return;
    this.activeTab = tabId;
    this.updateUI();
  },
  
  /**
   * Mettre à jour l'UI
   */
  updateUI() {
    // Mettre à jour les boutons
    document.querySelectorAll('.nav-tab').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === this.activeTab);
    });
    
    // Mettre à jour les contenus
    document.querySelectorAll('.tab-content').forEach(content => {
      content.classList.toggle('active', content.id === `tab-${this.activeTab}`);
    });
  },
  
  /**
   * Obtenir l'onglet actif
   */
  getActiveTab() {
    return this.activeTab;
  },
  
  /**
   * Obtenir la liste des onglets
   */
  getTabs() {
    return this.config.config.tabs;
  }
};

window.Module_navmenu = Module_navmenu;
