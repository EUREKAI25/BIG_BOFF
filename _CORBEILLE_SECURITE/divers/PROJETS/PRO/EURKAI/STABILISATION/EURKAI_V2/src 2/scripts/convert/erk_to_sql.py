#!/usr/bin/env python3
"""
EURKAI - ERK to SQL Converter
===============================
Génère du SQL à partir d'objets ERK.

Usage:
    python erk_to_sql.py objects.s.gev -o schema.sql
    python erk_to_sql.py objects.s.gev --dialect postgres
    python erk_to_sql.py objects.s.gev --tables-only

Output:
    - CREATE TABLE statements
    - Indexes et contraintes
    - Stored procedures pour les Methods
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from erk_parser import parse_gev_file, ERKObject, filter_by_type


# =============================================================================
# TYPE MAPPING ERK → SQL
# =============================================================================

TYPE_MAP_POSTGRES = {
    'string': 'TEXT',
    'str': 'TEXT',
    'number': 'NUMERIC',
    'int': 'INTEGER',
    'float': 'DOUBLE PRECISION',
    'boolean': 'BOOLEAN',
    'bool': 'BOOLEAN',
    'array': 'JSONB',
    'list': 'JSONB',
    'object': 'JSONB',
    'dict': 'JSONB',
    'any': 'JSONB',
    'date': 'DATE',
    'datetime': 'TIMESTAMP WITH TIME ZONE',
    'timestamp': 'TIMESTAMP WITH TIME ZONE',
    'uuid': 'UUID',
}

TYPE_MAP_MYSQL = {
    'string': 'TEXT',
    'str': 'VARCHAR(255)',
    'number': 'DECIMAL(20,6)',
    'int': 'INT',
    'float': 'DOUBLE',
    'boolean': 'BOOLEAN',
    'bool': 'BOOLEAN',
    'array': 'JSON',
    'list': 'JSON',
    'object': 'JSON',
    'dict': 'JSON',
    'any': 'JSON',
    'date': 'DATE',
    'datetime': 'DATETIME',
    'timestamp': 'TIMESTAMP',
    'uuid': 'CHAR(36)',
}

TYPE_MAP_SQLITE = {
    'string': 'TEXT',
    'str': 'TEXT',
    'number': 'REAL',
    'int': 'INTEGER',
    'float': 'REAL',
    'boolean': 'INTEGER',
    'bool': 'INTEGER',
    'array': 'TEXT',  # JSON as text
    'list': 'TEXT',
    'object': 'TEXT',
    'dict': 'TEXT',
    'any': 'TEXT',
    'date': 'TEXT',
    'datetime': 'TEXT',
    'timestamp': 'TEXT',
    'uuid': 'TEXT',
}


def get_type_map(dialect: str) -> Dict[str, str]:
    """Retourne le mapping de types pour le dialecte"""
    maps = {
        'postgres': TYPE_MAP_POSTGRES,
        'postgresql': TYPE_MAP_POSTGRES,
        'mysql': TYPE_MAP_MYSQL,
        'mariadb': TYPE_MAP_MYSQL,
        'sqlite': TYPE_MAP_SQLITE,
    }
    return maps.get(dialect.lower(), TYPE_MAP_POSTGRES)


def to_snake_case(name: str) -> str:
    """Convertit en snake_case"""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# =============================================================================
# SQL GENERATOR
# =============================================================================

class SQLGenerator:
    """Génère du SQL à partir d'objets ERK"""
    
    def __init__(self, objects: List[ERKObject], options: Dict[str, Any] = None):
        self.objects = objects
        self.options = options or {}
        self.dialect = options.get('dialect', 'postgres')
        self.type_map = get_type_map(self.dialect)
        
    def generate(self) -> str:
        """Génère le SQL complet"""
        lines = []
        
        # Header
        lines.extend(self._generate_header())
        lines.append("")
        
        # Tables pour les objets Structure
        structures = [o for o in self.objects if 'Structure' in o.type_chain]
        if structures:
            lines.append("-- ===========================================")
            lines.append("-- TABLES (from Structure objects)")
            lines.append("-- ===========================================")
            lines.append("")
            for struct in structures:
                lines.extend(self._generate_table(struct))
                lines.append("")
        
        # Table générique pour tous les objets ERK
        if not self.options.get('tables_only'):
            lines.append("-- ===========================================")
            lines.append("-- ERK OBJECTS TABLE")
            lines.append("-- ===========================================")
            lines.append("")
            lines.extend(self._generate_erk_objects_table())
            lines.append("")
        
        # Stored procedures pour les Methods
        methods = filter_by_type(self.objects, 'Method')
        if methods and not self.options.get('tables_only'):
            lines.append("-- ===========================================")
            lines.append("-- STORED PROCEDURES (from Method objects)")
            lines.append("-- ===========================================")
            lines.append("")
            for method in methods[:10]:  # Limiter à 10
                lines.extend(self._generate_procedure(method))
                lines.append("")
        
        # Insert statements pour les objets
        if self.options.get('with_data'):
            lines.append("-- ===========================================")
            lines.append("-- DATA INSERTS")
            lines.append("-- ===========================================")
            lines.append("")
            for obj in self.objects:
                lines.extend(self._generate_insert(obj))
        
        return '\n'.join(lines)
    
    def _generate_header(self) -> List[str]:
        """Génère le header SQL"""
        source = self.objects[0].source_file if self.objects else "ERK"
        
        return [
            f"-- EURKAI - Generated SQL ({self.dialect})",
            f"-- Source: {source}",
            f"-- Generated: {datetime.now().isoformat()}",
            f"-- Objects: {len(self.objects)}",
            "--",
        ]
    
    def _generate_erk_objects_table(self) -> List[str]:
        """Génère la table générique pour objets ERK"""
        lines = []
        
        if self.dialect in ('postgres', 'postgresql'):
            lines.extend([
                "CREATE TABLE IF NOT EXISTS erk_objects (",
                "    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),",
                "    lineage TEXT NOT NULL,",
                "    name TEXT NOT NULL,",
                "    type_chain TEXT[] NOT NULL,",
                "    attributes JSONB DEFAULT '{}',",
                "    relations JSONB DEFAULT '[]',",
                "    source_file TEXT,",
                "    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),",
                "    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                ");",
                "",
                "CREATE INDEX IF NOT EXISTS idx_erk_objects_lineage ON erk_objects(lineage);",
                "CREATE INDEX IF NOT EXISTS idx_erk_objects_name ON erk_objects(name);",
                "CREATE INDEX IF NOT EXISTS idx_erk_objects_type ON erk_objects USING GIN(type_chain);",
            ])
        elif self.dialect in ('mysql', 'mariadb'):
            lines.extend([
                "CREATE TABLE IF NOT EXISTS erk_objects (",
                "    uuid CHAR(36) PRIMARY KEY,",
                "    lineage TEXT NOT NULL,",
                "    name VARCHAR(255) NOT NULL,",
                "    type_chain JSON NOT NULL,",
                "    attributes JSON DEFAULT NULL,",
                "    relations JSON DEFAULT NULL,",
                "    source_file TEXT,",
                "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,",
                "    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,",
                "    INDEX idx_name (name)",
                ");",
            ])
        else:  # SQLite
            lines.extend([
                "CREATE TABLE IF NOT EXISTS erk_objects (",
                "    uuid TEXT PRIMARY KEY,",
                "    lineage TEXT NOT NULL,",
                "    name TEXT NOT NULL,",
                "    type_chain TEXT NOT NULL,",
                "    attributes TEXT DEFAULT '{}',",
                "    relations TEXT DEFAULT '[]',",
                "    source_file TEXT,",
                "    created_at TEXT DEFAULT (datetime('now')),",
                "    updated_at TEXT DEFAULT (datetime('now'))",
                ");",
                "",
                "CREATE INDEX IF NOT EXISTS idx_erk_objects_lineage ON erk_objects(lineage);",
                "CREATE INDEX IF NOT EXISTS idx_erk_objects_name ON erk_objects(name);",
            ])
        
        return lines
    
    def _generate_table(self, struct: ERKObject) -> List[str]:
        """Génère une table à partir d'un objet Structure"""
        lines = []
        
        table_name = to_snake_case(struct.name)
        attrs = struct.attributes
        
        lines.append(f"-- Table: {struct.name}")
        if attrs.get('description'):
            lines.append(f"-- {attrs['description']}")
        
        lines.append(f"CREATE TABLE IF NOT EXISTS {table_name} (")
        
        columns = ["    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid()"]
        
        # Colonnes depuis les attributs
        for attr_name, attr_value in attrs.items():
            if attr_name.startswith('field_'):
                field_name = attr_name[6:]  # Remove 'field_' prefix
                field_type = self.type_map.get(str(attr_value), 'TEXT')
                columns.append(f"    {to_snake_case(field_name)} {field_type}")
        
        # Colonnes standard
        columns.append("    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()")
        columns.append("    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()")
        
        lines.append(',\n'.join(columns))
        lines.append(");")
        
        return lines
    
    def _generate_procedure(self, method: ERKObject) -> List[str]:
        """Génère une stored procedure à partir d'un Method"""
        lines = []
        attrs = method.attributes
        
        name = to_snake_case(method.name)
        description = attrs.get('description', '')
        params = attrs.get('params', [])
        central_method = attrs.get('centralMethod', 'Execute')
        
        lines.append(f"-- Procedure: {method.name}")
        lines.append(f"-- CentralMethod: {central_method}")
        
        if self.dialect in ('postgres', 'postgresql'):
            # Build params
            param_parts = []
            for param in (params if isinstance(params, list) else []):
                if isinstance(param, str):
                    param_name = f"p_{to_snake_case(param)}"
                    param_type = attrs.get(f'param_{param}_type', 'any')
                else:
                    param_name = f"p_{to_snake_case(param.get('name', 'arg'))}"
                    param_type = param.get('type', 'any')
                sql_type = self.type_map.get(param_type, 'JSONB')
                param_parts.append(f"{param_name} {sql_type}")
            
            params_str = ', '.join(param_parts) if param_parts else ''
            
            lines.append(f"CREATE OR REPLACE FUNCTION {name}({params_str})")
            lines.append("RETURNS JSONB AS $$")
            lines.append("BEGIN")
            lines.append(f"    -- {central_method} logic")
            lines.append("    RETURN '{}'::JSONB;")
            lines.append("END;")
            lines.append("$$ LANGUAGE plpgsql;")
        
        elif self.dialect in ('mysql', 'mariadb'):
            lines.append(f"DELIMITER //")
            lines.append(f"CREATE PROCEDURE IF NOT EXISTS {name}()")
            lines.append("BEGIN")
            lines.append(f"    -- {central_method} logic")
            lines.append("    SELECT '{}' AS result;")
            lines.append("END //")
            lines.append("DELIMITER ;")
        
        return lines
    
    def _generate_insert(self, obj: ERKObject) -> List[str]:
        """Génère un INSERT pour un objet"""
        import json
        
        lines = []
        
        if self.dialect in ('postgres', 'postgresql'):
            attrs_json = json.dumps(obj.attributes).replace("'", "''")
            relations_json = json.dumps(obj.relations).replace("'", "''")
            type_chain = "ARRAY[" + ",".join(f"'{t}'" for t in obj.type_chain) + "]"
            
            lines.append(f"INSERT INTO erk_objects (lineage, name, type_chain, attributes, relations, source_file)")
            lines.append(f"VALUES ('{obj.lineage}', '{obj.name}', {type_chain}, '{attrs_json}'::JSONB, '{relations_json}'::JSONB, '{obj.source_file}');")
        
        return lines


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='EURKAI - ERK to SQL Converter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python erk_to_sql.py objects.s.gev                    # PostgreSQL
  python erk_to_sql.py objects.s.gev -o schema.sql      # Save to file
  python erk_to_sql.py objects.s.gev --dialect mysql    # MySQL dialect
  python erk_to_sql.py objects.s.gev --tables-only      # Only tables
  python erk_to_sql.py objects.s.gev --with-data        # Include INSERTs
        """
    )
    
    parser.add_argument('file', help='ERK/GEV file to convert')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('--dialect', default='postgres', 
                       choices=['postgres', 'postgresql', 'mysql', 'mariadb', 'sqlite'],
                       help='SQL dialect')
    parser.add_argument('--tables-only', action='store_true',
                       help='Generate only table definitions')
    parser.add_argument('--with-data', action='store_true',
                       help='Include INSERT statements for objects')
    parser.add_argument('--filter', help='Filter by type')
    
    args = parser.parse_args()
    
    objects = parse_gev_file(args.file)
    
    if args.filter:
        allowed = [t.strip() for t in args.filter.split(',')]
        objects = [o for o in objects if any(t in o.type_chain for t in allowed)]
    
    options = {
        'dialect': args.dialect,
        'tables_only': args.tables_only,
        'with_data': args.with_data,
    }
    
    generator = SQLGenerator(objects, options)
    output = generator.generate()
    
    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"✅ Generated {args.output} ({len(objects)} objects)")
    else:
        print(output)


if __name__ == '__main__':
    main()
