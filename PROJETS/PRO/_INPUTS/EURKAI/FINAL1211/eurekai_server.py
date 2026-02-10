#!/usr/bin/env python3
"""
EUREKAI MRG API Server
Expose le Core MRG via une API REST pour le cockpit VSCode
"""

import json
import os
import re
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import argparse

# ============================================================================
# STORE
# ============================================================================

class ErkStore:
    def __init__(self):
        self.objects = {}  # lineage -> object
        self.vectors = {}  # V_xxx -> object
        self.rules = []
    
    def clear(self):
        self.objects.clear()
        self.vectors.clear()
        self.rules.clear()
    
    def get(self, lineage):
        return self.objects.get(lineage)
    
    def set(self, lineage, obj):
        self.objects[lineage] = obj
        
        # Index vectors
        if ':Vector:' in lineage or obj.get('name', '').startswith('V_'):
            name = obj.get('attributes', {}).get('name', '').strip('"') or obj.get('name', '')
            if name.startswith('V_'):
                self.vectors[name] = obj
        
        # Index rules
        if ':Rule:' in lineage or obj.get('name', '').startswith('R_'):
            self.rules.append(obj)
    
    def get_children(self, lineage):
        prefix = lineage + ':'
        children = []
        for l in self.objects:
            if l.startswith(prefix) and ':' not in l[len(prefix):]:
                children.append(l)
        return sorted(children)
    
    def stats(self):
        return {
            'objects': len(self.objects),
            'vectors': len(self.vectors),
            'rules': len(self.rules)
        }

# ============================================================================
# PARSER
# ============================================================================

class ErkParser:
    def __init__(self, store):
        self.store = store
    
    def parse_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse(content, str(filepath))
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
            return 0
    
    def parse(self, content, source='unknown'):
        lines = content.split('\n')
        current_object = None
        count = 0
        
        for i, line in enumerate(lines):
            trimmed = line.strip()
            
            # Skip empty and comments
            if not trimmed or trimmed.startswith('#') or trimmed.startswith('//'):
                continue
            
            # Lineage declaration
            lineage_match = re.match(r'^([A-Z][A-Za-z0-9_]*(?::[A-Z][A-Za-z0-9_]*)*):$', trimmed)
            if lineage_match:
                if current_object:
                    self.store.set(current_object['lineage'], current_object)
                    count += 1
                
                lineage = lineage_match.group(1)
                if not lineage.startswith('Object:') and lineage != 'Object':
                    lineage = 'Object:' + lineage
                
                segments = lineage.split(':')
                current_object = {
                    'lineage': lineage,
                    'name': segments[-1],
                    'parent': ':'.join(segments[:-1]),
                    'attributes': {},
                    'relations': [],
                    'source': source,
                    'line': i + 1
                }
                
                # Auto-create ancestors
                for j in range(1, len(segments)):
                    ancestor = ':'.join(segments[:j])
                    if ancestor not in self.store.objects:
                        self.store.set(ancestor, {
                            'lineage': ancestor,
                            'name': segments[j-1],
                            'parent': ':'.join(segments[:j-1]),
                            'attributes': {},
                            'relations': [],
                            'source': source,
                            'line': -1
                        })
                continue
            
            # Attribute
            attr_match = re.match(r'^\.([a-zA-Z_][a-zA-Z0-9_.]*)\s*=\s*(.+)$', trimmed)
            if attr_match and current_object:
                current_object['attributes'][attr_match.group(1)] = attr_match.group(2)
                continue
            
            # Relation
            rel_match = re.match(r'^([A-Z][A-Za-z0-9_]*)\s+(IN|depends_on|related_to)\s+(.+)$', trimmed)
            if rel_match and current_object:
                current_object['relations'].append({
                    'type': rel_match.group(2),
                    'target': rel_match.group(3).strip()
                })
        
        if current_object:
            self.store.set(current_object['lineage'], current_object)
            count += 1
        
        return count

# ============================================================================
# RESOLVER
# ============================================================================

class ErkResolver:
    def __init__(self, store):
        self.store = store
        self.cache = {}
        self.resolving = set()
    
    def resolve(self, value):
        if value is None:
            return None
        
        s = str(value)
        
        if s in self.cache:
            return self.cache[s]
        
        # Vector reference
        if s.startswith('V_'):
            result = self.resolve_vector(s)
            self.cache[s] = result
            return result
        
        # String with quotes
        if s.startswith('"') and s.endswith('"'):
            return s[1:-1]
        
        # Number
        if re.match(r'^-?\d+(\.\d+)?$', s):
            return float(s) if '.' in s else int(s)
        
        # Boolean
        if s == 'true':
            return True
        if s == 'false':
            return False
        
        # Array
        if s.startswith('[') and s.endswith(']'):
            try:
                return json.loads(s)
            except:
                return s
        
        return s
    
    def resolve_vector(self, name):
        if name in self.resolving:
            return None  # Circular reference
        
        vector = self.store.vectors.get(name)
        if not vector:
            return None
        
        self.resolving.add(name)
        value = vector.get('attributes', {}).get('default')
        
        if value and str(value).startswith('V_'):
            value = self.resolve_vector(value)
        else:
            value = self.resolve(value)
        
        self.resolving.discard(name)
        return value
    
    def resolve_object(self, lineage):
        obj = self.store.get(lineage)
        if not obj:
            return None
        
        resolved = {
            'lineage': obj['lineage'],
            'name': obj['name'],
            'parent': obj['parent'],
            'attributes': {},
            'source': obj.get('source'),
            'line': obj.get('line')
        }
        
        for key, value in obj.get('attributes', {}).items():
            resolved['attributes'][key] = self.resolve(value)
        
        return resolved
    
    def clear_cache(self):
        self.cache.clear()

# ============================================================================
# SUPERREAD
# ============================================================================

class SuperRead:
    def __init__(self, store, resolver):
        self.store = store
        self.resolver = resolver
    
    def execute(self, query):
        query = query.strip()
        
        # help
        if query == 'help':
            return self.help()
        
        # stats
        if query == 'stats':
            return self.stats()
        
        # vectors
        if query == 'vectors':
            return self.vectors()
        
        # rules
        if query == 'rules':
            return self.rules_cmd()
        
        # tree
        tree_match = re.match(r'^tree(?:\s+(\d+))?$', query)
        if tree_match:
            depth = int(tree_match.group(1) or 4)
            return self.tree(depth)
        
        # resolve
        resolve_match = re.match(r'^resolve\s+(V_\w+)$', query)
        if resolve_match:
            return self.resolve_cmd(resolve_match.group(1))
        
        # get
        get_match = re.match(r'^get\s+(.+)$', query)
        if get_match:
            return self.get(get_match.group(1))
        
        # read
        read_match = re.match(r'^read\s+(\w+)(?:\.(.+?))?(?:\s+--(.+))?$', query)
        if read_match:
            return self.read(read_match.group(1), read_match.group(2), read_match.group(3))
        
        return {'error': f"Unknown command: {query}. Type 'help' for available commands."}
    
    def help(self):
        return {
            'type': 'help',
            'commands': [
                {'cmd': 'read <Type>', 'desc': 'List all objects of type'},
                {'cmd': 'read <Type>.attr=value', 'desc': 'Filter by equality'},
                {'cmd': 'read <Type>.attr~value', 'desc': 'Filter by contains'},
                {'cmd': 'read <Type>.attr>value', 'desc': 'Filter by greater than'},
                {'cmd': 'read <Type>.attr<value', 'desc': 'Filter by less than'},
                {'cmd': 'get <lineage>', 'desc': 'Get object by lineage'},
                {'cmd': 'resolve <V_xxx>', 'desc': 'Resolve vector value'},
                {'cmd': 'tree [depth]', 'desc': 'Show object tree'},
                {'cmd': 'stats', 'desc': 'Show statistics'},
                {'cmd': 'vectors', 'desc': 'List all vectors'},
                {'cmd': 'rules', 'desc': 'List all rules'},
            ]
        }
    
    def stats(self):
        s = self.store.stats()
        return {
            'type': 'stats',
            **s,
            'message': f"Objects: {s['objects']}, Vectors: {s['vectors']}, Rules: {s['rules']}"
        }
    
    def vectors(self):
        vecs = []
        for name, obj in self.store.vectors.items():
            value = self.resolver.resolve_vector(name)
            vecs.append({
                'name': name,
                'value': value,
                'description': obj.get('attributes', {}).get('description', '').strip('"')
            })
        return {
            'type': 'vectors',
            'count': len(vecs),
            'vectors': vecs,
            'message': '\n'.join([f"  {v['name']} = {v['value']}" for v in vecs])
        }
    
    def rules_cmd(self):
        rls = []
        for r in self.store.rules:
            rls.append({
                'name': r['name'],
                'target': r.get('attributes', {}).get('target', ''),
                'condition': r.get('attributes', {}).get('condition', '')
            })
        return {
            'type': 'rules',
            'count': len(rls),
            'rules': rls,
            'message': '\n'.join([f"  {r['name']}: {r['target']}" for r in rls])
        }
    
    def tree(self, max_depth=4):
        lines = []
        
        def build(lineage, depth, prefix=''):
            if depth > max_depth:
                return
            obj = self.store.get(lineage)
            name = obj['name'] if obj else lineage.split(':')[-1]
            lines.append(prefix + name)
            
            children = self.store.get_children(lineage)
            for i, child in enumerate(children):
                is_last = i == len(children) - 1
                child_prefix = prefix + ('└── ' if is_last else '├── ')
                next_prefix = prefix + ('    ' if is_last else '│   ')
                
                child_obj = self.store.get(child)
                child_name = child_obj['name'] if child_obj else child.split(':')[-1]
                lines.append(child_prefix + child_name)
                
                for gc in self.store.get_children(child):
                    build(gc, depth + 2, next_prefix)
        
        if 'Object' in self.store.objects:
            build('Object', 0)
        
        return {
            'type': 'tree',
            'lines': lines,
            'message': '\n'.join(lines)
        }
    
    def resolve_cmd(self, vector_name):
        value = self.resolver.resolve_vector(vector_name)
        return {
            'type': 'resolve',
            'vector': vector_name,
            'value': value,
            'message': f"{vector_name} = {value if value is not None else '(not found)'}"
        }
    
    def get(self, lineage):
        if not lineage.startswith('Object:'):
            lineage = 'Object:' + lineage
        
        obj = self.resolver.resolve_object(lineage)
        if not obj:
            return {'type': 'get', 'error': f"Object not found: {lineage}"}
        
        return {
            'type': 'get',
            'object': obj,
            'message': json.dumps(obj, indent=2, default=str)
        }
    
    def read(self, type_name, conditions, options):
        results = []
        
        for lineage, obj in self.store.objects.items():
            if f':{type_name}' in lineage or lineage.endswith(f':{type_name}') or obj['name'] == type_name:
                if not conditions or self.match_conditions(obj, conditions):
                    results.append(self.resolver.resolve_object(lineage))
        
        # Apply options
        if options:
            results = self.apply_options(results, options)
        
        return {
            'type': 'read',
            'query': f"read {type_name}" + (f".{conditions}" if conditions else ''),
            'count': len(results),
            'results': results,
            'message': '\n'.join([f"  {r['name']} ({r['lineage']})" for r in results]) if results else 'No results found'
        }
    
    def match_conditions(self, obj, conditions_str):
        for cond in conditions_str.split(','):
            cond = cond.strip()
            attrs = obj.get('attributes', {})
            
            def get_val(attr):
                v = attrs.get(attr, '')
                if isinstance(v, str) and v.startswith('"') and v.endswith('"'):
                    return v[1:-1]
                return v
            
            # Exists
            if cond.endswith('?'):
                if cond[:-1] not in attrs:
                    return False
                continue
            
            # Operators
            for op, func in [
                ('!=', lambda a, b: str(a) != str(b)),
                ('>=', lambda a, b: float(a) >= float(b)),
                ('<=', lambda a, b: float(a) <= float(b)),
                ('>', lambda a, b: float(a) > float(b)),
                ('<', lambda a, b: float(a) < float(b)),
                ('~', lambda a, b: str(b).lower() in str(a).lower()),
                ('=', lambda a, b: str(a) == str(b)),
            ]:
                if op in cond:
                    attr, value = cond.split(op, 1)
                    try:
                        if not func(get_val(attr.strip()), value.strip()):
                            return False
                    except:
                        return False
                    break
        
        return True
    
    def apply_options(self, results, options_str):
        for opt in options_str.split('--'):
            opt = opt.strip()
            if not opt:
                continue
            
            # order=field
            order_match = re.match(r'order=(\w+)', opt)
            if order_match:
                field = order_match.group(1)
                results.sort(key=lambda r: str(r.get('attributes', {}).get(field, '')))
            
            # limit=N
            limit_match = re.match(r'limit=(\d+)', opt)
            if limit_match:
                results = results[:int(limit_match.group(1))]
            
            # count
            if opt == 'count':
                return [{'count': len(results)}]
        
        return results

# ============================================================================
# GEVR PIPELINE
# ============================================================================

class GEVRPipeline:
    def __init__(self, store, resolver, superread):
        self.store = store
        self.resolver = resolver
        self.superread = superread
    
    def execute(self, query):
        result = {
            'stages': [],
            'success': True
        }
        
        # GET
        result['stages'].append({
            'name': 'GET',
            'status': 'running',
            'input': query
        })
        
        try:
            data = self.superread.execute(query)
            result['stages'][0]['status'] = 'success'
            result['stages'][0]['output'] = data
        except Exception as e:
            result['stages'][0]['status'] = 'error'
            result['stages'][0]['error'] = str(e)
            result['success'] = False
            return result
        
        # EXECUTE
        result['stages'].append({
            'name': 'EXECUTE',
            'status': 'success',
            'output': data
        })
        
        # VALIDATE
        validation = self.validate(data)
        result['stages'].append({
            'name': 'VALIDATE',
            'status': 'success' if validation['valid'] else 'warning',
            'output': validation
        })
        
        # RENDER
        rendered = self.render(data)
        result['stages'].append({
            'name': 'RENDER',
            'status': 'success',
            'output': rendered
        })
        
        result['final'] = rendered
        return result
    
    def validate(self, data):
        warnings = []
        errors = []
        
        # Check results if it's a read query
        if data.get('type') == 'read':
            for obj in data.get('results', []):
                # Check required attributes
                if not obj.get('attributes', {}).get('name'):
                    warnings.append(f"{obj['lineage']}: missing 'name' attribute")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def render(self, data):
        return {
            'format': 'json',
            'data': data
        }

# ============================================================================
# HTTP SERVER
# ============================================================================

class MRGServer:
    def __init__(self, workspace_path):
        self.store = ErkStore()
        self.parser = ErkParser(self.store)
        self.resolver = ErkResolver(self.store)
        self.superread = SuperRead(self.store, self.resolver)
        self.gevr = GEVRPipeline(self.store, self.resolver, self.superread)
        self.workspace = Path(workspace_path)
        self.load_workspace()
    
    def load_workspace(self):
        """Load all .gev files from workspace"""
        self.store.clear()
        count = 0
        
        for gev_file in self.workspace.rglob('*.gev'):
            # Skip node_modules, .git, etc.
            if any(p.startswith('.') or p == 'node_modules' for p in gev_file.parts):
                continue
            count += self.parser.parse_file(gev_file)
        
        print(f"Loaded {count} objects from {self.workspace}")
        return count
    
    def query(self, q):
        return self.superread.execute(q)
    
    def gevr_execute(self, q):
        return self.gevr.execute(q)
    
    def reload(self):
        self.resolver.clear_cache()
        return self.load_workspace()


class RequestHandler(BaseHTTPRequestHandler):
    server_instance = None
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        # CORS headers
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {}
        
        if path == '/stats':
            response = self.server_instance.store.stats()
        
        elif path == '/objects':
            response = {
                'objects': list(self.server_instance.store.objects.values())
            }
        
        elif path == '/vectors':
            response = self.server_instance.query('vectors')
        
        elif path == '/rules':
            response = self.server_instance.query('rules')
        
        elif path == '/tree':
            depth = int(params.get('depth', [4])[0])
            response = self.server_instance.query(f'tree {depth}')
        
        elif path == '/query':
            q = params.get('q', ['help'])[0]
            response = self.server_instance.query(q)
        
        elif path == '/gevr':
            q = params.get('q', ['help'])[0]
            response = self.server_instance.gevr_execute(q)
        
        elif path == '/reload':
            count = self.server_instance.reload()
            response = {'reloaded': True, 'objects': count}
        
        elif path == '/health':
            response = {'status': 'ok', 'workspace': str(self.server_instance.workspace)}
        
        else:
            response = {'error': 'Unknown endpoint', 'endpoints': [
                '/stats', '/objects', '/vectors', '/rules', '/tree',
                '/query?q=<command>', '/gevr?q=<command>', '/reload', '/health'
            ]}
        
        self.wfile.write(json.dumps(response, indent=2, default=str).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[MRG] {args[0]}")


def run_server(workspace, port=8420):
    server = MRGServer(workspace)
    RequestHandler.server_instance = server
    
    httpd = HTTPServer(('localhost', port), RequestHandler)
    print(f"EUREKAI MRG Server running on http://localhost:{port}")
    print(f"Workspace: {workspace}")
    print(f"Endpoints: /stats, /objects, /vectors, /query?q=..., /gevr?q=...")
    print("Press Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        httpd.shutdown()


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='EUREKAI MRG API Server')
    parser.add_argument('workspace', nargs='?', default='.', help='Workspace directory')
    parser.add_argument('-p', '--port', type=int, default=8420, help='Server port')
    parser.add_argument('-q', '--query', help='Execute single query and exit')
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace).resolve()
    
    if args.query:
        # Single query mode
        server = MRGServer(workspace)
        result = server.query(args.query)
        print(json.dumps(result, indent=2, default=str))
    else:
        # Server mode
        run_server(workspace, args.port)


if __name__ == '__main__':
    main()
