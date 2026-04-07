"""
AI_INQUIRY_MODULE — Module EURKAI agnostique
Interroge plusieurs IA, extrait les citations, détecte la présence du prospect.

Contrat de sortie uniforme:
  { "success": bool, "result": {...}, "message": str, "error": null|{...} }

4 étapes internes:
  1) prompt_generate  → inquiry_dict
  2) ask_ia           → answers
  3) extract_citations → citations
  4) presence_check   → prospect_present + competitors
"""
import logging
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

# Accès unifié aux modèles IA via MODEL_EXECUTOR
_MODULES_DIR = Path(__file__).parent.parent
if str(_MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULES_DIR))
from MODEL_EXECUTOR import model_execute

log = logging.getLogger(__name__)
TEMP = 0.1  # ≤ 0.2 imposé (cohérence avec PRESENCE_IA)


# ── Normalisation ──────────────────────────────────────────────────────────────

_LEGAL = re.compile(
    r"\b(sarl|sas|eurl|srl|snc|sa|spa|ltd|llc|gmbh|cie|group[e]?|et fils)\b", re.I
)
_LEGAL_SUFFIXES = re.compile(
    r"\b(sarl|sas|eurl|snc|sa|spa|ltd|llc|gmbh|cie|groupe?|et fils|and co)\b", re.I
)
_ORG_RE = re.compile(
    r"\b(?:[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝ]"
    r"[a-zàáâãäåæçèéêëìíîïðñòóôõöøùúûüý]{2,}"
    r"(?:[-\s][A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝ]"
    r"[a-zàáâãäåæçèéêëìíîïðñòóôõöøùúûüý]{2,}){1,4})\b"
)
_ORG_CAPS_RE = re.compile(
    r"\b(?:[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝ]{3,}"
    r"(?:['\s\-][A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝ]{3,}){0,4})\b"
)

_STOPWORDS: set = {
    # Villes / géographie
    "bordeaux", "paris", "lyon", "marseille", "toulouse", "nantes", "rennes",
    "strasbourg", "lille", "nice", "montpellier", "grenoble", "tours",
    "brest", "quimper", "lorient", "vannes", "saint", "bretagne",
    "rouen", "caen", "dijon", "reims", "metz", "nancy", "amiens",
    "clermont", "ferrand", "limoges", "poitiers", "angers", "le mans",
    "france", "europe", "normandie", "alsace",
    # Plateformes / générique
    "google", "maps", "googlemaps", "pagesjaunes", "pages", "jaunes", "yelp",
    "tripadvisor", "leboncoin", "facebook", "instagram", "twitter", "linkedin",
    "youtube", "whatsapp",
    # Verbes / interjections fréquents dans les réponses IA
    "voici", "voila", "demandez", "recommandations", "recommandez",
    "attention", "important", "note", "remarque", "conseil", "conseils",
    "informations", "information", "contact", "contactez", "appelez",
    "trouver", "recherchez", "consultez", "ressources", "services",
    "avis", "devis", "urgent", "disponible", "disponibles",
    # Réponses IA génériques
    "content", "context", "listmodels", "models", "response", "error",
    "call", "api", "query", "result", "results", "output",
    # Termes ultra-génériques
    "artisan", "artisans", "entreprise", "entreprises",
    "societe", "societes", "professionnel", "professionnels",
}


def _no_accent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm(name: str) -> str:
    if not name:
        return ""
    s = _LEGAL.sub(" ", name.lower())
    s = _no_accent(s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return " ".join(s.split())


def domain(url: str) -> str:
    if not url or not url.startswith(("http://", "https://")):
        return ""
    u = re.sub(r"^https?://(?:www\.)?", "", url.lower()).split("/")[0].split("?")[0]
    return u if "." in u else ""


def is_mentioned(text: str, name: str, website: Optional[str] = None, thr: float = 0.82) -> bool:
    nt, nn = norm(text), norm(name)
    if not nn:
        return False
    if nn in nt:
        return True
    words = [w for w in nn.split() if len(w) > 2]
    if words and all(w in nt for w in words):
        return True
    tw, nw = nt.split(), nn.split()
    for i in range(len(tw)):
        chunk = " ".join(tw[i : i + len(nw) + 3])
        if SequenceMatcher(None, nn, chunk).ratio() >= thr:
            return True
    if website:
        d = domain(website)
        nd = norm(d)
        if nd and len(nd) > 2 and nd in nt:
            return True
    return False


def _is_valid_org(name: str) -> bool:
    tokens = name.split()
    if len(tokens) < 2:
        return False
    if any(len(t) < 3 for t in tokens):
        return False
    norm_tokens = {_no_accent(t.lower()) for t in tokens}
    if norm_tokens & _STOPWORDS:
        return False
    if _no_accent(name.lower().strip()) in _STOPWORDS:
        return False
    return True


def extract_entities(text: str) -> list:
    out = []
    for url in re.findall(r"https?://[^\s,;)\"'>]+", text):
        d = domain(url)
        if d and len(d) > 3:
            out.append({"type": "url", "value": url, "domain": d})
    for m in _ORG_RE.finditer(text):
        candidate = m.group().strip()
        clean = _LEGAL_SUFFIXES.sub("", candidate).strip()
        if _is_valid_org(clean):
            out.append({"type": "company", "value": candidate})
    for m in _ORG_CAPS_RE.finditer(text):
        candidate = m.group().strip()
        candidate_title = candidate.replace("'", " ").replace("-", " ")
        clean = _LEGAL_SUFFIXES.sub("", candidate_title).strip()
        tokens = [t for t in clean.split() if t]
        if len(tokens) >= 2 and not ({_no_accent(t.lower()) for t in tokens} & _STOPWORDS):
            out.append({"type": "company", "value": candidate})
    seen: set = set()
    return [e for e in out if not (e["value"].lower() in seen or seen.add(e["value"].lower()))]


def competitors_from(entities: list, name: str, website: Optional[str] = None) -> list:
    nt, dt = norm(name), domain(website or "")
    result = []
    for e in entities:
        v = e["value"]
        if nt and nt in norm(v):
            continue
        if dt and dt in v.lower():
            continue
        if e["type"] == "url":
            d = e.get("domain", "")
            if d and d != dt:
                result.append(d)
        else:
            result.append(v)
    return result


# ── Adaptateurs IA ─────────────────────────────────────────────────────────────

def _openai(q: str) -> str:
    r = model_execute(
        "text2text", q,
        data={"max_tokens": 600, "temperature": TEMP, "model_override": "gpt-4o-mini"},
        provider="openai",
    )
    return r["result"] or ""


def _anthropic(q: str) -> str:
    r = model_execute(
        "text2text", q,
        data={"max_tokens": 600, "temperature": TEMP, "model_override": "claude-haiku-4-5-20251001"},
        provider="anthropic",
    )
    return r["result"] or ""


def _gemini(q: str) -> str:
    r = model_execute(
        "text2text", q,
        data={"max_tokens": 600, "temperature": TEMP, "model_override": "gemini-2.0-flash"},
        provider="gemini",
    )
    return r["result"] or ""


_CALLERS = {
    "openai":    (_openai,    "OPENAI_API_KEY"),
    "anthropic": (_anthropic, "ANTHROPIC_API_KEY"),
    "gemini":    (_gemini,    "GEMINI_API_KEY"),
}


def active_models() -> list:
    return [m for m, (_, k) in _CALLERS.items() if os.getenv(k)]


# ── Étapes internes ────────────────────────────────────────────────────────────

def prompt_generate(question_prompt: str, payload: dict, poll_inquiry_datas: Optional[dict] = None) -> dict:
    """
    Étape 1 — Génère les questions à partir du template et des variantes.
    question_prompt peut contenir des {clés} remplacées par payload.
    poll_inquiry_datas: variantes supplémentaires {key: override_value}.
    Returns: {"questions": [str, ...], "payload": dict}
    """
    try:
        base = question_prompt.format(**payload)
    except KeyError as e:
        base = question_prompt  # clé manquante → question brute
        log.warning("Clé manquante dans question_prompt: %s", e)

    questions = [base]
    if poll_inquiry_datas:
        for key, val in poll_inquiry_datas.items():
            merged = {**payload, key: val}
            try:
                questions.append(question_prompt.format(**merged))
            except KeyError:
                pass

    return {"questions": questions, "payload": payload}


def ask_ia(inquiry_dict: dict, output_format: str = "json", dry_run: bool = False) -> list:
    """
    Étape 2 — Interroge les modèles IA actifs.
    Returns: [{"model": str, "question": str, "answer": str, "ts": str}, ...]
    """
    models = active_models() if not dry_run else list(_CALLERS)
    questions = inquiry_dict.get("questions", [])
    answers = []

    for model in models:
        caller, _ = _CALLERS[model]
        for q in questions:
            ts = datetime.now(timezone.utc).isoformat()
            if dry_run:
                ans = f"[DRY_RUN:{model}] {q[:80]}"
            else:
                try:
                    ans = caller(q)
                except Exception as e:
                    ans = f"[ERROR:{type(e).__name__}:{e}]"
                    log.warning("Erreur %s sur modèle %s: %s", type(e).__name__, model, e)
            answers.append({"model": model, "question": q, "answer": ans, "ts": ts})

    return answers


def extract_citations(answers: list) -> list:
    """
    Étape 3 — Extrait et déduplique les entités de toutes les réponses.
    Returns: [{"type": str, "value": str, "from_model": str, ...}, ...]
    """
    all_entities = []
    for a in answers:
        for e in extract_entities(a.get("answer", "")):
            e["from_model"] = a.get("model", "unknown")
            all_entities.append(e)

    seen: set = set()
    return [e for e in all_entities if not (e["value"].lower() in seen or seen.add(e["value"].lower()))]


def presence_check(
    prospect_name: str,
    answers: list,
    citations: list,
    prospect_website: Optional[str] = None,
) -> tuple:
    """
    Étape 4 — Vérifie la présence du prospect dans les réponses brutes + concurrents.
    Returns: (prospect_present: bool, competitors: list[str])
    """
    prospect_present = False
    if prospect_name:
        # Vérifie dans les réponses brutes (plus fiable que dans les citations extraites)
        for a in answers:
            if is_mentioned(a.get("answer", ""), prospect_name, prospect_website):
                prospect_present = True
                break

    competitors = competitors_from(citations, prospect_name or "", prospect_website)
    return prospect_present, competitors


# ── Point d'entrée principal ───────────────────────────────────────────────────

def run(
    payload: dict,
    question_prompt: str,
    poll_inquiry_datas: Optional[dict] = None,
    output_format: str = "json",
    dry_run: bool = False,
) -> dict:
    """
    Fonction principale du module AI_INQUIRY_MODULE.

    Args:
        payload: dict — ex: {"profession": "couvreur", "city": "Rennes", "prospect_name": "Toit Breton"}
        question_prompt: str — template avec {clés} de payload
                         ex: "Quels sont les meilleurs {profession}s à {city} ?"
        poll_inquiry_datas: dict optionnel — variantes à tester en plus
                            ex: {"city": "Brest"} pour tester une autre ville
        output_format: "json" (seul format supporté pour l'instant)
        dry_run: bool — si True, pas d'appel IA réel (réponses simulées)

    Returns:
        Contrat uniforme EURKAI:
        {
          "success": bool,
          "result": {
            "inquiry_dict": {...},
            "answers": [...],
            "citations": [...],
            "prospect_present": bool,
            "competitors": [...],
            "meta": {"models": [...], "ts": [...], "dry_run": bool}
          },
          "message": str,
          "error": null | {"code": str, "detail": str}
        }
    """
    ts_start = datetime.now(timezone.utc).isoformat()
    try:
        prospect_name = payload.get("prospect_name", "")
        prospect_website = payload.get("website") or payload.get("prospect_website")
        models_used = active_models() if not dry_run else list(_CALLERS)

        # Étape 1 — Génération des questions
        inquiry_dict = prompt_generate(question_prompt, payload, poll_inquiry_datas)

        # Étape 2 — Appels IA
        answers = ask_ia(inquiry_dict, output_format, dry_run=dry_run)

        # Étape 3 — Extraction des citations
        citations = extract_citations(answers)

        # Étape 4 — Présence prospect + concurrents
        prospect_present, competitors = presence_check(
            prospect_name, answers, citations, prospect_website
        )

        ts_end = datetime.now(timezone.utc).isoformat()

        return {
            "success": True,
            "result": {
                "inquiry_dict": inquiry_dict,
                "answers": answers,
                "citations": citations,
                "prospect_present": prospect_present,
                "competitors": competitors,
                "meta": {
                    "models": models_used,
                    "ts": [ts_start, ts_end],
                    "dry_run": dry_run,
                },
            },
            "message": (
                f"{len(answers)} réponse(s) collectée(s), "
                f"{len(citations)} citation(s) extraite(s)"
                + (" — prospect détecté" if prospect_present else "")
                + (" [DRY_RUN]" if dry_run else "")
            ),
            "error": None,
        }

    except Exception as e:
        log.exception("AI_INQUIRY_MODULE erreur inattendue")
        return {
            "success": False,
            "result": None,
            "message": "Erreur inattendue dans AI_INQUIRY_MODULE",
            "error": {"code": "INTERNAL_ERROR", "detail": str(e)},
        }
