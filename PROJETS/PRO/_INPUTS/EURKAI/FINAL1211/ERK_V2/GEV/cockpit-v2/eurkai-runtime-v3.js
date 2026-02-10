/**
 * EURKAI Runtime v3 - MRG (Machine de Rendu Générique)
 * =====================================================
 * Génère le cockpit complet depuis les seeds GEV
 */

class EurkaiRuntime {
    constructor() {
        this.store = new Map();
        this.byName = new Map();
        this.relations = [];
        this.context = {};
        this.stats = { types: 0, vectors: 0, aliases: 0 };
    }

    // =========================================================================
    // PARSER
    // =========================================================================

    parseGev(content, sourceName = '') {
        const objects = [];
        let current = null;
        const lines = content.split('\n');
        let multilineAttr = null;  // {key, value, quoteChar}

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const lineNum = i + 1;

            // Skip comments and empty lines (but not if we're in multiline mode)
            if (!multilineAttr && (/^\s*#/.test(line) || /^\s*$/.test(line))) continue;

            // If we're accumulating a multiline attribute
            if (multilineAttr) {
                // Check if this line ends the multiline (ends with closing quote)
                const quoteChar = multilineAttr.quoteChar;
                if (line.endsWith(quoteChar)) {
                    // End of multiline - add line without the closing quote
                    multilineAttr.value += '\n' + line.slice(0, -1);
                    current.attributes[multilineAttr.key] = multilineAttr.value;
                    multilineAttr = null;
                } else {
                    // Continue accumulating
                    multilineAttr.value += '\n' + line;
                }
                continue;
            }

            // Lineage: Type:SubType:Name:
            const lm = line.match(/^([A-Z][a-zA-Z0-9_]*(?::[A-Za-z][a-zA-Z0-9_]*)*):$/);
            if (lm) {
                if (current) objects.push(current);
                const lineage = lm[1];
                const typeChain = lineage.split(':');
                current = {
                    uuid: this.uuid(),
                    lineage,
                    typeChain,
                    name: typeChain[typeChain.length - 1],
                    attributes: {},
                    _source: { file: sourceName, line: lineNum }
                };
                continue;
            }

            // Attribute: .name = value
            const am = line.match(/^\s*\.(\w+)\s*=\s*(.*)$/);
            if (am && current) {
                const key = am[1];
                let val = am[2].trim();
                
                // Check for quoted string
                const quoteChar = val[0];
                if (quoteChar === '"' || quoteChar === "'") {
                    // Check if it's a complete single-line string
                    if (val.length > 1 && val.endsWith(quoteChar)) {
                        // Complete string on one line
                        current.attributes[key] = val.slice(1, -1);
                    } else {
                        // Start of multiline string
                        multilineAttr = {
                            key: key,
                            value: val.slice(1),  // Remove opening quote
                            quoteChar: quoteChar
                        };
                    }
                } else {
                    // Non-quoted value
                    if (val === 'true') current.attributes[key] = true;
                    else if (val === 'false') current.attributes[key] = false;
                    else if (/^-?\d+(\.\d+)?$/.test(val)) current.attributes[key] = parseFloat(val);
                    else current.attributes[key] = val;
                }
                continue;
            }

            // Relation: Subject IN Target.List
            const rm = line.match(/^(\w+)\s+IN\s+(\w+)\.(\w+)$/);
            if (rm) {
                this.relations.push({
                    subject: rm[1],
                    target: rm[2],
                    list: rm[3],
                    _source: { file: sourceName, line: lineNum }
                });
            }
        }
        if (current) objects.push(current);
        return objects;
    }

    uuid() {
        return 'xxxx-xxxx-xxxx'.replace(/x/g, () => (Math.random()*16|0).toString(16));
    }

    // =========================================================================
    // STORE
    // =========================================================================

    load(objects) {
        for (const o of objects) {
            this.store.set(o.lineage, o);
            this.byName.set(o.name, o);
            if (o.typeChain.includes('Vector')) this.stats.vectors++;
            else this.stats.types++;
        }
    }

    loadFile(path, fs) {
        const content = fs.readFileSync(path, 'utf-8');
        const objects = this.parseGev(content, path);
        this.load(objects);
        return objects;
    }

    loadDir(dir, fs, path) {
        const all = [];
        const scan = d => {
            for (const e of fs.readdirSync(d, { withFileTypes: true })) {
                const p = path.join(d, e.name);
                if (e.isDirectory() && !e.name.startsWith('.')) scan(p);
                else if (e.name.endsWith('.gev')) all.push(...this.loadFile(p, fs));
            }
        };
        scan(dir);
        return all;
    }

    get(lineage) { return this.store.get(lineage); }
    getByName(name) { return this.byName.get(name); }
    findByType(type) { return [...this.store.values()].filter(o => o.typeChain.includes(type)); }

    // =========================================================================
    // RELATIONS
    // =========================================================================

    getList(targetName, listName) {
        const items = [];
        for (const r of this.relations) {
            if (r.target === targetName && r.list === listName) {
                const obj = this.getByName(r.subject);
                if (obj) items.push(obj);
            }
        }
        return items;
    }

    // =========================================================================
    // INHERITANCE
    // =========================================================================

    resolveAttribute(mod, attrName) {
        // Check own attributes first
        if (mod.attributes[attrName] !== undefined) {
            return mod.attributes[attrName];
        }
        // Walk up the type chain
        for (let i = mod.typeChain.length - 2; i >= 0; i--) {
            const parentName = mod.typeChain[i];
            const parent = this.getByName(parentName);
            if (parent?.attributes?.[attrName] !== undefined) {
                return parent.attributes[attrName];
            }
        }
        return undefined;
    }

    // =========================================================================
    // MRG - MACHINE DE RENDU GÉNÉRIQUE
    // =========================================================================

    renderModule(mod, data = null) {
        if (!mod) return '';

        // Get HTML from inheritance
        let html = this.resolveAttribute(mod, 'html');
        
        if (!html) {
            // No HTML, just render children
            const children = this.getList(mod.name, 'ModuleList');
            return children.map(c => this.renderModule(c, data)).join('');
        }

        // Build data context: merge stats + module attrs + passed data
        const ctx = {
            ...this.stats,
            typeCount: this.stats.types,
            vectorCount: this.stats.vectors,
            aliasCount: this.stats.aliases,
            objectCount: this.store.size,
            ...mod.attributes,
            ...data
        };

        // Render children for {{content}}
        const children = this.getList(mod.name, 'ModuleList');
        const childHtml = children.map(c => this.renderModule(c, data)).join('');
        html = html.replace(/\{\{content\}\}/g, childHtml);

        // Render tabs for {{tabs}}
        const tabs = this.getList(mod.name, 'TabList');
        if (tabs.length > 0) {
            const tabsHtml = tabs.map(t => this.renderModule(t, data)).join('');
            html = html.replace(/\{\{tabs\}\}/g, tabsHtml);
        }

        // Render panels for {{panels}}
        const panels = this.getList(mod.name, 'PanelList');
        if (panels.length > 0) {
            const panelsHtml = panels.map(p => this.renderModule(p, data)).join('');
            html = html.replace(/\{\{panels\}\}/g, panelsHtml);
        }

        // Replace placeholders
        html = this.replacePlaceholders(html, ctx);

        return html;
    }

    replacePlaceholders(html, data = {}) {
        // {{#if attr}}...{{/if}}
        html = html.replace(/\{\{#if\s+(\w+)\}\}([\s\S]*?)\{\{\/if\}\}/g, (m, cond, content) => {
            return data[cond] ? content : '';
        });

        // {{#each attr}}...{{/each}}
        html = html.replace(/\{\{#each\s+(\w+)\}\}([\s\S]*?)\{\{\/each\}\}/g, (m, arr, content) => {
            const items = data[arr] || [];
            return items.map(i => this.replacePlaceholders(content, i)).join('');
        });

        // {{attr}}
        html = html.replace(/\{\{(\w+)\}\}/g, (m, k) => {
            if (data[k] !== undefined) return String(data[k]);
            return '';
        });

        return html;
    }

    // =========================================================================
    // COCKPIT RENDER
    // =========================================================================

    renderCockpit() {
        const cockpit = this.getByName('CockpitTemplate');
        if (!cockpit) return this.renderNoTemplate();

        const content = this.renderModule(cockpit);
        const cssObj = this.getByName('CockpitCSS');
        const css = cssObj?.attributes?.css || '';
        
        // Unescape and clean content
        let cleanContent = content
            .replace(/\\"/g, '"')
            .replace(/\\'/g, "'")
            .replace(/"\s*</g, '<')  // Remove stray quotes before tags
            .replace(/>\s*"/g, '>')  // Remove stray quotes after tags
            .replace(/""/g, '"');    // Remove double quotes

        return `<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<style>
${css}
</style>
</head>
<body>
${cleanContent}
<script>
const vscode = typeof acquireVsCodeApi !== 'undefined' ? acquireVsCodeApi() : { postMessage: console.log };
const hasProject = true;
const objects = [];
const treeData = { name: 'Object', lineage: 'Object', children: [] };
const vectors = {};

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const panelId = 'panel-' + tab.dataset.tab;
        const panel = document.getElementById(panelId);
        if (!panel) return;
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        panel.classList.add('active');
    });
});

// Search
const searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('input', e => {
        const q = e.target.value.toLowerCase();
        document.querySelectorAll('.tree-node').forEach(n => {
            const name = n.querySelector('.name');
            if (name) n.style.display = name.textContent.toLowerCase().includes(q) ? 'flex' : 'none';
        });
    });
}

// Radio scan
document.querySelectorAll('input[name="walkerScan"]').forEach(radio => {
    radio.addEventListener('change', function() {
        const customGroup = document.getElementById('customScanGroup');
        if (customGroup) customGroup.style.display = this.value === 'other' ? 'block' : 'none';
    });
});

// Functions
function openHtmlPreview() { vscode.postMessage({ command: 'openHtmlPreview' }); }
function refreshProject() { vscode.postMessage({ command: 'refreshProject' }); }
function selectObject(l) { vscode.postMessage({ command: 'selectObject', lineage: l }); }
function gotoObject(l) { vscode.postMessage({ command: 'gotoObject', lineage: l }); }
function runWalker(action) {
    const dict = document.getElementById('walkerDict')?.value || 'Object';
    const scan = document.querySelector('input[name="walkerScan"]:checked')?.value || 'pass';
    vscode.postMessage({ command: 'runWalker', action, dict, scan });
}
function runQuery() {
    const q = document.getElementById('queryInput')?.value || '';
    vscode.postMessage({ command: 'runQuery', query: q });
}
function testRule() {
    const target = document.getElementById('ruleTarget')?.value || '';
    const expr = document.getElementById('ruleExpr')?.value || '';
    vscode.postMessage({ command: 'testRule', target, expr });
}
function resolveValue() {
    const input = document.getElementById('resolveInput')?.value || '';
    vscode.postMessage({ command: 'resolveValue', input });
}
function evalErk() {
    const expr = document.getElementById('erkExpr')?.value || '';
    const ctx = document.getElementById('erkContext')?.value || '{}';
    vscode.postMessage({ command: 'evalErk', expr, context: ctx });
}
function createAlias() {
    const name = document.getElementById('aliasName')?.value || '';
    const target = document.getElementById('aliasTarget')?.value || '';
    const query = document.getElementById('aliasQuery')?.value || '';
    vscode.postMessage({ command: 'createAlias', aliasName: name, target, query });
}
function deployWebsite() { vscode.postMessage({ command: 'deployWebsite' }); }
</script>
</body>
</html>`;
    }

    renderNoTemplate() {
        return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>body{font-family:system-ui;margin:0;padding:40px;background:#1e1e1e;color:#ccc;text-align:center}
button{padding:12px 24px;cursor:pointer;background:#0e639c;color:#fff;border:none;border-radius:4px;font-size:14px}
button:hover{background:#1177bb}p{margin:20px 0;opacity:0.7}</style>
</head><body>
<h2>EURKAI</h2>
<p>No CockpitTemplate found. Load a project with .gev files.</p>
<button onclick="vscode.postMessage({command:'selectProject'})">Select Project Folder</button>
<script>const vscode = typeof acquireVsCodeApi !== 'undefined' ? acquireVsCodeApi() : { postMessage: console.log };</script>
</body></html>`;
    }

    setContext(k, v) { this.context[k] = v; }
}

if (typeof module !== 'undefined') module.exports = { EurkaiRuntime };
