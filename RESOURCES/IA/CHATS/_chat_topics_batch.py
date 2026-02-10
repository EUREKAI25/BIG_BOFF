#!/usr/bin/env python3
# _chat_topics_batch.py
# Traitement par lots (avec boucle optionnelle) des conversations JSON:
# - intention, problematic, tags
# - subjects (evidence + pointeurs file/chunk/spans)
# - special_focus (tes 5 thèmes) avec status/answers/evidence
# - mesure tokens + coût estimé
# - exécution par lots + mode boucle (--loop) jusqu’à épuisement
#
# Sorties:
#   - /Users/nathalie/Dropbox/CHATS/_index/chats_ai_index.json   (append)
#   - /Users/nathalie/Dropbox/CHATS/_index/chats_ai_costs.json   (cumul)
#   - /Users/nathalie/Dropbox/CHATS/_index/state.json            (checkpoint)
#
# CLI (exemples):
#   python _chat_topics_batch.py --dry-run --batch-size 15 --include "chatgpt*" --model gpt-4o-mini
#   python _chat_topics_batch.py --batch-size 10 --model gpt-4o-mini
#   python _chat_topics_batch.py --resume --batch-size 10 --loop --loop-sleep 2 --max-cost 2.00
#
# ============================================================================

# ----------- CONFIG DE BASE -----------
ROOT_DIR   = "/Users/nathalie/Dropbox/CHATS"
INDEX_DIR  = "/Users/nathalie/Dropbox/CHATS/_index"
OUTPUT_JSON = f"{INDEX_DIR}/chats_ai_index.json"
COSTS_JSON  = f"{INDEX_DIR}/chats_ai_costs.json"
STATE_JSON  = f"{INDEX_DIR}/state.json"

# Modèle par défaut recommandé
DEFAULT_MODEL       = "gpt-4o-mini"
FALLBACK_MODEL      = "gpt-4.1-mini"
LANG = "fr"

# Chunking
MAX_CHARS_PER_CHUNK = 12000
MAX_CHUNKS_PER_CHAT = 12

# I/O
INCLUDE_EXTS = (".json",)
IGNORE_DIR_PARTS = ("_index", "_files", "static", "assets", "node_modules", "__pycache__")

# Temps / retries
TIMEOUT_SECS = 120
RETRY_MAX    = 4

# Tarifs réels (sept. 2025)
PRICES_PER_1K = {
    "gpt-4o-mini":  {"input": 0.00015, "output": 0.00060},
    "gpt-4o":       {"input": 0.00500, "output": 0.01500},
    "gpt-4.1-mini": {"input": 0.00100, "output": 0.00500},
    "gpt-3.5-turbo": {"input": 0.00050, "output": 0.00150},
}

# ============================================================================

import os, sys, re, json, time, html, io, math, fnmatch, argparse, signal
from typing import List, Dict, Any, Tuple, Optional

STOP_REQUESTED = False
def _signal_handler(signum, frame):
    global STOP_REQUESTED
    STOP_REQUESTED = True
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)

# ----------------- Utils -----------------
def _mask(k: str) -> str:
    if not k or len(k) < 12: return k
    return k[:7] + "…" + k[-4:]

def now_str() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")

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

# ----------------- Tarifs & usages -----------------
def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    prices = PRICES_PER_1K.get(model) or {"input": 0.0, "output": 0.0}
    return (prompt_tokens / 1000.0) * prices["input"] + (completion_tokens / 1000.0) * prices["output"]

GLOBAL_USAGE = {
    "by_model": {},   # model -> {"prompt_tokens":..., "completion_tokens":..., "total_tokens":..., "cost_usd":...}
    "by_file":  {},   # filepath -> {"calls": N, "prompt_tokens":..., "completion_tokens":..., "total_tokens":..., "cost_usd":...}
    "grand":    {"prompt_tokens":0,"completion_tokens":0,"total_tokens":0,"cost_usd":0.0},
    "model_used": DEFAULT_MODEL,
    "prices_per_1k": PRICES_PER_1K,
    "updated_at": now_str(),
}

def _add_usage(model: str, file_path: str, pt: int, ct: int, tt: int):
    cost = estimate_cost(model, pt, ct)
    bm = GLOBAL_USAGE["by_model"].setdefault(model, {"prompt_tokens":0,"completion_tokens":0,"total_tokens":0,"cost_usd":0.0})
    bm["prompt_tokens"] += pt; bm["completion_tokens"] += ct; bm["total_tokens"] += tt; bm["cost_usd"] += cost
    bf = GLOBAL_USAGE["by_file"].setdefault(file_path, {"calls":0,"prompt_tokens":0,"completion_tokens":0,"total_tokens":0,"cost_usd":0.0})
    bf["calls"] += 1; bf["prompt_tokens"] += pt; bf["completion_tokens"] += ct; bf["total_tokens"] += tt; bf["cost_usd"] += cost
    g = GLOBAL_USAGE["grand"]
    g["prompt_tokens"] += pt; g["completion_tokens"] += ct; g["total_tokens"] += tt; g["cost_usd"] += cost
    GLOBAL_USAGE["updated_at"] = now_str()

def _write_costs():
    os.makedirs(INDEX_DIR, exist_ok=True)
    with open(COSTS_JSON, "w", encoding="utf-8") as f:
        json.dump(GLOBAL_USAGE, f, ensure_ascii=False, indent=2)
    print(f"[ok] Wrote costs → {COSTS_JSON}  total_tokens={GLOBAL_USAGE['grand']['total_tokens']:,}  cost≈${GLOBAL_USAGE['grand']['cost_usd']:.4f}")

def _load_costs():
    if os.path.isfile(COSTS_JSON):
        try:
            with open(COSTS_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    GLOBAL_USAGE.clear()
                    GLOBAL_USAGE.update(data)
        except Exception:
            pass

# ----------------- Clé OpenAI -----------------
def _assert_key_valid(key: str):
    if not key or len(key) < 20: raise RuntimeError("OPENAI_API_KEY invalide ou manquante.")

def load_openai_key() -> Dict[str, Optional[str]]:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [(script_dir, "openai_key.py"), (ROOT_DIR, "openai_key.py")]

    key, org, project = None, None, None
    for base, fname in candidates:
        path = os.path.join(base, fname)
        if os.path.isfile(path):
            if base not in sys.path: sys.path.append(base)
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("openai_key", path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore
                if hasattr(mod, "OPENAI_API_KEY"): key = (getattr(mod, "OPENAI_API_KEY") or "").strip()
                if hasattr(mod, "OPENAI_ORG"): org = (getattr(mod, "OPENAI_ORG") or "").strip() or None
                if hasattr(mod, "OPENAI_PROJECT"): project = (getattr(mod, "OPENAI_PROJECT") or "").strip() or None
            except Exception as e:
                raise RuntimeError(f"Erreur en important {path}: {e}")

    key = key or os.environ.get("OPENAI_API_KEY", "").strip()
    org = org or os.environ.get("OPENAI_ORG", "").strip() or None
    project = project or os.environ.get("OPENAI_PROJECT", "").strip() or None
    _assert_key_valid(key)
    os.environ["OPENAI_API_KEY"] = key
    if org: os.environ["OPENAI_ORG"] = org
    if project: os.environ["OPENAI_PROJECT"] = project
    print(f"[auth] Using key: {_mask(key)}  org={org or '-'}  project={project or '-'}")
    return {"api_key": key, "org": org, "project": project}

# ----------------- JSON robust parsing -----------------
JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
BRACE_START_RE = re.compile(r"\{", re.DOTALL)

def safe_json_loads(text: str) -> Optional[dict]:
    txt = (text or "").strip()
    if not txt: return None
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
    if not m2: return None
    start = m2.start(); depth = 0
    for i in range(start, len(txt)):
        if txt[i] == "{": depth += 1
        elif txt[i] == "}":
            depth -= 1
            if depth == 0:
                candidate = txt[start:i+1]
                try:
                    return json.loads(candidate)
                except Exception:
                    break
    return None

# ----------------- OpenAI client (compat) -----------------
def _parse_usage_from_response(resp) -> Tuple[int,int,int]:
    try:
        u = getattr(resp, "usage", None)
        if u:
            pt = getattr(u, "prompt_tokens", None) or getattr(u, "input_tokens", 0) or 0
            ct = getattr(u, "completion_tokens", None) or getattr(u, "output_tokens", 0) or 0
            tt = getattr(u, "total_tokens", None) or (pt + ct)
            return int(pt or 0), int(ct or 0), int(tt or 0)
    except Exception:
        pass
    try:
        u = resp.get("usage", None)  # type: ignore
        if u:
            pt = u.get("prompt_tokens") or u.get("input_tokens") or 0
            ct = u.get("completion_tokens") or u.get("output_tokens") or 0
            tt = u.get("total_tokens") or (pt + ct)
            return int(pt or 0), int(ct or 0), int(tt or 0)
    except Exception:
        pass
    return 0,0,0

def make_openai_complete(model: str):
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            organization=os.environ.get("OPENAI_ORG"),
            project=os.environ.get("OPENAI_PROJECT"),
        )
        def _complete(prompt: str, temperature: float = 0.1):
            messages = [
                {"role": "system", "content": "You are a precise JSON-only generator. Reply with valid JSON only."},
                {"role": "user", "content": prompt},
            ]
            try:
                resp = client.chat.completions.create(
                    model=model, messages=messages, temperature=temperature, timeout=TIMEOUT_SECS,
                    response_format={"type": "json_object"},
                )
            except TypeError:
                resp = client.chat.completions.create(
                    model=model, messages=messages, temperature=temperature, timeout=TIMEOUT_SECS,
                )
            try:
                text = resp.choices[0].message.content  # type: ignore
            except Exception:
                text = str(resp)
            pt, ct, tt = _parse_usage_from_response(resp)
            return text, {"prompt_tokens": pt, "completion_tokens": ct, "total_tokens": tt}
        return _complete
    except Exception:
        import openai
        openai.api_key = os.environ["OPENAI_API_KEY"]
        if os.environ.get("OPENAI_ORG"): openai.organization = os.environ["OPENAI_ORG"]
        def _complete(prompt: str, temperature: float = 0.1):
            resp = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a precise JSON-only generator. Reply with valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature, timeout=TIMEOUT_SECS,
            )
            text = resp["choices"][0]["message"]["content"]
            u = resp.get("usage", {})
            usage = {
                "prompt_tokens": int(u.get("prompt_tokens", 0)),
                "completion_tokens": int(u.get("completion_tokens", 0)),
                "total_tokens": int(u.get("total_tokens", 0)),
            }
            return text, usage
        return _complete

# ----------------- Extraction texte -----------------
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

# ----------------- Chunking -----------------
def chunk_text_with_spans(text: str, max_chars: int) -> List[Tuple[str,int,int]]:
    text = normalize_space(text)
    n = len(text)
    if n <= max_chars:
        return [(text, 0, n)] if text else []
    chunks: List[Tuple[str,int,int]] = []
    i = 0
    while i < n and len(chunks) < MAX_CHUNKS_PER_CHAT:
        j = min(n, i + max_chars)
        k = text.rfind(". ", i, j)
        k = j if k == -1 else k + 2
        chunks.append((text[i:k], i, k)); i = k
    return chunks

def backoff_sleep(attempt: int):
    time.sleep(min(30, (2 ** attempt)) * (1.0 + 0.05 * attempt))

# ----------------- Prompts -----------------
def build_chunk_prompt(title: str, chunk: str, meta: Dict[str, Any]) -> str:
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

# ----------------- Pipeline IA -----------------
def analyze_chat(file_path: str, model: str, complete_fn) -> Optional[Dict[str, Any]]:
    title, text = extract_title_and_text(file_path)
    title = normalize_space(title) or os.path.basename(file_path)
    norm = normalize_space(text)
    if not norm:
        print(f"[skip] {file_path} (empty)"); return None

    # 1) fragmentation
    chunks = chunk_text_with_spans(norm, MAX_CHARS_PER_CHUNK)
    chunk_jsons = []
    for idx, (ch_text, ch_start, ch_end) in enumerate(chunks):
        meta = {"file": file_path, "chunk_index": idx, "chunk_char_start": ch_start, "chunk_char_end": ch_end}
        prompt = build_chunk_prompt(title, ch_text, meta)
        for attempt in range(RETRY_MAX):
            try:
                out, usage = complete_fn(prompt, temperature=0.1)
                if not out or not out.strip(): raise ValueError("empty response from model")
                j = safe_json_loads(out)
                if not j:
                    snippet = normalize_space(out)[:200]
                    raise ValueError(f"non-JSON output: {snippet}")
                _add_usage(model, file_path, usage.get("prompt_tokens",0), usage.get("completion_tokens",0), usage.get("total_tokens",0))
                subs = j.get("subjects_candidates") or []
                for s in subs:
                    for ev in s.get("evidence") or []:
                        ev["pointer"] = meta
                j["_pointer"] = meta
                chunk_jsons.append(j)
                break
            except Exception as e:
                if attempt + 1 >= RETRY_MAX:
                    print(f"[warn] chunk analyze failed ({os.path.basename(file_path)} #{idx}): {e}")
                    return None
                backoff_sleep(attempt)

    # 2) fusion
    prompt = build_merge_prompt(title, chunk_jsons)
    for attempt in range(RETRY_MAX):
        try:
            out, usage = complete_fn(prompt, temperature=0.0)
            if not out or not out.strip(): raise ValueError("empty merge response from model")
            res = safe_json_loads(out)
            _add_usage(model, file_path, usage.get("prompt_tokens",0), usage.get("completion_tokens",0), usage.get("total_tokens",0))
            if isinstance(res, dict) and "chat_name" in res and "subjects" in res:
                for subj in res.get("subjects", []) or []:
                    for ev in subj.get("evidence", []) or []:
                        if "pointer" not in ev or not isinstance(ev["pointer"], dict):
                            ev["pointer"] = {"file": file_path, "chunk_index": 0, "chunk_char_start": 0, "chunk_char_end": min(len(norm), MAX_CHARS_PER_CHUNK)}
                res["_source_path"] = file_path
                return res
            raise ValueError("merge response not valid JSON object")
        except Exception as e:
            if attempt + 1 >= RETRY_MAX:
                print(f"[warn] merge failed ({os.path.basename(file_path)}): {e}")
                return None
            backoff_sleep(attempt)

# ----------------- Fichiers & état -----------------
def list_candidate_files(root: str, include_pattern: Optional[str], exclude_pattern: Optional[str]) -> List[str]:
    paths = []
    for dirpath, _, filenames in os.walk(root):
        if any(part in dirpath for part in IGNORE_DIR_PARTS): continue
        for fn in filenames:
            if fn.startswith("_"): continue
            if not fn.lower().endswith(INCLUDE_EXTS): continue
            if include_pattern and not fnmatch.fnmatch(fn.lower(), include_pattern.lower()):
                continue
            if exclude_pattern and fnmatch.fnmatch(fn.lower(), exclude_pattern.lower()):
                continue
            fp = os.path.join(dirpath, fn)
            if os.path.abspath(fp).startswith(os.path.abspath(INDEX_DIR)): continue
            paths.append(fp)
    return sorted(paths)

def load_index() -> List[dict]:
    if os.path.isfile(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                return json.load(f) or []
        except Exception:
            return []
    return []

def save_index(items: List[dict]):
    os.makedirs(INDEX_DIR, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def load_state() -> dict:
    if os.path.isfile(STATE_JSON):
        try:
            with open(STATE_JSON, "r", encoding="utf-8") as f:
                return json.load(f) or {}
        except Exception:
            return {}
    return {}

def save_state(state: dict):
    os.makedirs(INDEX_DIR, exist_ok=True)
    with open(STATE_JSON, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def already_processed_set(index_items: List[dict]) -> set:
    s = set()
    for it in index_items:
        src = it.get("_source_path")
        if src: s.add(os.path.abspath(src))
    return s

# ----------------- Estimation -----------------
def approx_tokens_from_size(bytes_len: int) -> int:
    return int((bytes_len / 1024.0) * 200)  # ~200 tokens/Ko (observé)

def estimate_batch_cost(model: str, files: List[str]) -> Tuple[int, float]:
    tokens = sum(approx_tokens_from_size(os.path.getsize(f)) for f in files)
    pt = int(tokens * 0.6); ct = tokens - pt
    cost = estimate_cost(model, pt, ct)
    return tokens, cost

# ----------------- Exécution d’un lot -----------------
def run_batch(model: str, batch_files: List[str], dry_run: bool, max_tokens: Optional[int], max_cost: Optional[float]) -> Tuple[int,int,float,int]:
    if dry_run:
        tokens, cost = estimate_batch_cost(model, batch_files)
        print(f"[dry-run] {len(batch_files)} fichiers sélectionnés → tokens≈{tokens:,}  coût≈${cost:.4f} (model={model})")
        return 0, 0, 0.0, 0

    _load_costs()
    GLOBAL_USAGE["model_used"] = model

    index_items = load_index()
    processed_set = already_processed_set(index_items)
    complete_fn = make_openai_complete(model)

    processed_count = 0
    errors = 0
    for fp in batch_files:
        if STOP_REQUESTED:
            print("[stop] Interruption demandée (signal). Fin du lot en cours.")
            break

        abspath = os.path.abspath(fp)
        if abspath in processed_set:
            print(f"[skip] already indexed: {fp}")
            continue

        if max_cost is not None and GLOBAL_USAGE["grand"]["cost_usd"] >= max_cost:
            print(f"[stop] max-cost atteint (${GLOBAL_USAGE['grand']['cost_usd']:.4f} ≥ ${max_cost:.4f})")
            break
        if max_tokens is not None and GLOBAL_USAGE["grand"]["total_tokens"] >= max_tokens:
            print(f"[stop] max-tokens atteint ({GLOBAL_USAGE['grand']['total_tokens']:,} ≥ {max_tokens:,})")
            break

        print(f"[run] {os.path.basename(fp)}")
        res = analyze_chat(fp, model, complete_fn)
        if res:
            index_items.append(res)
            save_index(index_items)
            processed_set.add(abspath)
            processed_count += 1
            _write_costs()
        else:
            errors += 1
            _write_costs()

    return processed_count, GLOBAL_USAGE["grand"]["total_tokens"], GLOBAL_USAGE["grand"]["cost_usd"], errors

# ----------------- Orchestration + BOUCLE -----------------
def main():
    parser = argparse.ArgumentParser(description="Analyse par lots des chats (JSON) avec OpenAI.")
    parser.add_argument("--root", default=ROOT_DIR, help="Répertoire racine à scanner (défaut: %(default)s)")
    parser.add_argument("--batch-size", type=int, default=10, help="Nombre de fichiers à traiter par lot (défaut: %(default)s)")
    parser.add_argument("--start", type=int, default=0, help="Index de départ (0-based) si pas de --resume (défaut: %(default)s)")
    parser.add_argument("--resume", action="store_true", help="Reprendre après le dernier fichier traité (via state.json)")
    parser.add_argument("--include", default=None, help="Pattern d'inclusion (ex: 'chatgpt*')")
    parser.add_argument("--exclude", default=None, help="Pattern d'exclusion (ex: '*_old.json')")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Modèle OpenAI (défaut: {DEFAULT_MODEL})")
    parser.add_argument("--dry-run", action="store_true", help="Ne pas appeler l'IA, juste lister et estimer le coût")
    parser.add_argument("--max-tokens", type=int, default=None, help="Plafond de tokens cumulés (stop global)")
    parser.add_argument("--max-cost", type=float, default=None, help="Plafond de coût cumulé USD (stop global)")

    # options de boucle
    parser.add_argument("--loop", action="store_true", help="Enchaîner les lots jusqu'à épuisement (ou plafond/durée atteints)")
    parser.add_argument("--loop-sleep", type=int, default=0, help="Pause (en minutes) entre lots (défaut: 0)")
    parser.add_argument("--max-batches", type=int, default=None, help="Nombre max de lots à enchaîner (défaut: illimité)")
    parser.add_argument("--max-minutes", type=int, default=None, help="Durée max totale (minutes) avant arrêt (défaut: illimité)")
    args = parser.parse_args()

    load_openai_key()

    files_all = list_candidate_files(args.root, args.include, args.exclude)
    print(f"[plan] {len(files_all)} fichiers candidats")

    state = load_state()
    processed_list = state.get("processed_files", [])
    processed_set = set(processed_list)

    # point de départ
    start_idx = state.get("next_start", 0) if args.resume else args.start
    if start_idx < 0: start_idx = 0

    # filtre sur déjà traités
    files_ordered = [f for f in files_all if os.path.abspath(f) not in processed_set]

    if not files_ordered:
        print("[done] Rien à traiter (tout est déjà indexé).")
        return

    # BOUCLE
    lots_done = 0
    t0 = time.time()

    while True:
        if STOP_REQUESTED:
            print("[stop] Interruption demandée (signal).")
            break

        # Durée max
        if args.max_minutes is not None and (time.time() - t0) >= args.max_minutes * 60:
            print(f"[stop] Durée max atteinte ({args.max_minutes} min).")
            break

        # Remise à jour de la liste restante (au cas où)
        files_ordered = [f for f in files_all if os.path.abspath(f) not in processed_set]
        if start_idx >= len(files_ordered):
            if not args.loop:
                print(f"[done] start={start_idx} ≥ {len(files_ordered)} (rien à traiter).")
                break
            # Si loop et plus rien à faire
            if not files_ordered:
                print("[done] Tous les fichiers ont été traités.")
                break
            # sinon, repartir de 0 sur le flux restant (devrait être vide)
            start_idx = 0

        end_idx = min(start_idx + args.batch_size, len(files_ordered))
        batch_files = files_ordered[start_idx:end_idx]

        est_tokens, est_cost = estimate_batch_cost(args.model, batch_files)
        print(f"[batch] start={start_idx} size={len(batch_files)} / remaining={len(files_ordered)}  est_tokens≈{est_tokens:,}  est_cost≈${est_cost:.4f} (model={args.model})")

        processed_count, used_tokens, used_cost, errors = run_batch(args.model, batch_files, args.dry_run, args.max_tokens, args.max_cost)

        # maj état si exécution réelle
        if not args.dry_run:
            for f in batch_files:
                abspath = os.path.abspath(f)
                if abspath not in processed_set:
                    processed_list.append(abspath)
                    processed_set.add(abspath)
            state["processed_files"] = processed_list
            state["next_start"] = end_idx
            state["last_run"] = now_str()
            save_state(state)

        print(f"[summary] lot#{lots_done+1} processed={processed_count} errors={errors} next_start={end_idx}  usage_total_tokens={GLOBAL_USAGE['grand']['total_tokens']:,} cost≈${GLOBAL_USAGE['grand']['cost_usd']:.4f}")

        lots_done += 1

        # Conditions d'arrêt de la boucle
        if args.dry_run:
            print("[done] Dry-run terminé (un seul lot en mode dry-run).")
            break
        if (args.max_batches is not None) and (lots_done >= args.max_batches):
            print(f"[stop] Nombre max de lots atteint ({args.max_batches}).")
            break
        if STOP_REQUESTED:
            print("[stop] Interruption demandée.")
            break

        # Plus rien à traiter ?
        files_ordered = [f for f in files_all if os.path.abspath(f) not in processed_set]
        if not files_ordered:
            print("[done] Tous les fichiers ont été traités.")
            break

        # Avancer pour le prochain lot
        start_idx = end_idx

        # Pause entre lots
        if args.loop:
            if args.loop_sleep and args.loop_sleep > 0:
                print(f"[sleep] Pause de {args.loop_sleep} minute(s) avant le lot suivant…")
                for _ in range(args.loop_sleep * 60):
                    if STOP_REQUESTED: break
                    time.sleep(1)
            # et boucle continue
            continue
        else:
            # pas de --loop ⇒ un seul lot
            break

if __name__ == "__main__":
    main()
