"""
placeholder_resolve — méthode universelle de résolution de placeholders.
Définie dans Placeholder, overridable par Format et ses descendants.
Délimiteur résolu depuis le catalog (default: double_brace = {{ }}).
Pattern supporté : {{field}} ou {{object.field}} (navigation par point).
"""

import re


def placeholder_resolve(what, catalog):
    """
    Résout les placeholders dans what.object_template (ou what lui-même si string).
    Contexte de résolution : what + catalog.
    Retourne what enrichi de placeholder_resolve_result.
    """
    storage  = catalog.get("_storage") or catalog.get("_storage_ref")
    template = what.get("object_template") or what.get("placeholder_template") or ""
    context  = what.get("placeholder_context") or what

    delimiter_ident = what.get("placeholder_delimiter") or "double_brace"
    delimiter = storage.get("delimiter", delimiter_ident) if storage else None

    open_d  = delimiter.get("delimiter_open",  "{{") if delimiter else "{{"
    close_d = delimiter.get("delimiter_close", "}}") if delimiter else "}}"

    resolved = _resolve(template, context, open_d, close_d)

    return {
        "success":                    True,
        "placeholder_resolve_result": resolved,
        "delimiter_used":             delimiter_ident,
        "what":                       what,
    }


def resolve_template(template, context, catalog=None, delimiter_ident="double_brace"):
    """
    Fonction utilitaire directe — résout un template string depuis un context dict.
    Utilisable sans passer par la MRG.
    """
    open_d  = "{{"
    close_d = "}}"

    if catalog:
        storage   = catalog.get("_storage") or catalog.get("_storage_ref")
        delimiter = storage.get("delimiter", delimiter_ident) if storage else None
        if delimiter:
            open_d  = delimiter.get("delimiter_open",  "{{")
            close_d = delimiter.get("delimiter_close", "}}")

    return _resolve(template, context, open_d, close_d)


def _resolve(template, context, open_d, close_d):
    """
    Résolution interne — remplace chaque {{key}} par sa valeur dans context.
    Navigation par point supportée : {{object.field.subfield}}.
    Si la clé n'est pas résolue, le placeholder est laissé tel quel.
    """
    open_re  = re.escape(open_d)
    close_re = re.escape(close_d)
    pattern  = f"{open_re}([^{re.escape(close_d[0])}]+){close_re}"

    def resolve_match(match):
        key   = match.group(1).strip()
        value = _navigate(context, key.split("."))
        if value is None:
            return match.group(0)   # non résolu — laisser tel quel
        return str(value)

    return re.sub(pattern, resolve_match, template)


def _navigate(obj, parts):
    """Navigation récursive dans un dict selon une liste de clés."""
    if not parts or obj is None:
        return obj
    head, *tail = parts
    if isinstance(obj, dict):
        return _navigate(obj.get(head), tail)
    return None
