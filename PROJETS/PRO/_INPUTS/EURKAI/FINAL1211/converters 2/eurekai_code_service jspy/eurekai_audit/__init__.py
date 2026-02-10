"""
EUREKAI Audit - Module d'audit et analyse de code JavaScript
"""
from .parser import parse_js, parse_js_file, ParseResult, JsFunction, JsParam
from .analyzer import analyze, AnalysisResult, FunctionAnalysis, Issue, Severity
from .reporter import generate_report, Reporter

__all__ = [
    'parse_js', 'parse_js_file', 'ParseResult', 'JsFunction', 'JsParam',
    'analyze', 'AnalysisResult', 'FunctionAnalysis', 'Issue', 'Severity',
    'generate_report', 'Reporter'
]


def audit_file(filepath: str, format: str = "yaml") -> str:
    """Audit complet d'un fichier JS - point d'entrée simplifié"""
    parsed = parse_js_file(filepath)
    analysis = analyze(parsed)
    return generate_report(parsed, analysis, filepath, format)


def audit_source(source: str, filename: str = "<source>", format: str = "yaml") -> str:
    """Audit complet d'une source JS"""
    parsed = parse_js(source)
    analysis = analyze(parsed)
    return generate_report(parsed, analysis, filename, format)
