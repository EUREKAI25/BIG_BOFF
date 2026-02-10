#!/usr/bin/env python3
# _chat_topics_ai.py
# Analyse des exports (JSON) de discussions, appel OpenAI, sortie unique JSON structuré.
# Résultats:
#   - /Users/nathalie/Dropbox/CHATS/_index/chats_ai_index.json   (synthèses par chat)
#   - /Users/nathalie/Dropbox/CHATS/_index/chats_ai_costs.json   (usages tokens & coûts estimés)

# ----------------------------------------------------------------------------- 
# ⚙️ CONFIG DE BASE
ROOT_DIR = "/Users/nathalie/Dropbox/CHATS"                 # dossier des chats (scan récursif)
OUTPUT_JSON = "/Users/nathalie/Dropbox/CHATS/_index/chats_ai_index.json"
COSTS_JSON  = "/Users/nathalie/Dropbox/CHATS/_index/chats_ai_costs.json"

# Modèle principal + fallback si non autorisé
PREFERRED_MODEL = "gpt-4.1-mini"
FALLBACK_MODEL  = "gpt-4o-mini"
MODEL = PREFERRED_MODEL

# 💸 Prix estimés par 1K tokens (modifiables)
PRICES_PER_1K = {
    "gpt-4.1-mini": {"input": 0.30, "output": 1.20},
    "gpt-4o-mini":  {"input": 0.15, "output": 0.60},
}
# Si ton compte a d'autres tarifs, ajuste ce dict (ou passe par env PRICES_JSON)

LANG = "fr"                                                # langue de sortie
MAX_CHARS_PER_CHUNK = 12000
MAX_CHUNKS_PER_CHAT = 12
INCLUDE_EXTS = (".json",)                                  # JSON uniquement
TIMEOUT_SECS = 120
RETRY_MAX = 4

# Exclusions
IGNORE_DIR_PARTS = ("_index", "_files", "static", "assets", "node_modules", "__pycache__")
# Tous les fichiers qui commencent par "_" sont ignorés.
# ----------------------------------------------------------------------------- 

import os, sys, re, json, time, html, io, math
from typing import List, Dict, Any, Tuple, Optional

# -------------- Utils génériques --------------
def _mask(k: str) -> str:
    if not k or len(k) < 12: return k
    return k[:7] + "…" + k[-4:]

def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

HTML_TAG_RE = re.compile(r"<[^>]+>")
def strip_html(s: str) -> str:
    try: s = html.unescape(s)
    except Exception: pass
    return HTML_TAG_RE.sub(" ", s)

def safe_open_text(path: str) -> Optional[io.TextIOBase]:
    try: return open(path, "r", encoding="utf-8", errors="ignore")
    except Exception:
        try: return open(path, "r", encoding="latin-1", errors="ignore")
        except Exception: return None

# -------------- Chargement robuste de la clé OpenAI --------------
def _assert_key_valid(key: str, source: str) -> None:
    bad = ("XXXX", "***", "*****", "REPLACE", "YOUR_KEY", "{", "}")
    if any(b in key for b in bad) or len(key) < 20:
        raise RuntimeError(
            f"⚠️ Clé OpenAI invalide depuis {source}. Valeur: {_mask(key)}\n"
            "   Assure-toi d’avoir collé la vraie clé sk-…/sk-proj-… (sans espaces ni retours)."
        )

def load_openai_secrets() -> Dict[str, Optional[str]]:
    secrets: Dict[str, Optional[str]] = {"OPENAI_API_KEY": None, "OPENAI_ORG": None, "OPENAI_PROJECT": None}
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [(script_dir, "openai_key.py"), (ROOT_DIR, "openai_key.py")]

    for base, fname in candidates:
        path = os.path.join(base, fname)
        if os.path.isfile(path):
            if base not in sys.path:
                sys.path.append(base)
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("openai_key", path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore
                for k in ("OPENAI_API_KEY", "OPENAI_ORG", "OPENAI_PROJECT"):
                    if hasattr(mod, k) and isinstance(getattr(mod, k), str):
                        secrets[k] = getattr(mod, k).strip()
            except Exception as e:
                raise RuntimeError(f"⚠️ Erreur lors du chargement de {path}: {e}")

    secrets["OPENAI_API_KEY"] = secrets["OPENAI_API_KEY"] or os.environ.get("OPENAI_API_KEY", "").strip() or None
    secrets["OPENAI_ORG"]     = secrets["OPENAI_ORG"] or os.environ.get("OPENAI_ORG", "").strip() or None
    secrets["OPENAI_PROJECT"] = secrets["OPENAI_PROJECT"] or os.environ.get("OPENAI_PROJECT", "").strip() or None

    if not secrets["OPENAI_API_KEY"]:
        raise RuntimeError(
            "⚠️ Impossible de trouver OPENAI_API_KEY.\n"
            f"- Place un fichier openai_key.py avec OPENAI_API_KEY=\"sk-…\" dans:\n"
            f"  • {script_dir}\n  • ou {ROOT_DIR}\n"
            f"- Ou exporte OPENAI_API_KEY dans l’environnement."
        )
    _assert_key_valid(secrets["OPENAI_API_KEY"], source="file/env")

    # Prix custom via env PRICES_JSON (optionnel)
    try:
        _prices = os.environ.get("PRICES_JSON")
        if _prices:
            data = json.loads(_prices)
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, dict) and "input" in v and "output" in v:
                        PRICES_PER_1K[k] = {"input": float(v["input"]), "output": float(v["output"])}
    except Exception:
        pass

    return secrets

SECRETS = load_openai_secrets()
OPENAI_API_KEY = SECRETS["OPENAI_API_KEY"]  # type: ignore
OPENAI_ORG = SECRETS["OPENAI_ORG"]
OPENAI_PROJECT = SECRETS["OPENAI_PROJECT"]

# Forcer l’usage par tous les SDK
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY  # type: ignore
if OPENAI_ORG: os.environ["OPENAI_ORG"] = OPENAI_ORG
if OPENAI_PROJECT: os.environ["OPENAI_PROJECT"] = OPENAI_PROJECT

print(f"[auth] Using key: {_mask(OPENAI_API_KEY)}  org={OPENAI_ORG or '-'}  project={OPENAI_PROJECT or '-'}")

# -------------- Extraction JSON sûre depuis la réponse --------------
JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
BRACE_START_RE = re.compile(r"\{", re.DOTALL)

def safe_json_loads(text: str) -> Optional[dict]:
    txt = (text or "").strip()
    if not txt:
        return None
    try:
        return json.loads(txt)
    except Exception:
        pass
    m = JSON_BLOCK_RE.search(txt)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    m2 = BRACE_START_RE.search(txt)
    if not m2:
        return None
    start = m2.start()
    depth = 0
    for i in range(start, len(txt)):
        if txt[i] == "{":
            depth += 1
        elif txt[i] == "}":
            depth -= 1
            if depth == 0:
                candidate = txt[start:i+1]
                try:
                    return json.loads(candidate)
                except Exception:
                    break
    return None

# -------------- Coûts & usages --------------
def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    prices = PRICES_PER_1K.get(model) or {"input": 0.0, "output": 0.0}
    return (prompt_tokens / 1000.0) * prices["input"] + (completion_tokens / 1000.0) * prices["output"]

GLOBAL_USAGE = {
    "by_model": {},   # model -> {"prompt_tokens":..., "completion_tokens":..., "total_tokens":..., "cost_usd":...}
    "by_chat":   {},  # chat_name -> {"calls": N, "prompt_tokens":..., "completion_tokens":..., "total_tokens":..., "cost_usd":...}
}

def _add_usage(model: str, chat_name: str, pt: int, ct: int, tt: int):
    cost = estimate_cost(model, pt, ct)
    # global by model
    bm = GLOBAL_USAGE["by_model"].setdefault(model, {"prompt_tokens":0,"completion_tokens":0,"total_tokens":0,"cost_usd":0.0})
    bm["prompt_tokens"] += pt; bm["completion_tokens"] += ct; bm["total_tokens"] += tt; bm["cost_usd"] += cost
    # by chat
    bc = GLOBAL_USAGE["by_chat"].setdefault(chat_name, {"calls":0,"prompt_tokens":0,"completion_tokens":0,"total_tokens":0,"cost_usd":0.0})
    bc["calls"] += 1; bc["prompt_tokens"] += pt; bc["completion_tokens"] += ct; bc["total_tokens"] += tt; bc["cost_usd"] += cost

# -------------- Client OpenAI (compat SDK) --------------
def _parse_usage_from_response(resp) -> Tuple[int,int,int]:
    """Retourne (prompt_tokens, completion_tokens, total_tokens) si dispo, sinon (0,0,0)."""
    # Nouveau SDK: resp.usage.input_tokens / output_tokens / total_tokens
    try:
        u = getattr(resp, "usage", None)
        if u:
            pt = getattr(u, "prompt_tokens", None) or getattr(u, "input_tokens", 0) or 0
            ct = getattr(u, "completion_tokens", None) or getattr(u, "output_tokens", 0) or 0
            tt = getattr(u, "total_tokens", None) or (pt + ct)
            return int(pt or 0), int(ct or 0), int(tt or 0)
    except Exception:
        pass
    # Legacy dict-like
    try:
        u = resp.get("usage", None)  # type: ignore
        if u:
            pt = u.get("prompt_tokens") or u.get("input_tokens") or 0
            ct = u.get("completion_tokens") or u.get("output_tokens") or 0
            tt = u.get("total_tokens") or (pt + ct)
            return int(pt or 0), int(ct or 0), int(tt or 0)
    except Exception:
        pass
    # Certaines réponses mettent usage au niveau choice/message
    try:
        choices = resp.choices  # type: ignore
        if choices and hasattr(choices[0], "usage") and choices[0].usage:
            u = choices[0].usage
            pt = getattr(u, "prompt_tokens", 0)
            ct = getattr(u, "completion_tokens", 0)
            tt = getattr(u, "total_tokens", pt + ct)
            return int(pt), int(ct), int(tt)
    except Exception:
        pass
    return 0,0,0

def _make_openai_complete(current_model: str):
    """
    Retourne openai_complete(prompt, temperature) pour un modèle donné.
    Utilise *chat completions* (universel). Si response_format n’est pas supporté,
    on retente sans; safe_json_loads() gère le bruit éventuel.
    Renvoie: (text, usage_dict) avec usage_dict = {"prompt_tokens":..,"completion_tokens":..,"total_tokens":..}
    """
    try:
        # Nouveau paquet openai>=1.x
        from openai import OpenAI
        kwargs = {"api_key": OPENAI_API_KEY}
        if OPENAI_ORG: kwargs["organization"] = OPENAI_ORG
        if OPENAI_PROJECT: kwargs["project"] = OPENAI_PROJECT
        client = OpenAI(**kwargs)

        def _complete(prompt: str, temperature: float = 0.1):
            messages = [
                {"role": "system", "content": "You are a precise JSON-only generator. Reply with valid JSON only."},
                {"role": "user", "content": prompt},
            ]
            try:
                resp = client.chat.completions.create(
                    model=current_model,
                    messages=messages,
                    temperature=temperature,
                    timeout=TIMEOUT_SECS,
                    response_format={"type": "json_object"},
                )
            except TypeError:
                resp = client.chat.completions.create(
                    model=current_model,
                    messages=messages,
                    temperature=temperature,
                    timeout=TIMEOUT_SECS,
                )
            # texte
            try:
                text = resp.choices[0].message.content  # type: ignore
            except Exception:
                text = str(resp)
            # usage
            pt, ct, tt = _parse_usage_from_response(resp)
            usage = {"prompt_tokens": pt, "completion_tokens": ct, "total_tokens": tt}
            return text, usage
        return _complete

    except Exception:
        # Fallback vers ancien SDK openai<1.x
        import openai
        openai.api_key = OPENAI_API_KEY  # type: ignore
        if OPENAI_ORG:
            openai.organization = OPENAI_ORG

        def _complete(prompt: str, temperature: float = 0.1):
            resp = openai.ChatCompletion.create(
                model=current_model,
                messages=[
                    {"role": "system", "content": "You are a precise JSON-only generator. Reply with valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                timeout=TIMEOUT_SECS,
            )
            text = resp["choices"][0]["message"]["content"]
            u = resp.get("usage", {})  # type: ignore
            usage = {
                "prompt_tokens": int(u.get("prompt_tokens", 0)),
                "completion_tokens": int(u.get("completion_tokens", 0)),
                "total_tokens": int(u.get("total_tokens", 0)),
            }
            return text, usage
        return _complete

def _preflight(model: str) -> Tuple[bool, Optional[str]]:
    try:
        test_complete = _make_openai_complete(model)
        _ = test_complete("ping", temperature=0.0)
        return True, None
    except Exception as e:
        return False, str(e)

ok, err = _preflight(MODEL)
if not ok:
    print(f"[auth] Préflight sur {MODEL} a échoué: {err}")
    print(f"[auth] Tentative avec modèle de secours: {FALLBACK_MODEL}")
    MODEL = FALLBACK_MODEL
    ok2, err2 = _preflight(MODEL)
    if not ok2:
        raise RuntimeError(
            "❌ Auth OpenAI échouée.\n"
            f"- Clé {_mask(OPENAI_API_KEY)} active ? (Dashboard > API keys)\n"
            "- Modèle autorisé par ton projet/org ?\n"
            f"Dernière erreur: {err2 or err}"
        )

openai_complete = _make_openai_complete(MODEL)
print(f"[auth] Using model: {MODEL}")

# -------------- Fichiers --------------
def iter_files(root: str, exts: Tuple[str, ...]) -> List[str]:
    paths = []
    for dirpath, _, filenames in os.walk(root):
        if any(part in dirpath for part in IGNORE_DIR_PARTS): continue
        for fn in filenames:
            if fn.startswith("_"): continue
            if not fn.lower().endswith(exts): continue
            fp = os.path.join(dirpath, fn)
            if os.path.abspath(fp) == os.path.abspath(OUTPUT_JSON): continue
            if any(part in fp for part in IGNORE_DIR_PARTS): continue
            paths.append(fp)
    paths.sort()
    return paths

# -------------- Extraction JSON (incl. ChatGPT "mapping") --------------
def _from_chatgpt_mapping(obj) -> str:
    try:
        mapping = obj.get("mapping", {})
        parts = []
        for node in mapping.values():
            msg = (node or {}).get("message") or {}
            content = msg.get("content") or {}
            if isinstance(content, dict) and isinstance(content.get("parts"), list):
                for p in content["parts"]:
                    if isinstance(p, str): parts.append(p)
            if isinstance(content, str): parts.append(content)
        return "\n".join(parts).strip()
    except Exception:
        return ""

def extract_title_and_text(path: str) -> Tuple[str, str]:
    f = safe_open_text(path)
    if not f: return (os.path.basename(path), "")
    with f: raw = f.read()

    title = os.path.basename(path)
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict) and "mapping" in obj:
            body = _from_chatgpt_mapping(obj)
            if body:
                for k in ("title","subject","conversation_title","thread","name"):
                    if k in obj and isinstance(obj[k], str) and obj[k].strip():
                        title = obj[k].strip(); break
                return (title, body)
        if isinstance(obj, dict):
            for k in ("title","subject","conversation_title","thread","name"):
                if k in obj and isinstance(obj[k], str) and obj[k].strip():
                    title = obj[k].strip(); break
            for msgs_key in ("messages","items","chats","log"):
                if msgs_key in obj and isinstance(obj[msgs_key], list):
                    parts = []
                    for it in obj[msgs_key]:
                        for mk in ("content","text","message","body","msg"):
                            if isinstance(it, dict) and mk in it:
                                val = it[mk]
                                if isinstance(val, str):
                                    parts.append(val)
                                elif isinstance(val, list):
                                    for v in val:
                                        if isinstance(v, dict) and "text" in v and isinstance(v["text"], str):
                                            parts.append(v["text"])
                    if parts: return (title, "\n".join(parts))
            for k in ("content","text","message","body"):
                if k in obj and isinstance(obj[k], str):
                    return (title, obj[k])
        elif isinstance(obj, list):
            parts = []
            for it in obj:
                if isinstance(it, dict):
                    for mk in ("content","text","message","body","msg"):
                        if mk in it and isinstance(it[mk], str):
                            parts.append(it[mk])
            if parts: return (title, "\n".join(parts))
    except Exception:
        return (title, normalize_space(raw))

    return (title, normalize_space(raw))

# -------------- Chunking (avec positions) --------------
def chunk_text_with_spans(text: str, max_chars: int) -> List[Tuple[str, int, int]]:
    """Renvoie [(chunk_text, start_idx, end_idx)] en indices du texte normalisé."""
    text = normalize_space(text)
    n = len(text)
    if n <= max_chars:
        return [(text, 0, n)] if text else []
    chunks: List[Tuple[str,int,int]] = []
    i = 0
    while i < n and len(chunks) < MAX_CHUNKS_PER_CHAT:
        j = min(n, i + max_chars)
        k = text.rfind(". ", i, j)
        if k == -1:
            k = j
        else:
            k = k + 2
        chunks.append((text[i:k], i, k))
        i = k
    return chunks

def backoff_sleep(attempt: int):
    # backoff exponentiel doux + jitter (jusqu'à 30s)
    time.sleep(min(30, (2 ** attempt)) * (1.0 + 0.05 * attempt))

# -------------- Prompts enrichis --------------
def build_chunk_prompt(title: str, chunk: str, meta: Dict[str, Any]) -> str:
    """
    meta = {
      "file": "...", "chunk_index": int, "chunk_char_start": int, "chunk_char_end": int
    }
    """
    return (
        "Tu es un analyste. Lis UNIQUEMENT le fragment de conversation fourni et produis un JSON d’INDICES.\n"
        f"Conversation: {title}\n"
        f"META: file={meta.get('file')}, chunk_index={meta.get('chunk_index')}, "
        f"chunk_char_start={meta.get('chunk_char_start')}, chunk_char_end={meta.get('chunk_char_end')}\n"
        "Réponds STRICTEMENT en JSON (aucun texte hors JSON) avec ce schéma:\n"
        "{\n"
        "  \"type_votes\": {\"pro\": int, \"perso\": int},\n"
        "  \"nature_votes\": {\"code\": int, \"discussion\": int, \"idée\": int, \"stratégie\": int},\n"
        "  \"interest_votes\": [0,1,2,3,4,5],\n"
        "  \"intention\": str,\n"
        "  \"problematic\": str,\n"
        "  \"tags\": [str],\n"
        "  \"subjects_candidates\": [\n"
        "    {\"title\": str, \"description\": str, \"contribution_to_agency\": str,\n"
        "     \"evidence\": [{\"quote\": str}]}\n"
        "  ],\n"
        "  \"special_focus\": {\n"
        "    \"rdf_triples_performance\": {\"status\": \"found|not_found|uncertain\", \"answers\": [{\"answer\": str, \"evidence\": str}]},\n"
        "    \"rules_to_respect\": {\"status\": \"found|not_found|uncertain\", \"answers\": [{\"answer\": str, \"evidence\": str}]},\n"
        "    \"scenario_method_categories\": {\"status\": \"found|not_found|uncertain\", \"answers\": [{\"answer\": str, \"evidence\": str}]},\n"
        "    \"excel_like_methods\": {\"status\": \"found|not_found|uncertain\", \"answers\": [{\"answer\": str, \"evidence\": str}]},\n"
        "    \"auto_push_github\": {\"status\": \"found|not_found|uncertain\", \"answers\": [{\"answer\": str, \"evidence\": str}]}\n"
        "  }\n"
        "}\n"
        "IMPORTANT: si aucune info pertinente, mets status=\"not_found\" et explique brièvement pourquoi.\n"
        "FRAGMENT:\n"
        "\"\"\"\n" + chunk + "\n\"\"\"\n"
    )

def build_merge_prompt(title: str, chunk_jsons: List[Dict[str, Any]]) -> str:
    serialized = json.dumps(chunk_jsons, ensure_ascii=False)
    return (
        "Tu es un synthétiseur. Tu reçois une LISTE de JSON d’indices (issus de fragments d’un même chat).\n"
        "Fusionne-les en UN SEUL objet JSON FINAL avec ce schéma EXACT:\n"
        "{\n"
        "  \"chat_name\": str,\n"
        "  \"type\": \"pro\" | \"perso\",\n"
        "  \"interest\": 0|1|2|3|4|5,\n"
        "  \"nature\": [\"code\"|\"discussion\"|\"idée\"|\"stratégie\"...],\n"
        "  \"intention\": str,\n"
        "  \"problematic\": str,\n"
        "  \"tags\": [str],\n"
        "  \"subjects\": [\n"
        "    {\"title\": str, \"description\": str, \"contribution_to_agency\": str,\n"
        "     \"evidence\": [{\"quote\": str, \"pointer\": {\"file\": str, \"chunk_index\": int, \"chunk_char_start\": int, \"chunk_char_end\": int}}]}\n"
        "  ],\n"
        "  \"special_focus\": {\n"
        "    \"rdf_triples_performance\": {\"status\": str, \"answers\": [{\"answer\": str, \"evidence\": str}]},\n"
        "    \"rules_to_respect\": {\"status\": str, \"answers\": [{\"answer\": str, \"evidence\": str}]},\n"
        "    \"scenario_method_categories\": {\"status\": str, \"answers\": [{\"answer\": str, \"evidence\": str}]},\n"
        "    \"excel_like_methods\": {\"status\": str, \"answers\": [{\"answer\": str, \"evidence\": str}]},\n"
        "    \"auto_push_github\": {\"status\": str, \"answers\": [{\"answer\": str, \"evidence\": str}]}\n"
        "  }\n"
        "}\n"
        "Règles:\n"
        "- \"type\": classe majoritaire à partir de type_votes.\n"
        "- \"interest\": médiane arrondie de interest_votes (0..5).\n"
        "- \"nature\": labels dont le score > 0, triés par score décroissant (max 4).\n"
        "- \"subjects\": 1..8; si type=\"perso\", mets description & contribution_to_agency=\"\".\n"
        "- \"intention\"/\"problematic\": phrases courtes, concrètes.\n"
        "- \"tags\": dédupliqués, 5–12 max, pertinents pour le classement.\n"
        "- \"special_focus\": condense par thème (status + 0..5 meilleures réponses).\n"
        f"- \"chat_name\": \"{title}\".\n"
        "Voici la liste des JSON d’indices:\n" + serialized + "\n"
        "RENVOIE UNIQUEMENT le JSON FINAL, rien d’autre.\n"
    )

# -------------- Pipeline --------------
def analyze_chat(title: str, text: str, file_path: str) -> Optional[Dict[str, Any]]:
    chunks = chunk_text_with_spans(text, MAX_CHARS_PER_CHUNK)
    if not chunks: return None

    # 1) Notes par fragment (+ pointeurs)
    chunk_jsons = []
    for idx, (ch_text, ch_start, ch_end) in enumerate(chunks):
        meta = {
            "file": file_path,
            "chunk_index": idx,
            "chunk_char_start": ch_start,
            "chunk_char_end": ch_end
        }
        prompt = build_chunk_prompt(title, ch_text, meta)
        for attempt in range(RETRY_MAX):
            try:
                out, usage = openai_complete(prompt, temperature=0.1)
                if not out or not out.strip():
                    raise ValueError("empty response from model")
                j = safe_json_loads(out)
                if not j:
                    snippet = normalize_space(out)[:200]
                    raise ValueError(f"non-JSON output: {snippet}")
                # usage
                _add_usage(MODEL, title, usage.get("prompt_tokens",0), usage.get("completion_tokens",0), usage.get("total_tokens",0))

                # Injecter le pointeur META dans chaque evidence de subjects_candidates
                subs = j.get("subjects_candidates") or []
                for s in subs:
                    evs = s.get("evidence") or []
                    for ev in evs:
                        ev["pointer"] = meta  # on attache le pointeur au niveau chunk
                j["_pointer"] = meta
                chunk_jsons.append(j)
                break
            except Exception as e:
                if attempt + 1 >= RETRY_MAX:
                    print(f"[warn] chunk analyze failed ({title} #{idx}): {e}")
                    return None
                backoff_sleep(attempt)

    # 2) Fusion
    prompt = build_merge_prompt(title, chunk_jsons)
    for attempt in range(RETRY_MAX):
        try:
            out, usage = openai_complete(prompt, temperature=0.0)
            if not out or not out.strip():
                raise ValueError("empty merge response from model")
            result = safe_json_loads(out)
            # usage
            _add_usage(MODEL, title, usage.get("prompt_tokens",0), usage.get("completion_tokens",0), usage.get("total_tokens",0))

            if isinstance(result, dict) and "chat_name" in result and "subjects" in result:
                # Sécurité : s'assurer que chaque evidence possède un pointer (si le modèle a oublié)
                for subj in result.get("subjects", []):
                    for ev in subj.get("evidence", []) or []:
                        if "pointer" not in ev or not isinstance(ev["pointer"], dict):
                            ev["pointer"] = {
                                "file": file_path,
                                "chunk_index": 0,
                                "chunk_char_start": 0,
                                "chunk_char_end": min(len(normalize_space(text)), MAX_CHARS_PER_CHUNK)
                            }
                return result
            raise ValueError("merge response not a valid JSON object")
        except Exception as e:
            if attempt + 1 >= RETRY_MAX:
                print(f"[warn] merge failed ({title}): {e}")
                return None
            backoff_sleep(attempt)

# -------------- Fichiers & Main --------------
def iter_files(root: str, exts: Tuple[str, ...]) -> List[str]:
    paths = []
    for dirpath, _, filenames in os.walk(root):
        if any(part in dirpath for part in IGNORE_DIR_PARTS): continue
        for fn in filenames:
            if fn.startswith("_"): continue
            if not fn.lower().endswith(exts): continue
            fp = os.path.join(dirpath, fn)
            if os.path.abspath(fp) == os.path.abspath(OUTPUT_JSON): continue
            if any(part in fp for part in IGNORE_DIR_PARTS): continue
            paths.append(fp)
    paths.sort()
    return paths

def _write_costs_report():
    # Totaux globaux
    grand = {"prompt_tokens":0,"completion_tokens":0,"total_tokens":0,"cost_usd":0.0}
    for m, agg in GLOBAL_USAGE["by_model"].items():
        grand["prompt_tokens"] += agg["prompt_tokens"]
        grand["completion_tokens"] += agg["completion_tokens"]
        grand["total_tokens"] += agg["total_tokens"]
        grand["cost_usd"] += agg["cost_usd"]
    report = {
        "by_model": GLOBAL_USAGE["by_model"],
        "by_chat": GLOBAL_USAGE["by_chat"],
        "grand_totals": grand,
        "prices_per_1k": PRICES_PER_1K,
        "model_used": MODEL,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    os.makedirs(os.path.dirname(COSTS_JSON), exist_ok=True)
    with open(COSTS_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"[ok] Wrote costs report → {COSTS_JSON}")
    print(f"     Grand total: tokens={grand['total_tokens']:,}  cost≈${grand['cost_usd']:.4f}")

def main(test_limit: Optional[int] = 2):
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    files = iter_files(ROOT_DIR, INCLUDE_EXTS)

    hints = ("chatgpt", "claude", "conversation", "messages", "chat")
    filtered = [f for f in files if any(h in os.path.basename(f).lower() for h in hints)] or files

    if test_limit:
        filtered = filtered[:test_limit]
        print(f"[test mode] Scanning limited to {len(filtered)} files:")
        for f in filtered: print(" -", f)

    results = []
    total = len(filtered)
    print(f"[info] Found {total} candidate files. Starting analysis with model {MODEL}...")

    for i, path in enumerate(filtered, 1):
        title, text = extract_title_and_text(path)
        title = normalize_space(title) or os.path.basename(path)
        norm = normalize_space(text)
        if not norm:
            print(f"[skip] {i}/{total} {path} (empty)"); continue

        print(f"[{i}/{total}] analyzing: {title} …")
        res = analyze_chat(title, text, file_path=path)
        if res:
            res["_source_path"] = path
            results.append(res)
            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        else:
            print(f"[warn] analysis failed for: {path}")

    print(f"[ok] Wrote {len(results)} chat summaries → {OUTPUT_JSON}")
    _write_costs_report()

# -------------- Entry point --------------
if __name__ == "__main__":
    TEST_LIMIT = 2  # Mets None pour tout, ou un entier pour tester
    main(TEST_LIMIT)
