/**
 * BIG_BOFF Search — Extension Chrome
 * Recherche par tags avec co-occurrence.
 */

const API = "http://127.0.0.1:7777/api";

// État
const state = {
  includeTags: [],
  excludeTags: [],
  autocompleteIndex: -1,
  autocompleteItems: [],
  currentOffset: 0,
  pageSize: 50,
  totalResults: 0,
  activeTypes: [],
};

// Éléments DOM
const input = document.getElementById("search-input");
const autocompleteEl = document.getElementById("autocomplete");
const selectedTagsEl = document.getElementById("selected-tags");
const coocSection = document.getElementById("cooc-section");
const coocTagsEl = document.getElementById("cooc-tags");
const resultsHeader = document.getElementById("results-header");
const resultsCount = document.getElementById("results-count");
const resultsNav = document.getElementById("results-nav");
const resultsList = document.getElementById("results-list");
const emptyState = document.getElementById("empty-state");
const errorBanner = document.getElementById("error-banner");
const statsEl = document.getElementById("stats");
const typeFiltersEl = document.getElementById("type-filters");

// ── Filtres par type ────────────────────────────────

const TYPE_BUTTONS = [
  { type: "all", label: "Tous", icon: "" },
  { type: "file", label: "Fichiers", icon: '<i class="fa-solid fa-folder"></i>' },
  { type: "email", label: "Emails", icon: '<i class="fa-solid fa-envelope"></i>' },
  { type: "note", label: "Notes", icon: '<i class="fa-solid fa-note-sticky"></i>' },
  { type: "video", label: "Vid\u00e9os", icon: '<i class="fa-solid fa-video"></i>' },
  { type: "event", label: "\u00c9v\u00e9nements", icon: '<i class="fa-solid fa-calendar-days"></i>' },
  { type: "contact", label: "Contacts", icon: '<i class="fa-solid fa-user"></i>' },
  { type: "lieu", label: "Lieux", icon: '<i class="fa-solid fa-location-dot"></i>' },
  { type: "vault", label: "Vault", icon: '<i class="fa-solid fa-lock"></i>' },
  { type: "favori", label: "Favoris", icon: '<i class="fa-solid fa-heart"></i>' },
];

function renderTypeFilters() {
  typeFiltersEl.innerHTML = TYPE_BUTTONS.map(b => {
    const isActive = b.type === "all"
      ? state.activeTypes.length === 0
      : b.type === "favori"
        ? state.includeTags.includes("favori")
        : state.activeTypes.includes(b.type);
    return `<span class="type-btn${isActive ? ' active' : ''}" data-type="${b.type}">${b.icon ? b.icon + ' ' : ''}${b.label}</span>`;
  }).join("");

  typeFiltersEl.querySelectorAll(".type-btn").forEach(el => {
    el.addEventListener("click", () => {
      const t = el.dataset.type;
      if (t === "all") {
        state.activeTypes = [];
      } else if (t === "favori") {
        if (state.includeTags.includes("favori")) {
          state.includeTags = state.includeTags.filter(x => x !== "favori");
        } else {
          state.includeTags.push("favori");
        }
      } else {
        // Radio : un seul type actif à la fois
        if (state.activeTypes.includes(t)) state.activeTypes = [];
        else state.activeTypes = [t];
      }
      refresh();
    });
  });
}

// ── Favoris ─────────────────────────────────────────

async function toggleFavorite(itemId, btnEl) {
  try {
    const resp = await fetch(`${API}/favorite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: parseInt(itemId) }),
    });
    const data = await resp.json();
    if (data.ok) {
      btnEl.innerHTML = data.favorited ? '<i class="fa-solid fa-heart"></i>' : '<i class="fa-regular fa-heart"></i>';
      btnEl.classList.toggle("active", data.favorited);
    }
  } catch {}
}

async function checkFavorites(ids) {
  if (!ids.length) return;
  try {
    const data = await apiFetch("favorite/check", { ids: ids.join(",") });
    const favSet = new Set(data.favorited || []);
    document.querySelectorAll(".fav-btn[data-fav-id]").forEach(btn => {
      const id = parseInt(btn.dataset.favId);
      if (favSet.has(id)) {
        btn.innerHTML = '<i class="fa-solid fa-heart"></i>';
        btn.classList.add("active");
      }
    });
  } catch {}
}

// ── API ─────────────────────────────────────────────

async function apiFetch(endpoint, params = {}) {
  const url = new URL(`${API}/${endpoint}`);
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) {
      v.forEach(val => url.searchParams.append(k, val));
    } else {
      url.searchParams.set(k, v);
    }
  }
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

async function checkServer() {
  try {
    const data = await apiFetch("stats");
    statsEl.textContent = `${data.total_items.toLocaleString()} fichiers · ${data.unique_tags.toLocaleString()} tags`;
    errorBanner.style.display = "none";
    return true;
  } catch {
    errorBanner.style.display = "block";
    statsEl.textContent = "";
    return false;
  }
}

// ── Autocomplete ────────────────────────────────────

let debounceTimer;

function onInput() {
  clearTimeout(debounceTimer);
  const q = input.value.trim();
  if (q.length < 1) {
    hideAutocomplete();
    return;
  }
  debounceTimer = setTimeout(() => fetchAutocomplete(q), 150);
}

async function fetchAutocomplete(q) {
  try {
    const data = await apiFetch("autocomplete", { q });
    // Filtrer les tags déjà sélectionnés
    const selected = new Set([...state.includeTags, ...state.excludeTags]);
    state.autocompleteItems = data.tags.filter(t => !selected.has(t.tag));
    state.autocompleteIndex = -1;
    renderAutocomplete();
  } catch {
    hideAutocomplete();
  }
}

function renderAutocomplete() {
  if (state.autocompleteItems.length === 0) {
    hideAutocomplete();
    return;
  }
  autocompleteEl.innerHTML = state.autocompleteItems.map((t, i) => `
    <div class="item ${i === state.autocompleteIndex ? 'selected' : ''}"
         data-tag="${esc(t.tag)}">
      <span>${highlight(t.tag, input.value.trim())}</span>
      <span class="count">${t.count.toLocaleString()}</span>
    </div>
  `).join("");
  autocompleteEl.style.display = "block";

  // Click handlers
  autocompleteEl.querySelectorAll(".item").forEach(el => {
    el.addEventListener("click", () => {
      addIncludeTag(el.dataset.tag);
    });
  });
}

function hideAutocomplete() {
  autocompleteEl.style.display = "none";
  state.autocompleteItems = [];
  state.autocompleteIndex = -1;
}

function highlight(text, query) {
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  if (idx < 0) return esc(text);
  return esc(text.slice(0, idx)) +
    `<strong>${esc(text.slice(idx, idx + query.length))}</strong>` +
    esc(text.slice(idx + query.length));
}

// ── Tags ────────────────────────────────────────────

function addIncludeTag(tag) {
  if (!state.includeTags.includes(tag) && !state.excludeTags.includes(tag)) {
    state.includeTags.push(tag);
  }
  input.value = "";
  hideAutocomplete();
  refresh();
  input.focus();
}

function addExcludeTag(tag) {
  if (!state.excludeTags.includes(tag) && !state.includeTags.includes(tag)) {
    state.excludeTags.push(tag);
  }
  refresh();
}

function removeTag(tag) {
  state.includeTags = state.includeTags.filter(t => t !== tag);
  state.excludeTags = state.excludeTags.filter(t => t !== tag);
  refresh();
}

function toggleTagType(tag) {
  if (state.includeTags.includes(tag)) {
    state.includeTags = state.includeTags.filter(t => t !== tag);
    state.excludeTags.push(tag);
  } else if (state.excludeTags.includes(tag)) {
    state.excludeTags = state.excludeTags.filter(t => t !== tag);
    state.includeTags.push(tag);
  }
  refresh();
}

function renderSelectedTags() {
  let html = "";
  state.includeTags.forEach(tag => {
    html += `<span class="tag include" data-tag="${esc(tag)}">+${esc(tag)}</span>`;
  });
  state.excludeTags.forEach(tag => {
    html += `<span class="tag exclude" data-tag="${esc(tag)}">−${esc(tag)}</span>`;
  });
  selectedTagsEl.innerHTML = html;

  // Clic → toggle +/-. Long clic ou double clic → supprimer.
  selectedTagsEl.querySelectorAll(".tag").forEach(el => {
    let longTimer;
    let wasLong = false;

    el.addEventListener("mousedown", () => {
      wasLong = false;
      longTimer = setTimeout(() => { wasLong = true; removeTag(el.dataset.tag); }, 500);
    });
    el.addEventListener("mouseup", () => {
      clearTimeout(longTimer);
      if (!wasLong) toggleTagType(el.dataset.tag);
    });
    el.addEventListener("mouseleave", () => clearTimeout(longTimer));
    el.addEventListener("dblclick", () => removeTag(el.dataset.tag));
    el.addEventListener("contextmenu", (e) => e.preventDefault());
  });
}

// ── Co-occurrence ───────────────────────────────────

async function fetchCooccurrence() {
  if (state.includeTags.length === 0 && state.activeTypes.length === 0) {
    coocSection.style.display = "none";
    return;
  }
  try {
    const coocParams = {
      include: state.includeTags,
      exclude: state.excludeTags,
    };
    if (state.activeTypes.length > 0) coocParams.types = state.activeTypes.join(",");
    const data = await apiFetch("cooccurrence", coocParams);
    renderCooccurrence(data.tags);
  } catch {
    coocSection.style.display = "none";
  }
}

function renderCooccurrence(tags) {
  if (tags.length === 0) {
    coocSection.style.display = "none";
    return;
  }
  coocSection.style.display = "block";
  coocTagsEl.innerHTML = tags.map(t => `
    <span class="cooc-tag" data-tag="${esc(t.tag)}">
      ${esc(t.tag)}
      <span class="cnt">${t.count.toLocaleString()}</span>
    </span>
  `).join("");

  coocTagsEl.querySelectorAll(".cooc-tag").forEach(el => {
    let longTimer;
    let wasLong = false;

    // Clic = inclure (+)
    el.addEventListener("mousedown", () => {
      wasLong = false;
      longTimer = setTimeout(() => { wasLong = true; addExcludeTag(el.dataset.tag); }, 500);
    });
    el.addEventListener("mouseup", () => {
      clearTimeout(longTimer);
      if (!wasLong) addIncludeTag(el.dataset.tag);
    });
    el.addEventListener("mouseleave", () => clearTimeout(longTimer));

    // Double clic = exclure (-) aussi
    el.addEventListener("dblclick", (e) => {
      e.preventDefault();
      // Retirer le tag s'il a été ajouté en + par le premier clic, puis l'ajouter en -
      removeTag(el.dataset.tag);
      addExcludeTag(el.dataset.tag);
    });

    el.addEventListener("contextmenu", (e) => e.preventDefault());
  });
}

// ── Résultats ───────────────────────────────────────

async function fetchResults() {
  if (state.includeTags.length === 0 && state.activeTypes.length === 0) {
    resultsList.innerHTML = "";
    resultsHeader.style.display = "none";
    typeFiltersEl.style.display = "none";
    coocSection.style.display = "none";
    emptyState.style.display = "block";
    return;
  }
  emptyState.style.display = "none";
  typeFiltersEl.style.display = "";

  try {
    const searchParams = {
      include: state.includeTags,
      exclude: state.excludeTags,
      limit: state.pageSize,
      offset: state.currentOffset,
    };
    if (state.activeTypes.length > 0) {
      searchParams.types = state.activeTypes.join(",");
    }
    const data = await apiFetch("search", searchParams);
    state.totalResults = data.total;
    renderResults(data.results);
  } catch {
    resultsList.innerHTML = '<div class="loading">Erreur de chargement</div>';
  }
}

function renderResults(results) {
  resultsHeader.style.display = "flex";
  const start = state.currentOffset + 1;
  const end = Math.min(state.currentOffset + results.length, state.totalResults);
  resultsCount.textContent = `${start}-${end} sur ${state.totalResults.toLocaleString()}`;

  // Navigation
  let nav = "";
  if (state.currentOffset > 0) {
    nav += '<a href="#" id="prev-page" style="margin-right:8px;color:#4a90d9">&larr; Prec</a>';
  }
  if (state.currentOffset + state.pageSize < state.totalResults) {
    nav += '<a href="#" id="next-page" style="color:#4a90d9">Suiv &rarr;</a>';
  }
  resultsNav.innerHTML = nav;

  document.getElementById("prev-page")?.addEventListener("click", (e) => {
    e.preventDefault();
    state.currentOffset = Math.max(0, state.currentOffset - state.pageSize);
    fetchResults();
  });
  document.getElementById("next-page")?.addEventListener("click", (e) => {
    e.preventDefault();
    state.currentOffset += state.pageSize;
    fetchResults();
  });

  if (results.length === 0) {
    resultsList.innerHTML = '<div class="loading">Aucun resultat</div>';
    return;
  }

  const favHeart = (id) => `<span class="fav-btn" data-fav-id="${id}" title="Favori"><i class="fa-regular fa-heart"></i></span>`;

  resultsList.innerHTML = results.map(r => {
    if (r.type === "email") {
      const snippetHtml = r.snippet ? `<div class="result-snippet">${esc(r.snippet)}</div>` : "";
      return `
        <div class="result-item result-email" data-id="${r.id}">
          <div class="result-name">
            <span class="icon icon-email"><i class="fa-solid fa-envelope"></i></span>
            ${esc(r.nom)}
            ${favHeart(r.id)}
          </div>
          <div class="result-meta">${esc(r.chemin)}</div>
          ${snippetHtml}
          <div class="result-meta">${r.date_modif || "?"}</div>
        </div>`;
    }
    if (r.type === "note") {
      return `
        <div class="result-item result-note" data-id="${r.id}">
          <div class="result-name">
            <span class="icon icon-note"><i class="fa-solid fa-note-sticky"></i></span>
            ${esc(r.nom)}
            ${favHeart(r.id)}
          </div>
          <div class="result-meta">${esc(r.chemin)}</div>
          <div class="result-meta">${r.date_modif || "?"}</div>
        </div>`;
    }
    if (r.type === "video") {
      const pIcons = {"youtube":'<i class="fa-brands fa-youtube"></i>',"facebook":'<i class="fa-brands fa-facebook"></i>',"vimeo":'<i class="fa-brands fa-vimeo-v"></i>',"dailymotion":'<i class="fa-solid fa-play"></i>',"instagram":'<i class="fa-brands fa-instagram"></i>',"tiktok":'<i class="fa-brands fa-tiktok"></i>'};
      const pIcon = pIcons[r.platform] || '<i class="fa-solid fa-play"></i>';
      return `
        <div class="result-item result-video" data-id="${r.id}" data-url="${esc(r.url || r.chemin)}">
          <div class="result-name">
            <span class="icon icon-video">${pIcon}</span>
            ${esc(r.nom)}
            ${favHeart(r.id)}
          </div>
          <div class="result-meta">${esc(r.platform || "")} · ${r.date_modif || "?"}</div>
        </div>`;
    }
    if (r.type === "event") {
      const recLabels = {"daily":"chaque jour","weekly":"chaque semaine","monthly":"chaque mois","yearly":"chaque ann\u00e9e"};
      const recStr = r.recurrence && r.recurrence !== "none" ? ' \u00b7 <i class="fa-solid fa-rotate"></i> ' + (recLabels[r.recurrence] || "") : "";
      const tagsStr = r.tags_raw ? `<div class="result-meta" style="margin-top:2px">${esc(r.tags_raw)}</div>` : "";
      return `
        <div class="result-item result-event" data-id="${r.id}">
          <div class="result-name">
            <span class="icon icon-event"><i class="fa-solid fa-calendar-days"></i></span>
            ${esc(r.nom)}
            ${favHeart(r.id)}
          </div>
          <div class="result-meta">${esc(r.date_fr || r.date_modif || "")}${recStr}</div>
          ${tagsStr}
        </div>`;
    }
    if (r.type === "contact") {
      const ctIcon = r.contact_type === "entreprise" ? '<i class="fa-solid fa-building"></i>' : '<i class="fa-solid fa-user"></i>';
      return `
        <div class="result-item result-contact" data-id="${r.id}">
          <div class="result-name">
            <span class="icon icon-contact">${ctIcon}</span>
            ${esc(r.nom)}
            ${favHeart(r.id)}
          </div>
          <div class="result-meta">${esc(r.chemin)}</div>
        </div>`;
    }
    if (r.type === "lieu") {
      return `
        <div class="result-item result-lieu" data-id="${r.id}">
          <div class="result-name">
            <span class="icon icon-lieu"><i class="fa-solid fa-location-dot"></i></span>
            ${esc(r.nom)}
            ${favHeart(r.id)}
          </div>
          <div class="result-meta">${esc(r.chemin)}</div>
        </div>`;
    }
    if (r.type === "vault") {
      return `
        <div class="result-item result-vault" data-id="${r.id}">
          <div class="result-name">
            <span class="icon icon-vault"><i class="fa-solid fa-lock"></i></span>
            ${esc(r.nom)}
            ${favHeart(r.id)}
          </div>
          <div class="result-meta">${esc(r.chemin)} ${r.project ? "· " + esc(r.project) : ""}</div>
        </div>`;
    }
    const iconContent = r.est_dossier ? '<i class="fa-solid fa-folder"></i>' : fileIcon(r.extension);
    const iconHtml = r.is_media
      ? `<img class="thumb" data-thumb-id="${r.id}" src="" alt="" style="display:none"><span class="icon" style="display:inline">${iconContent}</span>`
      : `<span class="icon">${iconContent}</span>`;
    return `
      <div class="result-item" data-id="${r.id}" title="${esc(r.chemin)}">
        <div class="result-name">
          ${iconHtml}
          ${esc(r.nom)}
          ${favHeart(r.id)}
          <span class="result-actions">
            <span class="action-btn open-btn" data-id="${r.id}" title="Ouvrir"><i class="fa-solid fa-arrow-up-right-from-square"></i></span>
            <span class="action-btn reveal-btn" data-id="${r.id}" title="Montrer dans Finder"><i class="fa-solid fa-folder-open"></i></span>
          </span>
        </div>
        <div class="result-meta">${formatSize(r.taille)} · ${r.date_modif || "?"}</div>
      </div>`;
  }).join("");

  // Charger les miniatures en lazy
  resultsList.querySelectorAll("img.thumb[data-thumb-id]").forEach(img => {
    img.onerror = () => { img.style.display = "none"; if (img.nextElementSibling) img.nextElementSibling.style.display = "inline"; };
    apiFetch("thumbnail", { id: img.dataset.thumbId, size: "48" }).then(d => {
      if (d.data) { img.src = d.data; img.style.display = "inline-block"; img.nextElementSibling.style.display = "none"; }
    }).catch(() => {});
  });

  // Clic événement → toggle détail
  resultsList.querySelectorAll(".result-event").forEach(el => {
    el.addEventListener("click", () => toggleEventView(el));
  });
  // Clic contact → toggle détail
  resultsList.querySelectorAll(".result-contact").forEach(el => {
    el.addEventListener("click", () => toggleContactView(el));
  });
  // Clic lieu → toggle détail
  resultsList.querySelectorAll(".result-lieu").forEach(el => {
    el.addEventListener("click", () => toggleLieuView(el));
  });
  // Clic fichier → ouvrir
  resultsList.querySelectorAll(".result-item:not(.result-email):not(.result-note):not(.result-vault):not(.result-video):not(.result-event):not(.result-contact):not(.result-lieu)").forEach(el => {
    el.addEventListener("click", (e) => {
      if (e.target.classList.contains("action-btn")) return;
      openFile(el.dataset.id);
    });
  });
  // Clic email → afficher contenu
  resultsList.querySelectorAll(".result-email").forEach(el => {
    el.addEventListener("click", () => toggleEmailView(el));
  });
  // Clic vault → afficher mot de passe
  resultsList.querySelectorAll(".result-vault").forEach(el => {
    el.addEventListener("click", () => toggleVaultView(el));
  });
  // Clic note → afficher contenu
  resultsList.querySelectorAll(".result-note").forEach(el => {
    el.addEventListener("click", () => toggleNoteView(el));
  });
  // Clic vidéo → ouvrir l'URL
  resultsList.querySelectorAll(".result-video").forEach(el => {
    el.addEventListener("click", () => window.open(el.dataset.url, "_blank"));
  });
  resultsList.querySelectorAll(".open-btn").forEach(el => {
    el.addEventListener("click", () => openFile(el.dataset.id));
  });
  resultsList.querySelectorAll(".reveal-btn").forEach(el => {
    el.addEventListener("click", () => revealFile(el.dataset.id));
  });
  // Coeurs favoris
  resultsList.querySelectorAll(".fav-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleFavorite(btn.dataset.favId, btn);
    });
  });
  // Vérifier les favoris existants
  const allIds = results.map(r => r.id);
  checkFavorites(allIds);
}

async function openFile(id) {
  try { await apiFetch("open", { id }); } catch {}
}

async function revealFile(id) {
  try { await apiFetch("reveal", { id }); } catch {}
}

// ── Refresh ─────────────────────────────────────────

function refresh() {
  state.currentOffset = 0;
  renderTypeFilters();
  renderSelectedTags();
  fetchResults();
  fetchCooccurrence();
}

// ── Keyboard ────────────────────────────────────────

input.addEventListener("input", onInput);

input.addEventListener("keydown", (e) => {
  const items = state.autocompleteItems;
  if (e.key === "ArrowDown") {
    e.preventDefault();
    state.autocompleteIndex = Math.min(state.autocompleteIndex + 1, items.length - 1);
    renderAutocomplete();
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    state.autocompleteIndex = Math.max(state.autocompleteIndex - 1, -1);
    renderAutocomplete();
  } else if (e.key === "Enter") {
    e.preventDefault();
    if (state.autocompleteIndex >= 0 && items[state.autocompleteIndex]) {
      addIncludeTag(items[state.autocompleteIndex].tag);
    } else if (items.length > 0) {
      addIncludeTag(items[0].tag);
    }
  } else if (e.key === "Escape") {
    hideAutocomplete();
  } else if (e.key === "Backspace" && input.value === "" && state.includeTags.length > 0) {
    // Supprimer le dernier tag inclus
    state.includeTags.pop();
    refresh();
  }
});

// ── Helpers ─────────────────────────────────────────

function esc(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function formatSize(bytes) {
  if (!bytes || bytes === 0) return "—";
  if (bytes < 1024) return bytes + " o";
  if (bytes < 1048576) return (bytes / 1024).toFixed(0) + " Ko";
  if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + " Mo";
  return (bytes / 1073741824).toFixed(2) + " Go";
}

function fileIcon(ext) {
  if (!ext) return '<i class="fa-solid fa-file icon-file"></i>';
  ext = ext.toLowerCase();
  const icons = {
    ".py": '<i class="fa-brands fa-python icon-file"></i>',
    ".js": '<i class="fa-brands fa-js icon-file"></i>',
    ".ts": '<i class="fa-brands fa-js icon-file"></i>',
    ".html": '<i class="fa-brands fa-html5 icon-file"></i>',
    ".css": '<i class="fa-brands fa-css3-alt icon-file"></i>',
    ".md": '<i class="fa-solid fa-file-lines icon-file"></i>',
    ".txt": '<i class="fa-solid fa-file-lines icon-file"></i>',
    ".pdf": '<i class="fa-solid fa-file-pdf" style="color:#c00"></i>',
    ".jpg": '<i class="fa-solid fa-file-image" style="color:#27ae60"></i>',
    ".jpeg": '<i class="fa-solid fa-file-image" style="color:#27ae60"></i>',
    ".png": '<i class="fa-solid fa-file-image" style="color:#27ae60"></i>',
    ".gif": '<i class="fa-solid fa-file-image" style="color:#27ae60"></i>',
    ".svg": '<i class="fa-solid fa-file-image" style="color:#27ae60"></i>',
    ".webp": '<i class="fa-solid fa-file-image" style="color:#27ae60"></i>',
    ".mp4": '<i class="fa-solid fa-file-video icon-video"></i>',
    ".mov": '<i class="fa-solid fa-file-video icon-video"></i>',
    ".avi": '<i class="fa-solid fa-file-video icon-video"></i>',
    ".mp3": '<i class="fa-solid fa-file-audio" style="color:#9b59b6"></i>',
    ".wav": '<i class="fa-solid fa-file-audio" style="color:#9b59b6"></i>',
    ".flac": '<i class="fa-solid fa-file-audio" style="color:#9b59b6"></i>',
    ".zip": '<i class="fa-solid fa-file-zipper" style="color:#7f8c8d"></i>',
    ".rar": '<i class="fa-solid fa-file-zipper" style="color:#7f8c8d"></i>',
    ".json": '<i class="fa-solid fa-file-code icon-file"></i>',
    ".csv": '<i class="fa-solid fa-file-csv icon-file"></i>',
    ".xml": '<i class="fa-solid fa-file-code icon-file"></i>',
  };
  return icons[ext] || '<i class="fa-solid fa-file icon-file"></i>';
}

// ── Email viewer ─────────────────────────────────────

let expandedEmailId = null;

async function toggleEmailView(el) {
  const id = el.dataset.id;

  // Si déjà ouvert → fermer
  const existing = el.nextElementSibling;
  if (existing && existing.classList.contains("email-content")) {
    existing.remove();
    expandedEmailId = null;
    return;
  }

  // Fermer tout autre email ouvert
  document.querySelectorAll(".email-content, .email-loading").forEach(e => e.remove());

  // Loading
  const loading = document.createElement("div");
  loading.className = "email-loading";
  loading.textContent = "Chargement de l\u2019email...";
  el.after(loading);
  expandedEmailId = id;

  try {
    const data = await apiFetch("email", { id });
    loading.remove();
    if (expandedEmailId !== id) return;

    if (data.error) {
      const err = document.createElement("div");
      err.className = "email-content";
      err.innerHTML = '<div style="color:#c00">Erreur : ' + esc(data.error) + '</div>';
      el.after(err);
      return;
    }

    renderEmailPanel(el, data);
  } catch {
    loading.remove();
    const err = document.createElement("div");
    err.className = "email-content";
    err.innerHTML = '<div style="color:#c00">Impossible de charger l\u2019email</div>';
    el.after(err);
  }
}

function renderEmailPanel(el, data) {
  const div = document.createElement("div");
  div.className = "email-content";

  // En-tête
  const subj = document.createElement("div");
  subj.className = "eml-hdr";
  subj.innerHTML = "<strong>" + esc(data.subject || "(sans sujet)") + "</strong>";
  div.appendChild(subj);

  const fromTo = document.createElement("div");
  fromTo.className = "eml-hdr";
  fromTo.textContent = "De : " + (data.from || "?") + "  \u2192  " + (data.to || "?");
  div.appendChild(fromTo);

  const date = document.createElement("div");
  date.className = "eml-hdr";
  date.textContent = data.date || "";
  div.appendChild(date);

  const hr = document.createElement("hr");
  hr.style.cssText = "border:none;border-top:1px solid #ddd;margin:8px 0";
  div.appendChild(hr);

  // Corps
  if (data.body_html) {
    const iframe = document.createElement("iframe");
    iframe.sandbox = "allow-same-origin";
    iframe.style.cssText = "width:100%;border:none;min-height:150px;background:#fff;border-radius:4px;";
    iframe.srcdoc = data.body_html;
    div.appendChild(iframe);
    iframe.addEventListener("load", () => {
      try {
        const h = iframe.contentDocument.body.scrollHeight;
        iframe.style.height = Math.min(h + 20, 400) + "px";
      } catch {}
    });
  } else if (data.body_text) {
    const pre = document.createElement("pre");
    pre.textContent = data.body_text;
    div.appendChild(pre);
  } else {
    const empty = document.createElement("div");
    empty.style.color = "#aaa";
    empty.textContent = "(contenu vide)";
    div.appendChild(empty);
  }

  // Tags
  const tagsSection = document.createElement("div");
  tagsSection.style.cssText = "margin-top:12px;padding-top:8px;border-top:1px solid #eee";
  tagsSection.innerHTML = '<div style="font-size:11px;color:#666;margin-bottom:6px;font-weight:500">TAGS</div><div class="tags-container"></div>';
  div.appendChild(tagsSection);

  el.after(div);

  // Charger les tags (item_id = id négatif pour email)
  const tagsContainer = div.querySelector('.tags-container');
  renderItemTags(id, tagsContainer);
}

// ── Note viewer ─────────────────────────────────────

function linkifyBody(text) {
  const escaped = esc(text);
  return escaped.replace(/(https?:\/\/[^\s<]+)/g, (url) => {
    const isVideo = /youtube\.com|youtu\.be|vimeo\.com|dailymotion\.com|facebook\.com\/.*\/videos/i.test(url);
    const cls = isVideo ? "video-link" : "";
    const icon = isVideo ? "\u25B6 " : "";
    return `<a href="${url}" target="_blank" class="${cls}">${icon}${url}</a>`;
  });
}

async function toggleNoteView(el) {
  const id = el.dataset.id;

  // Si déjà ouvert → fermer
  const existing = el.nextElementSibling;
  if (existing && existing.classList.contains("note-content")) {
    existing.remove();
    return;
  }

  // Fermer tout autre note ouverte
  document.querySelectorAll(".note-content, .note-loading").forEach(e => e.remove());

  // Loading
  const loading = document.createElement("div");
  loading.className = "note-loading";
  loading.textContent = "Chargement\u2026";
  el.after(loading);

  try {
    const data = await apiFetch("note", { id });
    loading.remove();

    if (data.error) {
      const err = document.createElement("div");
      err.className = "note-content";
      err.innerHTML = '<div style="color:#c00">Erreur : ' + esc(data.error) + '</div>';
      el.after(err);
      return;
    }

    const div = document.createElement("div");
    div.className = "note-content";

    const title = document.createElement("div");
    title.className = "note-title";
    title.textContent = data.title || "(sans titre)";
    div.appendChild(title);

    const date = document.createElement("div");
    date.className = "note-date";
    date.textContent = data.date || "";
    div.appendChild(date);

    const hr = document.createElement("hr");
    hr.style.cssText = "border:none;border-top:1px solid #e0d5c0;margin:6px 0";
    div.appendChild(hr);

    const body = document.createElement("div");
    body.className = "note-body";
    body.innerHTML = linkifyBody(data.body || "(vide)");
    div.appendChild(body);

    // Tags
    const tagsSection = document.createElement("div");
    tagsSection.style.cssText = "margin-top:12px;padding-top:8px;border-top:1px solid #e0d5c0";
    tagsSection.innerHTML = '<div style="font-size:11px;color:#666;margin-bottom:6px;font-weight:500">TAGS</div><div class="tags-container"></div>';
    div.appendChild(tagsSection);

    el.after(div);
    div.querySelectorAll("a").forEach(a => { a.addEventListener("click", e => e.stopPropagation()); });

    // Charger les tags
    const tagsContainer = div.querySelector('.tags-container');
    renderItemTags(id, tagsContainer);
  } catch {
    loading.remove();
  }
}

// ── Vault viewer ─────────────────────────────────────

let vaultUnlocked = false;

async function checkVaultStatus() {
  try {
    const data = await apiFetch("vault/status");
    vaultUnlocked = data.unlocked;
  } catch {
    vaultUnlocked = false;
  }
}

async function toggleVaultView(el) {
  const id = el.dataset.id;

  // Si déjà ouvert → fermer
  const existing = el.nextElementSibling;
  if (existing && existing.classList.contains("vault-panel")) {
    existing.remove();
    return;
  }

  // Fermer tout autre panneau vault
  document.querySelectorAll(".vault-panel, .vault-loading").forEach(e => e.remove());

  // Vérifier si déverrouillé
  await checkVaultStatus();
  if (!vaultUnlocked) {
    showVaultModal(el);
    return;
  }

  loadVaultEntry(el, id);
}

function showVaultModal(afterEl) {
  // Créer la modale
  const overlay = document.createElement("div");
  overlay.className = "vault-modal-overlay";
  overlay.innerHTML = `
    <div class="vault-modal">
      <h3><i class="fa-solid fa-lock"></i> Mot de passe maitre</h3>
      <div class="vm-error" style="display:none"></div>
      <input type="password" placeholder="Entrer le mot de passe maitre..." autofocus>
      <div class="vm-btns">
        <button class="vm-btn vm-btn-cancel">Annuler</button>
        <button class="vm-btn vm-btn-ok">OK</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  const inputEl = overlay.querySelector("input");
  const errorEl = overlay.querySelector(".vm-error");
  const okBtn = overlay.querySelector(".vm-btn-ok");
  const cancelBtn = overlay.querySelector(".vm-btn-cancel");

  cancelBtn.addEventListener("click", () => overlay.remove());
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.remove();
  });

  async function doUnlock() {
    const master = inputEl.value;
    if (!master) return;
    try {
      const resp = await fetch(`${API}/vault/unlock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ master }),
      });
      const data = await resp.json();
      if (data.ok) {
        vaultUnlocked = true;
        overlay.remove();
        // Charger l'entrée
        if (afterEl) loadVaultEntry(afterEl, afterEl.dataset.id);
      } else {
        errorEl.textContent = data.error || "Erreur";
        errorEl.style.display = "block";
        inputEl.value = "";
        inputEl.focus();
      }
    } catch {
      errorEl.textContent = "Erreur de connexion";
      errorEl.style.display = "block";
    }
  }

  okBtn.addEventListener("click", doUnlock);
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") doUnlock();
    if (e.key === "Escape") overlay.remove();
  });
  inputEl.focus();
}

async function loadVaultEntry(el, id) {
  const loading = document.createElement("div");
  loading.className = "vault-loading";
  loading.textContent = "D\u00e9chiffrement...";
  el.after(loading);

  try {
    const data = await apiFetch("vault/get", { id });
    loading.remove();

    if (data.error) {
      const err = document.createElement("div");
      err.className = "vault-panel";
      err.innerHTML = '<div style="color:#c00">' + esc(data.error) + '</div>';
      el.after(err);
      return;
    }

    const div = document.createElement("div");
    div.className = "vault-panel";

    let html = '';
    html += '<div class="vp-row"><span class="vp-label">Service</span><span class="vp-value">' + esc(data.service) + '</span></div>';
    if (data.login) {
      html += '<div class="vp-row"><span class="vp-label">Login</span><span class="vp-value">' + esc(data.login) + '</span></div>';
    }
    if (data.password) {
      html += '<div class="vp-row"><span class="vp-label">Mdp</span><span class="vp-pwd" id="vault-pwd-display">\u25CF\u25CF\u25CF\u25CF\u25CF\u25CF\u25CF\u25CF</span>';
      html += ' <button class="vp-btn" id="vault-show-btn">Voir</button>';
      html += ' <button class="vp-btn" id="vault-copy-btn">Copier</button>';
      html += '</div>';
    }
    if (data.url) {
      html += '<div class="vp-row"><span class="vp-label">URL</span><span class="vp-value" style="font-size:10px">' + esc(data.url) + '</span></div>';
    }
    if (data.notes) {
      html += '<div class="vp-row"><span class="vp-label">Notes</span><span class="vp-value" style="font-size:10px">' + esc(data.notes) + '</span></div>';
    }

    div.innerHTML = html;
    el.after(div);

    // Bouton Voir
    const showBtn = div.querySelector("#vault-show-btn");
    const pwdDisplay = div.querySelector("#vault-pwd-display");
    if (showBtn && pwdDisplay) {
      let visible = false;
      showBtn.addEventListener("click", () => {
        visible = !visible;
        pwdDisplay.textContent = visible ? data.password : "\u25CF\u25CF\u25CF\u25CF\u25CF\u25CF\u25CF\u25CF";
        showBtn.textContent = visible ? "Masquer" : "Voir";
      });
    }

    // Bouton Copier
    const copyBtn = div.querySelector("#vault-copy-btn");
    if (copyBtn) {
      copyBtn.addEventListener("click", async () => {
        try {
          await apiFetch("vault/copy", { id });
          copyBtn.textContent = "Copi\u00e9 !";
          copyBtn.classList.add("copied");
          setTimeout(() => {
            copyBtn.textContent = "Copier";
            copyBtn.classList.remove("copied");
          }, 2000);
        } catch {
          copyBtn.textContent = "Erreur";
        }
      });
    }
  } catch {
    loading.remove();
  }
}

// ── Event viewer ─────────────────────────────────────

async function toggleEventView(el) {
  const id = el.dataset.id;
  const existing = el.nextElementSibling;
  if (existing && existing.classList.contains("event-content")) {
    existing.remove();
    return;
  }
  document.querySelectorAll(".event-content").forEach(e => e.remove());
  try {
    const data = await apiFetch("event", { id });
    if (data.error) return;
    const div = document.createElement("div");
    div.className = "event-content";
    const recLabels = {"daily":"chaque jour","weekly":"chaque semaine","monthly":"chaque mois","yearly":"chaque ann\u00e9e"};
    let h = `<div class="ev-title"><i class="fa-solid fa-calendar-days icon-event"></i> ${esc(data.title)}</div>`;
    h += `<div class="ev-row"><span class="ev-label">Date</span>${esc(data.date_fr || data.date_start)}</div>`;
    if (data.date_end) h += `<div class="ev-row"><span class="ev-label">Fin</span>${esc(data.date_end)}</div>`;
    if (data.location) h += `<div class="ev-row"><span class="ev-label">Lieu</span>${esc(data.location)}</div>`;
    if (data.description) h += `<div class="ev-row"><span class="ev-label">D\u00e9tail</span>${esc(data.description)}</div>`;
    if (data.recurrence && data.recurrence !== "none") {
      let rl = recLabels[data.recurrence] || data.recurrence;
      if (data.recurrence_interval > 1) {
        const units = {"daily":"jours","weekly":"semaines","monthly":"mois","yearly":"ans"};
        rl = "tous les " + data.recurrence_interval + " " + (units[data.recurrence] || "");
      }
      h += `<div class="ev-row"><span class="ev-label">R\u00e9currence</span><i class="fa-solid fa-rotate"></i> ${rl}</div>`;
    }
    if (data.tags_raw) {
      h += '<div class="ev-tags">';
      data.tags_raw.split(",").forEach(t => { t = t.trim(); if (t) h += `<span class="ev-tag">${esc(t)}</span>`; });
      h += '</div>';
    }
    div.innerHTML = h;

    // Tags modifiables (table tags)
    const tagsSection = document.createElement("div");
    tagsSection.style.cssText = "margin-top:8px;padding-top:6px;border-top:1px solid #f5e6d3";
    tagsSection.innerHTML = '<div style="font-size:11px;color:#666;margin-bottom:6px;font-weight:500">TAGS (modifiables)</div><div class="tags-container"></div>';
    div.appendChild(tagsSection);

    el.after(div);

    // Charger les tags
    const tagsContainer = div.querySelector('.tags-container');
    renderItemTags(id, tagsContainer);
  } catch {}
}

// ── Contact / Lieu detail ─────────────────────────────

async function toggleContactView(el) {
  const id = el.dataset.id;
  const existing = el.nextElementSibling;
  if (existing && existing.classList.contains("contact-content")) {
    existing.remove();
    return;
  }
  document.querySelectorAll(".contact-content").forEach(e => e.remove());
  try {
    const data = await apiFetch("contact", { id });
    if (data.error) return;
    const div = document.createElement("div");
    div.className = "contact-content";
    const display = ((data.prenom || "") + " " + (data.nom || "")).trim();
    let h = `<div class="ct-name">${data.type === "entreprise" ? '<i class="fa-solid fa-building icon-contact"></i>' : '<i class="fa-solid fa-user icon-contact"></i>'} ${esc(display)}</div>`;
    if (data.type) h += `<div class="ct-row"><span class="ct-label">Type</span>${esc(data.type)}</div>`;
    const tels = data.telephones || [];
    if (tels.length) h += `<div class="ct-row"><span class="ct-label">T\u00e9l\u00e9phone</span>${tels.map(t => esc(t)).join(", ")}</div>`;
    const emls = data.emails || [];
    if (emls.length) h += `<div class="ct-row"><span class="ct-label">Email</span>${emls.map(e => `<a href="mailto:${esc(e)}">${esc(e)}</a>`).join(", ")}</div>`;
    if (data.adresse) h += `<div class="ct-row"><span class="ct-label">Adresse</span>${esc(data.adresse)}</div>`;
    if (data.date_naissance) {
      let birth = esc(data.date_naissance);
      if (data.heure_naissance) birth += ` \u00e0 ${esc(data.heure_naissance)}`;
      if (data.lieu_naissance) birth += ` (${esc(data.lieu_naissance)})`;
      h += `<div class="ct-row"><span class="ct-label">Naissance</span>${birth}</div>`;
    }
    if (data.site_web) h += `<div class="ct-row"><span class="ct-label">Site web</span><a href="${esc(data.site_web)}" target="_blank">${esc(data.site_web)}</a></div>`;
    if (data.commentaire) h += `<div class="ct-row"><span class="ct-label">Note</span>${esc(data.commentaire)}</div>`;
    if (data.tags_raw) {
      h += '<div style="margin-top:4px;display:flex;flex-wrap:wrap;gap:3px">';
      data.tags_raw.split(",").forEach(t => { t = t.trim(); if (t) h += `<span class="ev-tag">${esc(t)}</span>`; });
      h += '</div>';
    }
    // Relations
    try {
      const rels = await apiFetch("relations", { type: "contact", id: String(data.id) });
      if (rels.relations && rels.relations.length) {
        h += '<div style="margin-top:6px;border-top:1px solid #eee;padding-top:4px"><span class="ct-label">\u00c9l\u00e9ments li\u00e9s</span>';
        rels.relations.forEach(r => {
          const other = (r.source_type === "contact" && r.source_id === data.id)
            ? `${r.target_type} #${r.target_id}` : `${r.source_type} #${r.source_id}`;
          const label = r.relation ? ` (${esc(r.relation)})` : "";
          h += `<div style="font-size:11px;color:#555;margin:2px 0">\u2192 ${esc(other)}${label}</div>`;
        });
        h += '</div>';
      }
    } catch {}
    div.innerHTML = h;

    // Tags modifiables (table tags)
    const tagsSection = document.createElement("div");
    tagsSection.style.cssText = "margin-top:8px;padding-top:6px;border-top:1px solid #eee";
    tagsSection.innerHTML = '<div style="font-size:11px;color:#666;margin-bottom:6px;font-weight:500">TAGS (modifiables)</div><div class="tags-container"></div>';
    div.appendChild(tagsSection);

    el.after(div);

    // Charger les tags
    const tagsContainer = div.querySelector('.tags-container');
    renderItemTags(id, tagsContainer);
  } catch {}
}

async function toggleLieuView(el) {
  const id = el.dataset.id;
  const existing = el.nextElementSibling;
  if (existing && existing.classList.contains("lieu-content")) {
    existing.remove();
    return;
  }
  document.querySelectorAll(".lieu-content").forEach(e => e.remove());
  try {
    const data = await apiFetch("lieu", { id });
    if (data.error) return;
    const div = document.createElement("div");
    div.className = "lieu-content";
    let h = `<div class="li-name"><i class="fa-solid fa-location-dot icon-lieu"></i> ${esc(data.nom)}</div>`;
    if (data.adresse) {
      h += `<div class="li-row"><span class="li-label">Adresse</span>${esc(data.adresse)}</div>`;
      if (data.maps_url) {
        h += `<a class="maps-btn" href="${esc(data.maps_url)}" target="_blank"><i class="fa-solid fa-map-location-dot"></i> Google Maps</a>`;
      }
    }
    if (data.description) h += `<div class="li-row" style="margin-top:4px"><span class="li-label">Description</span>${esc(data.description)}</div>`;
    if (data.tags_raw) {
      h += '<div style="margin-top:4px;display:flex;flex-wrap:wrap;gap:3px">';
      data.tags_raw.split(",").forEach(t => { t = t.trim(); if (t) h += `<span class="ev-tag">${esc(t)}</span>`; });
      h += '</div>';
    }
    // Relations
    try {
      const rels = await apiFetch("relations", { type: "lieu", id: String(data.id) });
      if (rels.relations && rels.relations.length) {
        h += '<div style="margin-top:6px;border-top:1px solid #eee;padding-top:4px"><span class="li-label">\u00c9l\u00e9ments li\u00e9s</span>';
        rels.relations.forEach(r => {
          const other = (r.source_type === "lieu" && r.source_id === data.id)
            ? `${r.target_type} #${r.target_id}` : `${r.source_type} #${r.source_id}`;
          const label = r.relation ? ` (${esc(r.relation)})` : "";
          h += `<div style="font-size:11px;color:#555;margin:2px 0">\u2192 ${esc(other)}${label}</div>`;
        });
        h += '</div>';
      }
    } catch {}
    div.innerHTML = h;

    // Tags modifiables (table tags)
    const tagsSection = document.createElement("div");
    tagsSection.style.cssText = "margin-top:8px;padding-top:6px;border-top:1px solid #eee";
    tagsSection.innerHTML = '<div style="font-size:11px;color:#666;margin-bottom:6px;font-weight:500">TAGS (modifiables)</div><div class="tags-container"></div>';
    div.appendChild(tagsSection);

    el.after(div);

    // Charger les tags
    const tagsContainer = div.querySelector('.tags-container');
    renderItemTags(id, tagsContainer);
  } catch {}
}

// ── Formulaire d'ajout ──────────────────────────────

const ADD_TYPES = [
  { key: "contact", label: "Contact", icon: '<i class="fa-solid fa-user"></i>' },
  { key: "entreprise", label: "Entreprise", icon: '<i class="fa-solid fa-building"></i>' },
  { key: "lieu", label: "Lieu", icon: '<i class="fa-solid fa-location-dot"></i>' },
  { key: "event", label: "\u00c9v\u00e9nement", icon: '<i class="fa-solid fa-calendar-days"></i>' },
  { key: "anniversaire", label: "Anniversaire", icon: '<i class="fa-solid fa-cake-candles"></i>' },
  { key: "rdv", label: "RDV", icon: '<i class="fa-solid fa-clock"></i>' },
];

function showAddForm() {
  // Supprimer un overlay existant
  document.querySelector(".add-overlay")?.remove();

  const overlay = document.createElement("div");
  overlay.className = "add-overlay";

  // Tags hérités du contexte
  const inheritedTags = [...state.includeTags].filter(t => t !== "favori");

  let currentType = "contact";
  let formTags = inheritedTags.map(t => ({ value: t, auto: true }));
  let contactSearchResults = [];
  let lieuSearchResults = [];
  let systemContactsAvailable = null; // null = pas encore vérifié

  function buildForm() {
    const t = currentType;
    const isContact = t === "contact";
    const isEntreprise = t === "entreprise";
    const isLieu = t === "lieu";
    const isEvent = t === "event";
    const isAnniv = t === "anniversaire";
    const isRdv = t === "rdv";
    const isEventType = isEvent || isAnniv || isRdv;

    let fields = "";

    // Suggestions contacts système (si type contact)
    if (isContact) {
      fields += `<div id="af-sys-contacts" style="margin-bottom:8px;display:none">
        <div style="margin-bottom:4px">
          <span style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.3px">Remplir depuis mes contacts</span>
        </div>
        <input type="text" id="af-sys-search" placeholder="Chercher un contact existant..." style="width:100%;padding:5px 8px;border:1px solid #ddd;border-radius:4px;font-size:12px;margin-bottom:4px">
        <div id="af-sys-results" style="max-height:120px;overflow-y:auto;font-size:11px"></div>
      </div>`;
    }

    // Nom / Prénom (contact, entreprise, lieu)
    if (isContact) {
      fields += `
        <div class="form-group"><label>Pr\u00e9nom</label><input type="text" id="af-prenom" placeholder="Pr\u00e9nom"></div>
        <div class="form-group"><label>Nom</label><input type="text" id="af-nom" placeholder="Nom"></div>`;
    }
    if (isEntreprise || isLieu) {
      fields += `<div class="form-group"><label>Nom <span class="required">*</span></label><input type="text" id="af-nom" placeholder="Nom" required></div>`;
    }

    // Titre (events)
    if (isEventType) {
      fields += `<div class="form-group"><label>Titre <span class="required">*</span></label><input type="text" id="af-titre" placeholder="Titre"></div>`;
    }

    // Date (events)
    if (isEventType) {
      fields += `<div class="form-group"><label>Date <span class="required">*</span></label><input type="date" id="af-date"></div>`;
    }

    // Téléphones (contact, entreprise) — répétables
    if (isContact || isEntreprise) {
      fields += `<div class="form-group"><label>T\u00e9l\u00e9phone</label><div id="af-tels"><div class="repeatable-row"><input type="tel" placeholder="T\u00e9l\u00e9phone"><button type="button" class="repeatable-add" data-target="af-tels">+</button></div></div></div>`;
    }

    // Emails (contact, entreprise) — répétables
    if (isContact || isEntreprise) {
      fields += `<div class="form-group"><label>Email</label><div id="af-emails"><div class="repeatable-row"><input type="email" placeholder="Email"><button type="button" class="repeatable-add" data-target="af-emails">+</button></div></div></div>`;
    }

    // Date de naissance (contact)
    if (isContact) {
      fields += `<div class="form-group"><label>Date de naissance</label><input type="date" id="af-naissance"></div>`;
      fields += `<div style="display:flex;gap:8px">
        <div class="form-group" style="flex:1"><label>Heure naissance</label><input type="time" id="af-heure-naissance"></div>
        <div class="form-group" style="flex:1"><label>Lieu naissance</label><input type="text" id="af-lieu-naissance" placeholder="Ville"></div>
      </div>`;
    }

    // Adresse (contact, entreprise, lieu)
    if (isContact || isEntreprise || isLieu) {
      fields += `<div class="form-group"><label>Adresse</label><input type="text" id="af-adresse" placeholder="Adresse"></div>`;
    }

    // Site web (entreprise)
    if (isEntreprise) {
      fields += `<div class="form-group"><label>Site web</label><input type="url" id="af-site" placeholder="https://"></div>`;
    }

    // Contact lié (lieu, event, anniversaire, rdv)
    if (isLieu || isEventType) {
      const req = isAnniv || isRdv ? ' <span class="required">*</span>' : "";
      fields += `<div class="form-group form-autocomplete">
        <label>Contact${req}</label>
        <input type="text" id="af-contact-search" placeholder="Chercher un contact..." autocomplete="off">
        <input type="hidden" id="af-contact-id">
        <div class="form-ac-dropdown" id="af-contact-dropdown"></div>
      </div>`;
    }

    // Lieu lié (rdv)
    if (isRdv) {
      fields += `<div class="form-group form-autocomplete">
        <label>Lieu <span class="required">*</span></label>
        <input type="text" id="af-lieu-search" placeholder="Chercher un lieu..." autocomplete="off">
        <input type="hidden" id="af-lieu-id">
        <div class="form-ac-dropdown" id="af-lieu-dropdown"></div>
      </div>`;
    }

    // Lieu (event, anniversaire — optionnel)
    if (isEvent || isAnniv) {
      fields += `<div class="form-group"><label>Lieu</label><input type="text" id="af-location" placeholder="Lieu"></div>`;
    }

    // Description (lieu, events)
    if (isLieu || isEventType) {
      fields += `<div class="form-group"><label>Description</label><textarea id="af-desc" rows="2" placeholder="Description"></textarea></div>`;
    }

    // Commentaire (contact, entreprise)
    if (isContact || isEntreprise) {
      fields += `<div class="form-group"><label>Commentaire</label><textarea id="af-commentaire" rows="2" placeholder="Commentaire"></textarea></div>`;
    }

    // Récurrence (events)
    if (isEventType) {
      const defaultRec = isAnniv ? "yearly" : "none";
      fields += `<div class="form-group"><label>R\u00e9currence</label>
        <select id="af-recurrence">
          <option value="none"${defaultRec==="none"?" selected":""}>Aucune</option>
          <option value="daily">Chaque jour</option>
          <option value="weekly">Chaque semaine</option>
          <option value="monthly">Chaque mois</option>
          <option value="yearly"${defaultRec==="yearly"?" selected":""}>Chaque ann\u00e9e</option>
        </select></div>`;
    }

    // Tags
    const tagsHtml = formTags.map((t, i) =>
      `<span class="af-tag${t.auto ? " auto" : ""}">${esc(t.value)}${t.auto ? "" : `<span class="remove" data-tag-idx="${i}">\u00d7</span>`}</span>`
    ).join("");

    fields += `<div class="form-group">
      <label>Tags</label>
      <div class="add-form-tags" id="af-tags-list">${tagsHtml}</div>
      <div class="form-autocomplete">
        <input type="text" id="af-tag-input" placeholder="Ajouter un tag...">
        <div class="form-ac-dropdown" id="af-tag-dropdown"></div>
      </div>
    </div>`;

    return fields;
  }

  function render() {
    overlay.innerHTML = `
      <div class="add-form">
        <div class="add-form-header">
          <span>Ajouter un \u00e9l\u00e9ment</span>
          <span class="close-btn" id="af-close">\u00d7</span>
        </div>
        <div class="add-type-selector">
          ${ADD_TYPES.map(t =>
            `<span class="add-type-btn${t.key === currentType ? " active" : ""}" data-add-type="${t.key}">${t.icon} ${t.label}</span>`
          ).join("")}
        </div>
        <div class="add-form-body">${buildForm()}</div>
        <div class="af-status" id="af-status"></div>
        <div class="add-form-footer">
          <button class="af-btn af-btn-cancel" id="af-cancel">Annuler</button>
          <button class="af-btn af-btn-ok" id="af-submit">Enregistrer</button>
        </div>
      </div>`;

    // Events
    overlay.querySelector("#af-close").addEventListener("click", () => overlay.remove());
    overlay.querySelector("#af-cancel").addEventListener("click", () => overlay.remove());
    overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });

    // Type selector
    overlay.querySelectorAll(".add-type-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        currentType = btn.dataset.addType;
        render();
      });
    });

    // Tag remove buttons
    overlay.querySelectorAll(".af-tag .remove").forEach(el => {
      el.addEventListener("click", () => {
        formTags.splice(parseInt(el.dataset.tagIdx), 1);
        renderTags();
      });
    });

    // Repeatable fields
    overlay.querySelectorAll(".repeatable-add").forEach(btn => {
      btn.addEventListener("click", () => {
        const container = overlay.querySelector(`#${btn.dataset.target}`);
        const row = document.createElement("div");
        row.className = "repeatable-row";
        const input = container.querySelector("input").cloneNode(true);
        input.value = "";
        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.className = "repeatable-remove";
        removeBtn.textContent = "\u00d7";
        removeBtn.addEventListener("click", () => row.remove());
        row.appendChild(input);
        row.appendChild(removeBtn);
        container.appendChild(row);
      });
    });

    // Tag autocomplete
    setupTagAutocomplete();

    // Contact search autocomplete
    setupContactSearch();

    // Lieu search autocomplete
    setupLieuSearch();

    // Contacts système (suggestion semi-auto)
    setupSystemContacts();

    // Date inputs : calendrier on focus
    overlay.querySelectorAll('input[type="date"]').forEach(dateInput => {
      dateInput.addEventListener("focus", () => {
        try { dateInput.showPicker(); } catch {}
      });
    });

    // Submit
    overlay.querySelector("#af-submit").addEventListener("click", submitForm);
  }

  function renderTags() {
    const list = overlay.querySelector("#af-tags-list");
    if (!list) return;
    list.innerHTML = formTags.map((t, i) =>
      `<span class="af-tag${t.auto ? " auto" : ""}">${esc(t.value)}${t.auto ? "" : `<span class="remove" data-tag-idx="${i}">\u00d7</span>`}</span>`
    ).join("");
    list.querySelectorAll(".af-tag .remove").forEach(el => {
      el.addEventListener("click", () => {
        formTags.splice(parseInt(el.dataset.tagIdx), 1);
        renderTags();
      });
    });
  }

  function addTag(value) {
    value = value.trim().toLowerCase();
    if (!value || formTags.some(t => t.value === value)) return;
    formTags.push({ value, auto: false });
    renderTags();
  }

  function setupTagAutocomplete() {
    const input = overlay.querySelector("#af-tag-input");
    const dropdown = overlay.querySelector("#af-tag-dropdown");
    if (!input || !dropdown) return;

    let debounceTimer;
    input.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      const q = input.value.trim();
      if (q.length < 1) { dropdown.style.display = "none"; return; }
      debounceTimer = setTimeout(async () => {
        try {
          const data = await apiFetch("autocomplete", { q });
          const existing = new Set(formTags.map(t => t.value));
          const filtered = (data.tags || []).filter(t => !existing.has(t.tag)).slice(0, 8);
          let html = filtered.map(t => `<div class="ac-item" data-tag="${esc(t.tag)}">${esc(t.tag)} <span style="color:#888;font-size:10px">(${t.count})</span></div>`).join("");
          if (!filtered.some(t => t.tag === q.toLowerCase())) {
            html += `<div class="ac-item create" data-tag="${esc(q.toLowerCase())}">Cr\u00e9er "${esc(q)}"</div>`;
          }
          dropdown.innerHTML = html;
          dropdown.style.display = html ? "block" : "none";
          dropdown.querySelectorAll(".ac-item").forEach(item => {
            item.addEventListener("click", () => {
              addTag(item.dataset.tag);
              input.value = "";
              dropdown.style.display = "none";
            });
          });
        } catch { dropdown.style.display = "none"; }
      }, 150);
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const q = input.value.trim();
        if (q) { addTag(q); input.value = ""; dropdown.style.display = "none"; }
      }
    });
  }

  function setupSystemContacts() {
    const container = overlay.querySelector("#af-sys-contacts");
    if (!container) return;

    async function loadSystemContacts(q) {
      try {
        const params = q ? { q } : {};
        const data = await apiFetch("system-contacts/list", params);
        if (!data.available) { container.style.display = "none"; return; }
        systemContactsAvailable = true;
        container.style.display = "block";
        const resultsEl = container.querySelector("#af-sys-results");
        const contacts = data.contacts || [];
        if (contacts.length === 0) {
          resultsEl.innerHTML = '<div style="color:#aaa;padding:4px">Aucun contact trouv\u00e9</div>';
          return;
        }
        resultsEl.innerHTML = contacts.slice(0, 20).map(c => {
          const display = ((c.prenom || "") + " " + (c.nom || "")).trim();
          const info = [
            ...(c.telephones || []).slice(0, 1),
            ...(c.emails || []).slice(0, 1),
          ].join(" \u00b7 ");
          return `<div class="sys-contact-item" style="padding:4px 6px;cursor:pointer;border-bottom:1px solid #f0f0f0;display:flex;justify-content:space-between;align-items:center" data-sys='${esc(JSON.stringify(c))}'>
            <span>\uD83D\uDC64 ${esc(display)}</span>
            <span style="color:#aaa;font-size:10px">${esc(info)}</span>
          </div>`;
        }).join("") + (data.total > 20 ? `<div style="color:#888;padding:4px;text-align:center;font-size:10px">${data.total} contacts au total</div>` : "");

        // Clic sur un contact système → pré-remplir le formulaire
        resultsEl.querySelectorAll(".sys-contact-item").forEach(item => {
          item.addEventListener("click", () => {
            const c = JSON.parse(item.dataset.sys);
            const prenomEl = overlay.querySelector("#af-prenom");
            const nomEl = overlay.querySelector("#af-nom");
            if (prenomEl) prenomEl.value = c.prenom || "";
            if (nomEl) nomEl.value = c.nom || "";
            // Remplir les téléphones
            const telContainer = overlay.querySelector("#af-tels");
            if (telContainer && c.telephones && c.telephones.length) {
              const firstInput = telContainer.querySelector("input");
              if (firstInput) firstInput.value = c.telephones[0];
              for (let i = 1; i < c.telephones.length; i++) {
                const row = document.createElement("div");
                row.className = "repeatable-row";
                const inp = document.createElement("input");
                inp.type = "tel"; inp.placeholder = "T\u00e9l\u00e9phone"; inp.value = c.telephones[i];
                const rb = document.createElement("button");
                rb.type = "button"; rb.className = "repeatable-remove"; rb.textContent = "\u00d7";
                rb.addEventListener("click", () => row.remove());
                row.appendChild(inp); row.appendChild(rb);
                telContainer.appendChild(row);
              }
            }
            // Remplir les emails
            const emailContainer = overlay.querySelector("#af-emails");
            if (emailContainer && c.emails && c.emails.length) {
              const firstInput = emailContainer.querySelector("input");
              if (firstInput) firstInput.value = c.emails[0];
              for (let i = 1; i < c.emails.length; i++) {
                const row = document.createElement("div");
                row.className = "repeatable-row";
                const inp = document.createElement("input");
                inp.type = "email"; inp.placeholder = "Email"; inp.value = c.emails[i];
                const rb = document.createElement("button");
                rb.type = "button"; rb.className = "repeatable-remove"; rb.textContent = "\u00d7";
                rb.addEventListener("click", () => row.remove());
                row.appendChild(inp); row.appendChild(rb);
                emailContainer.appendChild(row);
              }
            }
            // Masquer les suggestions
            container.style.display = "none";
          });
          // Hover effect
          item.addEventListener("mouseenter", () => { item.style.background = "#fef5ed"; });
          item.addEventListener("mouseleave", () => { item.style.background = ""; });
        });
      } catch {
        container.style.display = "none";
      }
    }

    // Charger au démarrage (sans filtre)
    loadSystemContacts("");

    // Recherche dans les contacts système
    const searchInput = container.querySelector("#af-sys-search");
    if (searchInput) {
      let dt;
      searchInput.addEventListener("input", () => {
        clearTimeout(dt);
        dt = setTimeout(() => loadSystemContacts(searchInput.value.trim()), 200);
      });
    }

  }

  function setupContactSearch() {
    const input = overlay.querySelector("#af-contact-search");
    const dropdown = overlay.querySelector("#af-contact-dropdown");
    const hiddenId = overlay.querySelector("#af-contact-id");
    if (!input || !dropdown) return;

    let debounceTimer;
    input.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      hiddenId.value = "";
      const q = input.value.trim();
      if (q.length < 1) { dropdown.style.display = "none"; return; }
      debounceTimer = setTimeout(async () => {
        try {
          const data = await apiFetch("contacts/search", { q });
          contactSearchResults = data.results || [];
          let html = contactSearchResults.map(c => {
            const display = ((c.prenom || "") + " " + (c.nom || "")).trim();
            const icon = c.type === "entreprise" ? "\uD83C\uDFE2" : "\uD83D\uDC64";
            return `<div class="ac-item" data-contact-id="${c.id}">${icon} ${esc(display)}</div>`;
          }).join("");
          html += `<div class="ac-item create" data-contact-new="1">\u2795 Cr\u00e9er un nouveau contact...</div>`;
          dropdown.innerHTML = html;
          dropdown.style.display = "block";
          dropdown.querySelectorAll(".ac-item[data-contact-id]").forEach(item => {
            item.addEventListener("click", () => {
              const c = contactSearchResults.find(x => x.id === parseInt(item.dataset.contactId));
              if (c) {
                input.value = ((c.prenom || "") + " " + (c.nom || "")).trim();
                hiddenId.value = c.id;
                dropdown.style.display = "none";
              }
            });
          });
          dropdown.querySelector("[data-contact-new]")?.addEventListener("click", () => {
            dropdown.style.display = "none";
            // Switch to contact type
            const prevType = currentType;
            currentType = "contact";
            render();
          });
        } catch { dropdown.style.display = "none"; }
      }, 200);
    });
  }

  function setupLieuSearch() {
    const input = overlay.querySelector("#af-lieu-search");
    const dropdown = overlay.querySelector("#af-lieu-dropdown");
    const hiddenId = overlay.querySelector("#af-lieu-id");
    if (!input || !dropdown) return;

    let debounceTimer;
    input.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      hiddenId.value = "";
      const q = input.value.trim();
      if (q.length < 1) { dropdown.style.display = "none"; return; }
      debounceTimer = setTimeout(async () => {
        try {
          const data = await apiFetch("lieux/search", { q });
          lieuSearchResults = data.results || [];
          let html = lieuSearchResults.map(l =>
            `<div class="ac-item" data-lieu-id="${l.id}">\uD83D\uDCCD ${esc(l.nom)}${l.adresse ? " \u2014 " + esc(l.adresse) : ""}</div>`
          ).join("");
          html += `<div class="ac-item create" data-lieu-new="1">\u2795 Cr\u00e9er un nouveau lieu...</div>`;
          dropdown.innerHTML = html;
          dropdown.style.display = "block";
          dropdown.querySelectorAll(".ac-item[data-lieu-id]").forEach(item => {
            item.addEventListener("click", () => {
              const l = lieuSearchResults.find(x => x.id === parseInt(item.dataset.lieuId));
              if (l) {
                input.value = l.nom;
                hiddenId.value = l.id;
                dropdown.style.display = "none";
              }
            });
          });
          dropdown.querySelector("[data-lieu-new]")?.addEventListener("click", () => {
            dropdown.style.display = "none";
            currentType = "lieu";
            render();
          });
        } catch { dropdown.style.display = "none"; }
      }, 200);
    });
  }

  async function submitForm() {
    const statusEl = overlay.querySelector("#af-status");
    const submitBtn = overlay.querySelector("#af-submit");
    statusEl.className = "af-status";
    statusEl.style.display = "none";
    submitBtn.disabled = true;

    const tagsStr = formTags.map(t => t.value).join(",");

    try {
      let result;
      const t = currentType;

      if (t === "contact" || t === "entreprise") {
        const nom = (overlay.querySelector("#af-nom")?.value || "").trim();
        const prenom = (overlay.querySelector("#af-prenom")?.value || "").trim();
        if (t === "contact" && !nom && !prenom) throw new Error("Nom ou pr\u00e9nom requis");
        if (t === "entreprise" && !nom) throw new Error("Nom requis");

        const tels = [];
        overlay.querySelectorAll("#af-tels input").forEach(i => { if (i.value.trim()) tels.push(i.value.trim()); });
        const emails = [];
        overlay.querySelectorAll("#af-emails input").forEach(i => { if (i.value.trim()) emails.push(i.value.trim()); });

        result = await fetchJSON(`${API}/contact`, "POST", {
          type: t === "entreprise" ? "entreprise" : "personne",
          nom, prenom,
          telephones: tels,
          emails: emails,
          date_naissance: overlay.querySelector("#af-naissance")?.value || null,
          heure_naissance: overlay.querySelector("#af-heure-naissance")?.value || null,
          lieu_naissance: overlay.querySelector("#af-lieu-naissance")?.value || null,
          adresse: overlay.querySelector("#af-adresse")?.value || "",
          site_web: overlay.querySelector("#af-site")?.value || "",
          commentaire: overlay.querySelector("#af-commentaire")?.value || "",
          tags_raw: tagsStr,
        });
      }
      else if (t === "lieu") {
        const nom = (overlay.querySelector("#af-nom")?.value || "").trim();
        if (!nom) throw new Error("Nom requis");
        result = await fetchJSON(`${API}/lieu`, "POST", {
          nom,
          adresse: overlay.querySelector("#af-adresse")?.value || "",
          description: overlay.querySelector("#af-desc")?.value || "",
          contact_id: overlay.querySelector("#af-contact-id")?.value ? parseInt(overlay.querySelector("#af-contact-id").value) : null,
          tags_raw: tagsStr,
        });
      }
      else if (t === "event" || t === "anniversaire" || t === "rdv") {
        const titre = (overlay.querySelector("#af-titre")?.value || "").trim();
        const date = (overlay.querySelector("#af-date")?.value || "").trim();
        if (!titre || !date) throw new Error("Titre et date requis");

        const contactId = overlay.querySelector("#af-contact-id")?.value ? parseInt(overlay.querySelector("#af-contact-id").value) : null;
        const lieuId = overlay.querySelector("#af-lieu-id")?.value ? parseInt(overlay.querySelector("#af-lieu-id").value) : null;

        if (t === "anniversaire" && !contactId) throw new Error("Contact obligatoire pour un anniversaire");
        if (t === "rdv" && (!contactId || !lieuId)) throw new Error("Contact et lieu obligatoires pour un RDV");

        const subtype = t === "anniversaire" ? "anniversaire" : t === "rdv" ? "rendez_vous" : "generic";
        result = await fetchJSON(`${API}/event`, "POST", {
          title: titre,
          date_start: date,
          description: overlay.querySelector("#af-desc")?.value || "",
          location: overlay.querySelector("#af-location")?.value || "",
          tags_raw: tagsStr,
          recurrence: overlay.querySelector("#af-recurrence")?.value || "none",
          subtype,
          contact_id: contactId,
          lieu_id: lieuId,
        });
      }

      if (result && result.error) throw new Error(result.error);

      statusEl.className = "af-status success";
      statusEl.textContent = "\u2705 Enregistr\u00e9 !";
      statusEl.style.display = "block";
      setTimeout(() => { overlay.remove(); refresh(); }, 1500);

    } catch (e) {
      statusEl.className = "af-status error";
      statusEl.textContent = e.message || "Erreur";
      statusEl.style.display = "block";
      submitBtn.disabled = false;
    }
  }

  render();
  document.body.appendChild(overlay);
}

async function fetchJSON(url, method, body) {
  const resp = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return resp.json();
}

// ── Gestion des tags ──────────────────────────────────

async function renderItemTags(itemId, container) {
  // Affiche les tags d'un item avec boutons de suppression
  try {
    const resp = await fetch(`${API_URL}/api/tags/get?item_id=${itemId}`);
    const data = await resp.json();

    if (!data.tags || data.tags.length === 0) {
      container.innerHTML = '<div style="color:#999;font-size:11px;font-style:italic">Aucun tag</div>';
      return;
    }

    container.innerHTML = data.tags.map(tag => `
      <span class="item-tag" data-tag="${tag}">
        ${tag}
        <button class="tag-remove-btn" title="Supprimer ce tag">×</button>
      </span>
    `).join('');

    // Event listeners pour suppression
    container.querySelectorAll('.tag-remove-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const tagEl = e.target.parentElement;
        const tag = tagEl.dataset.tag;

        if (!confirm(`Supprimer le tag "${tag}" ?`)) return;

        try {
          const resp = await fetch(`${API_URL}/api/tags/delete`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId, tag })
          });
          const result = await resp.json();

          if (result.success) {
            tagEl.remove();
            // Si plus de tags, afficher "Aucun tag"
            if (container.querySelectorAll('.item-tag').length === 0) {
              container.innerHTML = '<div style="color:#999;font-size:11px;font-style:italic">Aucun tag</div>';
            }
          } else {
            alert('Erreur : ' + (result.error || 'Suppression échouée'));
          }
        } catch (err) {
          alert('Erreur réseau : ' + err.message);
        }
      });
    });
  } catch (err) {
    container.innerHTML = '<div style="color:#c0392b;font-size:11px">Erreur chargement tags</div>';
  }
}

// Bouton +
document.getElementById("add-btn").addEventListener("click", showAddForm);

// ── Init ────────────────────────────────────────────

checkServer();
checkVaultStatus();
input.focus();

// Pleine page
document.getElementById("fullpage-btn").addEventListener("click", (e) => {
  e.preventDefault();
  chrome.tabs.create({ url: "http://127.0.0.1:7777/" });
});
