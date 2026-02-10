/* =============================================================================
   EUREKAI Modular — Module Loader
   Charge et assemble les modules depuis le manifest
   ============================================================================= */

const ModuleLoader = {
  manifest: null,
  modules: {},
  templates: {},
  loadedScripts: new Set(),
  loadedStyles: new Set(),
  
  /**
   * Initialiser le loader avec un manifest
   * @param {string|Object} manifestSource - URL ou objet manifest
   */
  async init(manifestSource) {
    console.log('[ModuleLoader] Initializing...');
    
    // Charger le manifest
    if (typeof manifestSource === 'string') {
      const response = await fetch(manifestSource);
      this.manifest = await response.json();
    } else {
      this.manifest = manifestSource;
    }
    
    console.log(`[ModuleLoader] Manifest loaded: ${this.manifest.manifest.name} v${this.manifest.manifest.version}`);
    
    // Charger le thème
    await this.loadTheme(this.manifest.config.theme);
    
    // Charger les modules core
    await this.loadCoreModules();
    
    // Créer la structure de base
    this.createBaseStructure();
    
    // Charger les modules UI
    await this.loadUIModules();
    
    // Émettre l'événement ready
    EventBus.emit('app:ready', { manifest: this.manifest }, 'ModuleLoader');
    
    console.log('[ModuleLoader] Initialization complete');
  },
  
  /**
   * Charger le thème CSS
   */
  async loadTheme(themeId) {
    const theme = this.manifest.themes[themeId];
    if (!theme) {
      console.warn(`[ModuleLoader] Theme not found: ${themeId}`);
      return;
    }
    
    await this.loadStyle(theme.file, `theme-${themeId}`);
    console.log(`[ModuleLoader] Theme loaded: ${theme.name}`);
  },
  
  /**
   * Charger les modules core
   */
  async loadCoreModules() {
    const core = this.manifest.core;
    const loadOrder = this.resolveDependencyOrder(core);
    
    console.log(`[ModuleLoader] Loading ${loadOrder.length} core modules...`);
    
    for (const moduleId of loadOrder) {
      const config = core[moduleId];
      await this.loadScript(config.entry, moduleId);
    }
  },
  
  /**
   * Charger les modules UI
   */
  async loadUIModules() {
    const modules = this.manifest.modules;
    
    console.log(`[ModuleLoader] Loading ${Object.keys(modules).length} UI modules...`);
    
    for (const [moduleId, config] of Object.entries(modules)) {
      await this.loadModule(moduleId, config);
    }
  },
  
  /**
   * Charger un module complet (script + styles + template)
   */
  async loadModule(moduleId, config) {
    console.log(`[ModuleLoader] Loading module: ${moduleId}`);
    
    // Charger les styles
    if (config.styles) {
      await this.loadStyle(config.styles, moduleId);
    }
    
    // Charger le template
    if (config.template) {
      await this.loadTemplate(config.template, moduleId);
    }
    
    // Charger le script
    if (config.entry) {
      await this.loadScript(config.entry, moduleId);
    }
    
    // Initialiser le module
    if (window[`Module_${moduleId}`]?.init) {
      await window[`Module_${moduleId}`].init(config, this.templates[moduleId]);
    }
    
    // Monter le module
    if (config.mountPoint) {
      this.mountModule(moduleId, config);
    }
    
    this.modules[moduleId] = {
      id: moduleId,
      config,
      loaded: true,
      mountedAt: config.mountPoint
    };
    
    EventBus.emit('module:loaded', { moduleId, config }, 'ModuleLoader');
  },
  
  /**
   * Charger un script JS
   */
  loadScript(src, moduleId) {
    return new Promise((resolve, reject) => {
      if (this.loadedScripts.has(src)) {
        resolve();
        return;
      }
      
      const script = document.createElement('script');
      script.src = src;
      script.dataset.module = moduleId;
      script.onload = () => {
        this.loadedScripts.add(src);
        resolve();
      };
      script.onerror = () => reject(new Error(`Failed to load: ${src}`));
      document.body.appendChild(script);
    });
  },
  
  /**
   * Charger une feuille de style CSS
   */
  loadStyle(href, moduleId) {
    return new Promise((resolve) => {
      if (this.loadedStyles.has(href)) {
        resolve();
        return;
      }
      
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      link.dataset.module = moduleId;
      link.onload = () => {
        this.loadedStyles.add(href);
        resolve();
      };
      link.onerror = () => {
        console.warn(`[ModuleLoader] Style not found: ${href}`);
        resolve(); // Continue anyway
      };
      document.head.appendChild(link);
    });
  },
  
  /**
   * Charger un template JSON
   */
  async loadTemplate(src, moduleId) {
    try {
      const response = await fetch(src);
      if (response.ok) {
        this.templates[moduleId] = await response.json();
      }
    } catch (err) {
      console.warn(`[ModuleLoader] Template not found: ${src}`);
    }
  },
  
  /**
   * Créer la structure HTML de base depuis le layout du manifest
   */
  createBaseStructure() {
    const layout = this.manifest.layout;
    const app = document.getElementById('app') || document.body;
    
    // Créer les containers principaux
    const html = `
      <div class="app-container" style="display: grid; grid-template-areas: '${layout.areas.join("' '")}'; grid-template-rows: auto auto 1fr; height: 100vh;">
        <nav id="app-nav" style="grid-area: nav;"></nav>
        <header id="app-header" style="grid-area: header;"></header>
        <main id="app-content" style="grid-area: content; overflow: hidden;"></main>
      </div>
      <div id="toast-container"></div>
      <div id="modal-container"></div>
    `;
    
    app.innerHTML = html;
    
    // Créer les tabs dans le content
    this.createTabContainers(layout.containers.content.tabs);
  },
  
  /**
   * Créer les containers pour chaque tab
   */
  createTabContainers(tabs) {
    const content = document.getElementById('app-content');
    let html = '';
    
    for (const [tabId, tabConfig] of Object.entries(tabs)) {
      const isDefault = this.manifest.modules.navmenu?.config?.tabs?.find(t => t.id === tabId)?.default;
      
      if (tabConfig.layout === 'three-panel') {
        html += `
          <div class="tab-content ${isDefault ? 'active' : ''}" id="tab-${tabId}" data-layout="three-panel">
            <aside class="panel" id="panel-${tabConfig.panels[0]}"></aside>
            <div class="resizer" id="resizer-left"></div>
            <section class="panel" id="panel-${tabConfig.panels[1]}"></section>
            <div class="resizer" id="resizer-right"></div>
            <aside class="panel" id="panel-${tabConfig.panels[2]}"></aside>
          </div>
        `;
      } else {
        html += `
          <div class="tab-content ${isDefault ? 'active' : ''}" id="tab-${tabId}" data-layout="full"></div>
        `;
      }
    }
    
    content.innerHTML = html;
  },
  
  /**
   * Monter un module dans son container
   */
  mountModule(moduleId, config) {
    const container = document.querySelector(config.mountPoint);
    if (!container) {
      console.warn(`[ModuleLoader] Mount point not found: ${config.mountPoint}`);
      return;
    }
    
    // Si le module a une méthode render
    if (window[`Module_${moduleId}`]?.render) {
      const html = window[`Module_${moduleId}`].render(config, this.templates[moduleId]);
      container.innerHTML = html;
    }
    
    // Si le module a un template fractal
    else if (this.templates[moduleId]) {
      const html = this.renderTemplate(this.templates[moduleId]);
      container.innerHTML = html;
    }
  },
  
  /**
   * Rendre un template fractal en HTML
   */
  renderTemplate(template) {
    // Utilise le dom_converter inverse si disponible
    if (window.jsonToDOM) {
      return window.jsonToDOM(template);
    }
    
    // Fallback simple
    return this.simpleFractalRender(template.template || template);
  },
  
  /**
   * Rendu fractal simplifié (fallback)
   */
  simpleFractalRender(node) {
    if (!node) return '';
    
    // Si c'est un objet avec des listes d'éléments
    let html = '';
    
    for (const [key, value] of Object.entries(node)) {
      if (key === 'textList' && Array.isArray(value)) {
        html += value.join('');
      }
      else if (key.endsWith('List') && Array.isArray(value)) {
        const tagName = key.replace('List', '');
        for (const item of value) {
          html += this.renderElement(tagName, item);
        }
      }
    }
    
    return html;
  },
  
  /**
   * Rendre un élément
   */
  renderElement(tag, item) {
    if (typeof item === 'string') {
      return `<${tag}>${item}</${tag}>`;
    }
    
    // Extraire les attributs
    let attrs = '';
    const attrsList = item.attrsList?.[0] || {};
    for (const [attrKey, attrValue] of Object.entries(attrsList)) {
      if (attrKey.endsWith('List')) {
        const attrName = attrKey.replace('List', '');
        const val = Array.isArray(attrValue) ? attrValue.join(' ') : attrValue;
        attrs += ` ${attrName}="${val}"`;
      }
    }
    
    // Extraire les enfants
    const children = item.childrenList?.[0] || {};
    const innerHtml = this.simpleFractalRender(children);
    
    // Void elements
    const voidElements = ['br', 'hr', 'img', 'input', 'meta', 'link'];
    if (voidElements.includes(tag)) {
      return `<${tag}${attrs}>`;
    }
    
    return `<${tag}${attrs}>${innerHtml}</${tag}>`;
  },
  
  /**
   * Résoudre l'ordre de chargement selon les dépendances
   */
  resolveDependencyOrder(modules) {
    const order = [];
    const visited = new Set();
    const visiting = new Set();
    
    const visit = (moduleId) => {
      if (visited.has(moduleId)) return;
      if (visiting.has(moduleId)) {
        throw new Error(`Circular dependency detected: ${moduleId}`);
      }
      
      visiting.add(moduleId);
      
      const config = modules[moduleId];
      if (config?.dependencies) {
        for (const dep of config.dependencies) {
          if (modules[dep]) {
            visit(dep);
          }
        }
      }
      
      visiting.delete(moduleId);
      visited.add(moduleId);
      order.push(moduleId);
    };
    
    for (const moduleId of Object.keys(modules)) {
      visit(moduleId);
    }
    
    return order;
  },
  
  /**
   * Obtenir un module chargé
   */
  getModule(moduleId) {
    return this.modules[moduleId];
  },
  
  /**
   * Recharger un module
   */
  async reloadModule(moduleId) {
    const config = this.manifest.modules[moduleId];
    if (!config) return false;
    
    // Nettoyer les listeners
    EventBus.clearModule(moduleId);
    
    // Recharger
    await this.loadModule(moduleId, config);
    
    return true;
  }
};

// Export global
window.ModuleLoader = ModuleLoader;
