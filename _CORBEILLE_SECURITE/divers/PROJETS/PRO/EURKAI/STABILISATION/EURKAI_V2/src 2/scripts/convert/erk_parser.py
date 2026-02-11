#!/usr/bin/env python3
"""
EURKAI - ERK Parser
====================
Parse les fichiers .gev (syntaxe ERK) et retourne une structure Python.

C'est le parser central utilisé par tous les converters erk_to_*.

Usage:
    from erk_parser import parse_gev, parse_gev_file
    
    objects = parse_gev_file("methods.s.gev")
    for obj in objects:
        print(obj['lineage'], obj['attributes'])
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path


@dataclass
class ERKObject:
    """Objet ERK parsé"""
    lineage: str
    type_chain: List[str]  # ["Object", "Method", "JSScript", "myFunc"]
    name: str              # Dernier élément du lineage
    attributes: Dict[str, Any] = field(default_factory=dict)
    relations: List[Dict[str, str]] = field(default_factory=list)
    source_file: str = ""
    source_line: int = 0


class ERKParser:
    """Parse la syntaxe ERK/GEV"""
    
    # Patterns
    PATTERNS = {
        # Object:Type:SubType:Name:
        'lineage': re.compile(r'^([A-Z][a-zA-Z0-9]*(?::[A-Z]?[a-zA-Z0-9]*)*):$'),
        
        # .attribute = value
        'attribute': re.compile(r'^\s+\.(\w+)\s*=\s*(.+)$'),
        
        # A IN B.list
        'relation_in': re.compile(r'^(\S+)\s+IN\s+(\S+)\.(\w+)$'),
        
        # A inherits_from B
        'relation_named': re.compile(r'^(\S+)\s+(inherits_from|depends_on|related_to|element_of)\s+(\S+)$'),
        
        # Commentaires
        'comment': re.compile(r'^#.*$'),
        'empty': re.compile(r'^\s*$'),
    }
    
    def __init__(self, source: str, filename: str = ""):
        self.source = source
        self.filename = filename
        self.objects: List[ERKObject] = []
        self.current_object: Optional[ERKObject] = None
        
    def parse(self) -> List[ERKObject]:
        """Parse le fichier GEV complet"""
        lines = self.source.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            self._parse_line(line, line_num)
        
        # Finaliser le dernier objet
        if self.current_object:
            self.objects.append(self.current_object)
        
        return self.objects
    
    def _parse_line(self, line: str, line_num: int):
        """Parse une ligne"""
        # Skip commentaires et lignes vides
        if self.PATTERNS['comment'].match(line) or self.PATTERNS['empty'].match(line):
            return
        
        # Nouveau lineage (nouvel objet)
        match = self.PATTERNS['lineage'].match(line)
        if match:
            # Sauvegarder l'objet précédent
            if self.current_object:
                self.objects.append(self.current_object)
            
            lineage = match.group(1)
            type_chain = lineage.rstrip(':').split(':')
            name = type_chain[-1] if type_chain[-1] else type_chain[-2]
            
            self.current_object = ERKObject(
                lineage=lineage,
                type_chain=type_chain,
                name=name,
                source_file=self.filename,
                source_line=line_num
            )
            return
        
        # Attribut
        match = self.PATTERNS['attribute'].match(line)
        if match and self.current_object:
            attr_name = match.group(1)
            attr_value = self._parse_value(match.group(2))
            self.current_object.attributes[attr_name] = attr_value
            return
        
        # Relation IN
        match = self.PATTERNS['relation_in'].match(line)
        if match:
            self._add_relation({
                'subject': match.group(1),
                'type': 'element_of',
                'target': match.group(2),
                'list': match.group(3)
            })
            return
        
        # Relation nommée
        match = self.PATTERNS['relation_named'].match(line)
        if match:
            self._add_relation({
                'subject': match.group(1),
                'type': match.group(2),
                'target': match.group(3)
            })
            return
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse une valeur ERK"""
        value_str = value_str.strip()
        
        # String entre guillemets
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]
        if value_str.startswith("'") and value_str.endswith("'"):
            return value_str[1:-1]
        
        # Liste [a, b, c]
        if value_str.startswith('[') and value_str.endswith(']'):
            inner = value_str[1:-1]
            if not inner.strip():
                return []
            items = []
            for item in self._split_list(inner):
                items.append(self._parse_value(item.strip()))
            return items
        
        # Booléens
        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False
        
        # Nombres
        try:
            if '.' in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass
        
        # Référence ou identifiant
        return value_str
    
    def _split_list(self, inner: str) -> List[str]:
        """Split une liste en tenant compte des strings"""
        items = []
        current = ""
        in_string = False
        string_char = None
        depth = 0
        
        for char in inner:
            if char in ('"', "'") and not in_string:
                in_string = True
                string_char = char
                current += char
            elif char == string_char and in_string:
                in_string = False
                string_char = None
                current += char
            elif char == '[':
                depth += 1
                current += char
            elif char == ']':
                depth -= 1
                current += char
            elif char == ',' and not in_string and depth == 0:
                items.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            items.append(current.strip())
        
        return items
    
    def _add_relation(self, relation: Dict[str, str]):
        """Ajoute une relation à l'objet courant ou global"""
        if self.current_object:
            self.current_object.relations.append(relation)


def parse_gev(source: str, filename: str = "") -> List[ERKObject]:
    """Parse une string GEV"""
    parser = ERKParser(source, filename)
    return parser.parse()


def parse_gev_file(filepath: str) -> List[ERKObject]:
    """Parse un fichier GEV"""
    path = Path(filepath)
    source = path.read_text(encoding='utf-8')
    return parse_gev(source, str(path))


def objects_to_dict(objects: List[ERKObject]) -> Dict[str, Dict]:
    """Convertit la liste d'objets en dictionnaire indexé par lineage"""
    return {obj.lineage: {
        'lineage': obj.lineage,
        'type_chain': obj.type_chain,
        'name': obj.name,
        'attributes': obj.attributes,
        'relations': obj.relations,
        'source': {'file': obj.source_file, 'line': obj.source_line}
    } for obj in objects}


def filter_by_type(objects: List[ERKObject], type_name: str) -> List[ERKObject]:
    """Filtre les objets par type (présent dans type_chain)"""
    return [obj for obj in objects if type_name in obj.type_chain]


# =============================================================================
# CLI
# =============================================================================

def main():
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python erk_parser.py <file.gev> [--json]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    as_json = '--json' in sys.argv
    
    objects = parse_gev_file(filepath)
    
    if as_json:
        data = objects_to_dict(objects)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"📄 File: {filepath}")
        print(f"📦 Objects: {len(objects)}")
        print()
        
        # Grouper par type
        by_type = {}
        for obj in objects:
            t = obj.type_chain[1] if len(obj.type_chain) > 1 else 'Object'
            by_type.setdefault(t, []).append(obj)
        
        for type_name, objs in sorted(by_type.items()):
            print(f"  {type_name}: {len(objs)}")
            for obj in objs[:5]:  # Max 5 par type
                attrs = len(obj.attributes)
                print(f"    - {obj.name} ({attrs} attrs)")
            if len(objs) > 5:
                print(f"    ... et {len(objs) - 5} autres")


if __name__ == '__main__':
    main()
