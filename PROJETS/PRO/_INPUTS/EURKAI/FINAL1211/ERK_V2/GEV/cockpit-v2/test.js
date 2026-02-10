#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { EurkaiRuntime } = require('./eurkai-runtime-v3.js');

const runtime = new EurkaiRuntime();

console.log('🔄 Loading seeds...');
const objects = runtime.loadDir('./seeds', fs, path);
console.log(`✅ Loaded ${objects.length} objects`);

// Debug
const modules = runtime.findByType('Module');
console.log(`📦 Modules: ${modules.length}`);

const panels = runtime.findByType('Panel');
console.log(`📋 Panels: ${panels.length}`);
panels.forEach(p => console.log(`   - ${p.name} (active: ${p.attributes.active || false})`));

// Relations
console.log(`\n🔗 Relations: ${runtime.relations.length}`);
runtime.relations.forEach(r => console.log(`   ${r.subject} IN ${r.target}.${r.list}`));

// Render
console.log('\n🎨 Rendering...');
const html = runtime.renderCockpit();
console.log(`✅ Generated ${html.length} chars`);

fs.writeFileSync('./cockpit-generated.html', html);
console.log('📁 Saved to cockpit-generated.html');

// Count lines
const lines = html.split('\n').length;
console.log(`📊 Lines: ${lines}`);
