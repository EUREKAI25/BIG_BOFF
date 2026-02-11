"""
EURKAI Audit - Analyzer
Analyse la qualité, patterns et convertibilité d'un script JS
"""
from dataclasses import dataclass, field
from enum import Enum
from .parser import ParseResult, JsFunction

class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

@dataclass
class Issue:
    severity: Severity
    code: str
    message: str
    location: str = ""

@dataclass
class FunctionAnalysis:
    name: str
    complexity: str  # low, medium, high
    convertible: bool
    convert_strategy: str  # direct, with_variants, manual
    issues: list[Issue] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

@dataclass
class AnalysisResult:
    score: int  # 0-100
    functions: list[FunctionAnalysis] = field(default_factory=list)
    dependencies: dict = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

class Analyzer:
    """Analyse un ParseResult pour évaluer la convertibilité"""
    
    def __init__(self, parsed: ParseResult):
        self.parsed = parsed
        self.result = AnalysisResult(score=100)
    
    def analyze(self) -> AnalysisResult:
        """Analyse complète"""
        self._analyze_functions()
        self._analyze_dependencies()
        self._calculate_score()
        self._generate_recommendations()
        return self.result
    
    def _analyze_functions(self):
        """Analyse chaque fonction"""
        for func in self.parsed.functions:
            analysis = self._analyze_function(func)
            self.result.functions.append(analysis)
    
    def _analyze_function(self, func: JsFunction) -> FunctionAnalysis:
        """Analyse une fonction individuelle"""
        issues = []
        recommendations = []
        
        # Complexité basée sur la taille du body et les structures
        complexity = self._estimate_complexity(func)
        
        # Stratégie de conversion
        if func.has_callback:
            strategy = "with_variants"
            recommendations.append(
                f"Fonction '{func.name}' a un callback - générer variantes utilitaires"
            )
        else:
            strategy = "direct"
        
        # Vérifier les dépendances manquantes
        for ref in func.body_refs:
            if ref.split('.')[0] in self.parsed.globals_read:
                issues.append(Issue(
                    severity=Severity.WARNING,
                    code="MISSING_DEP",
                    message=f"Dépendance externe: {ref}",
                    location=func.name
                ))
        
        # Export non détecté
        if not func.is_exported:
            issues.append(Issue(
                severity=Severity.INFO,
                code="NOT_EXPORTED",
                message=f"Fonction '{func.name}' non exportée",
                location=func.name
            ))
        
        convertible = len([i for i in issues if i.severity == Severity.ERROR]) == 0
        
        return FunctionAnalysis(
            name=func.name,
            complexity=complexity,
            convertible=convertible,
            convert_strategy=strategy,
            issues=issues,
            recommendations=recommendations
        )
    
    def _estimate_complexity(self, func: JsFunction) -> str:
        """Estime la complexité d'une fonction"""
        body = func.body
        
        # Compteurs
        lines = body.count('\n')
        loops = body.count('for ') + body.count('while ')
        conditions = body.count('if ') + body.count('? ')
        
        score = lines / 10 + loops * 2 + conditions
        
        if score < 5:
            return "low"
        elif score < 15:
            return "medium"
        else:
            return "high"
    
    def _analyze_dependencies(self):
        """Analyse les dépendances externes"""
        external = list(self.parsed.globals_read)
        
        self.result.dependencies = {
            'external': external,
            'globals_written': list(self.parsed.globals_written)
        }
        
        # Issues pour dépendances non standard
        for dep in external:
            self.result.issues.append(Issue(
                severity=Severity.WARNING,
                code="EXTERNAL_DEP",
                message=f"Dépendance externe '{dep}' - doit être injectée ou mockée"
            ))
    
    def _calculate_score(self):
        """Calcule le score global de convertibilité (0-100)"""
        score = 100
        
        # Pénalités
        for issue in self.result.issues:
            if issue.severity == Severity.ERROR:
                score -= 20
            elif issue.severity == Severity.WARNING:
                score -= 5
            elif issue.severity == Severity.INFO:
                score -= 1
        
        for func_analysis in self.result.functions:
            for issue in func_analysis.issues:
                if issue.severity == Severity.ERROR:
                    score -= 10
                elif issue.severity == Severity.WARNING:
                    score -= 3
        
        # Bonus
        exported_count = len([f for f in self.parsed.functions if f.is_exported])
        if exported_count > 0:
            score += min(10, exported_count * 2)
        
        self.result.score = max(0, min(100, score))
    
    def _generate_recommendations(self):
        """Génère des recommandations globales"""
        recs = []
        
        # Dépendances
        if self.parsed.globals_read:
            deps = ', '.join(self.parsed.globals_read)
            recs.append(f"Fournir implémentation ou mock pour: {deps}")
        
        # window.x → module.exports
        if any('window.' in g for g in self.parsed.globals_written):
            recs.append("Adapter window.* → module.exports pour Node.js")
        
        # Callbacks
        callback_funcs = [f.name for f in self.parsed.functions if f.has_callback]
        if callback_funcs:
            recs.append(
                f"Fonctions avec callback ({', '.join(callback_funcs)}) - "
                "variantes utilitaires seront générées"
            )
        
        # Stats
        exportable = len([f for f in self.parsed.functions if f.is_exported])
        total = len(self.parsed.functions)
        recs.append(f"{exportable}/{total} fonctions exportables")
        
        self.result.recommendations = recs


def analyze(parsed: ParseResult) -> AnalysisResult:
    """Point d'entrée principal"""
    return Analyzer(parsed).analyze()
