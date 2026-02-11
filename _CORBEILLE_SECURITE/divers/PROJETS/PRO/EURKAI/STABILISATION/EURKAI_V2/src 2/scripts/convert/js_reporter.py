"""
EURKAI Audit - Reporter
Génère des rapports d'audit en JSON, YAML, Markdown
"""
import json
from datetime import datetime
from .parser import ParseResult
from .analyzer import AnalysisResult, Severity

class Reporter:
    """Génère des rapports d'audit en différents formats"""
    
    def __init__(self, parsed: ParseResult, analysis: AnalysisResult, filename: str = ""):
        self.parsed = parsed
        self.analysis = analysis
        self.filename = filename
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire"""
        return {
            'meta': {
                'file': self.filename,
                'generated': datetime.now().isoformat(),
                'score': self.analysis.score
            },
            'functions': [
                {
                    'name': f.name,
                    'params': [
                        {
                            'name': p.name,
                            'type': p.type,
                            'required': p.required,
                            'default': p.default
                        }
                        for p in f.params
                    ],
                    'has_callback': f.has_callback,
                    'is_exported': f.is_exported,
                    'jsdoc': f.jsdoc,
                    'options_schema': f.options_schema,
                    'body_refs': f.body_refs
                }
                for f in self.parsed.functions
            ],
            'analysis': [
                {
                    'name': fa.name,
                    'complexity': fa.complexity,
                    'convertible': fa.convertible,
                    'strategy': fa.convert_strategy,
                    'issues': [
                        {'severity': i.severity.value, 'code': i.code, 'message': i.message}
                        for i in fa.issues
                    ]
                }
                for fa in self.analysis.functions
            ],
            'dependencies': self.analysis.dependencies,
            'issues': [
                {'severity': i.severity.value, 'code': i.code, 'message': i.message}
                for i in self.analysis.issues
            ],
            'recommendations': self.analysis.recommendations
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Export JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def to_yaml(self) -> str:
        """Export YAML-like (sans dépendance)"""
        d = self.to_dict()
        lines = []
        
        lines.append(f"# Rapport d'audit EURKAI")
        lines.append(f"file: {d['meta']['file']}")
        lines.append(f"score: {d['meta']['score']}/100")
        lines.append(f"generated: {d['meta']['generated']}")
        lines.append("")
        
        lines.append("functions:")
        for f in d['functions']:
            params_str = ', '.join([
                f"{p['name']}: {p['type']}" + ("?" if not p['required'] else "")
                for p in f['params']
            ])
            lines.append(f"  - name: {f['name']}")
            lines.append(f"    params: [{params_str}]")
            lines.append(f"    has_callback: {str(f['has_callback']).lower()}")
            lines.append(f"    is_exported: {str(f['is_exported']).lower()}")
            if f['options_schema']:
                lines.append(f"    options_schema:")
                for opt, spec in f['options_schema'].items():
                    lines.append(f"      {opt}: {{default: {spec.get('default', 'null')}, type: {spec.get('type', 'any')}}}")
            lines.append("")
        
        lines.append("analysis:")
        for fa in d['analysis']:
            lines.append(f"  - name: {fa['name']}")
            lines.append(f"    complexity: {fa['complexity']}")
            lines.append(f"    convertible: {str(fa['convertible']).lower()}")
            lines.append(f"    strategy: {fa['strategy']}")
            if fa['issues']:
                lines.append(f"    issues:")
                for i in fa['issues']:
                    lines.append(f"      - [{i['severity']}] {i['message']}")
            lines.append("")
        
        lines.append("dependencies:")
        lines.append(f"  external: {d['dependencies'].get('external', [])}")
        lines.append(f"  globals_written: {d['dependencies'].get('globals_written', [])}")
        lines.append("")
        
        if d['issues']:
            lines.append("issues:")
            for i in d['issues']:
                lines.append(f"  - severity: {i['severity']}")
                lines.append(f"    message: {i['message']}")
            lines.append("")
        
        lines.append("recommendations:")
        for r in d['recommendations']:
            lines.append(f"  - {r}")
        
        return '\n'.join(lines)
    
    def to_markdown(self) -> str:
        """Export Markdown"""
        d = self.to_dict()
        lines = []
        
        # Header
        lines.append(f"# Rapport d'Audit EURKAI")
        lines.append("")
        lines.append(f"**Fichier:** `{d['meta']['file']}`")
        lines.append(f"**Score:** {d['meta']['score']}/100")
        lines.append(f"**Date:** {d['meta']['generated']}")
        lines.append("")
        
        # Score badge
        score = d['meta']['score']
        if score >= 80:
            badge = "🟢"
        elif score >= 60:
            badge = "🟡"
        else:
            badge = "🔴"
        lines.append(f"## {badge} Score de Convertibilité: {score}/100")
        lines.append("")
        
        # Functions
        lines.append("## Fonctions Détectées")
        lines.append("")
        
        for f, fa in zip(d['functions'], d['analysis']):
            # Status icon
            if fa['convertible']:
                icon = "✅"
            else:
                icon = "❌"
            
            lines.append(f"### {icon} `{f['name']}`")
            lines.append("")
            
            # Signature
            params = ', '.join([p['name'] for p in f['params']])
            lines.append(f"```javascript")
            lines.append(f"function {f['name']}({params})")
            lines.append(f"```")
            lines.append("")
            
            # Description from JSDoc
            if f['jsdoc'].get('description'):
                lines.append(f"> {f['jsdoc']['description']}")
                lines.append("")
            
            # Table des paramètres
            if f['params']:
                lines.append("| Paramètre | Type | Requis | Défaut |")
                lines.append("|-----------|------|--------|--------|")
                for p in f['params']:
                    req = "✓" if p['required'] else ""
                    default = f"`{p['default']}`" if p['default'] else "-"
                    lines.append(f"| `{p['name']}` | `{p['type']}` | {req} | {default} |")
                lines.append("")
            
            # Options schema
            if f['options_schema']:
                lines.append("**Options destructurées:**")
                lines.append("")
                for opt, spec in f['options_schema'].items():
                    lines.append(f"- `{opt}`: {spec.get('type', 'any')} (défaut: `{spec.get('default', 'undefined')}`)")
                lines.append("")
            
            # Analysis
            lines.append(f"**Complexité:** {fa['complexity']} | **Stratégie:** {fa['strategy']}")
            if fa['issues']:
                lines.append("")
                for i in fa['issues']:
                    sev_icon = "⚠️" if i['severity'] == 'warning' else "ℹ️" if i['severity'] == 'info' else "❌"
                    lines.append(f"- {sev_icon} {i['message']}")
            lines.append("")
        
        # Dependencies
        lines.append("## Dépendances")
        lines.append("")
        ext = d['dependencies'].get('external', [])
        if ext:
            lines.append("**Externes (à fournir):**")
            for e in ext:
                lines.append(f"- `{e}`")
            lines.append("")
        
        glob = d['dependencies'].get('globals_written', [])
        if glob:
            lines.append("**Globales écrites:**")
            for g in glob:
                lines.append(f"- `{g}`")
            lines.append("")
        
        # Issues
        if d['issues']:
            lines.append("## ⚠️ Problèmes Détectés")
            lines.append("")
            for i in d['issues']:
                sev_icon = "⚠️" if i['severity'] == 'warning' else "ℹ️" if i['severity'] == 'info' else "❌"
                lines.append(f"- {sev_icon} **{i['code']}**: {i['message']}")
            lines.append("")
        
        # Recommendations
        lines.append("## 📋 Recommandations")
        lines.append("")
        for r in d['recommendations']:
            lines.append(f"- {r}")
        
        return '\n'.join(lines)


def generate_report(parsed: ParseResult, analysis: AnalysisResult, 
                   filename: str = "", format: str = "yaml") -> str:
    """Génère un rapport dans le format spécifié"""
    reporter = Reporter(parsed, analysis, filename)
    
    if format == "json":
        return reporter.to_json()
    elif format == "markdown" or format == "md":
        return reporter.to_markdown()
    else:
        return reporter.to_yaml()
