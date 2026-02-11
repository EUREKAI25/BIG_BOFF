"""
EURKAI GEV Parser - Bootstrap
Fonctions atomiques pour parser la syntaxe GEV.

Syntaxe supportée:
  :Object:Path:           Déclaration schema (: initial)
  Object:Path:            Utilisation/référence (sans :)
  .attr = value           Attribut (indenté)
  .attr                   Attribut booléen true
  A IN B.list             Relation d'appartenance
  A depends_on B          Relation de dépendance
  @alias = <target>       Alias
  # commentaire           Ignoré
"""

from __future__ import annotations
import re
from typing import Dict, List, Any, Optional, Tuple


# =============================================================================
# FONCTIONS ATOMIQUES - PARSING
# =============================================================================

def is_comment(line: str) -> bool:
    """Ligne est un commentaire."""
    return line.strip().startswith("#")


def is_empty(line: str) -> bool:
    """Ligne est vide."""
    return not line.strip()


def is_object_declaration(line: str) -> bool:
    """Ligne déclare un objet (:Path: ou Path:)."""
    stripped = line.strip()
    if not stripped:
        return False
    # Doit finir par : et contenir au moins un segment
    if not stripped.endswith(":"):
        return False
    # Ne doit pas commencer par . (attribut)
    if stripped.startswith("."):
        return False
    # Ne doit pas contenir = (relation ou attribut)
    if "=" in stripped and not stripped.startswith(":"):
        return False
    # Ne doit pas contenir IN ou depends_on
    if " IN " in stripped or " depends_on " in stripped:
        return False
    return True


def is_attribute(line: str) -> bool:
    """Ligne est un attribut (.attr ou .attr = value)."""
    return line.strip().startswith(".")


def is_relation_in(line: str) -> bool:
    """Ligne est une relation IN."""
    return " IN " in line and not line.strip().startswith(".")


def is_relation_depends(line: str) -> bool:
    """Ligne est une relation depends_on."""
    return " depends_on " in line


def is_alias(line: str) -> bool:
    """Ligne est un alias (@alias = <target>)."""
    return line.strip().startswith("@")


# =============================================================================
# FONCTIONS ATOMIQUES - EXTRACTION
# =============================================================================

def extract_object_id(line: str) -> Tuple[str, bool]:
    """
    Extrait l'ID d'un objet et indique si c'est une déclaration schema.
    Retourne (id_normalisé, is_schema).
    """
    stripped = line.strip()
    is_schema = stripped.startswith(":")
    
    # Enlever : initial si présent
    if is_schema:
        stripped = stripped[1:]
    
    # Normaliser : s'assurer que ça finit par :
    if not stripped.endswith(":"):
        stripped = stripped + ":"
    
    return stripped, is_schema


def extract_attribute(line: str) -> Tuple[str, Any]:
    """
    Extrait un attribut.
    Retourne (key, value).
    """
    stripped = line.strip()
    
    # Enlever le . initial
    if stripped.startswith("."):
        stripped = stripped[1:]
    
    if "=" in stripped:
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        
        # Enlever quotes si présentes
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        # Convertir booléens
        elif value.lower() == "true":
            value = True
        elif value.lower() == "false":
            value = False
        # Convertir nombres
        elif value.isdigit():
            value = int(value)
        
        return key, value
    else:
        # Attribut booléen
        return stripped.strip(), True


def extract_relation_in(line: str) -> Tuple[str, str, str]:
    """
    Extrait une relation IN.
    Retourne (source, target_object, target_list).
    Ex: "AttributeList IN ElementList" -> ("AttributeList", "", "ElementList")
    Ex: "name IN Object.attributeList" -> ("name", "Object", "attributeList")
    """
    parts = line.strip().split(" IN ")
    source = parts[0].strip()
    target = parts[1].strip()
    
    if "." in target:
        target_obj, target_list = target.rsplit(".", 1)
        return source, target_obj, target_list
    else:
        return source, "", target


def extract_relation_depends(line: str) -> Tuple[str, str]:
    """
    Extrait une relation depends_on.
    Retourne (source, target).
    """
    parts = line.strip().split(" depends_on ")
    return parts[0].strip(), parts[1].strip()


def extract_alias(line: str) -> Tuple[str, str]:
    """
    Extrait un alias.
    Retourne (alias_name, target).
    """
    stripped = line.strip()
    # @alias = <target> ou @alias = target
    match = re.match(r"@(\w+)\s*=\s*<?([^>]+)>?", stripped)
    if match:
        return match.group(1), match.group(2)
    return "", ""


def extract_name_from_lineage(object_id: str) -> str:
    """
    Extrait le name implicite depuis le lineage.
    Ex: "Object:List:AttributeList:" -> "AttributeList"
    """
    parts = [p for p in object_id.split(":") if p]
    return parts[-1] if parts else ""


def extract_parent_id(object_id: str) -> Optional[str]:
    """
    Extrait l'ID du parent depuis le lineage.
    Ex: "Object:List:AttributeList:" -> "Object:List:"
    """
    parts = [p for p in object_id.split(":") if p]
    if len(parts) <= 1:
        return None
    return ":".join(parts[:-1]) + ":"


# =============================================================================
# FONCTION PRINCIPALE - PARSE FICHIER
# =============================================================================

def parse_gev_file(text: str) -> Dict[str, Any]:
    """
    Parse un fichier GEV complet.
    Retourne {
        "objects": {id: {id, name, is_schema, attrs, parent}},
        "relations": [{"type": "IN"|"depends_on", "source", "target", ...}],
        "aliases": {alias: target}
    }
    """
    objects: Dict[str, Dict[str, Any]] = {}
    relations: List[Dict[str, Any]] = []
    aliases: Dict[str, str] = {}
    
    current_object: Optional[str] = None
    
    for line in text.splitlines():
        # Ignorer commentaires et lignes vides
        if is_comment(line) or is_empty(line):
            continue
        
        # Déclaration d'objet
        if is_object_declaration(line):
            obj_id, is_schema = extract_object_id(line)
            current_object = obj_id
            
            if obj_id not in objects:
                objects[obj_id] = {
                    "id": obj_id,
                    "name": extract_name_from_lineage(obj_id),
                    "is_schema": is_schema,
                    "attrs": {},
                    "parent": extract_parent_id(obj_id)
                }
            else:
                # Mettre à jour is_schema si on le déclare
                if is_schema:
                    objects[obj_id]["is_schema"] = True
            continue
        
        # Attribut (doit être sous un objet)
        if is_attribute(line):
            if current_object:
                key, value = extract_attribute(line)
                objects[current_object]["attrs"][key] = value
            continue
        
        # Relation IN
        if is_relation_in(line):
            source, target_obj, target_list = extract_relation_in(line)
            relations.append({
                "type": "IN",
                "source": source,
                "target_object": target_obj,
                "target_list": target_list
            })
            current_object = None  # Reset contexte
            continue
        
        # Relation depends_on
        if is_relation_depends(line):
            source, target = extract_relation_depends(line)
            relations.append({
                "type": "depends_on",
                "source": source,
                "target": target
            })
            current_object = None
            continue
        
        # Alias
        if is_alias(line):
            alias_name, target = extract_alias(line)
            if alias_name:
                aliases[alias_name] = target
            continue
    
    return {
        "objects": objects,
        "relations": relations,
        "aliases": aliases
    }


# =============================================================================
# FONCTION - SERIALIZE TO GEV
# =============================================================================

def serialize_object_to_gev(obj: Dict[str, Any]) -> str:
    """Sérialise un objet en GEV."""
    lines = []
    
    # Déclaration
    prefix = ":" if obj.get("is_schema", True) else ""
    lines.append(f"{prefix}{obj['id']}")
    
    # Attributs
    for key, value in obj.get("attrs", {}).items():
        if isinstance(value, bool):
            if value:
                lines.append(f"  .{key}")
        elif isinstance(value, str):
            lines.append(f'  .{key} = "{value}"')
        else:
            lines.append(f"  .{key} = {value}")
    
    return "\n".join(lines)


def serialize_relation_to_gev(rel: Dict[str, Any]) -> str:
    """Sérialise une relation en GEV."""
    if rel["type"] == "IN":
        target = rel["target_list"]
        if rel.get("target_object"):
            target = f"{rel['target_object']}.{target}"
        return f"{rel['source']} IN {target}"
    elif rel["type"] == "depends_on":
        return f"{rel['source']} depends_on {rel['target']}"
    return ""


def serialize_alias_to_gev(alias: str, target: str) -> str:
    """Sérialise un alias en GEV."""
    return f"@{alias} = <{target}>"
