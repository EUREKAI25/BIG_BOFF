/* =============================================================================
   EUREKAI Cockpit — Tree UI
   ============================================================================= */

/**
 * Render the object tree
 */
function renderTree() {
  const container = document.getElementById('treeContainer');
  if (!container) return;
  
  container.innerHTML = '';
  
  const roots = Store.lineageIndex.roots;
  if (roots.length === 0) {
    container.innerHTML = '<div class="empty-state">Aucun objet</div>';
    return;
  }
  
  for (const root of roots) {
    container.appendChild(renderTreeNode(root, 0));
  }
  
  updateObjectCount();
}

/**
 * Render a single tree node
 */
function renderTreeNode(lineage, depth) {
  const obj = Store.get(lineage);
  if (!obj) return document.createElement('div');
  
  // Filter by active tags
  if (Store.ui.activeTags.length > 0) {
    const objTags = obj.tags || [];
    const hasActiveTag = Store.ui.activeTags.some(t => objTags.includes(t));
    const children = getChildren(lineage);
    if (!hasActiveTag && children.length === 0) {
      return document.createElement('div');
    }
  }
  
  const node = document.createElement('div');
  node.className = 'tree-node';
  node.dataset.lineage = lineage;
  
  const children = getChildren(lineage);
  const hasChildren = children.length > 0;
  const isExpanded = Store.ui.expandedNodes.has(lineage);
  const isSelected = Store.ui.selectedLineage === lineage;
  const name = getLineageName(lineage);
  
  // Header
  const header = document.createElement('div');
  header.className = `tree-node-header${isSelected ? ' selected' : ''}`;
  header.onclick = () => selectNode(lineage);
  
  // Toggle
  const toggle = document.createElement('span');
  toggle.className = `tree-toggle${hasChildren ? ' has-children' : ''}`;
  toggle.textContent = hasChildren ? (isExpanded ? '▼' : '▶') : '·';
  toggle.onclick = (e) => {
    e.stopPropagation();
    if (hasChildren) {
      if (isExpanded) {
        Store.ui.expandedNodes.delete(lineage);
      } else {
        Store.ui.expandedNodes.add(lineage);
      }
      renderTree();
    }
  };
  
  // Label
  const label = document.createElement('span');
  label.className = 'tree-label';
  label.textContent = name;
  
  header.appendChild(toggle);
  header.appendChild(label);
  node.appendChild(header);
  
  // Children
  if (hasChildren && isExpanded) {
    const childrenContainer = document.createElement('div');
    childrenContainer.className = 'tree-children expanded';
    for (const childLineage of children) {
      childrenContainer.appendChild(renderTreeNode(childLineage, depth + 1));
    }
    node.appendChild(childrenContainer);
  }
  
  return node;
}

/**
 * Select a node
 */
function selectNode(lineage) {
  Store.ui.selectedLineage = lineage;
  renderTree();
  renderFractal(lineage);
  updateBreadcrumb(lineage);
  updateJSON();
}

/**
 * Search tree nodes
 */
function searchTree(query) {
  const container = document.getElementById('treeContainer');
  if (!container) return;
  
  if (!query.trim()) {
    renderTree();
    return;
  }
  
  const lowerQuery = query.toLowerCase();
  const matches = Store.getAllLineages().filter(lineage => 
    lineage.toLowerCase().includes(lowerQuery)
  );
  
  container.innerHTML = '';
  
  if (matches.length === 0) {
    container.innerHTML = '<div class="empty-state">Aucun résultat</div>';
    return;
  }
  
  // Expand all ancestors of matches
  for (const match of matches) {
    const ancestors = getAncestors(match);
    for (const ancestor of ancestors) {
      Store.ui.expandedNodes.add(ancestor);
    }
  }
  
  renderTree();
  
  // Highlight matches
  for (const match of matches) {
    const node = container.querySelector(`[data-lineage="${match}"]`);
    if (node) {
      node.querySelector('.tree-node-header')?.classList.add('search-match');
    }
  }
}

/**
 * Update object count
 */
function updateObjectCount() {
  const countEl = document.getElementById('objectCount');
  if (countEl) {
    countEl.textContent = Store.count();
  }
}

/**
 * Update breadcrumb
 */
function updateBreadcrumb(lineage) {
  const container = document.getElementById('breadcrumb');
  if (!container) return;
  
  if (!lineage) {
    container.innerHTML = '';
    return;
  }
  
  const segments = lineage.split(':');
  container.innerHTML = '';
  
  for (let i = 0; i < segments.length; i++) {
    const partialLineage = segments.slice(0, i + 1).join(':');
    
    if (i > 0) {
      const sep = document.createElement('span');
      sep.className = 'breadcrumb-separator';
      sep.textContent = ':';
      container.appendChild(sep);
    }
    
    const item = document.createElement('span');
    item.className = `breadcrumb-item${i === segments.length - 1 ? ' active' : ''}`;
    item.textContent = segments[i];
    item.onclick = () => selectNode(partialLineage);
    container.appendChild(item);
  }
}

// Global access
window.renderTree = renderTree;
window.selectNode = selectNode;
window.searchTree = searchTree;
window.updateObjectCount = updateObjectCount;
window.updateBreadcrumb = updateBreadcrumb;
