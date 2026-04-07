"""
gev_compile — compilateur GEV → dict catalog.
Lit un fichier .gev ou une string GEV et produit les entrées JSON correspondantes.
Source de vérité : GEV_LANG_v1.md

Produit :
  catalog_object_list  — archetypes (Object:X:Y:)
  catalog_schema_list  — schemas (Schema:XSchema:)
  catalog_rule_list    — règles (RuleName IN X:RuleList  |  $RuleName IN X)
  catalog_method_list  — méthodes (Method IN X:MethodList  |  Object:X>Method)
"""

import re
from pathlib import Path


# ─── Entrée publique ──────────────────────────────────────────────────────────

def gev_compile(source):
    """
    source : str (contenu GEV) ou Path (fichier .gev).
    Retourne un dict avec les listes catalog produites.
    """
    if isinstance(source, Path):
        source = source.read_text(encoding="utf-8")

    lines  = _strip_comments(source)
    blocks = _split_blocks(lines)

    result = {
        "catalog_object_list": {},
        "catalog_schema_list": {},
        "catalog_rule_list":   {},
        "catalog_method_list": {},
    }

    for block in blocks:
        kind, parsed = _parse_block(block)
        if parsed is None:
            continue
        if kind == "object":
            result["catalog_object_list"][parsed["object_ident"]] = parsed
        elif kind == "schema":
            result["catalog_schema_list"][parsed["schema_ident"]] = parsed
        elif kind == "rule":
            result["catalog_rule_list"][parsed["rule_ident"]] = parsed
        elif kind == "method":
            result["catalog_method_list"][parsed["method_ident"]] = parsed
        elif kind == "method_shorthand":
            result["catalog_method_list"][parsed["method_ident"]] = parsed

    # Supprimer les listes vides
    return {k: v for k, v in result.items() if v}


def gev_compile_file(path):
    """Compile un fichier .gev et retourne le dict catalog."""
    return gev_compile(Path(path))


# ─── Parsing interne ──────────────────────────────────────────────────────────

def _strip_comments(source):
    """Supprime les commentaires GEV (// ligne, /* */ bloc) et les lignes vides."""
    # Supprimer les blocs /* ... */ (multi-lignes)
    source = re.sub(r'/\*.*?\*/', '', source, flags=re.DOTALL)
    out = []
    for line in source.splitlines():
        stripped = line.rstrip()
        # Commentaire ligne : commence par // (après espaces optionnels)
        if re.match(r'^\s*//', stripped):
            continue
        out.append(stripped)
    return out


def _split_blocks(lines):
    """
    Découpe les lignes en blocs logiques.
    Un bloc commence par une ligne non-indentée (déclaration de haut niveau).
    """
    blocks = []
    current = []

    for line in lines:
        if not line:
            if current:
                # Ligne vide = fin de bloc potentielle, on garde dans current
                current.append(line)
            continue

        is_indented = line.startswith("  ") or line.startswith("\t")
        if not is_indented and current:
            # Nouvelle déclaration de haut niveau → fermer le bloc courant
            blocks.append(current)
            current = [line]
        elif not is_indented:
            current = [line]
        else:
            current.append(line)

    if current:
        blocks.append(current)

    return [b for b in blocks if any(l.strip() for l in b)]


def _parse_block(lines):
    """
    Analyse un bloc et retourne (kind, dict) ou (None, None).
    """
    header = next((l for l in lines if l.strip()), "")
    attrs  = [l for l in lines[1:] if l.strip()]

    h = header.strip()

    # Object:X:Y:
    m = re.match(r'^(Object(?::[A-Za-z][A-Za-z0-9_]*)+):$', h)
    if m:
        return "object", _parse_object(m.group(1), attrs)

    # Schema:XSchema:
    m = re.match(r'^Schema:([A-Za-z][A-Za-z0-9_]*):$', h)
    if m:
        return "schema", _parse_schema(m.group(1), attrs)

    # RuleName IN Object:X:Y:RuleList  (forme complète)
    m = re.match(r'^([A-Za-z][A-Za-z0-9_]*)\s+IN\s+(Object(?::[A-Za-z][A-Za-z0-9_]*)+):RuleList$', h)
    if m:
        return "rule", _parse_rule(m.group(1), m.group(2), attrs)

    # $RuleName IN Object:X:Y  (forme courte)
    m = re.match(r'^\$([A-Za-z][A-Za-z0-9_]*)\s+IN\s+(Object(?::[A-Za-z][A-Za-z0-9_]*)*)$', h)
    if m:
        return "rule", _parse_rule(m.group(1), m.group(2), attrs)

    # MethodName IN Object:X:Y:MethodList  (forme complète)
    m = re.match(r'^([A-Za-z][A-Za-z0-9_]*)\s+IN\s+(Object(?::[A-Za-z][A-Za-z0-9_]*)+):MethodList$', h)
    if m:
        return "method", _parse_method(m.group(1), m.group(2), attrs)

    # Object:X:Y>MethodName  (forme courte avec >)
    m = re.match(r'^(Object(?::[A-Za-z][A-Za-z0-9_]*)*)>([A-Za-z][A-Za-z0-9_]*)$', h)
    if m:
        return "method_shorthand", _parse_method(m.group(2), m.group(1), attrs)

    return None, None


def _parse_object(lineage, attr_lines):
    """Compile une déclaration Object:X:Y: → entrée catalog_object_list."""
    ident = lineage.split(":")[-1]
    obj = {
        "object_ident":      ident,
        "object_lineage":    lineage,
        "object_schema":     "ObjectSchema",
        "object_version":    "1.0",
        "object_description": None,
        "object_how":        None,
        "object_status":     None,
        "object_lifecycle":  None,
        "object_automated":  False,
    }

    element_list = {}

    for line in attr_lines:
        s = line.strip()

        # Attribut déclaré inline : attr IN Object:X:AttributeList
        # Forme optionnelle : attr? IN Object:X:AttributeList  (? = required false)
        m = re.match(r'^(\w+)(\?)\s+IN\s+.+:AttributeList$', s)
        if m:
            element_list[m.group(1)] = {"field_type": "string", "field_required": False, "field_default": None}
            continue
        m = re.match(r'^(\w+)\s+IN\s+.+:AttributeList$', s)
        if m:
            element_list[m.group(1)] = {"field_type": "string", "field_required": True, "field_default": None}
            continue

        # .key = value
        m = re.match(r'^\.(\w+)\s*=\s*(.+)$', s)
        if m:
            key, val = m.group(1), _parse_value(m.group(2))
            json_key = f"object_{key}"
            if json_key in obj:
                obj[json_key] = val
            continue

        # .type = ... (dans un bloc d'attribut imbriqué — on ignore les sous-blocs ici)
        # Sous-attributs d'un AttributeList member : traités par le bloc parent

    if element_list:
        obj["object_elementlist"] = {"object_base_list": element_list}

    return obj


def _parse_schema(schema_ident, attr_lines):
    """Compile une déclaration Schema:XSchema: → entrée catalog_schema_list."""
    schema = {
        "schema_ident":                 schema_ident,
        "object_schema":                "SchemaSchema",
        "schema_required_element_list": {},
        "schema_validation_rule_list":  {},
    }

    in_required = False
    for line in attr_lines:
        s = line.strip()
        if not s:
            continue

        if s == ".required:":
            in_required = True
            continue

        if s.startswith(".for"):
            continue  # métadonnée de documentation, pas dans JSON

        if in_required:
            # field_name   FORMULA(...)
            m = re.match(r'^(\w+)\s+(.+)$', s)
            if m:
                field, condition = m.group(1), m.group(2).strip()
                schema["schema_required_element_list"][field] = {
                    "rule_condition": condition
                }

    return schema


def _parse_rule(rule_ident, object_lineage, attr_lines):
    """Compile une déclaration de règle → entrée catalog_rule_list."""
    rule = {
        "rule_ident":          rule_ident,
        "rule_object":         object_lineage,
        "rule_type":           "validation",
        "rule_condition":      None,
        "rule_severity":       "error",
        "rule_message":        None,
        "rule_scope":          "*",
        "rule_justification":  None,
    }
    for line in attr_lines:
        m = re.match(r'^\s*\.(\w+)\s*=\s*(.+)$', line)
        if m:
            key, val = m.group(1), _parse_value(m.group(2))
            if f"rule_{key}" in rule:
                rule[f"rule_{key}"] = val
    return rule


def _parse_method(method_ident, object_lineage, attr_lines):
    """Compile une déclaration de méthode → entrée catalog_method_list."""
    method = {
        "method_ident":    method_ident,
        "method_object":   object_lineage,
        "method_type":     "secondary",
        "method_parent":   None,
        "method_input":    None,
        "method_output":   None,
        "method_scope":    "*",
        "method_source":   None,
    }
    for line in attr_lines:
        m = re.match(r'^\s*\.(\w+)\s*=\s*(.+)$', line)
        if m:
            key, val = m.group(1), _parse_value(m.group(2))
            if f"method_{key}" in method:
                method[f"method_{key}"] = val
    return method


def _parse_value(raw):
    """Parse une valeur GEV brute en type Python natif."""
    v = raw.strip().strip('"').strip("'")
    if raw.strip().lower() == "true":
        return True
    if raw.strip().lower() == "false":
        return False
    if raw.strip().lower() in ("null", "none"):
        return None
    try:
        return int(raw.strip())
    except ValueError:
        pass
    try:
        return float(raw.strip())
    except ValueError:
        pass
    return v
