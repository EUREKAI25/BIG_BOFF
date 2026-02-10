"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const store = {
    objects: new Map(),
    vectors: new Map(),
    rules: []
};
let cockpitPanel;
let fractaleProvider;
let rulesProvider;
// ============================================================================
// PARSER
// ============================================================================
function parseAllFiles() {
    store.objects.clear();
    store.vectors.clear();
    store.rules = [];
    // Parse open documents
    vscode.workspace.textDocuments.forEach(doc => {
        if (doc.fileName.endsWith('.gev') || doc.fileName.endsWith('.erk')) {
            parseFile(doc);
        }
    });
    // Also scan workspace folders for .gev files
    if (vscode.workspace.workspaceFolders) {
        for (const folder of vscode.workspace.workspaceFolders) {
            scanFolder(folder.uri.fsPath);
        }
    }
}
function scanFolder(folderPath, depth = 0) {
    // Limite de profondeur pour éviter les scans trop longs
    if (depth > 5)
        return;
    // Dossiers à ignorer
    const ignoreDirs = new Set([
        'node_modules', '.git', '.vscode', 'dist', 'build', 'out',
        '__pycache__', '.cache', 'coverage', '.next', '.nuxt',
        'vendor', 'bower_components', '.idea', '.DS_Store'
    ]);
    try {
        const entries = fs.readdirSync(folderPath, { withFileTypes: true });
        for (const entry of entries) {
            const fullPath = path.join(folderPath, entry.name);
            if (entry.isDirectory() && !entry.name.startsWith('.') && !ignoreDirs.has(entry.name)) {
                scanFolder(fullPath, depth + 1);
            }
            else if (entry.isFile() && (entry.name.endsWith('.gev') || entry.name.endsWith('.erk'))) {
                parseFileFromPath(fullPath);
            }
        }
    }
    catch (e) {
        // Ignore errors
    }
}
function parseFileFromPath(filePath) {
    try {
        const content = fs.readFileSync(filePath, 'utf-8');
        parseContent(content, filePath);
    }
    catch (e) {
        // Ignore errors
    }
}
function parseContent(text, source) {
    const lines = text.split('\n');
    let currentObject = null;
    for (let i = 0; i < lines.length; i++) {
        const trimmed = lines[i].trim();
        if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('//'))
            continue;
        const lineageMatch = trimmed.match(/^([A-Z][A-Za-z0-9_]*(?::[A-Z][A-Za-z0-9_]*)*):$/);
        if (lineageMatch) {
            if (currentObject)
                addObject(currentObject);
            let lineage = lineageMatch[1];
            if (!lineage.startsWith('Object:') && lineage !== 'Object') {
                lineage = 'Object:' + lineage;
            }
            const segments = lineage.split(':');
            currentObject = {
                lineage,
                name: segments[segments.length - 1],
                parent: segments.slice(0, -1).join(':'),
                attributes: {},
                relations: [],
                source,
                line: i + 1
            };
            // Auto-create ancestors
            for (let j = 1; j < segments.length; j++) {
                const ancestorLineage = segments.slice(0, j).join(':');
                if (!store.objects.has(ancestorLineage)) {
                    store.objects.set(ancestorLineage, {
                        lineage: ancestorLineage,
                        name: segments[j - 1],
                        parent: segments.slice(0, j - 1).join(':'),
                        attributes: {},
                        relations: [],
                        source,
                        line: -1
                    });
                }
            }
            continue;
        }
        const attrMatch = trimmed.match(/^\.([a-zA-Z_][a-zA-Z0-9_.]*)\s*=\s*(.+)$/);
        if (attrMatch && currentObject) {
            currentObject.attributes[attrMatch[1]] = attrMatch[2];
            continue;
        }
        const relMatch = trimmed.match(/^([A-Z][A-Za-z0-9_]*)\s+(IN|depends_on|related_to)\s+(.+)$/);
        if (relMatch && currentObject) {
            currentObject.relations.push({ type: relMatch[2], target: relMatch[3].trim() });
        }
    }
    if (currentObject)
        addObject(currentObject);
}
function parseFile(document) {
    parseContent(document.getText(), document.fileName);
}
function addObject(obj) {
    store.objects.set(obj.lineage, obj);
    if (obj.lineage.includes(':Vector:')) {
        const name = obj.attributes.name?.replace(/"/g, '') || obj.name;
        if (name.startsWith('V_'))
            store.vectors.set(name, obj);
    }
    if (obj.lineage.includes(':Rule:')) {
        store.rules.push(obj);
    }
}
function getChildren(lineage) {
    const prefix = lineage + ':';
    return Array.from(store.objects.keys()).filter(l => l.startsWith(prefix) && !l.substring(prefix.length).includes(':'));
}
function resolveVector(name) {
    const v = store.vectors.get(name);
    if (!v)
        return null;
    const def = v.attributes.default;
    if (def?.match(/^\d+(\.\d+)?$/))
        return parseFloat(def);
    return def?.replace(/"/g, '') || null;
}
// ============================================================================
// TREE PROVIDERS
// ============================================================================
class FractaleProvider {
    constructor() {
        this._onDidChange = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChange.event;
    }
    refresh() { this._onDidChange.fire(undefined); }
    getTreeItem(lineage) {
        const obj = store.objects.get(lineage);
        const children = getChildren(lineage);
        const item = new vscode.TreeItem(obj?.name || lineage.split(':').pop() || lineage, children.length ? vscode.TreeItemCollapsibleState.Expanded : vscode.TreeItemCollapsibleState.None);
        item.tooltip = lineage;
        item.description = children.length ? `(${children.length})` : '';
        item.contextValue = 'erkObject';
        item.command = { command: 'eurekai.selectObject', title: 'Select', arguments: [lineage] };
        // Icons
        if (lineage.includes(':Entity:'))
            item.iconPath = new vscode.ThemeIcon('person');
        else if (lineage.includes(':Vector:'))
            item.iconPath = new vscode.ThemeIcon('symbol-variable');
        else if (lineage.includes(':Rule:'))
            item.iconPath = new vscode.ThemeIcon('checklist');
        else if (lineage.includes(':Config:'))
            item.iconPath = new vscode.ThemeIcon('settings-gear');
        else
            item.iconPath = new vscode.ThemeIcon('symbol-class');
        return item;
    }
    getChildren(lineage) {
        if (!lineage)
            return store.objects.has('Object') ? ['Object'] : [];
        return getChildren(lineage);
    }
}
class RulesProvider {
    constructor() {
        this._onDidChange = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChange.event;
    }
    refresh() { this._onDidChange.fire(undefined); }
    getTreeItem(rule) {
        const item = new vscode.TreeItem(rule.name, vscode.TreeItemCollapsibleState.None);
        item.tooltip = rule.lineage;
        item.description = rule.attributes.target || '';
        item.iconPath = new vscode.ThemeIcon('checklist');
        return item;
    }
    getChildren() {
        return store.rules;
    }
}
// ============================================================================
// COCKPIT WEBVIEW
// ============================================================================
function showCockpit(context) {
    if (cockpitPanel) {
        cockpitPanel.reveal();
        updateCockpit();
        return;
    }
    cockpitPanel = vscode.window.createWebviewPanel('eurekaiCockpit', 'EUREKAI Cockpit', vscode.ViewColumn.Two, { enableScripts: true, retainContextWhenHidden: true });
    cockpitPanel.onDidDispose(() => { cockpitPanel = undefined; });
    cockpitPanel.webview.onDidReceiveMessage(async (msg) => {
        if (msg.command === 'gotoObject') {
            const obj = store.objects.get(msg.lineage);
            if (obj && obj.line > 0) {
                vscode.workspace.openTextDocument(obj.source).then(doc => {
                    vscode.window.showTextDocument(doc, vscode.ViewColumn.One).then(editor => {
                        const pos = new vscode.Position(obj.line - 1, 0);
                        editor.selection = new vscode.Selection(pos, pos);
                        editor.revealRange(new vscode.Range(pos, pos));
                    });
                });
            }
        }
        else if (msg.command === 'createObject') {
            await createObject(msg.parent, msg.name, msg.attributes, msg.methods || [], msg.relations || [], msg.rules || []);
        }
        else if (msg.command === 'query') {
            executeQuery(msg.query);
        }
        else if (msg.command === 'resolve') {
            const result = resolveVector(msg.value);
            cockpitPanel?.webview.postMessage({ type: 'resolved', value: msg.value, result });
        }
        else if (msg.command === 'deleteObject') {
            await deleteObject(msg.lineage);
        }
        else if (msg.command === 'updateAttribute') {
            await updateAttribute(msg.lineage, msg.key, msg.value);
        }
        else if (msg.command === 'addAttribute') {
            await addAttribute(msg.lineage, msg.key, msg.value);
        }
        else if (msg.command === 'addMethod') {
            await addMethod(msg.lineage, msg.name);
        }
        else if (msg.command === 'addRelation') {
            await addRelation(msg.lineage, msg.type, msg.target);
        }
        else if (msg.command === 'addRule') {
            await addRule(msg.lineage, msg.type, msg.name);
        }
        else if (msg.command === 'moveObject') {
            await moveObject(msg.sourceLineage, msg.targetLineage);
        }
        else if (msg.command === 'toggleServer') {
            await togglePythonServer();
        }
        else if (msg.command === 'openFile') {
            if (msg.path) {
                vscode.workspace.openTextDocument(msg.path).then(doc => {
                    vscode.window.showTextDocument(doc, vscode.ViewColumn.One);
                });
            }
        }
        else if (msg.command === 'selectAndSwitchTab') {
            // After creation, switch to explorer and select the object
            updateCockpit();
        }
        else if (msg.command === 'openInBrowser') {
            vscode.env.openExternal(vscode.Uri.parse('http://localhost:5000/cockpit'));
        }
    });
    updateCockpit();
}
async function createObject(parent, name, attributes, methods = [], relations = [], rules = []) {
    // Trouver le bon fichier pour créer l'objet
    const parentObj = store.objects.get(parent);
    let targetFile = parentObj?.source;
    if (!targetFile && vscode.workspace.workspaceFolders) {
        // Créer dans un nouveau fichier seeds (schémas)
        const folder = vscode.workspace.workspaceFolders[0].uri.fsPath;
        const seedsDir = path.join(folder, 'seeds');
        if (!fs.existsSync(seedsDir)) {
            fs.mkdirSync(seedsDir, { recursive: true });
        }
        targetFile = path.join(seedsDir, 'custom.s.gev');
        if (!fs.existsSync(targetFile)) {
            fs.writeFileSync(targetFile, '# EUREKAI Custom Seeds\n\n');
        }
    }
    if (!targetFile) {
        vscode.window.showErrorMessage('Impossible de créer l\'objet: aucun fichier cible');
        return;
    }
    // Construire le contenu
    const lineage = parent ? `${parent}:${name}` : `Object:${name}`;
    let content = `\n${lineage}:\n`;
    // Attributs
    for (const [key, value] of Object.entries(attributes)) {
        if (value) {
            const formattedValue = value.includes(' ') && !value.startsWith('"') && !value.startsWith('V_') ? `"${value}"` : value;
            content += `  .${key} = ${formattedValue}\n`;
        }
    }
    // Relations
    for (const rel of relations) {
        content += `  ${name} ${rel.type} ${rel.target}\n`;
    }
    // Ajouter au fichier
    fs.appendFileSync(targetFile, content);
    // Ajouter les méthodes comme sous-objets
    for (const methodName of methods) {
        const methodContent = `\n${lineage}:${methodName}Method:\n  .name = "${methodName}"\n  .belongs_to = ${name}\n`;
        fs.appendFileSync(targetFile, methodContent);
    }
    // Ajouter les règles
    for (const rule of rules) {
        const ruleContent = `\nObject:Rule:${rule.type}:${rule.name}:\n  .name = "${rule.name}"\n  .target = "${lineage}"\n  .type = "${rule.type.replace('Rule', '').toLowerCase()}"\n`;
        fs.appendFileSync(targetFile, ruleContent);
    }
    // Rafraîchir
    parseAllFiles();
    fractaleProvider.refresh();
    rulesProvider.refresh();
    updateCockpit();
    vscode.window.showInformationMessage(`Objet "${name}" créé`);
}
// Afficher message de redémarrage au démarrage si nécessaire
function showRestartMessage() {
    vscode.window.showInformationMessage('Extension EUREKAI mise à jour. Redémarrez VSCode (Cmd+Q / Ctrl+Q) pour appliquer.', 'OK');
}
async function deleteObject(lineage) {
    const obj = store.objects.get(lineage);
    if (!obj || !obj.source) {
        vscode.window.showErrorMessage('Objet non trouvé');
        return;
    }
    // Lire le fichier
    const content = fs.readFileSync(obj.source, 'utf-8');
    const lines = content.split('\n');
    // Trouver le début et la fin de l'objet
    const startLine = obj.line - 1;
    let endLine = startLine + 1;
    // Trouver la fin (prochaine définition d'objet ou fin de fichier)
    for (let i = startLine + 1; i < lines.length; i++) {
        const trimmed = lines[i].trim();
        if (trimmed && !trimmed.startsWith('.') && !trimmed.startsWith('#') && !trimmed.startsWith('//')) {
            if (trimmed.match(/^[A-Z]/)) {
                endLine = i;
                break;
            }
        }
        endLine = i + 1;
    }
    // Supprimer les lignes
    lines.splice(startLine, endLine - startLine);
    // Réécrire le fichier
    fs.writeFileSync(obj.source, lines.join('\n'));
    // Rafraîchir
    parseAllFiles();
    fractaleProvider.refresh();
    rulesProvider.refresh();
    updateCockpit();
    vscode.window.showInformationMessage(`Objet "${lineage}" supprimé`);
}
async function updateAttribute(lineage, key, value) {
    const obj = store.objects.get(lineage);
    if (!obj || !obj.source)
        return;
    // Lire le fichier
    const content = fs.readFileSync(obj.source, 'utf-8');
    const lines = content.split('\n');
    // Trouver l'attribut
    for (let i = obj.line; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();
        // Arrêter si on atteint un autre objet
        if (trimmed && !trimmed.startsWith('.') && !trimmed.startsWith('#') && trimmed.match(/^[A-Z]/)) {
            break;
        }
        // Trouver l'attribut à modifier
        const attrMatch = trimmed.match(new RegExp(`^\\.${key}\\s*=`));
        if (attrMatch) {
            const indent = line.match(/^(\s*)/)?.[1] || '  ';
            const formattedValue = value.includes(' ') && !value.startsWith('"') && !value.startsWith('V_') ? `"${value}"` : value;
            lines[i] = `${indent}.${key} = ${formattedValue}`;
            break;
        }
    }
    // Réécrire le fichier
    fs.writeFileSync(obj.source, lines.join('\n'));
    // Rafraîchir
    parseAllFiles();
    fractaleProvider.refresh();
    rulesProvider.refresh();
    updateCockpit();
}
async function addAttribute(lineage, key, value) {
    const obj = store.objects.get(lineage);
    if (!obj || !obj.source)
        return;
    // Vérifier si c'est une définition de vecteur V_xxx(type, default, desc)
    const vectorDefMatch = value.match(/^(V_[A-Za-z0-9_]+)\s*\((.+)\)$/);
    if (vectorDefMatch) {
        const [, vectorName, params] = vectorDefMatch;
        // Créer la définition du vecteur dans le même fichier
        const parts = params.split(',').map(p => p.trim());
        const vectorDef = `\nObject:Config:Vector:${vectorName}:\n  .name = "${vectorName}"\n  .type = "${parts[0] || 'string'}"\n  .default = ${parts[1] || '""'}\n  .description = ${parts[2] || '""'}\n`;
        // Ajouter la définition du vecteur au début du fichier (après les commentaires)
        const content = fs.readFileSync(obj.source, 'utf-8');
        const lines = content.split('\n');
        let insertAt = 0;
        for (let i = 0; i < lines.length; i++) {
            const trimmed = lines[i].trim();
            if (trimmed && !trimmed.startsWith('#') && !trimmed.startsWith('//')) {
                insertAt = i;
                break;
            }
            insertAt = i + 1;
        }
        lines.splice(insertAt, 0, vectorDef);
        fs.writeFileSync(obj.source, lines.join('\n'));
        // Mettre à jour la valeur pour référencer le vecteur
        value = vectorName;
    }
    // Lire le fichier
    const content = fs.readFileSync(obj.source, 'utf-8');
    const lines = content.split('\n');
    // Trouver la fin de l'objet pour ajouter l'attribut
    let insertLine = obj.line;
    for (let i = obj.line; i < lines.length; i++) {
        const trimmed = lines[i].trim();
        if (trimmed && !trimmed.startsWith('.') && !trimmed.startsWith('#') && trimmed.match(/^[A-Z]/)) {
            insertLine = i;
            break;
        }
        if (trimmed.startsWith('.')) {
            insertLine = i + 1;
        }
    }
    const formattedValue = value.includes(' ') && !value.startsWith('"') && !value.startsWith('V_') ? `"${value}"` : value;
    lines.splice(insertLine, 0, `  .${key} = ${formattedValue}`);
    // Réécrire le fichier
    fs.writeFileSync(obj.source, lines.join('\n'));
    // Rafraîchir
    parseAllFiles();
    fractaleProvider.refresh();
    rulesProvider.refresh();
    updateCockpit();
    vscode.window.showInformationMessage(`Attribut "${key}" ajouté`);
}
async function addMethod(lineage, name) {
    const obj = store.objects.get(lineage);
    if (!obj || !obj.source)
        return;
    // Créer la méthode comme sous-objet
    const methodLineage = `${lineage}:${name}Method`;
    const content = `\n${methodLineage}:\n  .name = "${name}"\n  .belongs_to = ${obj.name}\n`;
    fs.appendFileSync(obj.source, content);
    // Rafraîchir
    parseAllFiles();
    fractaleProvider.refresh();
    rulesProvider.refresh();
    updateCockpit();
    vscode.window.showInformationMessage(`Méthode "${name}" ajoutée`);
}
async function addRelation(lineage, type, target) {
    const obj = store.objects.get(lineage);
    if (!obj || !obj.source)
        return;
    // Lire le fichier
    const content = fs.readFileSync(obj.source, 'utf-8');
    const lines = content.split('\n');
    // Trouver la fin de l'objet pour ajouter la relation
    let insertLine = obj.line;
    for (let i = obj.line; i < lines.length; i++) {
        const trimmed = lines[i].trim();
        if (trimmed && !trimmed.startsWith('.') && !trimmed.startsWith('#') && trimmed.match(/^[A-Z]/)) {
            insertLine = i;
            break;
        }
        insertLine = i + 1;
    }
    lines.splice(insertLine, 0, `  ${obj.name} ${type} ${target}`);
    // Réécrire le fichier
    fs.writeFileSync(obj.source, lines.join('\n'));
    // Rafraîchir
    parseAllFiles();
    fractaleProvider.refresh();
    rulesProvider.refresh();
    updateCockpit();
    vscode.window.showInformationMessage(`Relation ajoutée`);
}
async function addRule(lineage, type, name) {
    const obj = store.objects.get(lineage);
    if (!obj || !obj.source)
        return;
    // Créer la règle
    const ruleLineage = `Object:Rule:${type}:${name}`;
    const content = `\n${ruleLineage}:\n  .name = "${name}"\n  .target = "${lineage}"\n  .type = "${type.replace('Rule', '').toLowerCase()}"\n`;
    // Ajouter dans un fichier rules si possible
    let targetFile = obj.source;
    if (vscode.workspace.workspaceFolders) {
        const folder = vscode.workspace.workspaceFolders[0].uri.fsPath;
        const rulesDir = path.join(folder, 'rules');
        if (fs.existsSync(rulesDir)) {
            targetFile = path.join(rulesDir, 'custom.r.gev');
            if (!fs.existsSync(targetFile)) {
                fs.writeFileSync(targetFile, '# EUREKAI Custom Rules\n\n');
            }
        }
    }
    fs.appendFileSync(targetFile, content);
    // Rafraîchir
    parseAllFiles();
    fractaleProvider.refresh();
    rulesProvider.refresh();
    updateCockpit();
    vscode.window.showInformationMessage(`Règle "${name}" ajoutée`);
}
async function moveObject(sourceLineage, targetLineage) {
    const sourceObj = store.objects.get(sourceLineage);
    if (!sourceObj || !sourceObj.source) {
        vscode.window.showErrorMessage('Objet source non trouvé');
        return;
    }
    // Extract object name from lineage
    const sourceName = sourceLineage.split(':').pop() || '';
    const newLineage = `${targetLineage}:${sourceName}`;
    // Check if target already has a child with this name
    if (store.objects.has(newLineage)) {
        vscode.window.showErrorMessage(`Un objet "${sourceName}" existe déjà sous "${targetLineage}"`);
        return;
    }
    // Read source file
    const content = fs.readFileSync(sourceObj.source, 'utf-8');
    const lines = content.split('\n');
    // Find and update the lineage declaration
    const startLine = sourceObj.line - 1;
    const oldDeclaration = lines[startLine];
    // Create new declaration with updated lineage
    const newDeclaration = oldDeclaration.replace(sourceLineage + ':', newLineage + ':');
    lines[startLine] = newDeclaration;
    // Also update any child objects that reference this lineage
    for (let i = 0; i < lines.length; i++) {
        if (i !== startLine && lines[i].includes(sourceLineage + ':')) {
            lines[i] = lines[i].replace(sourceLineage + ':', newLineage + ':');
        }
    }
    // Write back
    fs.writeFileSync(sourceObj.source, lines.join('\n'));
    // Rafraîchir
    parseAllFiles();
    fractaleProvider.refresh();
    rulesProvider.refresh();
    updateCockpit();
    vscode.window.showInformationMessage(`"${sourceName}" déplacé vers "${targetLineage}"`);
}
let pythonServerProcess = null;
async function togglePythonServer() {
    if (pythonServerProcess) {
        // Stop server
        pythonServerProcess.kill();
        pythonServerProcess = null;
        vscode.window.showInformationMessage('Serveur Python arrêté');
    }
    else {
        // Start server
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('Aucun dossier de travail ouvert');
            return;
        }
        // Look for server.py in the workspace or parent directories
        let serverPath = path.join(workspaceFolder, 'server.py');
        if (!fs.existsSync(serverPath)) {
            serverPath = path.join(workspaceFolder, '..', 'server.py');
        }
        if (!fs.existsSync(serverPath)) {
            serverPath = path.join(workspaceFolder, 'eurekai-core', 'server.py');
        }
        if (!fs.existsSync(serverPath)) {
            vscode.window.showErrorMessage('server.py non trouvé. Placez-le dans le dossier du projet.');
            return;
        }
        const { spawn } = require('child_process');
        pythonServerProcess = spawn('python3', [serverPath, workspaceFolder], {
            cwd: path.dirname(serverPath)
        });
        pythonServerProcess.stdout.on('data', (data) => {
            console.log('Python server:', data.toString());
        });
        pythonServerProcess.stderr.on('data', (data) => {
            console.error('Python server error:', data.toString());
        });
        pythonServerProcess.on('close', (code) => {
            console.log('Python server exited with code', code);
            pythonServerProcess = null;
        });
        vscode.window.showInformationMessage('Serveur Python démarré sur http://localhost:5000');
    }
}
function updateCockpit() {
    if (!cockpitPanel)
        return;
    const objects = Array.from(store.objects.values()).map(o => ({
        lineage: o.lineage,
        name: o.name,
        parent: o.parent,
        attributes: o.attributes,
        source: o.source,
        line: o.line
    }));
    const vectors = Array.from(store.vectors.entries()).map(([name, obj]) => ({
        name,
        lineage: obj.lineage,
        attributes: obj.attributes
    }));
    const rules = store.rules.map(r => ({
        lineage: r.lineage,
        name: r.name,
        attributes: r.attributes
    }));
    // Get unique source files
    const sourceFiles = [...new Set(objects.map(o => o.source).filter(Boolean))];
    // Get project name from workspace
    const projectName = vscode.workspace.workspaceFolders?.[0]?.name || 'Sans projet';
    cockpitPanel.webview.html = getCockpitHtml(objects, vectors, rules, sourceFiles, projectName);
}
function executeQuery(query) {
    const results = [];
    let message = '';
    // Parse command
    const readMatch = query.match(/^read\s+(\w+)(?:\.(.+))?(?:\s+--(\w+))?/);
    const resolveMatch = query.match(/^resolve\s+(V_\w+)/);
    const treeMatch = query.match(/^tree(?:\s+(\d+))?/);
    const statsMatch = query.match(/^stats/);
    const helpMatch = query.match(/^help/);
    if (helpMatch) {
        message = `SuperRead Commands:
  read <Type>              - List all objects of type
  read <Type>.attr=value   - Filter by attribute
  read <Type>.attr>value   - Filter by comparison
  resolve <V_xxx>          - Resolve vector value
  tree [depth]             - Show object tree
  stats                    - Show statistics
  
Examples:
  read Agent
  read Agent.role=architect
  read Entity.name~Main
  resolve V_Temperature`;
    }
    else if (statsMatch) {
        message = `Statistics:
  Objects: ${store.objects.size}
  Vectors: ${store.vectors.size}
  Rules: ${store.rules.length}`;
    }
    else if (treeMatch) {
        const depth = parseInt(treeMatch[1] || '3');
        message = buildTreeText('Object', 0, depth);
    }
    else if (resolveMatch) {
        const vectorName = resolveMatch[1];
        const resolved = resolveVector(vectorName);
        message = `${vectorName} => ${resolved !== null ? resolved : '(not found)'}`;
    }
    else if (readMatch) {
        const [, type, conditions] = readMatch;
        for (const [lineage, obj] of store.objects) {
            if (lineage.includes(`:${type}`) || lineage.endsWith(`:${type}`) || obj.name === type) {
                if (!conditions) {
                    results.push({ lineage: obj.lineage, name: obj.name, attributes: obj.attributes });
                }
                else {
                    // Parse conditions
                    const eqMatch = conditions.match(/(\w+)=(.+)/);
                    const gtMatch = conditions.match(/(\w+)>(.+)/);
                    const ltMatch = conditions.match(/(\w+)<(.+)/);
                    const containsMatch = conditions.match(/(\w+)~(.+)/);
                    let match = false;
                    const attrs = obj.attributes;
                    if (eqMatch) {
                        const [, attr, value] = eqMatch;
                        const objVal = attrs[attr]?.replace(/"/g, '');
                        match = objVal === value;
                    }
                    else if (gtMatch) {
                        const [, attr, value] = gtMatch;
                        const objVal = parseFloat(attrs[attr] || '0');
                        match = objVal > parseFloat(value);
                    }
                    else if (ltMatch) {
                        const [, attr, value] = ltMatch;
                        const objVal = parseFloat(attrs[attr] || '0');
                        match = objVal < parseFloat(value);
                    }
                    else if (containsMatch) {
                        const [, attr, value] = containsMatch;
                        const objVal = attrs[attr]?.replace(/"/g, '') || '';
                        match = objVal.toLowerCase().includes(value.toLowerCase());
                    }
                    if (match) {
                        results.push({ lineage: obj.lineage, name: obj.name, attributes: obj.attributes });
                    }
                }
            }
        }
        message = results.length > 0 ? '' : 'No results found';
    }
    else {
        message = `Unknown command: ${query}\nType 'help' for available commands`;
    }
    cockpitPanel?.webview.postMessage({ type: 'queryResult', query, results, message });
}
function buildTreeText(lineage, indent, maxDepth) {
    if (indent > maxDepth)
        return '';
    const obj = store.objects.get(lineage);
    const name = obj?.name || lineage.split(':').pop() || lineage;
    const prefix = '  '.repeat(indent) + (indent > 0 ? '├── ' : '');
    let text = prefix + name + '\n';
    const children = getChildren(lineage);
    for (const child of children) {
        text += buildTreeText(child, indent + 1, maxDepth);
    }
    return text;
}
function getCockpitHtml(objects, vectors, rules, sourceFiles = [], projectName = 'Sans projet') {
    const treeData = buildTreeData();
    // Préparer la liste des fichiers pour le HTML
    const filesHtml = sourceFiles.map(f => {
        const fileName = f.split('/').pop() || f;
        return `<div class="file-item" data-path="${f}" onclick="openFile('${f}')">${fileName}</div>`;
    }).join('');
    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #1a1a2e; color: #eee; height: 100vh; display: flex; flex-direction: column;
    }
    
    /* Header avec tabs */
    .header { background: #16213e; border-bottom: 1px solid #0f3460; display: flex; align-items: center; }
    .logo { padding: 12px 16px; color: #e94560; font-weight: bold; display: flex; align-items: center; gap: 8px; }
    .logo::before { content: '◆'; }
    .project-name { color: #888; font-weight: normal; font-size: 12px; margin-left: 8px; }
    .tabs { display: flex; flex: 1; }
    .tab { 
      padding: 12px 20px; cursor: pointer; border-bottom: 2px solid transparent;
      color: #888; transition: all 0.2s;
    }
    .tab:hover { color: #eee; background: rgba(255,255,255,0.05); }
    .tab.active { color: #e94560; border-bottom-color: #e94560; }
    .version { padding: 12px 16px; color: #666; font-size: 12px; }
    
    /* Main layout */
    .main { display: flex; flex: 1; overflow: hidden; }
    
    /* Sidebar - Tree */
    .sidebar { 
      width: 280px; background: #16213e; border-right: 1px solid #0f3460;
      display: flex; flex-direction: column; overflow: hidden;
    }
    .sidebar-header { 
      padding: 12px; border-bottom: 1px solid #0f3460; 
      display: flex; justify-content: space-between; align-items: center;
    }
    .sidebar-title { font-size: 11px; text-transform: uppercase; color: #888; letter-spacing: 1px; }
    .object-count { 
      background: #e94560; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;
    }
    .search { padding: 8px 12px; }
    .search input { 
      width: 100%; padding: 8px 12px; background: #1a1a2e; border: 1px solid #0f3460;
      border-radius: 4px; color: #eee; font-size: 13px;
    }
    .search input:focus { outline: none; border-color: #e94560; }
    .search input::placeholder { color: #666; }
    .tree { flex: 1; overflow-y: auto; padding: 8px; }
    
    /* Files section */
    .files-section { border-top: 1px solid #0f3460; padding: 8px; max-height: 150px; overflow-y: auto; }
    .files-title { font-size: 10px; text-transform: uppercase; color: #666; margin-bottom: 6px; }
    .file-item { 
      padding: 4px 8px; font-size: 11px; color: #888; cursor: pointer; 
      border-radius: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .file-item:hover { background: rgba(233, 69, 96, 0.1); color: #e94560; }
    
    /* Tree nodes */
    .tree ul { list-style: none; padding-left: 16px; }
    .tree > ul { padding-left: 0; }
    .tree-node { 
      padding: 6px 8px; cursor: pointer; border-radius: 4px; 
      display: flex; align-items: center; gap: 6px; margin: 2px 0;
    }
    .tree-node:hover { background: rgba(233, 69, 96, 0.1); }
    .tree-node.selected { background: #e94560; }
    .tree-node .icon { width: 16px; text-align: center; }
    .tree-node .name { flex: 1; }
    .tree-node .count { color: #666; font-size: 11px; }
    .tree-toggle { width: 16px; cursor: pointer; color: #666; }
    
    /* Content area */
    .content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
    
    /* Tab panels */
    .tab-panel { display: none; flex: 1; overflow: auto; }
    .tab-panel.active { display: flex; flex-direction: column; }
    
    /* Explorer panel */
    .explorer { padding: 20px; }
    .explorer-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .explorer-title { font-size: 18px; color: #888; }
    
    /* Object detail */
    .object-detail { background: #16213e; border-radius: 8px; padding: 20px; }
    .object-detail h2 { color: #e94560; margin-bottom: 8px; }
    .object-lineage { color: #666; font-family: monospace; font-size: 13px; margin-bottom: 20px; }
    .attrs-table { width: 100%; border-collapse: collapse; }
    .attrs-table th, .attrs-table td { 
      padding: 10px 12px; text-align: left; border-bottom: 1px solid #0f3460;
    }
    .attrs-table th { color: #e94560; width: 200px; }
    .attrs-table td { font-family: monospace; }
    .attrs-table tr:hover { background: rgba(255,255,255,0.02); }
    
    /* Goto button */
    .goto-btn {
      padding: 8px 16px; margin-bottom: 16px; background: #0f3460; border: 1px solid #e94560;
      color: #e94560; border-radius: 4px; cursor: pointer; font-size: 12px;
    }
    .goto-btn:hover { background: #e94560; color: white; }
    
    /* Form styles */
    .form-group { margin-bottom: 16px; }
    .form-group label { display: block; color: #888; font-size: 12px; margin-bottom: 6px; text-transform: uppercase; }
    .form-input {
      width: 100%; padding: 10px 12px; background: #1a1a2e; border: 1px solid #0f3460;
      border-radius: 4px; color: #eee; font-size: 14px;
    }
    .form-input:focus { outline: none; border-color: #e94560; }
    .attr-row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
    .attr-row input { flex: 1; padding: 8px; background: #1a1a2e; border: 1px solid #0f3460; border-radius: 4px; color: #eee; }
    .attr-row span { color: #e94560; }
    .method-row, .relation-row, .rule-row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
    .method-row input, .relation-row input, .rule-row input { flex: 1; padding: 8px; background: #1a1a2e; border: 1px solid #0f3460; border-radius: 4px; color: #eee; }
    .relation-row select, .rule-row select { padding: 8px; background: #1a1a2e; border: 1px solid #0f3460; border-radius: 4px; color: #eee; }
    .create-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .btn-small { padding: 8px 12px; background: #0f3460; border: none; color: #e94560; border-radius: 4px; cursor: pointer; }
    .btn-small:hover { background: #1a3a6e; }
    .btn-primary { padding: 12px 24px; background: #e94560; border: none; color: white; border-radius: 6px; cursor: pointer; font-weight: 500; }
    .btn-primary:hover { background: #c73e54; }
    
    /* GEVR Pipeline Builder */
    .gevr-builder { display: flex; align-items: stretch; gap: 8px; flex-wrap: wrap; }
    .gevr-step-input { 
      flex: 1; min-width: 160px; background: #16213e; border-radius: 8px; padding: 12px;
      border: 1px solid #0f3460; transition: all 0.3s;
    }
    .gevr-step-input:focus-within { border-color: #e94560; }
    .gevr-step-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
    .gevr-step-header .gevr-icon { font-size: 18px; }
    .gevr-step-header .gevr-title { color: #e94560; font-weight: bold; font-size: 13px; }
    .gevr-step-header .gevr-hint { color: #666; font-size: 10px; margin-left: auto; }
    .gevr-method-input { 
      width: 100%; padding: 8px; background: #1a1a2e; border: 1px solid #0f3460; 
      border-radius: 4px; color: #eee; font-family: monospace; font-size: 11px;
    }
    .gevr-method-input:focus { outline: none; border-color: #e94560; }
    .gevr-arrow { color: #e94560; font-size: 20px; padding-top: 35px; }
    .btn-secondary { 
      padding: 12px 24px; background: #0f3460; border: none; 
      border-radius: 6px; color: #888; cursor: pointer;
    }
    .btn-secondary:hover { color: #eee; background: #1a3a6e; }
    
    /* Console panel */
    .console-panel { padding: 20px; display: flex; flex-direction: column; gap: 12px; height: 100%; }
    .console-input { display: flex; gap: 12px; }
    .console-input input { 
      flex: 1; padding: 12px 16px; background: #16213e; border: 1px solid #0f3460;
      border-radius: 6px; color: #eee; font-family: monospace;
    }
    .console-input input:focus { border-color: #e94560; outline: none; }
    .console-input button { 
      padding: 12px 24px; background: #e94560; border: none; border-radius: 6px;
      color: white; cursor: pointer; font-weight: 500;
    }
    .console-input button:hover { background: #c73e54; }
    .console-history { display: flex; gap: 8px; flex-wrap: wrap; }
    .history-item {
      padding: 4px 10px; background: #0f3460; border-radius: 4px; font-size: 11px;
      color: #888; cursor: pointer; font-family: monospace;
    }
    .history-item:hover { background: #16213e; color: #e94560; }
    .console-actions { display: flex; gap: 8px; }
    .console-btn {
      padding: 6px 12px; background: #16213e; border: 1px solid #0f3460;
      border-radius: 4px; color: #888; cursor: pointer; font-size: 12px;
    }
    .console-btn:hover { border-color: #e94560; color: #e94560; }
    .console-output { 
      flex: 1; background: #0d0d1a; border-radius: 6px; padding: 16px;
      font-family: monospace; font-size: 13px; overflow: auto; white-space: pre-wrap;
      min-height: 300px;
    }
    
    /* Stats */
    .stats { display: flex; gap: 16px; margin-bottom: 20px; }
    .stat { 
      background: #16213e; padding: 16px 24px; border-radius: 8px; text-align: center;
    }
    .stat-value { font-size: 28px; font-weight: bold; color: #e94560; }
    .stat-label { color: #888; font-size: 12px; margin-top: 4px; }
    
    /* Tags sidebar */
    .tags-sidebar { 
      width: 200px; background: #16213e; border-left: 1px solid #0f3460; padding: 16px;
    }
    .tags-title { font-size: 11px; text-transform: uppercase; color: #888; margin-bottom: 12px; }
    
    /* Empty state */
    .empty-state { 
      flex: 1; display: flex; flex-direction: column; align-items: center; 
      justify-content: center; color: #666;
    }
    .empty-state .icon { font-size: 48px; margin-bottom: 16px; opacity: 0.3; }
    
    /* Legend */
    .legend { 
      padding: 12px; border-top: 1px solid #0f3460; display: flex; gap: 16px;
      font-size: 11px; color: #666;
    }
    .legend-item { display: flex; align-items: center; gap: 6px; }
    .legend-dot { width: 8px; height: 8px; border-radius: 50%; }
    .legend-dot.owned { background: #888; }
    .legend-dot.inherited { background: #3b82f6; }
    .legend-dot.injected { background: #22c55e; }
    
    /* Server status */
    .server-status { 
      padding: 4px 10px; border-radius: 4px; font-size: 11px; margin-right: 8px;
    }
    .server-status.connected { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
    .server-status.disconnected { background: rgba(136, 136, 136, 0.2); color: #888; }
    
    /* Server button */
    .server-btn {
      padding: 6px 12px; background: #0f3460; border: 1px solid #0f3460;
      border-radius: 4px; color: #888; cursor: pointer; font-size: 11px; margin-right: 8px;
    }
    .server-btn:hover { border-color: #22c55e; color: #22c55e; }
    .server-btn.running { background: rgba(34, 197, 94, 0.2); color: #22c55e; border-color: #22c55e; }
    
    /* Object detail panel */
    .object-header { display: flex; justify-content: space-between; align-items: center; }
    .object-header h2 { color: #e94560; margin: 0; }
    .object-actions { display: flex; gap: 8px; }
    .action-btn { 
      background: transparent; border: 1px solid #0f3460; border-radius: 4px;
      padding: 4px 8px; cursor: pointer; font-size: 14px;
    }
    .action-btn:hover { border-color: #e94560; }
    .object-lineage { color: #666; font-family: monospace; font-size: 12px; margin: 8px 0; }
    .object-source { color: #888; font-size: 11px; margin-bottom: 16px; }
    
    /* Sections accordéon */
    .section { margin-top: 8px; padding-top: 8px; border-top: 1px solid #0f3460; }
    .section.accordion .section-content { display: none; padding-top: 8px; }
    .section.accordion.open .section-content { display: block; }
    .section-header { 
      display: flex; align-items: center; gap: 8px;
      cursor: pointer; user-select: none;
    }
    .section-header span { font-size: 12px; text-transform: uppercase; color: #888; }
    .accordion-toggle { color: #666; font-size: 10px; width: 12px; transition: transform 0.2s; }
    .section.accordion.open .accordion-toggle { transform: rotate(90deg); }
    .add-btn { 
      background: transparent; border: 1px solid #0f3460; border-radius: 4px;
      padding: 2px 8px; color: #888; cursor: pointer; font-size: 11px; margin-left: auto;
    }
    .add-btn:hover { border-color: #22c55e; color: #22c55e; }
    .empty { color: #666; font-style: italic; font-size: 12px; margin: 0; }
    
    /* Attributes table */
    .attrs-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .attrs-table th, .attrs-table td { padding: 8px; text-align: left; border-bottom: 1px solid #0f3460; }
    .attrs-table th { color: #888; font-weight: normal; width: 30%; }
    .attrs-table td { font-family: monospace; }
    .attrs-table tr.owned td { color: #22c55e; }
    .attrs-table tr.inherited td { color: #3b82f6; }
    .edit-btn { 
      background: transparent; border: none; color: #666; cursor: pointer; 
      padding: 0 4px; margin-left: 8px; opacity: 0; transition: opacity 0.2s;
    }
    .attrs-table tr:hover .edit-btn { opacity: 1; }
    .edit-btn:hover { color: #e94560; }
    .edit-input { 
      background: #1a1a2e; border: 1px solid #e94560; border-radius: 4px;
      padding: 4px 8px; color: #eee; font-family: monospace; width: 80%;
    }
    .from { color: #666; font-size: 11px; font-style: italic; }
    
    /* Methods, Relations, Rules items */
    .method-item, .relation-item, .rule-item, .hook-item {
      padding: 6px 0; font-size: 13px; color: #888;
    }
    .method-item.owned { color: #22c55e; }
    .method-item.inherited { color: #3b82f6; }
    .rule-group { margin-bottom: 12px; }
    .rule-group strong { color: #e94560; font-size: 12px; }
    .rule-item { padding-left: 12px; }
    
    /* Clickable elements */
    .clickable { cursor: pointer; }
    .clickable:hover { color: #e94560; text-decoration: underline; }
    
    /* Source tags inline */
    .source-tag { 
      font-size: 10px; color: #666; margin-left: 8px; font-style: italic;
    }
    .source-tag:hover { color: #e94560; }
    
    /* Item colors by source */
    .attrs-table tr.owned td, .attrs-table tr.owned th { color: #eee; }
    .attrs-table tr.inherited td, .attrs-table tr.inherited th { color: #3b82f6; }
    .attrs-table tr.inherited .source-tag { color: #3b82f6; }
    .attrs-table tr.injected td, .attrs-table tr.injected th { color: #22c55e; }
    .method-item.owned { color: #eee; }
    .method-item.inherited { color: #3b82f6; }
    .method-item.inherited .source-tag { color: #3b82f6; }
    .method-item.injected { color: #22c55e; }
    
    /* Drag & drop */
    .tree-node.dragging { opacity: 0.5; }
    .tree-node.drag-over { 
      background: rgba(233, 69, 96, 0.2); 
      border-radius: 4px;
    }
    
    /* Modal */
    .modal-overlay {
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.7); display: flex; 
      align-items: center; justify-content: center; z-index: 1000;
    }
    .modal {
      background: #16213e; border-radius: 8px; padding: 24px;
      min-width: 400px; border: 1px solid #0f3460;
    }
    .modal h3 { color: #e94560; margin: 0 0 20px 0; }
    .modal .form-group { margin-bottom: 16px; }
    .modal .form-group label { display: block; color: #888; font-size: 12px; margin-bottom: 6px; }
    .modal .form-group input, .modal .form-group select {
      width: 100%; padding: 10px; background: #1a1a2e; 
      border: 1px solid #0f3460; border-radius: 4px; color: #eee;
    }
    .modal .form-group input:focus, .modal .form-group select:focus {
      outline: none; border-color: #e94560;
    }
    .modal-actions { display: flex; gap: 12px; justify-content: flex-end; margin-top: 20px; }
    .btn-secondary { 
      padding: 8px 16px; background: #0f3460; border: none; 
      border-radius: 4px; color: #888; cursor: pointer;
    }
    .btn-primary { 
      padding: 8px 16px; background: #e94560; border: none; 
      border-radius: 4px; color: white; cursor: pointer;
    }
    .btn-secondary:hover { color: #eee; }
    .btn-primary:hover { background: #c73e54; }
  </style>
</head>
<body>
  <div class="header">
    <div class="logo">EUREKAI Cockpit <span class="project-name">— ${projectName}</span></div>
    <div class="tabs">
      <div class="tab active" data-tab="explorer">◦ Explorer</div>
      <div class="tab" data-tab="create">+ Créer</div>
      <div class="tab" data-tab="console">✦ Console</div>
      <div class="tab" data-tab="gevr">⟡ GEVR</div>
      <div class="tab" data-tab="json">{} JSON</div>
    </div>
    <button class="server-btn" id="serverBtn" onclick="toggleServer()">▶ Python</button>
    <button class="server-btn" id="browserBtn" onclick="openInBrowser()" title="Ouvrir dans Chrome">🌐</button>
    <div class="server-status disconnected" id="serverStatus">○ Local JS</div>
    <div class="version">v51</div>
  </div>
  
  <div class="main">
    <div class="sidebar">
      <div class="sidebar-header">
        <span class="sidebar-title">OBJECTS</span>
        <span class="object-count">${objects.length}</span>
      </div>
      <div class="search">
        <input type="text" id="searchInput" placeholder="Rechercher..." onfocus="this.value=''">
      </div>
      <div class="tree" id="tree"></div>
      <div class="files-section">
        <div class="files-title">Fichiers (${sourceFiles.length})</div>
        ${filesHtml}
      </div>
      <div class="legend">
        <div class="legend-item"><span class="legend-dot owned"></span> owned</div>
        <div class="legend-item"><span class="legend-dot inherited"></span> inherited</div>
        <div class="legend-item"><span class="legend-dot injected"></span> injected</div>
      </div>
    </div>
    
    <div class="content">
      <!-- Explorer Tab -->
      <div class="tab-panel active" id="panel-explorer">
        <div class="explorer">
          <div class="stats">
            <div class="stat">
              <div class="stat-value">${objects.length}</div>
              <div class="stat-label">Objets</div>
            </div>
            <div class="stat">
              <div class="stat-value">${vectors.length}</div>
              <div class="stat-label">Vecteurs</div>
            </div>
            <div class="stat">
              <div class="stat-value">${rules.length}</div>
              <div class="stat-label">Rules</div>
            </div>
          </div>
          <div class="object-detail" id="objectDetail">
            <div class="empty-state">
              <div class="icon">◇</div>
              <div>Sélectionnez un objet dans l'arbre</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Create Tab -->
      <div class="tab-panel" id="panel-create">
        <div class="explorer" style="max-width: 700px;">
          <h2 style="color: #e94560; margin-bottom: 20px;">Créer un objet</h2>
          
          <div class="create-grid">
            <div class="form-group">
              <label>Parent</label>
              <select id="createParent" class="form-input">
                <option value="Object">Object (racine)</option>
                ${Array.from(new Set(objects.map((o) => o.lineage))).map((l) => `<option value="${l}">${l.split(':').pop()} (${l})</option>`).join('')}
              </select>
            </div>
            
            <div class="form-group">
              <label>Nom de l'objet</label>
              <input type="text" id="createName" class="form-input" placeholder="MonNouvelObjet">
            </div>
          </div>
          
          <div class="form-group">
            <label>Attributs</label>
            <div id="attributesList">
              <div class="attr-row">
                <input type="text" placeholder="name" class="attr-key">
                <span>=</span>
                <input type="text" placeholder="valeur ou V_xxx(type, default, desc)" class="attr-value">
                <button class="btn-small" onclick="addAttrRow()">+</button>
              </div>
            </div>
          </div>
          
          <div class="form-group">
            <label>Méthodes</label>
            <div id="methodsList">
              <div class="method-row">
                <input type="text" placeholder="nomMethode" class="method-name" onfocus="this.select()">
                <button class="btn-small" onclick="addMethodRow()">+</button>
              </div>
            </div>
          </div>
          
          <div class="form-group">
            <label>Relations</label>
            <div id="relationsList">
              <div class="relation-row">
                <select class="relation-type">
                  <option value="depends_on">depends_on</option>
                  <option value="related_to">related_to</option>
                  
                </select>
                <input type="text" placeholder="Object:Type:Name" class="relation-target" onfocus="this.select()">
                <button class="btn-small" onclick="addRelationRow()">+</button>
              </div>
            </div>
          </div>
          
          <div class="form-group">
            <label>Règles</label>
            <div id="rulesList">
              <div class="rule-row">
                <select class="rule-type">
                  <option value="ValidationRule">ValidationRule</option>
                  <option value="CreateRule">CreateRule</option>
                  <option value="ReadRule">ReadRule</option>
                  <option value="UpdateRule">UpdateRule</option>
                  <option value="DeleteRule">DeleteRule</option>
                </select>
                <input type="text" placeholder="NomDeLaRegle" class="rule-name" onfocus="this.select()">
                <button class="btn-small" onclick="addRuleRow()">+</button>
              </div>
            </div>
          </div>
          
          <button class="btn-primary" onclick="createObject()">Créer l'objet</button>
        </div>
      </div>
      
      <!-- Console Tab -->
      <div class="tab-panel" id="panel-console">
        <div class="console-panel">
          <div class="console-input">
            <input type="text" id="queryInput" placeholder="Tapez une commande... (help pour l'aide)" onfocus="this.value=''">
            <button onclick="executeQuery()">Exécuter</button>
          </div>
          <div class="console-actions">
            <button class="console-btn" onclick="copyOutput()">📋 Copier</button>
            <button class="console-btn" onclick="exportOutput()">💾 Exporter</button>
            <button class="console-btn" onclick="clearOutput()">🗑 Effacer</button>
          </div>
          <div class="console-output" id="consoleOutput">// Tapez 'help' pour voir les commandes disponibles</div>
        </div>
      </div>
      
      <!-- GEVR Tab -->
      <div class="tab-panel" id="panel-gevr">
        <div class="explorer" style="max-width: 900px;">
          <h2 style="color: #e94560; margin-bottom: 10px;">GEVR Pipeline Builder</h2>
          <p style="color: #888; font-size: 12px; margin-bottom: 16px;">Créez un Scenario GEVR. Utilisez Method:xxx, @methodName ou V_xxx(type, default, desc).</p>
          
          <div class="gevr-scenario-name" style="margin-bottom: 16px;">
            <label style="color: #888; font-size: 12px;">Nom du Scenario (facultatif pour tester)</label>
            <input type="text" id="scenarioName" class="form-input" placeholder="MonScenario" style="margin-top: 6px;" onfocus="this.select()">
          </div>
          
          <div class="gevr-builder">
            <div class="gevr-step-input" id="gevr-get">
              <div class="gevr-step-header">
                <span class="gevr-icon">📥</span>
                <span class="gevr-title">GET</span>
              </div>
              <input type="text" class="gevr-method-input" id="getMethod" 
                placeholder="Method:GetData ou @getData" 
                list="methodsList" onfocus="this.select()">
            </div>
            
            <div class="gevr-arrow">→</div>
            
            <div class="gevr-step-input" id="gevr-execute">
              <div class="gevr-step-header">
                <span class="gevr-icon">⚡</span>
                <span class="gevr-title">EXECUTE</span>
              </div>
              <input type="text" class="gevr-method-input" id="executeMethod" 
                placeholder="Method:Process" 
                list="methodsList" onfocus="this.select()">
            </div>
            
            <div class="gevr-arrow">→</div>
            
            <div class="gevr-step-input" id="gevr-validate">
              <div class="gevr-step-header">
                <span class="gevr-icon">✓</span>
                <span class="gevr-title">VALIDATE</span>
              </div>
              <input type="text" class="gevr-method-input" id="validateMethod" 
                placeholder="Method:Validate" 
                list="methodsList" onfocus="this.select()">
            </div>
            
            <div class="gevr-arrow">→</div>
            
            <div class="gevr-step-input" id="gevr-render">
              <div class="gevr-step-header">
                <span class="gevr-icon">🎨</span>
                <span class="gevr-title">RENDER</span>
              </div>
              <input type="text" class="gevr-method-input" id="renderMethod" 
                placeholder="Method:Render" 
                list="methodsList" onfocus="this.select()">
            </div>
          </div>
          
          <datalist id="methodsList">
            ${objects.filter((o) => o.lineage.includes(':Method:')).map((o) => `<option value="Method:${o.name}">`).join('')}
          </datalist>
          
          <div style="display: flex; gap: 12px; margin-top: 20px;">
            <button class="btn-primary" onclick="createScenario()">Créer le Scenario</button>
            <button class="btn-secondary" onclick="testGevr()">Tester (aperçu)</button>
          </div>
          
          <div class="gevr-results" style="display: flex; gap: 16px; margin-top: 20px;">
            <div class="gevr-preview" id="gevrPreview" style="flex: 1; display: none;">
              <div class="gevr-preview-title" style="color: #888; font-size: 11px; margin-bottom: 8px;">APERÇU CODE</div>
              <pre id="gevrCode" style="background: #0d0d1a; padding: 12px; border-radius: 4px; font-size: 11px; color: #888; max-height: 200px; overflow: auto;"></pre>
            </div>
            <div class="gevr-output" id="gevrOutput" style="flex: 1; display: none;">
              <div class="gevr-output-title" style="color: #888; font-size: 11px; margin-bottom: 8px;">RÉSULTAT TEST</div>
              <pre id="gevrResult" style="background: #0d0d1a; padding: 12px; border-radius: 4px; font-size: 11px; color: #22c55e; max-height: 200px; overflow: auto;"></pre>
            </div>
          </div>
        </div>
      </div>
      
      <!-- JSON Tab -->
      <div class="tab-panel" id="panel-json">
        <div class="console-panel">
          <div class="console-output" id="jsonOutput">${JSON.stringify(objects.slice(0, 10), null, 2)}</div>
        </div>
      </div>
    </div>
    
    <div class="tags-sidebar">
      <div class="tags-title">TAGS</div>
      <div style="color: #666; font-size: 13px;">Aucun tag</div>
    </div>
  </div>
  
  <script>
    const vscode = acquireVsCodeApi();
    const objects = ${JSON.stringify(objects)};
    const treeData = ${JSON.stringify(treeData)};
    
    // Tabs
    document.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
      });
    });
    
    // Drag & drop state
    let draggedLineage = null;
    
    // Tree rendering - closed by default
    function renderTree(node, container, level = 0) {
      const li = document.createElement('li');
      const hasChildren = node.children && node.children.length > 0;
      
      const nodeEl = document.createElement('div');
      nodeEl.className = 'tree-node';
      nodeEl.draggable = true;
      nodeEl.dataset.lineage = node.lineage;
      nodeEl.innerHTML = \`
        <span class="tree-toggle">\${hasChildren ? '▶' : ''}</span>
        <span class="icon">◇</span>
        <span class="name">\${node.name}</span>
        \${hasChildren ? \`<span class="count">(\${node.children.length})</span>\` : ''}
      \`;
      
      // Toggle handler (on the arrow only)
      const toggle = nodeEl.querySelector('.tree-toggle');
      if (hasChildren) {
        toggle.addEventListener('click', (e) => {
          e.stopPropagation();
          const ul = li.querySelector(':scope > ul');
          if (ul) {
            const isOpen = ul.style.display !== 'none';
            ul.style.display = isOpen ? 'none' : 'block';
            toggle.textContent = isOpen ? '▶' : '▼';
            
            // If closing, also close all children
            if (isOpen) {
              ul.querySelectorAll('ul').forEach(childUl => childUl.style.display = 'none');
              ul.querySelectorAll('.tree-toggle').forEach(t => { if (t.textContent === '▼') t.textContent = '▶'; });
            }
          }
        });
      }
      
      // Click handler (select object + fill parent in Create tab)
      nodeEl.addEventListener('click', (e) => {
        e.stopPropagation();
        document.querySelectorAll('.tree-node').forEach(n => n.classList.remove('selected'));
        nodeEl.classList.add('selected');
        selectObject(node.lineage);
        
        // Also update parent select in Create tab
        const parentSelect = document.getElementById('createParent');
        if (parentSelect) {
          parentSelect.value = node.lineage;
        }
      });
      
      // Drag start
      nodeEl.addEventListener('dragstart', (e) => {
        draggedLineage = node.lineage;
        nodeEl.classList.add('dragging');
        e.dataTransfer.setData('text/plain', node.lineage);
        e.dataTransfer.effectAllowed = 'move';
      });
      
      // Drag end
      nodeEl.addEventListener('dragend', () => {
        nodeEl.classList.remove('dragging');
        document.querySelectorAll('.tree-node').forEach(n => n.classList.remove('drag-over'));
        draggedLineage = null;
      });
      
      // Drag over
      nodeEl.addEventListener('dragover', (e) => {
        e.preventDefault();
        if (draggedLineage && draggedLineage !== node.lineage) {
          nodeEl.classList.add('drag-over');
        }
      });
      
      // Drag leave
      nodeEl.addEventListener('dragleave', () => {
        nodeEl.classList.remove('drag-over');
      });
      
      // Drop
      nodeEl.addEventListener('drop', (e) => {
        e.preventDefault();
        nodeEl.classList.remove('drag-over');
        
        if (draggedLineage && draggedLineage !== node.lineage) {
          // Don't allow dropping on a child of the dragged element
          if (node.lineage.startsWith(draggedLineage + ':')) {
            return;
          }
          
          vscode.postMessage({
            command: 'moveObject',
            sourceLineage: draggedLineage,
            targetLineage: node.lineage
          });
        }
      });
      
      li.appendChild(nodeEl);
      
      if (hasChildren) {
        const ul = document.createElement('ul');
        ul.style.display = 'none'; // Closed by default
        node.children.forEach(child => renderTree(child, ul, level + 1));
        li.appendChild(ul);
      }
      
      container.appendChild(li);
    }
    
    // Init tree
    const treeContainer = document.getElementById('tree');
    const ul = document.createElement('ul');
    renderTree(treeData, ul, 0);
    treeContainer.appendChild(ul);
    // Open first level
    const firstUl = treeContainer.querySelector('ul > li > ul');
    if (firstUl) {
      firstUl.style.display = 'block';
      const firstToggle = treeContainer.querySelector('ul > li > .tree-node .tree-toggle');
      if (firstToggle) firstToggle.textContent = '▼';
    }
    
    // Select object - simple clic = afficher détails, double-clic = ouvrir fichier
    function selectObject(lineage) {
      const obj = objects.find(o => o.lineage === lineage);
      const detail = document.getElementById('objectDetail');
      
      if (obj) {
        // Helper to strip quotes
        const stripQuotes = (v) => {
          if (typeof v === 'string' && v.startsWith('"') && v.endsWith('"')) {
            return v.slice(1, -1);
          }
          return v;
        };
        
        // Get inherited attributes from parent chain with source tracking
        const attrsBySource = {};  // {sourceName: [{key, value, sourceLineage}]}
        const owned = obj.attributes || {};
        
        // Add owned attributes first
        attrsBySource['owned'] = Object.entries(owned).map(([k, v]) => ({
          key: k, value: stripQuotes(v), sourceLineage: obj.lineage, sourceName: 'owned'
        }));
        
        // Traverse parent chain
        let parentLineage = obj.parent;
        while (parentLineage && parentLineage !== '') {
          const parentObj = objects.find(o => o.lineage === parentLineage);
          if (parentObj && parentObj.attributes) {
            const parentAttrs = [];
            for (const [k, v] of Object.entries(parentObj.attributes)) {
              // Skip if already defined
              const alreadyDefined = Object.values(attrsBySource).flat().some(a => a.key === k);
              if (!alreadyDefined) {
                parentAttrs.push({key: k, value: stripQuotes(v), sourceLineage: parentLineage, sourceName: parentObj.name});
              }
            }
            if (parentAttrs.length > 0) {
              attrsBySource[parentObj.name] = parentAttrs;
            }
          }
          parentLineage = parentObj?.parent || '';
        }
        
        // Find methods grouped by source
        const methodsBySource = {};
        
        // Owned methods
        const ownedMethods = objects.filter(o => 
          o.lineage.includes(':Method:') && 
          o.lineage.startsWith(obj.lineage + ':')
        );
        if (ownedMethods.length > 0) {
          methodsBySource['owned'] = ownedMethods.map(m => ({...m, sourceName: 'owned'}));
        }
        
        // Inherited methods
        parentLineage = obj.parent;
        while (parentLineage && parentLineage !== '') {
          const parentObj = objects.find(o => o.lineage === parentLineage);
          if (parentObj) {
            const parentMethods = objects.filter(o => 
              o.lineage.includes(':Method:') && 
              (o.attributes?.belongs_to === parentObj.name || o.lineage.startsWith(parentObj.lineage + ':'))
            );
            const newMethods = parentMethods.filter(m => 
              !Object.values(methodsBySource).flat().some(em => em.name === m.name)
            );
            if (newMethods.length > 0) {
              methodsBySource[parentObj.name] = newMethods.map(m => ({...m, sourceName: parentObj.name, sourceLineage: parentObj.lineage}));
            }
          }
          parentLineage = parentObj?.parent || '';
        }
        
        // Find relations
        const relations = obj.relations || [];
        
        // Find rules targeting this object - ONLY real rules
        const allRules = objects.filter(o => o.lineage.includes(':Rule:'));
        const rulesForObj = allRules.filter(r =>
          r.attributes?.target === obj.lineage || 
          r.attributes?.target === obj.name ||
          (r.attributes?.target && obj.lineage.endsWith(':' + r.attributes.target))
        );
        
        // Group rules by type
        const ruleGroups = [
          {name: 'CreateRule', rules: rulesForObj.filter(r => r.lineage.includes('CreateRule'))},
          {name: 'ReadRule', rules: rulesForObj.filter(r => r.lineage.includes('ReadRule'))},
          {name: 'UpdateRule', rules: rulesForObj.filter(r => r.lineage.includes('UpdateRule'))},
          {name: 'DeleteRule', rules: rulesForObj.filter(r => r.lineage.includes('DeleteRule'))},
          {name: 'ValidationRule', rules: rulesForObj.filter(r => r.lineage.includes('ValidationRule') || r.lineage.includes('ValidateRule'))},
          {name: 'FormatRule', rules: rulesForObj.filter(r => r.lineage.includes('FormatRule'))},
          {name: 'StructureRule', rules: rulesForObj.filter(r => r.lineage.includes('StructureRule'))}
        ].filter(g => g.rules.length > 0);
        
        // Build HTML - Attributes with inline source
        let attrsHtml = '';
        for (const [source, attrs] of Object.entries(attrsBySource)) {
          if (attrs.length === 0) continue;
          const isOwned = source === 'owned';
          const sourceClass = isOwned ? 'owned' : 'inherited';
          const sourceLineage = isOwned ? null : attrs[0].sourceLineage;
          
          attrs.forEach(attr => {
            const sourceTag = isOwned ? '' : \` <span class="source-tag clickable" onclick="selectObject('\${sourceLineage}')">(\${source})</span>\`;
            if (isOwned) {
              attrsHtml += \`<tr class="\${sourceClass}">
                <th>\${attr.key}</th>
                <td>
                  <span class="attr-value" data-key="\${attr.key}">\${attr.value}</span>
                  <button class="edit-btn" onclick="editAttr('\${obj.lineage}', '\${attr.key}')">✎</button>
                </td>
              </tr>\`;
            } else {
              attrsHtml += \`<tr class="\${sourceClass}">
                <th>\${attr.key}</th>
                <td><span class="attr-value">\${attr.value}</span>\${sourceTag}</td>
              </tr>\`;
            }
          });
        }
        
        // Build HTML - Methods with inline source (clickable)
        let methodsHtml = '';
        for (const [source, methods] of Object.entries(methodsBySource)) {
          if (methods.length === 0) continue;
          const isOwned = source === 'owned';
          const sourceClass = isOwned ? 'owned' : 'inherited';
          const sourceLineage = isOwned ? null : methods[0].sourceLineage;
          
          methods.forEach(m => {
            const sourceTag = isOwned ? '' : \` <span class="source-tag clickable" onclick="selectObject('\${sourceLineage}')">(\${source})</span>\`;
            methodsHtml += \`<div class="method-item \${sourceClass} clickable" onclick="selectObject('\${m.lineage}')">◦ \${m.name}\${sourceTag}</div>\`;
          });
        }
        
        // Build HTML - Relations (clickable)
        let relationsHtml = '';
        if (relations.length > 0) {
          relations.forEach(r => {
            relationsHtml += \`<div class="relation-item">\${r.type} → <span class="clickable" onclick="selectObject('\${r.target}')">\${r.target.split(':').pop()}</span></div>\`;
          });
        }
        
        // Build HTML - Rules (clickable)
        let rulesHtml = '';
        let rulesCount = 0;
        ruleGroups.forEach(group => {
          rulesCount += group.rules.length;
          rulesHtml += \`<div class="rule-group"><strong>\${group.name}:</strong>\`;
          group.rules.forEach(r => {
            rulesHtml += \`<div class="rule-item clickable" onclick="selectObject('\${r.lineage}')">• \${r.name}</div>\`;
          });
          rulesHtml += \`</div>\`;
        });
        
        // Hooks
        let hooksHtml = '';
        const hookAttrs = ['hook_before', 'hook_after', 'hook_error'];
        let hooksCount = 0;
        hookAttrs.forEach(h => {
          const val = owned[h] || Object.values(attrsBySource).flat().find(a => a.key === h)?.value;
          if (val) {
            hooksCount++;
            const source = owned[h] ? '' : Object.entries(attrsBySource).find(([s, attrs]) => attrs.some(a => a.key === h))?.[0];
            const sourceHtml = source && source !== 'owned' ? \` <span class="from">(\${source})</span>\` : '';
            hooksHtml += \`<div class="hook-item">\${h}: \${stripQuotes(val)}\${sourceHtml}</div>\`;
          }
        });
        
        // Count items
        const attrsCount = Object.values(attrsBySource).flat().length;
        const methodsCount = Object.values(methodsBySource).flat().length;
        const relationsCount = relations.length;
        
        // Get display name (without quotes)
        const displayName = stripQuotes(obj.attributes?.name || obj.name);
        
        detail.innerHTML = \`
          <div class="object-header">
            <h2>\${displayName}</h2>
            <div class="object-actions">
              <button class="action-btn" onclick="gotoObject('\${obj.lineage}')" title="Ouvrir">📄</button>
              <button class="action-btn" onclick="deleteObject('\${obj.lineage}')" title="Supprimer">🗑</button>
            </div>
          </div>
          <div class="object-lineage">\${obj.lineage}</div>
          <div class="object-source">\${obj.source ? obj.source.split('/').pop() + ':' + obj.line : ''}</div>
          
          <div class="section accordion">
            <div class="section-header" onclick="this.parentElement.classList.toggle('open')">
              <span class="accordion-toggle">▶</span>
              <span>Attributs (\${attrsCount})</span>
              <button class="add-btn" onclick="event.stopPropagation(); showAddAttr('\${obj.lineage}')">+ Ajouter</button>
            </div>
            <div class="section-content">
              \${attrsHtml ? \`<table class="attrs-table"><tbody>\${attrsHtml}</tbody></table>\` : '<p class="empty">Aucun attribut</p>'}
            </div>
          </div>
          
          <div class="section accordion">
            <div class="section-header" onclick="this.parentElement.classList.toggle('open')">
              <span class="accordion-toggle">▶</span>
              <span>Methods (\${methodsCount})</span>
              <button class="add-btn" onclick="event.stopPropagation(); showAddMethod('\${obj.lineage}')">+ Ajouter</button>
            </div>
            <div class="section-content">
              \${methodsHtml || '<p class="empty">Aucune méthode</p>'}
            </div>
          </div>
          
          <div class="section accordion">
            <div class="section-header" onclick="this.parentElement.classList.toggle('open')">
              <span class="accordion-toggle">▶</span>
              <span>Relations (\${relationsCount})</span>
              <button class="add-btn" onclick="event.stopPropagation(); showAddRelation('\${obj.lineage}')">+ Ajouter</button>
            </div>
            <div class="section-content">
              \${relationsHtml || '<p class="empty">Aucune relation</p>'}
            </div>
          </div>
          
          <div class="section accordion">
            <div class="section-header" onclick="this.parentElement.classList.toggle('open')">
              <span class="accordion-toggle">▶</span>
              <span>Rules (\${rulesCount})</span>
              <button class="add-btn" onclick="event.stopPropagation(); showAddRule('\${obj.lineage}')">+ Ajouter</button>
            </div>
            <div class="section-content">
              \${rulesHtml || '<p class="empty">Aucune règle</p>'}
            </div>
          </div>
          
          \${hooksHtml ? \`
          <div class="section">
            <div class="section-header"><span>Hooks</span></div>
            \${hooksHtml}
          </div>
          \` : ''}
        \`;
      }
    }
    
    // Edit attribute
    function editAttr(lineage, key) {
      const span = document.querySelector(\`.attr-value[data-key="\${key}"]\`);
      const currentValue = span.textContent;
      const input = document.createElement('input');
      input.type = 'text';
      input.value = currentValue;
      input.className = 'edit-input';
      input.onblur = () => {
        if (input.value !== currentValue) {
          vscode.postMessage({command: 'updateAttribute', lineage, key, value: input.value});
        }
        span.textContent = input.value;
        input.replaceWith(span);
      };
      input.onkeypress = (e) => { if (e.key === 'Enter') input.blur(); };
      span.replaceWith(input);
      input.focus();
      input.select();
    }
    
    // Delete object
    function deleteObject(lineage) {
      if (confirm('Supprimer ' + lineage + ' ?\\n\\nCette action va également supprimer les références.')) {
        vscode.postMessage({command: 'deleteObject', lineage});
      }
    }
    
    // Add attribute modal
    function showAddAttr(lineage) {
      const modal = document.createElement('div');
      modal.className = 'modal-overlay';
      modal.innerHTML = \`
        <div class="modal">
          <h3>Ajouter un attribut</h3>
          <div class="form-group">
            <label>Nom de l'attribut</label>
            <input type="text" id="newAttrKey" placeholder="name">
          </div>
          <div class="form-group">
            <label>Valeur (V_xxx existant ou V_xxx(type, default, desc) pour créer)</label>
            <input type="text" id="newAttrValue" placeholder="V_Name ou V_NewVector(string, \\"default\\", \\"description\\")">
          </div>
          <div class="modal-actions">
            <button class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Annuler</button>
            <button class="btn-primary" onclick="addAttribute('\${lineage}')">Ajouter</button>
          </div>
        </div>
      \`;
      document.body.appendChild(modal);
      document.getElementById('newAttrKey').focus();
    }
    
    function addAttribute(lineage) {
      const key = document.getElementById('newAttrKey').value.trim();
      const value = document.getElementById('newAttrValue').value.trim();
      if (key && value) {
        vscode.postMessage({command: 'addAttribute', lineage, key, value});
        document.querySelector('.modal-overlay').remove();
      }
    }
    
    // Add method modal
    function showAddMethod(lineage) {
      const modal = document.createElement('div');
      modal.className = 'modal-overlay';
      modal.innerHTML = \`
        <div class="modal">
          <h3>Ajouter une méthode</h3>
          <div class="form-group">
            <label>Nom de la méthode</label>
            <input type="text" id="newMethodName" placeholder="myMethod">
          </div>
          <div class="modal-actions">
            <button class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Annuler</button>
            <button class="btn-primary" onclick="addMethod('\${lineage}')">Ajouter</button>
          </div>
        </div>
      \`;
      document.body.appendChild(modal);
      document.getElementById('newMethodName').focus();
    }
    
    function addMethod(lineage) {
      const name = document.getElementById('newMethodName').value.trim();
      if (name) {
        vscode.postMessage({command: 'addMethod', lineage, name});
        document.querySelector('.modal-overlay').remove();
      }
    }
    
    // Add relation modal
    function showAddRelation(lineage) {
      const modal = document.createElement('div');
      modal.className = 'modal-overlay';
      modal.innerHTML = \`
        <div class="modal">
          <h3>Ajouter une relation</h3>
          <div class="form-group">
            <label>Type</label>
            <select id="newRelationType">
              <option value="depends_on">depends_on</option>
              <option value="related_to">related_to</option>
              <option value="IN">IN</option>
            </select>
          </div>
          <div class="form-group">
            <label>Cible</label>
            <input type="text" id="newRelationTarget" placeholder="Object:Type:Name">
          </div>
          <div class="modal-actions">
            <button class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Annuler</button>
            <button class="btn-primary" onclick="addRelation('\${lineage}')">Ajouter</button>
          </div>
        </div>
      \`;
      document.body.appendChild(modal);
    }
    
    function addRelation(lineage) {
      const type = document.getElementById('newRelationType').value;
      const target = document.getElementById('newRelationTarget').value.trim();
      if (target) {
        vscode.postMessage({command: 'addRelation', lineage, type, target});
        document.querySelector('.modal-overlay').remove();
      }
    }
    
    // Add rule modal
    function showAddRule(lineage) {
      const modal = document.createElement('div');
      modal.className = 'modal-overlay';
      modal.innerHTML = \`
        <div class="modal">
          <h3>Ajouter une règle</h3>
          <div class="form-group">
            <label>Type de règle</label>
            <select id="newRuleType">
              <option value="CreateRule">CreateRule</option>
              <option value="ReadRule">ReadRule</option>
              <option value="UpdateRule">UpdateRule</option>
              <option value="DeleteRule">DeleteRule</option>
              <option value="ValidationRule">ValidationRule</option>
            </select>
          </div>
          <div class="form-group">
            <label>Nom de la règle</label>
            <input type="text" id="newRuleName" placeholder="MyRule">
          </div>
          <div class="modal-actions">
            <button class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Annuler</button>
            <button class="btn-primary" onclick="addRule('\${lineage}')">Ajouter</button>
          </div>
        </div>
      \`;
      document.body.appendChild(modal);
    }
    
    function addRule(lineage) {
      const type = document.getElementById('newRuleType').value;
      const name = document.getElementById('newRuleName').value.trim();
      if (name) {
        vscode.postMessage({command: 'addRule', lineage, type, name});
        document.querySelector('.modal-overlay').remove();
      }
    }
    
    function gotoObject(lineage) {
      vscode.postMessage({command: 'gotoObject', lineage});
    }
    
    function openInBrowser() {
      if (serverConnected) {
        vscode.postMessage({command: 'openInBrowser'});
      } else {
        alert('Démarrez le serveur Python d\\'abord');
      }
    }
    
    // ========== EUREKAI CORE JS (intégré) ==========
    class ErkStore {
      constructor() { this.objects = new Map(); this.vectors = new Map(); this.rules = []; }
      clear() { this.objects.clear(); this.vectors.clear(); this.rules = []; }
      get(l) { return this.objects.get(l); }
      set(l, o) { 
        this.objects.set(l, o);
        if (l.includes(':Vector:') || o.name?.startsWith('V_')) {
          const n = o.attributes?.name?.replace(/"/g, '') || o.name;
          if (n.startsWith('V_')) this.vectors.set(n, o);
        }
        if (l.includes(':Rule:')) this.rules.push(o);
      }
      getChildren(l) {
        const p = l + ':';
        return [...this.objects.keys()].filter(k => k.startsWith(p) && !k.substring(p.length).includes(':'));
      }
      stats() { return { objects: this.objects.size, vectors: this.vectors.size, rules: this.rules.length }; }
    }
    
    class ErkResolver {
      constructor(s) { this.store = s; this.cache = new Map(); }
      resolve(v) {
        if (!v) return null;
        const s = String(v);
        if (this.cache.has(s)) return this.cache.get(s);
        if (s.startsWith('V_')) { const r = this.resolveVector(s); this.cache.set(s, r); return r; }
        if (s.startsWith('"') && s.endsWith('"')) return s.slice(1, -1);
        if (/^-?\\d+(\\.\\d+)?$/.test(s)) return parseFloat(s);
        if (s === 'true') return true;
        if (s === 'false') return false;
        return s;
      }
      resolveVector(n) {
        const v = this.store.vectors.get(n);
        if (!v) return null;
        return this.resolve(v.attributes?.default);
      }
      resolveObject(l) {
        const o = this.store.get(l);
        if (!o) return null;
        const r = { lineage: o.lineage, name: o.name, parent: o.parent, attributes: {} };
        for (const [k, v] of Object.entries(o.attributes || {})) r.attributes[k] = this.resolve(v);
        return r;
      }
    }
    
    // Initialize core with loaded objects (for fallback)
    const coreStore = new ErkStore();
    const coreResolver = new ErkResolver(coreStore);
    objects.forEach(o => coreStore.set(o.lineage, o));
    
    // Also extract vector references from attributes
    const vectorRefs = new Set();
    objects.forEach(o => {
      Object.values(o.attributes || {}).forEach(v => {
        if (typeof v === 'string' && v.startsWith('V_')) {
          vectorRefs.add(v);
        }
      });
    });
    // Add referenced vectors that aren't defined
    vectorRefs.forEach(vName => {
      if (!coreStore.vectors.has(vName)) {
        coreStore.vectors.set(vName, { name: vName, attributes: { default: '(undefined)' } });
      }
    });
    
    // Server URL
    const SERVER_URL = 'http://localhost:8420';
    let serverConnected = false;
    
    // Check server connection
    async function checkServer() {
      try {
        const res = await fetch(SERVER_URL + '/health');
        const data = await res.json();
        serverConnected = data.status === 'ok';
        updateServerStatus();
        return serverConnected;
      } catch (e) {
        serverConnected = false;
        updateServerStatus();
        return false;
      }
    }
    
    function updateServerStatus() {
      const statusEl = document.getElementById('serverStatus');
      if (statusEl) {
        statusEl.className = 'server-status ' + (serverConnected ? 'connected' : 'disconnected');
        statusEl.textContent = serverConnected ? '● Python API' : '○ Local JS';
      }
      
      // Update server button
      const btnEl = document.getElementById('serverBtn');
      if (btnEl) {
        btnEl.classList.toggle('running', serverConnected);
        btnEl.textContent = serverConnected ? '■ Python' : '▶ Python';
      }
    }
    
    // Toggle server (start/stop)
    function toggleServer() {
      vscode.postMessage({command: 'toggleServer'});
    }
    
    // Open file in editor
    function openFile(filePath) {
      vscode.postMessage({command: 'openFile', path: filePath});
    }
    
    // SuperRead execution via Python API (with JS fallback)
    async function executeQuery() {
      const input = document.getElementById('queryInput');
      const query = input.value.trim();
      const output = document.getElementById('consoleOutput');
      
      if (!query) return;
      
      // Clear input after execution
      input.value = '';
      
      // Try Python server first
      if (serverConnected || await checkServer()) {
        try {
          output.textContent = '> ' + query + '\\n\\nChargement...';
          const res = await fetch(SERVER_URL + '/query?q=' + encodeURIComponent(query));
          const data = await res.json();
          
          let text = '> ' + query + '\\n\\n';
          if (data.message) {
            text += data.message;
          } else if (data.error) {
            text += 'Erreur: ' + data.error;
          } else {
            text += JSON.stringify(data, null, 2);
          }
          output.textContent = text;
          return;
        } catch (e) {
          serverConnected = false;
          updateServerStatus();
        }
      }
      
      // Fallback to local JS
      let result = '';
      try {
        if (query === 'help') {
          result = \`SuperRead Commands:
  read <Type>              - List objects of type
  read <Type>.attr=value   - Filter by equality
  read <Type>.attr~value   - Filter by contains
  read <Type>.attr>value   - Filter numeric comparison
  resolve <V_xxx>          - Resolve vector value
  get <lineage>            - Get object by lineage
  tree [depth]             - Show object tree
  stats                    - Show statistics
  vectors                  - List all vectors
  rules                    - List all rules
  
[Mode local - lancez le serveur Python pour plus de fonctionnalités]\`;
        }
        else if (query === 'stats') {
          const s = coreStore.stats();
          result = \`Statistics:\\n  Objects: \${s.objects}\\n  Vectors: \${s.vectors}\\n  Rules: \${s.rules}\`;
        }
        else if (query === 'vectors') {
          const vecs = [...coreStore.vectors.entries()].map(([n, v]) => {
            const val = coreResolver.resolveVector(n);
            return \`  \${n} = \${val}\`;
          });
          result = \`Vectors (\${vecs.length}):\\n\${vecs.join('\\n')}\`;
        }
        else if (query === 'rules') {
          const rls = coreStore.rules.map(r => \`  \${r.name}: \${r.attributes?.target || ''}\`);
          result = \`Rules (\${rls.length}):\\n\${rls.join('\\n')}\`;
        }
        else if (query.startsWith('resolve ')) {
          const vName = query.substring(8).trim();
          const val = coreResolver.resolveVector(vName);
          result = \`\${vName} = \${val !== null ? val : '(not found)'}\`;
        }
        // get <lineage>
        else if (query.startsWith('get ')) {
          let lineage = query.substring(4).trim();
          if (!lineage.startsWith('Object:')) lineage = 'Object:' + lineage;
          const obj = coreResolver.resolveObject(lineage);
          result = obj ? JSON.stringify(obj, null, 2) : \`Object not found: \${lineage}\`;
        }
        // tree
        else if (query.startsWith('tree')) {
          const depth = parseInt(query.split(' ')[1]) || 4;
          const lines = [];
          const buildTree = (l, d, prefix = '') => {
            if (d > depth) return;
            const o = coreStore.get(l);
            lines.push(prefix + (o?.name || l.split(':').pop()));
            coreStore.getChildren(l).forEach((c, i, arr) => {
              const last = i === arr.length - 1;
              buildTree(c, d + 1, prefix + (last ? '└── ' : '├── '));
            });
          };
          if (coreStore.objects.has('Object')) buildTree('Object', 0);
          result = lines.join('\\n');
        }
        // read <Type>[.conditions]
        else if (query.startsWith('read ')) {
          const match = query.match(/^read\\s+(\\w+)(?:\\.(.*?))?$/);
          if (match) {
            const [, type, conditions] = match;
            let results = [];
            for (const [lineage, obj] of coreStore.objects) {
              if (lineage.includes(':' + type) || obj.name === type) {
                if (!conditions || matchConditions(obj, conditions)) {
                  results.push(coreResolver.resolveObject(lineage));
                }
              }
            }
            result = \`Results for "\${type}" (\${results.length}):\\n\`;
            result += results.map(r => \`  \${r.name} (\${r.lineage})\`).join('\\n');
            if (results.length > 0 && results.length <= 5) {
              result += '\\n\\nDetails:\\n' + JSON.stringify(results, null, 2);
            }
          }
        }
        else {
          result = \`Unknown command: \${query}\\nType 'help' for available commands.\`;
        }
      } catch (e) {
        result = \`Error: \${e.message}\`;
      }
      
      output.textContent = '> ' + query + '\\n\\n' + result;
    }
    
    function matchConditions(obj, cond) {
      const getVal = (a) => {
        const v = obj.attributes?.[a];
        return typeof v === 'string' && v.startsWith('"') ? v.slice(1, -1) : v;
      };
      
      // Multiple conditions (AND)
      for (const c of cond.split(',')) {
        const t = c.trim();
        let m;
        if (t.endsWith('?')) { if (!(t.slice(0, -1) in (obj.attributes || {}))) return false; }
        else if ((m = t.match(/^(\\w+)=(.+)$/))) { if (getVal(m[1]) !== m[2]) return false; }
        else if ((m = t.match(/^(\\w+)!=(.+)$/))) { if (getVal(m[1]) === m[2]) return false; }
        else if ((m = t.match(/^(\\w+)~(.+)$/))) { if (!String(getVal(m[1]) || '').toLowerCase().includes(m[2].toLowerCase())) return false; }
        else if ((m = t.match(/^(\\w+)>(.+)$/))) { if (parseFloat(getVal(m[1])) <= parseFloat(m[2])) return false; }
        else if ((m = t.match(/^(\\w+)<(.+)$/))) { if (parseFloat(getVal(m[1])) >= parseFloat(m[2])) return false; }
        else if ((m = t.match(/^(\\w+)>=(.+)$/))) { if (parseFloat(getVal(m[1])) < parseFloat(m[2])) return false; }
        else if ((m = t.match(/^(\\w+)<=(.+)$/))) { if (parseFloat(getVal(m[1])) > parseFloat(m[2])) return false; }
      }
      return true;
    }
    
    document.getElementById('queryInput').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') executeQuery();
    });
    
    // Set query from history
    function setQuery(q) {
      document.getElementById('queryInput').value = q;
      document.getElementById('queryInput').focus();
    }
    
    // Copy output to clipboard
    function copyOutput() {
      const output = document.getElementById('consoleOutput').textContent;
      navigator.clipboard.writeText(output).then(() => {
        const btn = event.target;
        const orig = btn.textContent;
        btn.textContent = '✓ Copié!';
        setTimeout(() => btn.textContent = orig, 1500);
      });
    }
    
    // Export output to file
    function exportOutput() {
      const output = document.getElementById('consoleOutput').textContent;
      const blob = new Blob([output], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'eurekai-console-' + new Date().toISOString().slice(0, 10) + '.txt';
      a.click();
      URL.revokeObjectURL(url);
    }
    
    // Clear output
    function clearOutput() {
      document.getElementById('consoleOutput').textContent = '// Console effacée';
      document.getElementById('queryInput').value = '';
      document.getElementById('queryInput').focus();
    }
    
    // Search
    document.getElementById('searchInput').addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase();
      document.querySelectorAll('.tree-node').forEach(node => {
        const name = node.querySelector('.name').textContent.toLowerCase();
        node.style.display = name.includes(query) ? 'flex' : 'none';
      });
    });
    
    // Handle messages from extension
    window.addEventListener('message', event => {
      const msg = event.data;
      if (msg.type === 'queryResult') {
        const output = document.getElementById('consoleOutput');
        let text = '> ' + msg.query + '\\n\\n';
        if (msg.message) {
          text += msg.message;
        }
        if (msg.results && msg.results.length > 0) {
          text += msg.results.map(r => r.name + ' (' + r.lineage + ')').join('\\n');
          text += '\\n\\n' + msg.results.length + ' résultat(s)';
        }
        output.textContent = text;
      }
    });
    
    // Create object functions
    function addAttrRow() {
      const list = document.getElementById('attributesList');
      const row = document.createElement('div');
      row.className = 'attr-row';
      row.innerHTML = \`
        <input type="text" placeholder="attribut" class="attr-key">
        <span>=</span>
        <input type="text" placeholder="valeur ou V_xxx(type, default, desc)" class="attr-value">
        <button class="btn-small" onclick="this.parentElement.remove()">−</button>
      \`;
      list.appendChild(row);
    }
    
    function addMethodRow() {
      const list = document.getElementById('methodsList');
      const row = document.createElement('div');
      row.className = 'method-row';
      row.innerHTML = \`
        <input type="text" placeholder="nomMethode" class="method-name" onfocus="this.select()">
        <button class="btn-small" onclick="this.parentElement.remove()">−</button>
      \`;
      list.appendChild(row);
    }
    
    function addRelationRow() {
      const list = document.getElementById('relationsList');
      const row = document.createElement('div');
      row.className = 'relation-row';
      row.innerHTML = \`
        <select class="relation-type">
          <option value="depends_on">depends_on</option>
          <option value="related_to">related_to</option>
          
        </select>
        <input type="text" placeholder="Object:Type:Name" class="relation-target" onfocus="this.select()">
        <button class="btn-small" onclick="this.parentElement.remove()">−</button>
      \`;
      list.appendChild(row);
    }
    
    function addRuleRow() {
      const list = document.getElementById('rulesList');
      const row = document.createElement('div');
      row.className = 'rule-row';
      row.innerHTML = \`
        <select class="rule-type">
          <option value="ValidationRule">ValidationRule</option>
          <option value="CreateRule">CreateRule</option>
          <option value="ReadRule">ReadRule</option>
          <option value="UpdateRule">UpdateRule</option>
          <option value="DeleteRule">DeleteRule</option>
        </select>
        <input type="text" placeholder="NomDeLaRegle" class="rule-name" onfocus="this.select()">
        <button class="btn-small" onclick="this.parentElement.remove()">−</button>
      \`;
      list.appendChild(row);
    }
    
    function createObject() {
      const parent = document.getElementById('createParent').value;
      const name = document.getElementById('createName').value;
      
      if (!name) {
        alert('Veuillez entrer un nom pour l\\'objet');
        return;
      }
      
      // Valider le nom (PascalCase)
      if (!/^[A-Z][A-Za-z0-9_]*$/.test(name)) {
        alert('Le nom doit commencer par une majuscule (PascalCase)');
        return;
      }
      
      const attributes = {};
      document.querySelectorAll('#attributesList .attr-row').forEach(row => {
        const key = row.querySelector('.attr-key').value.trim();
        const value = row.querySelector('.attr-value').value.trim();
        if (key && value) {
          attributes[key] = value;
        }
      });
      
      const methods = [];
      document.querySelectorAll('#methodsList .method-row').forEach(row => {
        const name = row.querySelector('.method-name').value.trim();
        if (name) methods.push(name);
      });
      
      const relations = [];
      document.querySelectorAll('#relationsList .relation-row').forEach(row => {
        const type = row.querySelector('.relation-type').value;
        const target = row.querySelector('.relation-target').value.trim();
        if (target) relations.push({type, target});
      });
      
      const rules = [];
      document.querySelectorAll('#rulesList .rule-row').forEach(row => {
        const type = row.querySelector('.rule-type').value;
        const ruleName = row.querySelector('.rule-name').value.trim();
        if (ruleName) rules.push({type, name: ruleName});
      });
      
      const lineage = parent === 'Object' ? 'Object:' + name : parent + ':' + name;
      
      vscode.postMessage({command: 'createObject', parent, name, attributes, methods, relations, rules});
      
      // Reset form
      document.getElementById('createName').value = '';
      ['attributesList', 'methodsList', 'relationsList', 'rulesList'].forEach(listId => {
        const list = document.getElementById(listId);
        if (!list) return;
        const rows = list.querySelectorAll('[class$="-row"]');
        rows.forEach((row, i) => {
          if (i === 0) {
            row.querySelectorAll('input').forEach(inp => inp.value = '');
          } else {
            row.remove();
          }
        });
      });
      
      // Switch to Explorer tab and select the new object
      setTimeout(() => {
        document.querySelector('[data-tab="explorer"]').click();
        selectObject(lineage);
      }, 500);
    }
    
    // GEVR Scenario Builder
    function createScenario() {
      const name = document.getElementById('scenarioName').value.trim();
      if (!name) {
        alert('Veuillez entrer un nom pour le Scenario');
        return;
      }
      
      const getMethod = document.getElementById('getMethod').value.trim();
      const executeMethod = document.getElementById('executeMethod').value.trim();
      const validateMethod = document.getElementById('validateMethod').value.trim();
      const renderMethod = document.getElementById('renderMethod').value.trim();
      
      // Créer le Scenario avec ses steps
      const attributes = {
        name: name,
        gevr: 'true'
      };
      
      if (getMethod) attributes.get_step = getMethod;
      if (executeMethod) attributes.execute_step = executeMethod;
      if (validateMethod) attributes.validate_step = validateMethod;
      if (renderMethod) attributes.render_step = renderMethod;
      
      vscode.postMessage({
        command: 'createObject',
        parent: 'Object:Scenario',
        name: name + 'Scenario',
        attributes,
        methods: [],
        relations: []
      });
      
      // Reset form
      document.getElementById('scenarioName').value = '';
      ['getMethod', 'executeMethod', 'validateMethod', 'renderMethod'].forEach(id => {
        document.getElementById(id).value = '';
      });
      
      // Switch to Explorer
      setTimeout(() => {
        document.querySelector('[data-tab="explorer"]').click();
        selectObject('Object:Scenario:' + name + 'Scenario');
      }, 500);
    }
    
    function testGevr() {
      const getMethod = document.getElementById('getMethod').value.trim() || 'pass';
      const executeMethod = document.getElementById('executeMethod').value.trim() || 'pass';
      const validateMethod = document.getElementById('validateMethod').value.trim() || 'pass';
      const renderMethod = document.getElementById('renderMethod').value.trim() || 'pass';
      const name = document.getElementById('scenarioName').value.trim() || 'TestScenario';
      
      // Show preview
      const preview = document.getElementById('gevrPreview');
      preview.style.display = 'block';
      
      const code = \`Object:Scenario:\${name}Scenario:
  .name = "\${name}"
  .gevr = true
  .get_step = \${getMethod}
  .execute_step = \${executeMethod}
  .validate_step = \${validateMethod}
  .render_step = \${renderMethod}\`;
      
      document.getElementById('gevrCode').textContent = code;
      
      // Simulate test result
      const outputEl = document.getElementById('gevrOutput');
      const resultEl = document.getElementById('gevrResult');
      outputEl.style.display = 'block';
      
      const mockResult = {
        status: 'success',
        steps: [
          {name: 'GET', method: getMethod || 'pass', result: 'data loaded'},
          {name: 'EXECUTE', method: executeMethod || 'pass', result: 'processed'},
          {name: 'VALIDATE', method: validateMethod || 'pass', result: 'valid'},
          {name: 'RENDER', method: renderMethod || 'pass', result: 'rendered'}
        ],
        output: '// Simulation - connectez le serveur Python pour un vrai test'
      };
      
      resultEl.textContent = JSON.stringify(mockResult, null, 2);
    }
    
    // Check server on load
    checkServer();
  </script>
</body>
</html>`;
}
function buildTreeData() {
    function buildNode(lineage) {
        const obj = store.objects.get(lineage);
        const children = getChildren(lineage);
        return {
            lineage,
            name: obj?.name || lineage.split(':').pop() || lineage,
            children: children.map(c => buildNode(c))
        };
    }
    return store.objects.has('Object') ? buildNode('Object') : { lineage: 'Object', name: 'Object', children: [] };
}
// ============================================================================
// DIAGNOSTICS (Validation temps réel)
// ============================================================================
let diagnosticCollection;
// Track all vector definitions globally
const vectorDefinitions = new Map();
function isManifestOrInstance(fileName) {
    return fileName.endsWith('.m.gev') || fileName.endsWith('.i.gev');
}
function isSeedOrSchema(fileName) {
    return fileName.endsWith('.s.gev') || fileName.endsWith('.t.gev') ||
        fileName.endsWith('.gev') && !isManifestOrInstance(fileName);
}
function validateDocument(document) {
    if (!document.fileName.endsWith('.gev') && !document.fileName.endsWith('.erk'))
        return;
    const diagnostics = [];
    const text = document.getText();
    const lines = text.split('\n');
    const fileName = document.fileName;
    const isManifest = isManifestOrInstance(fileName);
    let currentLineage = null;
    const definedLineages = new Set();
    const usedVectors = new Set();
    const localVectorDefs = new Map(); // V_xxx -> line number
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trim();
        // Skip comments and empty
        if (!trimmed || trimmed.startsWith('#') || trimmed.startsWith('//'))
            continue;
        // Check lineage declaration
        const lineageMatch = trimmed.match(/^([A-Z][A-Za-z0-9_]*(?::[A-Z][A-Za-z0-9_]*)*):$/);
        if (lineageMatch) {
            currentLineage = lineageMatch[1];
            if (!currentLineage.startsWith('Object:') && currentLineage !== 'Object') {
                currentLineage = 'Object:' + currentLineage;
            }
            // Check duplicate lineage in this file
            if (definedLineages.has(currentLineage)) {
                diagnostics.push(new vscode.Diagnostic(new vscode.Range(i, 0, i, line.length), `Duplicate lineage: ${currentLineage}`, vscode.DiagnosticSeverity.Error));
            }
            definedLineages.add(currentLineage);
            continue;
        }
        // Check attribute syntax
        const attrMatch = trimmed.match(/^\.([a-zA-Z_][a-zA-Z0-9_.]*)\s*=\s*(.*)$/);
        if (attrMatch) {
            const [, attrName, attrValue] = attrMatch;
            // Check empty value
            if (!attrValue.trim()) {
                diagnostics.push(new vscode.Diagnostic(new vscode.Range(i, 0, i, line.length), `Empty value for attribute: ${attrName}`, vscode.DiagnosticSeverity.Warning));
            }
            // Check for vector definition V_xxx(type, default, description)
            const vectorDefMatch = attrValue.match(/^(V_[A-Za-z0-9_]+)\s*\(/);
            if (vectorDefMatch) {
                const vectorName = vectorDefMatch[1];
                // Check if this is a manifest trying to define a vector
                if (isManifest) {
                    diagnostics.push(new vscode.Diagnostic(new vscode.Range(i, line.indexOf(vectorName), i, line.indexOf(vectorName) + vectorName.length), `Cannot define vector in manifest/instance. Use existing vector or define in seed.`, vscode.DiagnosticSeverity.Error));
                }
                else {
                    // Check for duplicate definition
                    const existing = vectorDefinitions.get(vectorName);
                    if (existing && existing.source !== fileName) {
                        diagnostics.push(new vscode.Diagnostic(new vscode.Range(i, line.indexOf(vectorName), i, line.indexOf(vectorName) + vectorName.length), `Duplicate vector definition: ${vectorName} (already defined in ${path.basename(existing.source)}:${existing.line + 1})`, vscode.DiagnosticSeverity.Error));
                    }
                    else if (localVectorDefs.has(vectorName)) {
                        diagnostics.push(new vscode.Diagnostic(new vscode.Range(i, line.indexOf(vectorName), i, line.indexOf(vectorName) + vectorName.length), `Duplicate vector definition: ${vectorName} (already defined at line ${localVectorDefs.get(vectorName) + 1})`, vscode.DiagnosticSeverity.Error));
                    }
                    else {
                        localVectorDefs.set(vectorName, i);
                        vectorDefinitions.set(vectorName, { source: fileName, line: i });
                    }
                }
            }
            // Check for vector reference (simple V_xxx without parentheses)
            else if (attrValue.match(/^V_[A-Za-z0-9_]+$/)) {
                const vectorName = attrValue.trim();
                usedVectors.add(vectorName);
            }
            // Check for vector reference within value
            else {
                const vectorRefs = attrValue.match(/V_[A-Za-z0-9_]+/g);
                if (vectorRefs) {
                    vectorRefs.forEach(v => usedVectors.add(v));
                }
            }
            continue;
        }
        // Check invalid lines (not comment, not lineage, not attribute)
        if (trimmed && !trimmed.match(/^[A-Z]/) && !trimmed.startsWith('.')) {
            diagnostics.push(new vscode.Diagnostic(new vscode.Range(i, 0, i, line.length), `Invalid syntax: expected lineage (Name:) or attribute (.name = value)`, vscode.DiagnosticSeverity.Error));
        }
    }
    // Check vector usage
    for (const vectorName of usedVectors) {
        const isDefined = store.vectors.has(vectorName) ||
            store.objects.has(`Object:Config:Vector:${vectorName}`) ||
            vectorDefinitions.has(vectorName) ||
            localVectorDefs.has(vectorName);
        if (!isDefined) {
            // Find the line where this vector is used
            for (let i = 0; i < lines.length; i++) {
                const idx = lines[i].indexOf(vectorName);
                if (idx >= 0) {
                    if (isManifest) {
                        // Error in manifest: vector must exist
                        diagnostics.push(new vscode.Diagnostic(new vscode.Range(i, idx, i, idx + vectorName.length), `Vector not defined: ${vectorName}. In manifest/instance, vectors must be pre-defined.`, vscode.DiagnosticSeverity.Error));
                    }
                    else {
                        // Hint in seed: vector should be defined
                        diagnostics.push(new vscode.Diagnostic(new vscode.Range(i, idx, i, idx + vectorName.length), `Vector not defined: ${vectorName}. Use V_xxx(type, default, description) to define it.`, vscode.DiagnosticSeverity.Hint));
                    }
                    break;
                }
            }
        }
    }
    diagnosticCollection.set(document.uri, diagnostics);
}
// Check for unused vectors (called periodically)
function checkUnusedVectors() {
    // This would require scanning all files - implement later if needed
}
// ============================================================================
// COMPLETION (Auto-complétion)
// ============================================================================
class ErkCompletionProvider {
    provideCompletionItems(document, position) {
        const lineText = document.lineAt(position).text;
        const textBefore = lineText.substring(0, position.character);
        const items = [];
        // After "=" suggest vectors
        if (textBefore.includes('=')) {
            // Add all known vectors
            for (const [name] of store.vectors) {
                const item = new vscode.CompletionItem(name, vscode.CompletionItemKind.Variable);
                item.detail = 'Vector';
                item.insertText = name;
                items.push(item);
            }
            // Add common values
            ['true', 'false', '"text"', '0', '1'].forEach(val => {
                items.push(new vscode.CompletionItem(val, vscode.CompletionItemKind.Value));
            });
        }
        // At start of line or after ":" suggest lineages
        else if (textBefore.match(/^[A-Z][A-Za-z0-9_]*:?$/) || textBefore.match(/:[A-Z][A-Za-z0-9_]*$/)) {
            for (const [lineage, obj] of store.objects) {
                const item = new vscode.CompletionItem(obj.name, vscode.CompletionItemKind.Class);
                item.detail = lineage;
                item.insertText = obj.name + ':';
                items.push(item);
            }
        }
        // After "." suggest common attributes
        else if (textBefore.trim().startsWith('.')) {
            const commonAttrs = [
                'name', 'description', 'type', 'default', 'role', 'model',
                'temperature', 'maxTokens', 'provider', 'permissions',
                'target', 'condition', 'severity', 'message'
            ];
            commonAttrs.forEach(attr => {
                const item = new vscode.CompletionItem(attr, vscode.CompletionItemKind.Property);
                item.insertText = attr + ' = ';
                items.push(item);
            });
        }
        // At start of line suggest structure
        else if (textBefore.trim() === '') {
            items.push(Object.assign(new vscode.CompletionItem('Object:', vscode.CompletionItemKind.Class), {
                detail: 'New object declaration'
            }));
            items.push(Object.assign(new vscode.CompletionItem('.', vscode.CompletionItemKind.Property), {
                detail: 'New attribute',
                insertText: '.name = '
            }));
            items.push(Object.assign(new vscode.CompletionItem('#', vscode.CompletionItemKind.Text), {
                detail: 'Comment',
                insertText: '# '
            }));
        }
        return items;
    }
}
// ============================================================================
// DEFINITION PROVIDER (Go to definition)
// ============================================================================
class ErkDefinitionProvider {
    provideDefinition(document, position) {
        const wordRange = document.getWordRangeAtPosition(position, /[A-Za-z0-9_:]+/);
        if (!wordRange)
            return undefined;
        const word = document.getText(wordRange);
        // Check if it's a vector reference (V_xxx)
        if (word.startsWith('V_')) {
            // Find in vectors
            const vectorObj = store.vectors.get(word);
            if (vectorObj && vectorObj.source && vectorObj.line > 0) {
                return new vscode.Location(vscode.Uri.file(vectorObj.source), new vscode.Position(vectorObj.line - 1, 0));
            }
            // Try to find Object:Config:Vector:V_xxx
            for (const [lineage, obj] of store.objects) {
                if (lineage.endsWith(`:${word}`) || obj.name === word) {
                    if (obj.source && obj.line > 0) {
                        return new vscode.Location(vscode.Uri.file(obj.source), new vscode.Position(obj.line - 1, 0));
                    }
                }
            }
        }
        // Check if it's a lineage reference
        const possibleLineages = [
            word,
            'Object:' + word,
            'Object:Entity:' + word,
            'Object:Entity:Agent:' + word,
            'Object:Config:' + word
        ];
        for (const lineage of possibleLineages) {
            const obj = store.objects.get(lineage);
            if (obj && obj.source && obj.line > 0) {
                return new vscode.Location(vscode.Uri.file(obj.source), new vscode.Position(obj.line - 1, 0));
            }
        }
        // Search partial match
        for (const [lineage, obj] of store.objects) {
            if (lineage.includes(`:${word}`) || lineage.endsWith(`:${word}`)) {
                if (obj.source && obj.line > 0) {
                    return new vscode.Location(vscode.Uri.file(obj.source), new vscode.Position(obj.line - 1, 0));
                }
            }
        }
        return undefined;
    }
}
// ============================================================================
// HOVER PROVIDER (Info au survol)
// ============================================================================
class ErkHoverProvider {
    provideHover(document, position) {
        const wordRange = document.getWordRangeAtPosition(position, /[A-Za-z0-9_:]+/);
        if (!wordRange)
            return undefined;
        const word = document.getText(wordRange);
        // Vector hover
        if (word.startsWith('V_')) {
            const vectorObj = store.vectors.get(word);
            if (vectorObj) {
                const defaultVal = vectorObj.attributes?.default || '(undefined)';
                const desc = vectorObj.attributes?.description?.replace(/"/g, '') || '';
                const md = new vscode.MarkdownString();
                md.appendMarkdown(`**Vector: ${word}**\n\n`);
                md.appendMarkdown(`Default: \`${defaultVal}\`\n\n`);
                if (desc)
                    md.appendMarkdown(`${desc}`);
                return new vscode.Hover(md);
            }
        }
        // Lineage hover
        for (const [lineage, obj] of store.objects) {
            if (lineage.endsWith(`:${word}`) || obj.name === word) {
                const md = new vscode.MarkdownString();
                md.appendMarkdown(`**${obj.name}**\n\n`);
                md.appendMarkdown(`Lineage: \`${lineage}\`\n\n`);
                const attrCount = Object.keys(obj.attributes || {}).length;
                if (attrCount > 0) {
                    md.appendMarkdown(`Attributes: ${attrCount}\n\n`);
                    for (const [key, val] of Object.entries(obj.attributes).slice(0, 5)) {
                        md.appendMarkdown(`- \`${key}\`: ${val}\n`);
                    }
                    if (attrCount > 5) {
                        md.appendMarkdown(`- ... and ${attrCount - 5} more`);
                    }
                }
                return new vscode.Hover(md);
            }
        }
        return undefined;
    }
}
// ============================================================================
// ACTIVATION
// ============================================================================
function activate(context) {
    console.log('EUREKAI ERK activated');
    // Diagnostics
    diagnosticCollection = vscode.languages.createDiagnosticCollection('erk');
    context.subscriptions.push(diagnosticCollection);
    fractaleProvider = new FractaleProvider();
    rulesProvider = new RulesProvider();
    // Tree views
    vscode.window.createTreeView('eurekaiExplorer', { treeDataProvider: fractaleProvider });
    vscode.window.createTreeView('eurekaiRules', { treeDataProvider: rulesProvider });
    // Language features
    const selector = [
        { language: 'erk', scheme: 'file' },
        { pattern: '**/*.gev' },
        { pattern: '**/*.erk' }
    ];
    context.subscriptions.push(vscode.languages.registerCompletionItemProvider(selector, new ErkCompletionProvider(), '.', ':', '='), vscode.languages.registerDefinitionProvider(selector, new ErkDefinitionProvider()), vscode.languages.registerHoverProvider(selector, new ErkHoverProvider()));
    // Commands
    context.subscriptions.push(vscode.commands.registerCommand('eurekai.showCockpit', () => showCockpit(context)), vscode.commands.registerCommand('eurekai.refresh', () => {
        parseAllFiles();
        fractaleProvider.refresh();
        rulesProvider.refresh();
        updateCockpit();
        // Revalidate all open documents
        vscode.workspace.textDocuments.forEach(validateDocument);
        vscode.window.showInformationMessage('EUREKAI refreshed');
    }), vscode.commands.registerCommand('eurekai.selectObject', (lineage) => {
        const obj = store.objects.get(lineage);
        if (obj && obj.line > 0) {
            vscode.workspace.openTextDocument(obj.source).then(doc => {
                vscode.window.showTextDocument(doc, vscode.ViewColumn.One).then(editor => {
                    const pos = new vscode.Position(obj.line - 1, 0);
                    editor.selection = new vscode.Selection(pos, pos);
                    editor.revealRange(new vscode.Range(pos, pos));
                });
            });
        }
    }));
    // Validate on events
    vscode.workspace.onDidOpenTextDocument(doc => {
        if (doc.fileName.endsWith('.gev') || doc.fileName.endsWith('.erk')) {
            parseFile(doc);
            fractaleProvider.refresh();
            rulesProvider.refresh();
            updateCockpit();
            validateDocument(doc);
        }
    });
    vscode.workspace.onDidSaveTextDocument(doc => {
        if (doc.fileName.endsWith('.gev') || doc.fileName.endsWith('.erk')) {
            parseAllFiles();
            fractaleProvider.refresh();
            rulesProvider.refresh();
            updateCockpit();
            validateDocument(doc);
        }
    });
    vscode.workspace.onDidChangeTextDocument(event => {
        if (event.document.fileName.endsWith('.gev') || event.document.fileName.endsWith('.erk')) {
            validateDocument(event.document);
        }
    });
    // Initial parse and validate
    parseAllFiles();
    fractaleProvider.refresh();
    vscode.workspace.textDocuments.forEach(validateDocument);
}
function deactivate() {
    store.objects.clear();
    if (diagnosticCollection) {
        diagnosticCollection.dispose();
    }
}
//# sourceMappingURL=extension.js.map