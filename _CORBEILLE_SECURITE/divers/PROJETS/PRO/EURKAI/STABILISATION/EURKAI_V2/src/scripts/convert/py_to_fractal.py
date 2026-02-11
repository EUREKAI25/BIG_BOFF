"""
Python to Fractal Template Converter
====================================

Convertit un fichier Python en template fractal agnostique uniforme.
Chaque élément (import, fonction, classe, méthode, constante) suit
la même structure fractale avec inputList, outputList, requirementList,
dependenciesList, etc.

Usage:
    from py_to_fractal_template import py_to_fractal
    result = py_to_fractal("/path/to/module.py")
    
Output:
    {
        "manifest": {...},
        "dictionary": {...},
        "template": {...}
    }
"""

import ast
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# =============================================================================
# DICTIONNAIRE FRACTAL
# =============================================================================

def get_dictionary() -> dict:
    """
    Retourne le dictionnaire de mapping pour la structure fractale.
    Définit tous les types d'objets et attributs possibles.
    """
    return {
        "objectTypes": {
            "moduleList": "module",
            "functionList": "function",
            "classList": "class",
            "methodList": "method",
            "constantList": "constant",
            "importList": "import",
            "commandList": "command",
            "cliList": "cli"
        },
        "attributes": {
            "nameList": "name",
            "typeList": "type",
            "descriptionList": "description",
            "inputList": "input",
            "outputList": "output",
            "bodyList": "body",
            "defaultList": "default",
            "requiredList": "required",
            "requirementList": "requirement",
            "dependenciesList": "dependencies",
            "childrenList": "children",
            "visibilityList": "visibility",
            "pureList": "pure",
            "ioList": "io",
            "inheritsList": "inherits",
            "valueList": "value",
            "moduleList": "module",
            "kindList": "kind",
            "lazyList": "lazy",
            "decoratorList": "decorator",
            "asyncList": "async"
        },
        "kindValues": {
            "requirements": ["stdlib", "pip", "system", "local"],
            "dependencies": ["function", "class", "constant", "method"]
        },
        "visibilityValues": ["public", "private", "protected"],
        "ioValues": ["none", "filesystem", "network", "stdout", "stdin"],
        "typeValues": [
            "str", "int", "float", "bool", "dict", "list", "set", 
            "tuple", "None", "any", "bytes", "callable", "type"
        ]
    }


# =============================================================================
# STDLIB DETECTION
# =============================================================================

STDLIB_MODULES = {
    'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio',
    'asyncore', 'atexit', 'audioop', 'base64', 'bdb', 'binascii',
    'binhex', 'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cgitb',
    'chunk', 'cmath', 'cmd', 'code', 'codecs', 'codeop', 'collections',
    'colorsys', 'compileall', 'concurrent', 'configparser', 'contextlib',
    'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
    'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal',
    'difflib', 'dis', 'distutils', 'doctest', 'email', 'encodings',
    'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput',
    'fnmatch', 'fractions', 'ftplib', 'functools', 'gc', 'getopt',
    'getpass', 'gettext', 'glob', 'graphlib', 'grp', 'gzip', 'hashlib',
    'heapq', 'hmac', 'html', 'http', 'idlelib', 'imaplib', 'imghdr',
    'imp', 'importlib', 'inspect', 'io', 'ipaddress', 'itertools',
    'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging',
    'lzma', 'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes',
    'mmap', 'modulefinder', 'multiprocessing', 'netrc', 'nis',
    'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev',
    'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil',
    'platform', 'plistlib', 'poplib', 'posix', 'posixpath', 'pprint',
    'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr',
    'pydoc', 'queue', 'quopri', 'random', 're', 'readline', 'reprlib',
    'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select',
    'selectors', 'shelve', 'shlex', 'shutil', 'signal', 'site',
    'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd',
    'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep',
    'struct', 'subprocess', 'sunau', 'symtable', 'sys', 'sysconfig',
    'syslog', 'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios',
    'test', 'textwrap', 'threading', 'time', 'timeit', 'tkinter',
    'token', 'tokenize', 'trace', 'traceback', 'tracemalloc', 'tty',
    'turtle', 'turtledemo', 'types', 'typing', 'unicodedata', 'unittest',
    'urllib', 'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref',
    'webbrowser', 'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml',
    'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib', 'zoneinfo'
}


def get_module_kind(module_name: str) -> str:
    """Détermine si un module est stdlib, pip, ou local"""
    root_module = module_name.split('.')[0]
    if root_module in STDLIB_MODULES:
        return "stdlib"
    return "pip"  # Par défaut, considéré comme pip


# =============================================================================
# AST HELPERS
# =============================================================================

def get_docstring(node: ast.AST) -> str | None:
    """Extrait le docstring d'un noeud AST"""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
        if (node.body and isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            return node.body[0].value.value.strip()
    return None


def get_visibility(name: str) -> str:
    """Détermine la visibilité basée sur le nom"""
    if name.startswith('__') and not name.endswith('__'):
        return "private"
    elif name.startswith('_'):
        return "protected"
    return "public"


def annotation_to_str(annotation: ast.AST | None) -> str:
    """Convertit une annotation de type en string"""
    if annotation is None:
        return "any"
    return ast.unparse(annotation)


def default_to_str(default: ast.AST | None) -> str | None:
    """Convertit une valeur par défaut en string"""
    if default is None:
        return None
    try:
        return ast.unparse(default)
    except:
        return "..."


def extract_body_summary(node: ast.FunctionDef | ast.AsyncFunctionDef, source_lines: list[str]) -> list[str]:
    """Extrait un résumé du corps de la fonction"""
    body_lines = []
    
    # Skip docstring
    start_idx = 0
    if (node.body and isinstance(node.body[0], ast.Expr) and
        isinstance(node.body[0].value, ast.Constant)):
        start_idx = 1
    
    for stmt in node.body[start_idx:]:
        if isinstance(stmt, ast.Return):
            if stmt.value:
                body_lines.append(f"return {ast.unparse(stmt.value)}")
            else:
                body_lines.append("return")
        elif isinstance(stmt, ast.Assign):
            body_lines.append(ast.unparse(stmt))
        elif isinstance(stmt, ast.If):
            body_lines.append(f"if {ast.unparse(stmt.test)}: ...")
        elif isinstance(stmt, ast.For):
            body_lines.append(f"for {ast.unparse(stmt.target)} in {ast.unparse(stmt.iter)}: ...")
        elif isinstance(stmt, ast.While):
            body_lines.append(f"while {ast.unparse(stmt.test)}: ...")
        elif isinstance(stmt, ast.With):
            body_lines.append(f"with ...: ...")
        elif isinstance(stmt, ast.Try):
            body_lines.append("try: ... except: ...")
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            body_lines.append(ast.unparse(stmt))
    
    return body_lines[:10]  # Limiter à 10 lignes


def detect_io_type(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Détecte le type d'I/O d'une fonction"""
    source = ast.unparse(node)
    
    if any(x in source for x in ['open(', 'Path(', 'os.path', 'shutil.', 'pathlib']):
        return "filesystem"
    if any(x in source for x in ['urllib', 'requests.', 'http.', 'socket.', 'urlopen']):
        return "network"
    if any(x in source for x in ['print(', 'sys.stdout', 'logging.']):
        return "stdout"
    if any(x in source for x in ['input(', 'sys.stdin']):
        return "stdin"
    
    return "none"


def detect_purity(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Détecte si une fonction est pure (sans effets de bord)"""
    source = ast.unparse(node)
    
    impure_indicators = [
        'open(', 'print(', 'input(', 'global ', 'nonlocal ',
        '.write(', '.append(', '.extend(', '.update(', '.pop(',
        '.remove(', '.clear(', '.insert(', 'del ',
        'self.', 'cls.', 'urllib', 'requests.', 'os.', 'shutil.'
    ]
    
    return not any(x in source for x in impure_indicators)


# =============================================================================
# DEPENDENCY EXTRACTION
# =============================================================================

class DependencyVisitor(ast.NodeVisitor):
    """Extrait les dépendances internes d'une fonction"""
    
    def __init__(self, defined_names: set[str]):
        self.defined_names = defined_names
        self.dependencies = set()
    
    def visit_Name(self, node: ast.Name):
        if node.id in self.defined_names:
            self.dependencies.add(node.id)
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in self.defined_names:
                self.dependencies.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # Pour les appels de méthode sur self, etc.
            pass
        self.generic_visit(node)


def extract_dependencies(node: ast.AST, defined_names: set[str]) -> list[str]:
    """Extrait les dépendances internes d'un noeud"""
    visitor = DependencyVisitor(defined_names)
    visitor.visit(node)
    return sorted(visitor.dependencies)


# =============================================================================
# FRACTAL OBJECT BUILDER
# =============================================================================

def make_empty_object() -> dict:
    """Crée un objet fractal vide avec toutes les clés"""
    return {
        "nameList": [],
        "typeList": [],
        "descriptionList": [],
        "inputList": [],
        "outputList": [],
        "bodyList": [],
        "requirementList": [],
        "dependenciesList": [],
        "visibilityList": [],
        "pureList": [],
        "ioList": [],
        "childrenList": [{}]
    }


def make_input_object(name: str, type_str: str, description: str, 
                      default: str | None, required: bool) -> dict:
    """Crée un objet fractal pour un paramètre d'entrée"""
    return {
        "nameList": [name],
        "typeList": [type_str],
        "descriptionList": [description],
        "defaultList": [default],
        "requiredList": [required],
        "childrenList": [{}]
    }


def make_output_object(type_str: str, description: str) -> dict:
    """Crée un objet fractal pour une sortie"""
    return {
        "nameList": ["result"],
        "typeList": [type_str],
        "descriptionList": [description],
        "childrenList": [{}]
    }


def make_requirement_object(name: str, module: str | None, kind: str) -> dict:
    """Crée un objet fractal pour un requirement"""
    return {
        "nameList": [name],
        "typeList": ["requirement"],
        "moduleList": [module],
        "kindList": [kind],
        "childrenList": [{}]
    }


def make_dependency_object(name: str, kind: str) -> dict:
    """Crée un objet fractal pour une dépendance interne"""
    return {
        "nameList": [name],
        "typeList": ["dependency"],
        "kindList": [kind],
        "childrenList": [{}]
    }


# =============================================================================
# MAIN CONVERTERS
# =============================================================================

def convert_import(node: ast.Import | ast.ImportFrom) -> list[dict]:
    """Convertit un import en objets fractals"""
    results = []
    
    if isinstance(node, ast.Import):
        for alias in node.names:
            module_name = alias.name
            kind = get_module_kind(module_name)
            obj = {
                "nameList": [alias.asname or alias.name],
                "typeList": ["import"],
                "descriptionList": [f"Import du module {module_name}"],
                "moduleList": [module_name],
                "kindList": [kind],
                "lazyList": [False],
                "childrenList": [{}]
            }
            results.append(obj)
    
    elif isinstance(node, ast.ImportFrom):
        module_name = node.module or ""
        kind = get_module_kind(module_name)
        
        for alias in node.names:
            obj = {
                "nameList": [alias.asname or alias.name],
                "typeList": ["import"],
                "descriptionList": [f"Import de {alias.name} depuis {module_name}"],
                "moduleList": [module_name],
                "kindList": [kind],
                "lazyList": [False],
                "childrenList": [{}]
            }
            results.append(obj)
    
    return results


def convert_constant(node: ast.Assign, source_lines: list[str]) -> dict | None:
    """Convertit une assignation constante (UPPER_CASE) en objet fractal"""
    if len(node.targets) != 1:
        return None
    
    target = node.targets[0]
    if not isinstance(target, ast.Name):
        return None
    
    name = target.id
    # Seules les constantes UPPER_CASE
    if not name.isupper() and not (name.startswith('_') and name[1:].isupper()):
        return None
    
    try:
        value_str = ast.unparse(node.value)
    except:
        value_str = "..."
    
    # Déterminer le type
    if isinstance(node.value, ast.Set):
        type_str = "set"
    elif isinstance(node.value, ast.List):
        type_str = "list"
    elif isinstance(node.value, ast.Dict):
        type_str = "dict"
    elif isinstance(node.value, ast.Tuple):
        type_str = "tuple"
    elif isinstance(node.value, ast.Constant):
        type_str = type(node.value.value).__name__
    else:
        type_str = "any"
    
    return {
        "nameList": [name],
        "typeList": [type_str],
        "descriptionList": [f"Constante {name}"],
        "valueList": [value_str],
        "visibilityList": [get_visibility(name)],
        "childrenList": [{}]
    }


def convert_function(node: ast.FunctionDef | ast.AsyncFunctionDef, 
                     source_lines: list[str],
                     defined_names: set[str]) -> dict:
    """Convertit une fonction en objet fractal"""
    
    name = node.name
    docstring = get_docstring(node) or f"Fonction {name}"
    visibility = get_visibility(name)
    is_async = isinstance(node, ast.AsyncFunctionDef)
    
    # Inputs
    inputs = []
    args = node.args
    
    # Calculer les defaults (alignés à droite)
    num_defaults = len(args.defaults)
    num_args = len(args.args)
    
    for i, arg in enumerate(args.args):
        # Skip 'self' et 'cls'
        if arg.arg in ('self', 'cls'):
            continue
        
        default_idx = i - (num_args - num_defaults)
        has_default = default_idx >= 0
        default_val = default_to_str(args.defaults[default_idx]) if has_default else None
        
        inputs.append(make_input_object(
            name=arg.arg,
            type_str=annotation_to_str(arg.annotation),
            description=f"Paramètre {arg.arg}",
            default=default_val,
            required=not has_default
        ))
    
    # Args avec *
    if args.vararg:
        inputs.append(make_input_object(
            name=f"*{args.vararg.arg}",
            type_str=annotation_to_str(args.vararg.annotation),
            description=f"Arguments variadiques",
            default=None,
            required=False
        ))
    
    # Kwargs avec **
    if args.kwarg:
        inputs.append(make_input_object(
            name=f"**{args.kwarg.arg}",
            type_str=annotation_to_str(args.kwarg.annotation),
            description=f"Arguments nommés variadiques",
            default=None,
            required=False
        ))
    
    # Output
    return_type = annotation_to_str(node.returns)
    outputs = [make_output_object(return_type, f"Résultat de type {return_type}")]
    
    # Body summary
    body = extract_body_summary(node, source_lines)
    
    # Dependencies
    deps = extract_dependencies(node, defined_names)
    dep_objects = [make_dependency_object(d, "function") for d in deps]
    
    # IO et pureté
    io_type = detect_io_type(node)
    is_pure = detect_purity(node)
    
    # Decorators
    decorators = [ast.unparse(d) for d in node.decorator_list]
    
    result = {
        "nameList": [name],
        "typeList": ["function"],
        "descriptionList": [docstring],
        "inputList": inputs,
        "outputList": outputs,
        "bodyList": body,
        "dependenciesList": dep_objects,
        "visibilityList": [visibility],
        "pureList": [is_pure],
        "ioList": [io_type],
        "asyncList": [is_async],
        "childrenList": [{}]
    }
    
    if decorators:
        result["decoratorList"] = decorators
    
    return result


def convert_class(node: ast.ClassDef, 
                  source_lines: list[str],
                  defined_names: set[str]) -> dict:
    """Convertit une classe en objet fractal"""
    
    name = node.name
    docstring = get_docstring(node) or f"Classe {name}"
    visibility = get_visibility(name)
    
    # Héritage
    bases = [ast.unparse(base) for base in node.bases]
    
    # Collecter les noms définis dans la classe
    class_defined = defined_names.copy()
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            class_defined.add(item.name)
    
    # Méthodes
    methods = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method_obj = convert_function(item, source_lines, class_defined)
            method_obj["typeList"] = ["method"]
            methods.append(method_obj)
    
    # Attributs de classe (constantes dans la classe)
    class_attrs = []
    for item in node.body:
        if isinstance(item, ast.Assign):
            const_obj = convert_constant(item, source_lines)
            if const_obj:
                class_attrs.append(const_obj)
    
    # Decorators
    decorators = [ast.unparse(d) for d in node.decorator_list]
    
    children = {}
    if methods:
        children["methodList"] = methods
    if class_attrs:
        children["constantList"] = class_attrs
    
    result = {
        "nameList": [name],
        "typeList": ["class"],
        "descriptionList": [docstring],
        "inheritsList": bases,
        "visibilityList": [visibility],
        "childrenList": [children]
    }
    
    if decorators:
        result["decoratorList"] = decorators
    
    return result


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def py_to_fractal(filepath: str) -> dict:
    """
    Convertit un fichier Python en template fractal agnostique.
    
    Args:
        filepath: Chemin vers le fichier Python à analyser
        
    Returns:
        dict contenant:
            - manifest: métadonnées du fichier source
            - dictionary: dictionnaire de mapping des clés fractales
            - template: structure fractale du code
    """
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"Fichier non trouvé: {filepath}")
    
    source = path.read_text(encoding='utf-8')
    source_lines = source.split('\n')
    
    # Parser l'AST
    tree = ast.parse(source, filename=filepath)
    
    # Collecter tous les noms définis (pour les dépendances)
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            defined_names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined_names.add(target.id)
    
    # Docstring du module
    module_docstring = get_docstring(tree) or f"Module {path.name}"
    
    # Construire le template
    template = {
        "importList": [],
        "constantList": [],
        "functionList": [],
        "classList": []
    }
    
    # Parser les éléments de premier niveau
    for node in tree.body:
        # Skip le docstring du module
        if (isinstance(node, ast.Expr) and 
            isinstance(node.value, ast.Constant) and
            isinstance(node.value.value, str)):
            continue
        
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            template["importList"].extend(convert_import(node))
        
        elif isinstance(node, ast.Assign):
            const_obj = convert_constant(node, source_lines)
            if const_obj:
                template["constantList"].append(const_obj)
        
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            template["functionList"].append(
                convert_function(node, source_lines, defined_names)
            )
        
        elif isinstance(node, ast.ClassDef):
            template["classList"].append(
                convert_class(node, source_lines, defined_names)
            )
    
    # Nettoyer les listes vides
    template = {k: v for k, v in template.items() if v}
    
    # Construire le manifest
    manifest = {
        "source": str(path.absolute()),
        "filename": path.name,
        "version": "1.0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "description": module_docstring,
        "stats": {
            "imports": len(template.get("importList", [])),
            "constants": len(template.get("constantList", [])),
            "functions": len(template.get("functionList", [])),
            "classes": len(template.get("classList", []))
        }
    }
    
    return {
        "manifest": manifest,
        "dictionary": get_dictionary(),
        "template": template
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    """Point d'entrée CLI"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python py_to_fractal_template.py <fichier.py> [output.json]")
        print("\nConvertit un fichier Python en template fractal agnostique.")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.py', '_fractal.json')
    
    try:
        result = py_to_fractal(input_file)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Converti: {input_file} → {output_file}")
        print(f"  - {result['manifest']['stats']['imports']} imports")
        print(f"  - {result['manifest']['stats']['constants']} constantes")
        print(f"  - {result['manifest']['stats']['functions']} fonctions")
        print(f"  - {result['manifest']['stats']['classes']} classes")
        
    except Exception as e:
        print(f"✗ Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
