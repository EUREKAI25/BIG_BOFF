from pathlib import Path
from fastapi import FastAPI
from AGENCY.BACKOFFICE.interagents_api import router as interagents_router
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


COCKPIT_SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "EXCHANGE" / "LIBRARY" / "TOOLS" / "schemas_cockpit"

SUBLYM_COCKPIT_BASE = Path(__file__).resolve().parents[2] / "EXCHANGE" / "LIBRARY"

app = FastAPI(title="EURKAI Agency Backoffice", version="0.1.0")




app.mount("/schemas", StaticFiles(directory=str(COCKPIT_SCHEMAS_DIR), html=True), name="schemas")
app.include_router(interagents_router)
@app.get("/api/health")
def health():
    return JSONResponse({"status": "ok"})


# --- Invisible HUB redirect (agnostic) ---
from fastapi import Query, HTTPException
from fastapi.responses import RedirectResponse
from urllib.parse import urlparse

def _hub_validate(dest: str) -> bool:
    if not dest:
        return False
    dest = dest.strip()
    if dest.startswith("/"):
        return True
    p = urlparse(dest)
    return False  # block absolute urls by default

@app.get("/api/hub/redirect")
def hub_redirect(to: str = Query(...)):
    if not _hub_validate(to):
        raise HTTPException(status_code=400, detail="invalid destination")
    print(f"[HUB] redirect -> {to}")
    return RedirectResponse(url=to, status_code=302)
# --- /HUB ---



@app.get("/__DEBUG_PROBE__")
def __debug_probe__():
    return {"status": "THIS FILE IS RUNNING"}





from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

@app.get("/lab", response_class=HTMLResponse)
def page_lab():
    return """
    <html>
      <head>
        <title>Lab</title>
        <style>
          body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont;
            background: #0f1115;
            color: #e5e7eb;
            padding: 4rem;
          }
          .box {
            max-width: 640px;
            margin: auto;
            opacity: 0.85;
          }
          h1 { margin-bottom: 1rem; }
          p { line-height: 1.6; }
        </style>
      </head>
      <body>
        <div class="box">
          <h1>Lab</h1>
          <p>This space is reserved for experimentation, prototypes, and internal research. No public interface yet.</p>
        </div>
      
    <div class="card">
      <div class="chips"><span class="chip">LIBRARY</span><span class="chip">SCHEMAS</span></div>
      <h3>Schemas</h3>
      <p>Cockpit SUBLYM pour gérer les schémas.</p>
      <a class="btn" href="/schemas">Open</a>
    </div>

</body>
    </html>
    """


from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

@app.get("/exchange", response_class=HTMLResponse)
def page_exchange():
    return """
    <html>
      <head>
        <title>Exchange</title>
        <style>
          body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont;
            background: #0f1115;
            color: #e5e7eb;
            padding: 4rem;
          }
          .box {
            max-width: 640px;
            margin: auto;
            opacity: 0.85;
          }
          h1 { margin-bottom: 1rem; }
          p { line-height: 1.6; }
        </style>
      </head>
      <body>
        <div class="box">
          <h1>Exchange</h1>
          <p>This space will host exchanges, flows, and structured interactions. Interface not available yet.</p>
        </div>
      </body>
    </html>
    """


from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

@app.get("/blog", response_class=HTMLResponse)
def page_blog():
    return """
    <html>
      <head>
        <title>Blog</title>
        <style>
          body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont;
            background: #0f1115;
            color: #e5e7eb;
            padding: 4rem;
          }
          .box {
            max-width: 640px;
            margin: auto;
            opacity: 0.85;
          }
          h1 { margin-bottom: 1rem; }
          p { line-height: 1.6; }
        </style>
      </head>
      <body>
        <div class="box">
          <h1>Blog</h1>
          <p>This space will contain long-form content, logs, and publications. Coming later.</p>
        </div>
      </body>
    </html>
    """


from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

@app.get("/library", response_class=HTMLResponse)
def library():
    return """
    <html>
      <head>
        <title>Library</title>
        <style>
          body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont;
            background: #0f1115;
            color: #e5e7eb;
            padding: 4rem;
          }
          .box {
            max-width: 720px;
            margin: auto;
          }
          h1 { margin-bottom: 1.5rem; }
          ul { list-style: none; padding: 0; }
          li {
            margin-bottom: 1rem;
            padding: 1rem;
            background: #161a22;
            border-radius: 8px;
          }
          a { color: #8ab4ff; text-decoration: none; }
        </style>
      </head>
      <body>
        <div class="box">
          <h1>Library</h1>
          <ul>
            <li>
              <strong>API</strong><br/>
              <small>Programmatic access to system capabilities.</small><br/>
              <a href="/docs" target="_blank">Open API reference</a>
            </li>
            <li>
              <strong>Models</strong><br/>
              <small>Available system models and schemas.</small>
            </li>
            <li>
              <strong>Resources</strong><br/>
              <small>Shared specifications, contracts and references.</small>
            </li>
          </ul>
        </div>
      </body>
    </html>
    """




# =========================
# CardMenu module (UI)
# Single source of truth: MENU dict
# =========================
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any, List

MENU: Dict[str, Any] = {
    "title": "EURKAI Backoffice",
    "subtitle": "Agency backoffice (minimal). Creator is an imported module. External spaces are opened via hubs.",
    "cards": [
        {
            "id": "create",
            "badges": ["AGENCY", "MODULE"],
            "title": "Create",
            "desc": "Uses the creator module (display interface: form/chat). Placeholder for now.",
            "href": "/create",
            "cta": "Open",
        },
        {
            "id": "modules",
            "badges": ["AGENCY", "LIBRARY-VIEW"],
            "title": "Modules",
            "desc": "List modules, state/tags, and how to plug IO (next).",
            "href": "/modules",
            "cta": "Open",
        },
        {
            "id": "projects",
            "badges": ["AGENCY"],
            "title": "Projects",
            "desc": "Empty for now (standardisation).",
            "href": "/projects",
            "cta": "Open",
        },
        {
            "id": "library",
            "badges": ["AGENCY", "LIBRARY"],
            "title": "Library",
            "desc": "Shared references and reusable assets (API, models, schemas, resources).",
            "href": "/library",
            "cta": "Open",
        },
    ],
    "system": [
        {"id": "exchange", "title": "Exchange", "href": "/exchange"},
        {"id": "lab", "title": "Lab", "href": "/lab"},
        {"id": "blog", "title": "Blog", "href": "/blog"},
    ],
}

def _esc(x: str) -> str:
    return (x or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def render_card_menu(menu: Dict[str, Any]) -> str:
    title = menu.get("title", "Backoffice")
    subtitle = menu.get("subtitle", "")
    cards: List[Dict[str, Any]] = menu.get("cards", [])
    system: List[Dict[str, Any]] = menu.get("system", [])

    def badge_html(badges):
        return "".join([f'<span class="badge">{_esc(b)}</span>' for b in (badges or [])])

    # Make the whole card clickable by rendering <a class="card cardlink" href="...">...</a>
    cards_html = ""
    for c in cards:
        href = c.get("href", "#")
        cta = c.get("cta", "Open")
        cards_html += f"""
        <a class="card cardlink" href="{_esc(href)}">
          <div class="badges">{badge_html(c.get("badges"))}</div>
          <h3>{_esc(c.get("title",""))}</h3>
          <p>{_esc(c.get("desc",""))}</p>
          <div class="actions">
            <span class="btn">{_esc(cta)}</span>
          </div>
        </a>
        """

    system_html = ""
    for it in system:
        system_html += f'<a class="pill" href="{_esc(it.get("href","#"))}" target="_blank" rel="noopener noreferrer">{_esc(it.get("title",""))}</a>'

    return f"""
    <html>
      <head>
        <title>{_esc(title)}</title>
        <style>
          body {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont;
            background: #ffffff;
            color: #111827;
            margin: 0;
            padding: 48px 64px;
          }}
          h1 {{ margin: 0 0 8px 0; font-size: 54px; letter-spacing: -0.02em; }}
          .subtitle {{ color: #6b7280; margin-bottom: 28px; max-width: 1100px; }}

          .cards {{
            display: grid;
            grid-template-columns: repeat(3, minmax(260px, 1fr));
            gap: 16px;
            max-width: 1200px;
          }}

          a.cardlink {{
            text-decoration: none;
            color: inherit;
          }}

          .card {{
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 18px 18px 16px 18px;
            background: #fff;
            display: block;
          }}
          .card:hover {{
            border-color: #d1d5db;
          }}

          .badges {{ display: flex; gap: 8px; margin-bottom: 10px; }}
          .badge {{
            display: inline-block;
            border: 1px solid #e5e7eb;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 12px;
            color: #111827;
          }}
          .card h3 {{ margin: 6px 0 8px 0; font-size: 20px; }}
          .card p {{ margin: 0 0 14px 0; color: #4b5563; line-height: 1.45; }}

          .actions {{ display: flex; justify-content: flex-start; }}
          .btn {{
            display: inline-block;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 8px 12px;
            font-size: 14px;
            background: #fff;
          }}

          .sep {{ height: 1px; background: #e5e7eb; margin: 18px 0; max-width: 1200px; }}
          .system-title {{ font-size: 14px; color: #6b7280; margin-bottom: 8px; }}
          .pills {{ display: flex; gap: 10px; flex-wrap: wrap; }}
          .pill {{
            display: inline-block;
            border: 1px solid #e5e7eb;
            border-radius: 999px;
            padding: 8px 14px;
            font-size: 14px;
            color: #111827;
            text-decoration: none;
            background: #fff;
          }}
          .note {{ color: #6b7280; margin-top: 10px; font-size: 13px; }}

          @media (max-width: 980px) {{
            body {{ padding: 36px 22px; }}
            .cards {{ grid-template-columns: 1fr; }}
          }}
        </style>
      </head>
      <body>
        <h1>{_esc(title)}</h1>
        <div class="subtitle">{_esc(subtitle)}</div>

        <div class="cards">
          {cards_html}
        </div>

        <div class="sep"></div>

        <div class="system-title">System</div>
        <div class="pills">{system_html}</div>
        <div class="note">Hubs are the only allowed articulation points (validate + log + redirect).</div>
      </body>
    </html>
    """




@app.get("/", response_class=HTMLResponse)
def home():
    return render_card_menu(MENU)


from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

def _get_catalog_modules():
    try:
        data = json.loads(Path(r"/Users/nathalie/Dropbox/____BIG_BOFF___/INTERAGENTS/TOOL/LIBRARY/REGISTRY/library_catalog.json").read_text(encoding="utf-8"))
    except Exception:
        return []
    mods = data.get("modules", [])
    if isinstance(mods, dict):
        mods = list(mods.values())
    if not isinstance(mods, list):
        return []
    out = []
    for m in mods:
        if isinstance(m, dict):
            mid = m.get("id") or m.get("name")
            side = m.get("side") or m.get("layer") or ""
            if mid:
                out.append((str(mid), str(side)))
    return out


import json
import html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

CATALOG_PATH = Path("/Users/nathalie/Dropbox/____BIG_BOFF___/INTERAGENTS/TOOL/LIBRARY/REGISTRY/library_catalog.json")

def _get_catalog_module_refs():
    if not CATALOG_PATH.exists():
        return []
    try:
        d = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    bucket = next((e for e in d.get("elementlist", []) if isinstance(e, dict) and e.get("id") == "modules"), None)
    refs = bucket.get("elementlist", []) if isinstance(bucket, dict) else []
    out = []
    for r in refs:
        if not isinstance(r, dict):
            continue
        v = r.get("value", {}) if isinstance(r.get("value"), dict) else {}
        out.append({
            "id": r.get("id") or "",
            "name": v.get("name") or "",
            "state": v.get("state") or "",
            "path": v.get("path") or "",
            "tags": v.get("tags") or []
        })
    return out

@app.get("/modules", response_class=HTMLResponse)
def modules_page():
    refs = _get_catalog_module_refs()
    if not refs:
        items = "<li>Aucun module déclaré dans le catalogue</li>"
    else:
        items = "".join(
            "<li><b>{}</b>{}{}{}{} </li>".format(
                html.escape(r["id"]),
                (" — " + html.escape(r["name"])) if r["name"] else "",
                (" — " + html.escape(r["state"])) if r["state"] else "",
                (" — <code>" + html.escape(r["path"]) + "</code>") if r["path"] else "",
                (" — " + ", ".join(html.escape(str(t)) for t in (r["tags"] or []))) if r["tags"] else ""
            )
            for r in refs
        )
    return HTMLResponse("<!doctype html><html><head><meta charset='utf-8'><title>Modules</title></head>"
                        "<body><h1>Modules</h1><ul>{}</ul></body></html>".format(items))

from fastapi import Body
from fastapi.responses import PlainTextResponse

TOOL_DIR = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = TOOL_DIR / "EXCHANGE" / "LIBRARY" / "RULES" / "SCHEMAS"

def _safe_name(name: str) -> str:
    name = name.strip().replace("\\", "/").split("/")[-1]
    if not name or ".." in name:
        raise ValueError("invalid name")
    return name

@app.get("/api/schemas_old_old")
def api_schemas_list():
    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for f in sorted(SCHEMAS_DIR.glob("*")):
        if f.is_file():
            out.append({"id": f.name, "size": f.stat().st_size})
    return {"items": out, "dir": str(SCHEMAS_DIR)}

@app.get("/api/schemas_old/{name}", response_class=PlainTextResponse)
def api_schemas_get(name: str):
    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
    name = _safe_name(name)
    fp = SCHEMAS_DIR / name
    if not fp.exists():
        return PlainTextResponse("", status_code=404)
    return fp.read_text(encoding="utf-8", errors="replace")

@app.put("/api/schemas_old_old/{name}")
def api_schemas_put(name: str, content: str = Body(..., media_type="text/plain")):
    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
    name = _safe_name(name)
    fp = SCHEMAS_DIR / name
    fp.write_text(content, encoding="utf-8")
    return {"ok": True, "id": name, "size": fp.stat().st_size}

@app.get("/schemas_old", response_class=HTMLResponse)
def schemas_page():
    return HTMLResponse("""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Schemas</title>
  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu; margin:24px; max-width:1100px}
    .row{display:flex; gap:16px}
    .col{flex:1}
    select, input, textarea, button{width:100%; padding:10px; font-size:14px}
    textarea{height:65vh; font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace}
    button{cursor:pointer}
    .muted{opacity:.7; font-size:12px}
  </style>
</head>
<body>
  <h1>Schemas</h1>
  <div class="row">
    <div class="col" style="max-width:360px">
      <div class="muted">Liste</div>
      <select id="list" size="18"></select>
      <div style="height:10px"></div>
      <div class="muted">Nouveau / renommer</div>
      <input id="name" placeholder="ex: module.schema.json"/>
      <div style="height:10px"></div>
      <button id="reload">Recharger</button>
      <button id="save">Enregistrer</button>
    </div>
    <div class="col">
      <div class="muted" id="meta"></div>
      <textarea id="editor" spellcheck="false"></textarea>
    </div>
  </div>

<script>
const list = document.getElementById("list");
const name = document.getElementById("name");
const editor = document.getElementById("editor");
const meta = document.getElementById("meta");

async function refresh() {
  const r = await fetch("/api/schemas");
  const j = await r.json();
  list.innerHTML = "";
  for (const it of (j.items || [])) {
    const o = document.createElement("option");
    o.value = it.id;
    o.textContent = it.id + " (" + it.size + "b)";
    list.appendChild(o);
  }
  meta.textContent = "dir: " + (j.dir || "");
}

async function loadOne(id) {
  const r = await fetch("/api/schemas/" + encodeURIComponent(id));
  if (!r.ok) { editor.value = ""; return; }
  editor.value = await r.text();
  name.value = id;
}

async function saveOne() {
  const id = name.value.trim();
  if (!id) return;
  const r = await fetch("/api/schemas/" + encodeURIComponent(id), {
    method: "PUT",
    headers: {"Content-Type": "text/plain; charset=utf-8"},
    body: editor.value
  });
  if (!r.ok) return;
  await refresh();
  for (const opt of list.options) if (opt.value === id) list.value = id;
}

list.addEventListener("change", () => loadOne(list.value));
document.getElementById("reload").addEventListener("click", refresh);
document.getElementById("save").addEventListener("click", saveOne);

refresh();
</script>
</body>
</html>
""")

@app.get("/api/tree")
def sublym_api_tree():
    base = SUBLYM_COCKPIT_BASE
    tree = {
        "root": "LIBRARY",
        "nodes": [
            {"id": "LIBRARY", "type": "folder", "name": "LIBRARY", "children": [
                {"id":"RULES", "type":"folder", "name":"RULES", "children":[
                    {"id":"SCHEMAS", "type":"folder", "name":"SCHEMAS", "children":[]}
                ]},
                {"id":"MODULES", "type":"folder", "name":"MODULES", "children":[]},
                {"id":"REGISTRY", "type":"folder", "name":"REGISTRY", "children":[]},
            ]}
        ],
        "base_path": str(base),
    }
    # multi-wrapper: top-level + aliases
    return {
        **tree,
        "data": tree,
        "result": tree,
        "tree": tree,
        "Tree": tree,
    }

@app.get("/api/object/{oid:path}")
def sublym_api_object(oid: str):
    base = SUBLYM_COCKPIT_BASE

    # objet "Object" minimal pour éviter le crash JS
    if oid in ("Object", "object", "Object.json"):
        obj = {"ObjectElementList": []}
        return {**obj, "data": obj, "result": obj, "object": obj, "Object": obj}

    rel = oid.lstrip("/")
    f = (base / rel).resolve()
    if str(base.resolve()) not in str(f):
        obj = {"ObjectElementList": []}
        return {**obj, "data": obj, "result": obj, "object": obj, "Object": obj, "error": "invalid_oid"}

    if f.is_file():
        try:
            import json
            obj = json.loads(f.read_text(encoding="utf-8"))
            # si le fichier n'a pas ObjectElementList, on ne force pas, mais on wrap quand même
            return {**obj, "data": obj, "result": obj, "object": obj, "Object": obj}
        except Exception as e:
            obj = {"ObjectElementList": []}
            return {**obj, "data": obj, "result": obj, "object": obj, "Object": obj, "error": "read_failed", "detail": str(e)}

    obj = {"ObjectElementList": []}
    return {**obj, "data": obj, "result": obj, "object": obj, "Object": obj, "error": "not_found", "oid": oid}

@app.post("/api/create")
def sublym_api_create(payload: dict = Body(...)):
    base = SUBLYM_COCKPIT_BASE
    rel = (payload.get("path") or payload.get("oid") or payload.get("name") or "").lstrip("/")
    if not rel:
        out = {"ok": False}
        return {**out, "data": out, "result": out, "error": "missing_path"}

    if not rel.endswith(".json"):
        rel = rel + ".json"

    f = (base / rel).resolve()
    if str(base.resolve()) not in str(f):
        out = {"ok": False}
        return {**out, "data": out, "result": out, "error": "invalid_path"}

    f.parent.mkdir(parents=True, exist_ok=True)
    if not f.exists():
        f.write_text("{}", encoding="utf-8")

    out = {"ok": True, "path": rel}
    return {**out, "data": out, "result": out}

    if not rel.endswith(".json"):
        rel = rel + ".json"

    f = (base / rel).resolve()
    if str(base.resolve()) not in str(f):
        return {"data": None, "error":"invalid_path"}

    f.parent.mkdir(parents=True, exist_ok=True)
    if not f.exists():
        f.write_text("{}", encoding="utf-8")

    return {"data": {"ok": True, "path": rel}}

def sublym_api_create(payload: dict = Body(...)):
    """
    Compat minimal : crée un fichier json vide.
    Attendu cockpit: payload contient typiquement name/path/type.
    """
    base = SUBLYM_COCKPIT_BASE
    rel = (payload.get("path") or payload.get("oid") or payload.get("name") or "").lstrip("/")
    if not rel:
        return {"error":"missing_path"}

    if not rel.endswith(".json"):
        rel = rel + ".json"

    f = (base / rel).resolve()
    if str(base.resolve()) not in str(f):
        return {"error":"invalid_path"}

    f.parent.mkdir(parents=True, exist_ok=True)
    if not f.exists():
        f.write_text("{}", encoding="utf-8")
    return {"ok": True, "path": rel}


from AGENCY.BACKOFFICE.sublym_api_compat import router as sublym_router
app.include_router(sublym_router)

from AGENCY.BACKOFFICE.sublym_add_to_list import router as addlist_router
app.include_router(addlist_router)

from AGENCY.BACKOFFICE.sublym_api_full_compat import router as sublym_router
app.include_router(sublym_router)
