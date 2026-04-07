"""
Admin UI — HTML généré server-side, stylé via les CSS variables du projet.
Design minimal dérivé du theme stocké en DB.
"""
import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..database import get_db, ProjectDB, PageDB, SectionDB, BlockDB

router = APIRouter(tags=["admin-ui"])

# ── CSS admin dérivé des variables du theme ───────────────────────────────────
_ADMIN_CSS = """
:root {
  --c-bg:        #f8fafc;
  --c-surface:   #ffffff;
  --c-border:    #e2e8f0;
  --c-text:      #1e293b;
  --c-text-2:    #64748b;
  --c-primary:   var(--color-primary, rgb(30,58,138));
  --c-accent:    var(--color-secondary, rgb(245,158,11));
  --c-danger:    #ef4444;
  --c-success:   #22c55e;
  --radius:      8px;
  --shadow:      0 1px 3px rgba(0,0,0,.08);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Inter', system-ui, sans-serif; background: var(--c-bg);
       color: var(--c-text); font-size: 14px; }
a { color: var(--c-primary); text-decoration: none; }
a:hover { text-decoration: underline; }

/* Layout */
.topbar { background: var(--c-primary); color: #fff; padding: 0 24px;
          height: 52px; display: flex; align-items: center; gap: 24px; }
.topbar strong { font-size: 16px; font-weight: 700; margin-right: auto; }
.topbar a { color: rgba(255,255,255,.8); font-size: 13px; }
.topbar a:hover { color: #fff; }

.container { max-width: 1100px; margin: 0 auto; padding: 32px 24px; }
h1 { font-size: 22px; font-weight: 700; margin-bottom: 4px; }
h2 { font-size: 16px; font-weight: 600; margin-bottom: 16px; }
.subtitle { color: var(--c-text-2); font-size: 13px; margin-bottom: 28px; }

/* Cards */
.card { background: var(--c-surface); border: 1px solid var(--c-border);
        border-radius: var(--radius); box-shadow: var(--shadow); padding: 20px; margin-bottom: 12px; }
.card-row { display: flex; align-items: center; gap: 12px; }
.card-row .label { font-weight: 500; flex: 1; }
.card-row .meta  { color: var(--c-text-2); font-size: 12px; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 99px; font-size: 11px; font-weight: 600; }
.badge-on  { background: #dcfce7; color: #166534; }
.badge-off { background: #fee2e2; color: #991b1b; }
.badge-type { background: #eff6ff; color: #1d4ed8; }

/* Sections list */
.section-item { background: var(--c-surface); border: 1px solid var(--c-border);
                border-radius: var(--radius); padding: 14px 16px; margin-bottom: 8px;
                display: flex; align-items: center; gap: 12px; }
.section-item.disabled { opacity: .5; }
.section-item .handle { cursor: grab; color: var(--c-text-2); font-size: 18px; user-select: none; }
.section-item .key   { font-weight: 600; flex: 1; }
.section-item .type  { color: var(--c-text-2); font-size: 12px; font-family: monospace; }

/* Buttons */
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 7px 14px;
       border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer;
       border: none; transition: opacity .15s; }
.btn:hover { opacity: .85; }
.btn-primary  { background: var(--c-primary); color: #fff; }
.btn-outline  { background: transparent; border: 1px solid var(--c-border); color: var(--c-text); }
.btn-danger   { background: var(--c-danger); color: #fff; }
.btn-sm       { padding: 4px 10px; font-size: 12px; }
.btn-toggle-on  { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
.btn-toggle-off { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }

/* Form */
.form-group  { margin-bottom: 16px; }
label        { display: block; font-weight: 500; margin-bottom: 6px; font-size: 13px; }
.hint        { font-size: 11px; color: var(--c-text-2); margin-top: 3px; }
input[type=text], textarea, select {
  width: 100%; padding: 8px 12px; border: 1px solid var(--c-border);
  border-radius: 6px; font-size: 13px; font-family: inherit;
  background: var(--c-surface); color: var(--c-text); }
textarea     { min-height: 80px; resize: vertical; }
input[type=text]:focus, textarea:focus { outline: 2px solid var(--c-primary); border-color: transparent; }

/* Breadcrumb */
.breadcrumb  { font-size: 12px; color: var(--c-text-2); margin-bottom: 20px; }
.breadcrumb a { color: var(--c-text-2); }
.breadcrumb span { margin: 0 6px; }

/* Seed editor */
.seed-field  { margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid var(--c-border); }
.seed-field:last-child { border-bottom: none; }
.seed-array-item { background: var(--c-bg); border: 1px solid var(--c-border);
                   border-radius: 6px; padding: 12px; margin-bottom: 8px; }

/* Flash */
#flash { position: fixed; top: 16px; right: 16px; padding: 10px 16px;
         border-radius: 8px; background: var(--c-success); color: #fff;
         font-weight: 500; font-size: 13px; display: none; z-index: 999; }
"""

_BASE_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AUTOSITES Admin</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
  <style>{css}</style>
</head>
<body>
<div class="topbar">
  <strong>AUTOSITES</strong>
  <a href="/admin">Pages</a>
</div>
<div id="flash"></div>
{body}
<script>
function flash(msg, ok=true) {{
  const el = document.getElementById('flash');
  el.textContent = msg;
  el.style.background = ok ? '#22c55e' : '#ef4444';
  el.style.display = 'block';
  setTimeout(() => el.style.display = 'none', 2500);
}}
async function api(method, url, data) {{
  const r = await fetch(url, {{
    method, headers: {{'Content-Type': 'application/json'}},
    body: data ? JSON.stringify(data) : undefined
  }});
  return r.json();
}}
</script>
</body>
</html>"""


def _html(body: str) -> HTMLResponse:
    return HTMLResponse(_BASE_HTML.format(css=_ADMIN_CSS, body=body))


# ── Pages index ───────────────────────────────────────────────────────────────

@router.get("/admin", response_class=HTMLResponse)
def admin_index(db: Session = Depends(get_db)):
    pages = db.query(PageDB).all()

    rows = ""
    for p in pages:
        badge    = f'<span class="badge badge-on">actif</span>' if p.enabled else \
                   f'<span class="badge badge-off">désactivé</span>'
        sections = len(p.sections)
        rows += f"""
        <div class="card">
          <div class="card-row">
            <div>
              <div class="label"><a href="/admin/pages/{p.id}">{p.slug}</a></div>
              <div class="meta">{p.page_type} · {p.lang} · {sections} section(s)</div>
            </div>
            {badge}
            <a href="/admin/pages/{p.id}" class="btn btn-outline btn-sm">Éditer</a>
            <a href="/api/generate/pages/{p.id}/preview" target="_blank"
               class="btn btn-outline btn-sm">Aperçu</a>
            <button class="btn btn-primary btn-sm"
              onclick="generatePage('{p.id}', '{p.slug}')">Générer</button>
          </div>
        </div>"""

    empty = "<p style='color:var(--c-text-2)'>Aucune page. Ajoutez un manifest JSON dans <code>manifests/</code> et redémarrez.</p>" if not pages else ""

    return _html(f"""
    <div class="container">
      <h1>Pages</h1>
      <p class="subtitle">Gérez vos pages, sections et contenus.</p>
      {rows}{empty}
    </div>
    <script>
    async function generatePage(id, slug) {{
      flash('Génération en cours…');
      const r = await api('POST', `/api/generate/pages/${{id}}`);
      if (r.ok) flash(`✓ ${{slug}} généré (${{r.size_kb}} Ko)`);
      else flash('Erreur : ' + JSON.stringify(r), false);
    }}
    </script>""")


# ── Page editor (sections) ────────────────────────────────────────────────────

@router.get("/admin/pages/{page_id}", response_class=HTMLResponse)
def admin_page(page_id: str, db: Session = Depends(get_db)):
    page = db.query(PageDB).filter_by(id=page_id).first()
    if not page:
        return _html("<div class='container'><p>Page introuvable.</p></div>")

    ctx = json.loads(page.placeholder_context or "{}")
    ctx_display = " · ".join(f"<code>{k}={v}</code>" for k, v in ctx.items())

    sections_html = ""
    for sec in page.sections:
        disabled_cls = "" if sec.enabled else " disabled"
        toggle_cls   = "btn-toggle-on" if sec.enabled else "btn-toggle-off"
        toggle_lbl   = "ON" if sec.enabled else "OFF"
        block_types  = ", ".join(b.block_type.replace("_block", "") for b in sec.blocks)

        sections_html += f"""
        <div class="section-item{disabled_cls}" id="sec-{sec.id}">
          <span class="handle" title="Réordonner">⋮⋮</span>
          <div class="key">{sec.key}</div>
          <div class="type">{block_types}</div>
          <a href="/admin/sections/{sec.id}" class="btn btn-outline btn-sm">Contenu</a>
          <button class="btn btn-sm {toggle_cls}"
            onclick="toggleSection('{sec.id}', {str(not sec.enabled).lower()})">
            {toggle_lbl}
          </button>
        </div>"""

    return _html(f"""
    <div class="container">
      <div class="breadcrumb"><a href="/admin">Pages</a><span>›</span>{page.slug}</div>
      <h1>{page.slug}</h1>
      <p class="subtitle">{page.page_type} · {ctx_display}</p>

      <div style="display:flex;gap:10px;margin-bottom:24px;">
        <a href="/api/generate/pages/{page_id}/preview" target="_blank"
           class="btn btn-outline">Aperçu</a>
        <button class="btn btn-primary" onclick="generatePage('{page_id}', '{page.slug}')">
          Générer HTML
        </button>
      </div>

      <h2>Sections <span style="color:var(--c-text-2);font-weight:400;font-size:13px">
        (glisser pour réordonner)</span></h2>
      <div id="sections-list">{sections_html}</div>
    </div>

    <script>
    async function toggleSection(id, enabled) {{
      const r = await api('PUT', `/api/sections/${{id}}/toggle`, {{enabled}});
      if (r.ok) {{ flash(enabled ? 'Section activée' : 'Section désactivée'); location.reload(); }}
    }}
    async function generatePage(id, slug) {{
      flash('Génération en cours…');
      const r = await api('POST', `/api/generate/pages/${{id}}`);
      if (r.ok) flash(`✓ ${{slug}} généré (${{r.size_kb}} Ko)`);
      else flash('Erreur', false);
    }}

    // Drag-and-drop simple pour réordonner
    let dragged = null;
    document.querySelectorAll('.section-item').forEach(el => {{
      el.draggable = true;
      el.addEventListener('dragstart', () => dragged = el);
      el.addEventListener('dragover',  e => {{ e.preventDefault(); el.style.borderColor='var(--c-primary)'; }});
      el.addEventListener('dragleave', () => el.style.borderColor='');
      el.addEventListener('drop', async () => {{
        el.style.borderColor='';
        if (!dragged || dragged === el) return;
        const list = document.getElementById('sections-list');
        const items = [...list.children];
        const di = items.indexOf(dragged), ti = items.indexOf(el);
        if (di < ti) list.insertBefore(dragged, el.nextSibling);
        else         list.insertBefore(dragged, el);
        // Sauvegarder nouvel ordre
        const order = [...list.children].map((c, i) => ({{
          id: c.id.replace('sec-',''), order_index: i
        }}));
        const r = await api('POST', '/api/sections/reorder', order);
        if (r.ok) flash('Ordre sauvegardé');
      }});
    }});
    </script>""")


# ── Section editor (seed fields) ─────────────────────────────────────────────

@router.get("/admin/sections/{section_id}", response_class=HTMLResponse)
def admin_section(section_id: str, db: Session = Depends(get_db)):
    sec = db.query(SectionDB).filter_by(id=section_id).first()
    if not sec:
        return _html("<div class='container'><p>Section introuvable.</p></div>")

    page = sec.page
    blocks_html = ""

    for blk in sec.blocks:
        seed = json.loads(blk.seed_json or "{}")
        fields_html = _render_seed_fields(blk.id, blk.block_type, seed)
        blocks_html += f"""
        <div class="card">
          <h2>{blk.block_type.replace('_block','').upper()}
            <span style="font-size:11px;font-weight:400;color:var(--c-text-2);margin-left:8px">
              col-{blk.column_span}
            </span>
          </h2>
          {fields_html}
        </div>"""

    return _html(f"""
    <div class="container">
      <div class="breadcrumb">
        <a href="/admin">Pages</a><span>›</span>
        <a href="/admin/pages/{page.id}">{page.slug}</a><span>›</span>
        {sec.key}
      </div>
      <h1>Section : {sec.key}</h1>
      <p class="subtitle">Éditez le contenu de chaque bloc. Sauvegarde automatique champ par champ.</p>
      {blocks_html}
    </div>

    <script>
    async function saveField(blockId, fieldPath, value) {{
      // fieldPath: "title" | "stats.0.value" | etc.
      const parts = fieldPath.split('.');
      const r = await api('PATCH', `/api/blocks/${{blockId}}/seed`,
        buildPatch(parts, value));
      if (r.ok) flash('Sauvegardé ✓');
      else flash('Erreur', false);
    }}

    function buildPatch(parts, value) {{
      // Construit un objet patch à plat pour les champs simples
      // Pour les champs imbriqués on relit + patch côté serveur
      const obj = {{}};
      let cur = obj;
      for (let i = 0; i < parts.length - 1; i++) {{
        cur[parts[i]] = {{}};
        cur = cur[parts[i]];
      }}
      cur[parts[parts.length-1]] = value;
      return obj;
    }}

    // Auto-save on blur
    document.querySelectorAll('[data-block][data-field]').forEach(el => {{
      el.addEventListener('blur', () => {{
        saveField(el.dataset.block, el.dataset.field, el.value);
      }});
    }});
    </script>""")


def _render_seed_fields(block_id: str, block_type: str, seed: dict) -> str:
    """Génère les champs de formulaire depuis le seed dict selon le block_type."""
    html = ""

    def field(key: str, val, label: str = None, multiline: bool = False) -> str:
        lbl  = label or key.replace("_", " ").capitalize()
        fld  = f'data-block="{block_id}" data-field="{key}"'
        val_s = val if val is not None else ""
        if multiline:
            return f"""<div class="form-group">
              <label>{lbl}</label>
              <textarea {fld}>{val_s}</textarea>
            </div>"""
        return f"""<div class="form-group">
          <label>{lbl}</label>
          <input type="text" {fld} value="{_esc(str(val_s))}">
        </div>"""

    # Champs communs à la plupart des blocs
    simple_keys = ["title", "subtitle", "badge", "logo_text", "logo_href",
                   "copyright", "btn_label", "btn_href",
                   "cta_primary_label", "cta_primary_href",
                   "cta_secondary_label", "cta_secondary_href"]

    multiline_keys = ["body", "text", "description", "answer"]

    for k in simple_keys:
        if k in seed:
            html += field(k, seed[k])

    for k in multiline_keys:
        if k in seed:
            html += field(k, seed[k], multiline=True)

    # Tableaux (stats, steps, items, links, cards, etc.)
    array_keys = ["stats", "steps", "items", "links", "cards", "columns"]
    for arr_key in array_keys:
        if arr_key not in seed or not isinstance(seed[arr_key], list):
            continue
        html += f'<div class="seed-field"><label style="font-weight:600">{arr_key.capitalize()}</label>'
        for i, item in enumerate(seed[arr_key]):
            if isinstance(item, dict):
                sub = ""
                for k, v in item.items():
                    if isinstance(v, (str, int, float)) and k not in ("avatar", "cta_js"):
                        is_ml = k in ("description", "answer", "text", "content")
                        sub += field(f"{arr_key}.{i}.{k}", v, f"{k}", multiline=is_ml)
                    elif isinstance(v, list):
                        # sous-listes (ex: features dans pricing, links dans footer)
                        for j, sv in enumerate(v):
                            if isinstance(sv, dict):
                                for sk, svv in sv.items():
                                    sub += field(f"{arr_key}.{i}.{k}.{j}.{sk}", svv, f"{k}[{j}].{sk}")
                            else:
                                sub += field(f"{arr_key}.{i}.{k}.{j}", sv, f"{k}[{j}]")
                html += f'<div class="seed-array-item"><small style="color:var(--c-text-2);font-weight:600"># {i+1}</small>{sub}</div>'
            elif isinstance(item, str):
                html += field(f"{arr_key}.{i}", item, f"{arr_key}[{i}]")
        html += "</div>"

    return html or "<p style='color:var(--c-text-2);font-size:13px'>Pas de champs éditables détectés.</p>"


def _esc(s: str) -> str:
    return s.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
