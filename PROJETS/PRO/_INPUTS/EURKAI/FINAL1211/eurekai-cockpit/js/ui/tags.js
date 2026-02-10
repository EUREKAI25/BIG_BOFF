/* =============================================================================
   EUREKAI Cockpit — Tags UI
   ============================================================================= */

function renderTags() {
  const container = document.getElementById('tagsContainer');
  if (!container) return;
  
  const tags = Object.keys(Store.tags).sort();
  
  if (tags.length === 0) {
    container.innerHTML = '<div class="empty-state">Aucun tag</div>';
    return;
  }
  
  container.innerHTML = '';
  
  for (const tag of tags) {
    const count = Store.tags[tag]?.length || 0;
    const isActive = Store.ui.activeTags.includes(tag);
    
    const tagEl = document.createElement('div');
    tagEl.className = `tag-item${isActive ? ' active' : ''}`;
    tagEl.innerHTML = `
      <span class="tag-name">${tag}</span>
      <span class="tag-count">${count}</span>
    `;
    tagEl.onclick = () => toggleTagFilter(tag);
    container.appendChild(tagEl);
  }
}

function createTag() {
  const input = document.getElementById('tagCreateInput');
  if (!input) return;
  
  const tagName = input.value.trim().toLowerCase();
  if (!tagName) return;
  
  if (!Store.tags[tagName]) {
    Store.tags[tagName] = [];
    renderTags();
    showToast(`Tag créé: ${tagName}`, 'success');
  } else {
    showToast('Ce tag existe déjà', 'warning');
  }
  
  input.value = '';
}

function toggleTagFilter(tag) {
  const idx = Store.ui.activeTags.indexOf(tag);
  if (idx >= 0) {
    Store.ui.activeTags.splice(idx, 1);
  } else {
    Store.ui.activeTags.push(tag);
  }
  
  renderTags();
  renderTree();
  updateClearFiltersButton();
}

function clearTagFilters() {
  Store.ui.activeTags = [];
  renderTags();
  renderTree();
  updateClearFiltersButton();
}

function updateClearFiltersButton() {
  const btn = document.getElementById('clearTagFilters');
  if (btn) {
    btn.style.display = Store.ui.activeTags.length > 0 ? 'block' : 'none';
  }
}

function addTagToObject(lineage, tag) {
  const obj = Store.get(lineage);
  if (!obj) return false;
  
  if (!obj.tags) obj.tags = [];
  if (!obj.tags.includes(tag)) {
    obj.tags.push(tag);
  }
  
  if (!Store.tags[tag]) Store.tags[tag] = [];
  if (!Store.tags[tag].includes(lineage)) {
    Store.tags[tag].push(lineage);
  }
  
  renderTags();
  return true;
}

function removeTagFromObject(lineage, tag) {
  const obj = Store.get(lineage);
  if (!obj) return false;
  
  if (obj.tags) {
    obj.tags = obj.tags.filter(t => t !== tag);
  }
  
  if (Store.tags[tag]) {
    Store.tags[tag] = Store.tags[tag].filter(l => l !== lineage);
    if (Store.tags[tag].length === 0) {
      delete Store.tags[tag];
    }
  }
  
  renderTags();
  return true;
}

window.renderTags = renderTags;
window.createTag = createTag;
window.toggleTagFilter = toggleTagFilter;
window.clearTagFilters = clearTagFilters;
window.addTagToObject = addTagToObject;
window.removeTagFromObject = removeTagFromObject;
