/**
 * BIG_BOFF Search — Tagger
 * Logique de la page de tagging (vidéos + images)
 */

const API = "http://127.0.0.1:7777/api";

// ── Lire les paramètres URL ──────────────────────────
const params = new URLSearchParams(window.location.search);
const itemType = params.get("type") || "video"; // "video" ou "image"
const itemUrl = params.get("url") || "";
const itemPlatform = params.get("platform") || "";
const pageTitle = params.get("pageTitle") || "";

// ── State ────────────────────────────────────────────
const tags = []; // [{value: "video", auto: true}, ...]
let autocompleteItems = [];
let autocompleteIndex = -1;
let imageBase64 = null; // Pour les images

// ── Éléments DOM ─────────────────────────────────────
const typeBadge = document.getElementById("type-badge");
const urlDisplay = document.getElementById("url-display");
const titleDisplay = document.getElementById("title-display");
const titleSection = document.getElementById("title-section");
const previewSection = document.getElementById("preview-section");
const imagePreview = document.getElementById("image-preview");
const tagsList = document.getElementById("tags-list");
const tagInput = document.getElementById("tag-input");
const tagDropdown = document.getElementById("tag-dropdown");
const coocSection = document.getElementById("cooc-section");
const coocTags = document.getElementById("cooc-tags");
const statusBar = document.getElementById("status-bar");
const btnOk = document.getElementById("btn-ok");
const btnCancel = document.getElementById("btn-cancel");

// ── Initialisation ───────────────────────────────────
function init() {
  // Badge type
  if (itemType === "video") {
    typeBadge.textContent = "Video";
    typeBadge.classList.add("badge-video");
  } else {
    typeBadge.textContent = "Image";
    typeBadge.classList.add("badge-image");
  }

  // URL
  urlDisplay.innerHTML = '<a href="' + esc(itemUrl) + '" target="_blank">' + esc(truncate(itemUrl, 80)) + '</a>';

  // Tags auto
  if (itemType === "video") {
    addTag("video", true);
    if (itemPlatform) addTag(itemPlatform, true);
    fetchTitle();
  } else {
    addTag("image", true);
    titleSection.style.display = "none";
    fetchImage();
  }

  // Events
  tagInput.addEventListener("input", onTagInput);
  tagInput.addEventListener("keydown", onTagKeydown);
  btnOk.addEventListener("click", submit);
  btnCancel.addEventListener("click", () => window.close());
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".tag-input-wrap")) hideDropdown();
  });

  tagInput.focus();
}

// ── Récupérer le titre (vidéo) ───────────────────────
async function fetchTitle() {
  let title = "";

  if (itemPlatform === "youtube") {
    try {
      const resp = await fetch("https://www.youtube.com/oembed?url=" + encodeURIComponent(itemUrl) + "&format=json");
      if (resp.ok) {
        const data = await resp.json();
        title = data.title || "";
      }
    } catch (e) {}
  }

  if (!title) {
    try {
      const resp = await fetch("https://noembed.com/embed?url=" + encodeURIComponent(itemUrl));
      if (resp.ok) {
        const data = await resp.json();
        title = data.title || "";
      }
    } catch (e) {}
  }

  if (!title && pageTitle) {
    title = pageTitle.replace(/ - YouTube$/, "").replace(/ \| Facebook$/, "").replace(/ on TikTok$/, "");
  }

  titleDisplay.textContent = title || "(titre non disponible)";
}

// ── Récupérer l'image (via service worker) ───────────
function fetchImage() {
  previewSection.style.display = "block";
  imagePreview.alt = "Chargement...";

  chrome.runtime.sendMessage({ action: "fetchImage", url: itemUrl }, (response) => {
    if (response && response.ok) {
      imageBase64 = response.data;
      imagePreview.src = imageBase64;
    } else {
      imagePreview.alt = "Impossible de charger l'image";
      imagePreview.style.display = "none";
      // Fallback : essai direct (même domaine possible)
      imagePreview.src = itemUrl;
      imagePreview.style.display = "block";
      imagePreview.onerror = () => {
        imagePreview.style.display = "none";
      };
      imagePreview.onload = () => {
        // Convertir en base64 via canvas
        try {
          const canvas = document.createElement("canvas");
          canvas.width = imagePreview.naturalWidth;
          canvas.height = imagePreview.naturalHeight;
          const ctx = canvas.getContext("2d");
          ctx.drawImage(imagePreview, 0, 0);
          imageBase64 = canvas.toDataURL("image/jpeg", 0.9);
        } catch (e) {
          // CORS block on canvas — use direct URL
        }
      };
    }
  });
}

// ── Tags ─────────────────────────────────────────────
function addTag(value, auto) {
  value = value.toLowerCase().trim();
  if (!value) return;
  if (tags.some(t => t.value === value)) return;
  tags.push({ value: value, auto: !!auto });
  renderTags();
  fetchCooccurrence();
}

function removeTag(value) {
  const idx = tags.findIndex(t => t.value === value);
  if (idx >= 0) {
    tags.splice(idx, 1);
    renderTags();
    fetchCooccurrence();
  }
}

function renderTags() {
  tagsList.innerHTML = tags.map(t =>
    '<span class="tag-chip' + (t.auto ? ' auto' : '') + '" data-tag="' + esc(t.value) + '">' +
    esc(t.value) +
    (t.auto ? '' : '<span class="remove" data-tag="' + esc(t.value) + '">&times;</span>') +
    '</span>'
  ).join("");
  tagsList.querySelectorAll(".remove").forEach(el => {
    el.addEventListener("click", (e) => {
      e.stopPropagation();
      removeTag(el.dataset.tag);
    });
  });
}

// ── Autocomplétion ───────────────────────────────────
let debounceTimer;

function onTagInput() {
  clearTimeout(debounceTimer);
  const q = tagInput.value.trim();
  if (q.length < 1) { hideDropdown(); return; }
  debounceTimer = setTimeout(() => fetchAutocomplete(q), 150);
}

async function fetchAutocomplete(q) {
  try {
    const resp = await fetch(API + "/autocomplete?q=" + encodeURIComponent(q));
    const data = await resp.json();
    const existing = new Set(tags.map(t => t.value));
    autocompleteItems = (data.tags || []).filter(t => !existing.has(t.tag));
    autocompleteIndex = -1;
    renderDropdown(q);
  } catch (e) {
    hideDropdown();
  }
}

function renderDropdown(q) {
  if (autocompleteItems.length === 0 && q) {
    // Aucun match exact → proposer création
    tagDropdown.innerHTML = '<div class="dd-create" data-tag="' + esc(q) + '">+ Creer "' + esc(q) + '"</div>';
    tagDropdown.style.display = "block";
    tagDropdown.querySelector(".dd-create").addEventListener("click", () => {
      addTag(q);
      tagInput.value = "";
      hideDropdown();
      tagInput.focus();
    });
    return;
  }

  let html = autocompleteItems.map((t, i) =>
    '<div class="dd-item' + (i === autocompleteIndex ? ' selected' : '') + '" data-tag="' + esc(t.tag) + '">' +
    '<span>' + highlight(t.tag, q) + '</span>' +
    '<span class="cnt">' + t.count.toLocaleString() + '</span>' +
    '</div>'
  ).join("");

  // Vérifier si le texte saisi est un tag exact existant
  const exactMatch = autocompleteItems.some(t => t.tag === q.toLowerCase());
  if (!exactMatch && q) {
    html += '<div class="dd-create" data-tag="' + esc(q) + '">+ Creer "' + esc(q) + '"</div>';
  }

  tagDropdown.innerHTML = html;
  tagDropdown.style.display = "block";

  tagDropdown.querySelectorAll(".dd-item").forEach(el => {
    el.addEventListener("click", () => {
      addTag(el.dataset.tag);
      tagInput.value = "";
      hideDropdown();
      tagInput.focus();
    });
  });
  tagDropdown.querySelectorAll(".dd-create").forEach(el => {
    el.addEventListener("click", () => {
      addTag(el.dataset.tag);
      tagInput.value = "";
      hideDropdown();
      tagInput.focus();
    });
  });
}

function hideDropdown() {
  tagDropdown.style.display = "none";
  autocompleteItems = [];
  autocompleteIndex = -1;
}

function onTagKeydown(e) {
  const items = tagDropdown.querySelectorAll(".dd-item");
  if (e.key === "ArrowDown") {
    e.preventDefault();
    autocompleteIndex = Math.min(autocompleteIndex + 1, items.length - 1);
    updateDropdownSelection(items);
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    autocompleteIndex = Math.max(autocompleteIndex - 1, -1);
    updateDropdownSelection(items);
  } else if (e.key === "Enter") {
    e.preventDefault();
    if (autocompleteIndex >= 0 && items[autocompleteIndex]) {
      addTag(items[autocompleteIndex].dataset.tag);
    } else if (autocompleteItems.length > 0) {
      addTag(autocompleteItems[0].tag);
    } else if (tagInput.value.trim()) {
      addTag(tagInput.value.trim());
    }
    tagInput.value = "";
    hideDropdown();
    tagInput.focus();
  } else if (e.key === "Escape") {
    hideDropdown();
  } else if (e.key === "Backspace" && tagInput.value === "" && tags.length > 0) {
    // Supprimer le dernier tag non-auto
    for (let i = tags.length - 1; i >= 0; i--) {
      if (!tags[i].auto) { removeTag(tags[i].value); break; }
    }
  }
}

function updateDropdownSelection(items) {
  items.forEach((el, i) => {
    el.classList.toggle("selected", i === autocompleteIndex);
  });
}

// ── Co-occurrence ────────────────────────────────────
async function fetchCooccurrence() {
  const tagValues = tags.map(t => t.value);
  if (tagValues.length === 0) { coocSection.style.display = "none"; return; }

  try {
    const url = new URL(API + "/cooccurrence");
    tagValues.forEach(t => url.searchParams.append("include", t));
    const resp = await fetch(url);
    const data = await resp.json();
    const existing = new Set(tagValues);
    const filtered = (data.tags || []).filter(t => !existing.has(t.tag));
    if (filtered.length === 0) { coocSection.style.display = "none"; return; }
    coocSection.style.display = "block";
    coocTags.innerHTML = filtered.map(t =>
      '<span class="cooc-tag" data-tag="' + esc(t.tag) + '">' + esc(t.tag) + ' <span class="cnt">' + t.count + '</span></span>'
    ).join("");
    coocTags.querySelectorAll(".cooc-tag").forEach(el => {
      el.addEventListener("click", () => {
        addTag(el.dataset.tag);
        tagInput.focus();
      });
    });
  } catch (e) {
    coocSection.style.display = "none";
  }
}

// ── Submit ───────────────────────────────────────────
async function submit() {
  btnOk.disabled = true;
  btnOk.textContent = "Envoi...";
  const userTags = tags.map(t => t.value);

  try {
    if (itemType === "video") {
      const resp = await fetch(API + "/video/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: itemUrl,
          platform: itemPlatform,
          title: titleDisplay.textContent !== "(titre non disponible)" ? titleDisplay.textContent : "",
          tags: userTags,
        }),
      });
      const data = await resp.json();
      if (data.error) throw new Error(data.error);
      showStatus("success", data.already_exists
        ? "Video deja en base — " + (data.tags_added || 0) + " tag(s) ajoute(s)"
        : "Video ajoutee !");
    } else {
      // Image : récupérer le base64
      let imgData = imageBase64;
      if (!imgData) {
        throw new Error("Image non chargee. Reessayer.");
      }
      const filename = itemUrl.split("/").pop().split("?")[0] || "image.jpg";
      const resp = await fetch(API + "/image/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_data: imgData,
          source_url: itemUrl,
          filename: filename,
          tags: userTags,
        }),
      });
      const data = await resp.json();
      if (data.error) throw new Error(data.error);
      showStatus("success", data.already_exists
        ? "Image deja sauvee — " + (data.tags_added || 0) + " tag(s) ajoute(s)"
        : "Image sauvegardee !");
    }
    // Fermer après 2s
    setTimeout(() => window.close(), 2000);
  } catch (e) {
    showStatus("error", "Erreur : " + e.message);
    btnOk.disabled = false;
    btnOk.textContent = "Valider";
  }
}

// ── Helpers ──────────────────────────────────────────
function showStatus(type, msg) {
  statusBar.textContent = msg;
  statusBar.className = "status-bar " + type;
}

function esc(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

function highlight(text, query) {
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  if (idx < 0) return esc(text);
  return esc(text.slice(0, idx)) + "<strong>" + esc(text.slice(idx, idx + query.length)) + "</strong>" + esc(text.slice(idx + query.length));
}

function truncate(str, len) {
  return str.length > len ? str.slice(0, len) + "..." : str;
}

// ── Go ───────────────────────────────────────────────
init();
