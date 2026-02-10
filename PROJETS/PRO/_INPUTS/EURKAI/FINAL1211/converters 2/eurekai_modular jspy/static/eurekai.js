/**
 * EUREKAI.js - Client universel
 * Charge les manifests et route les appels (frontend local / backend API)
 */
(function(global) {
    'use strict';

    const EUREKAI = {
        // Configuration
        config: {
            apiEndpoint: '/api',
            registryUrl: '/api/registry',
            token: null
        },

        // Cache des manifests chargés
        _manifests: {},
        _registry: null,
        _frontendFunctions: {},

        /**
         * Configure EUREKAI
         */
        init: function(options = {}) {
            Object.assign(this.config, options);
            return this;
        },

        /**
         * Définit le token d'authentification
         */
        setToken: function(token) {
            this.config.token = token;
            return this;
        },

        /**
         * Charge le registry
         */
        loadRegistry: async function() {
            if (this._registry) return this._registry;

            const response = await fetch(this.config.registryUrl);
            this._registry = await response.json();
            return this._registry;
        },

        /**
         * Charge un ou plusieurs modules
         * @param {string|Array} modules - Nom(s) du/des module(s)
         */
        load: async function(modules) {
            if (typeof modules === 'string') {
                modules = [modules];
            }

            await this.loadRegistry();

            const promises = modules.map(async (moduleName) => {
                if (this._manifests[moduleName]) {
                    return this._manifests[moduleName];
                }

                const url = `${this.config.apiEndpoint}/manifest/${moduleName}`;
                const response = await fetch(url);
                const manifest = await response.json();

                this._manifests[moduleName] = manifest;

                // Pour les modules frontend, créer les fonctions locales
                if (manifest.type === 'frontend') {
                    this._createFrontendFunctions(moduleName, manifest);
                }

                return manifest;
            });

            await Promise.all(promises);
            return this;
        },

        /**
         * Crée les fonctions frontend locales
         */
        _createFrontendFunctions: function(moduleName, manifest) {
            for (const [funcName, funcDef] of Object.entries(manifest.functions || {})) {
                const key = `${moduleName}.${funcName}`;
                
                if (funcDef.code) {
                    try {
                        // Créer la fonction dynamiquement
                        const params = funcDef.params || [];
                        this._frontendFunctions[key] = new Function(...params, funcDef.code);
                    } catch (e) {
                        console.error(`EUREKAI: Failed to create function ${key}:`, e);
                    }
                }
            }
        },

        /**
         * Appelle une fonction (frontend ou backend)
         * @param {string} path - "module.function" ou "function"
         * @param {object} params - Paramètres (objet ou vector ID)
         */
        call: async function(path, params = {}) {
            // Parser le path
            let moduleName, funcName;
            
            if (path.includes('.')) {
                [moduleName, funcName] = path.split('.');
            } else {
                // Chercher dans tous les modules chargés
                for (const [name, manifest] of Object.entries(this._manifests)) {
                    if (manifest.functions && manifest.functions[path]) {
                        moduleName = name;
                        funcName = path;
                        break;
                    }
                }
            }

            if (!moduleName) {
                throw new Error(`EUREKAI: Function "${path}" not found`);
            }

            const manifest = this._manifests[moduleName];
            if (!manifest) {
                throw new Error(`EUREKAI: Module "${moduleName}" not loaded. Call EUREKAI.load('${moduleName}') first.`);
            }

            const funcDef = manifest.functions[funcName];
            if (!funcDef) {
                throw new Error(`EUREKAI: Function "${funcName}" not found in module "${moduleName}"`);
            }

            // Frontend: exécuter localement
            if (manifest.type === 'frontend') {
                const key = `${moduleName}.${funcName}`;
                const fn = this._frontendFunctions[key];
                
                if (!fn) {
                    throw new Error(`EUREKAI: Frontend function "${key}" not compiled`);
                }

                // Mapper les paramètres
                const args = (funcDef.params || []).map(p => params[p]);
                return fn(...args);
            }

            // Backend: appeler l'API
            return this._callBackend(manifest, funcDef, funcName, params);
        },

        /**
         * Appelle une fonction backend via l'API
         */
        _callBackend: async function(manifest, funcDef, funcName, params) {
            const object = manifest.object;
            const centralMethod = funcDef.centralMethod;
            const methodAlias = funcDef.methodAlias;

            // Construire l'URL: /api/{object}/{centralMethod}/{methodAlias}?{vector}&{token}
            let url = `${this.config.apiEndpoint}/${object}/${centralMethod}/${methodAlias}`;
            
            // Vector: soit un ID, soit les params encodés
            let vectorParam;
            if (typeof params === 'string') {
                vectorParam = params;
            } else {
                vectorParam = encodeURIComponent(JSON.stringify(params));
            }
            
            url += `?${vectorParam}`;
            
            // Token
            if (this.config.token) {
                url += `&${this.config.token}`;
            }

            // Appel API
            const response = await fetch(url);
            const data = await response.json();

            if (!data.ok) {
                throw new Error(data.error || 'API call failed');
            }

            return data.result;
        },

        /**
         * Liste les modules chargés
         */
        modules: function() {
            return Object.keys(this._manifests);
        },

        /**
         * Liste les fonctions d'un module
         */
        functions: function(moduleName) {
            const manifest = this._manifests[moduleName];
            if (!manifest) return [];
            return Object.keys(manifest.functions || {});
        },

        /**
         * Raccourci pour charger et appeler
         */
        run: async function(moduleName, funcName, params = {}) {
            await this.load(moduleName);
            return this.call(`${moduleName}.${funcName}`, params);
        }
    };

    // Export
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = EUREKAI;
    } else {
        global.EUREKAI = EUREKAI;
    }

})(typeof window !== 'undefined' ? window : global);
