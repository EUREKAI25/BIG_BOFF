"""OptimizationRecommendation - Actionable recommendations."""
from typing import Dict, Any, Optional
from ..object import Object, TestResult


class OptimizationRecommendation(Object):
    """
    Optimization recommendation.

    Extends: Object → domain.product.Deliverable

    Represents an actionable recommendation with generated content
    and integration guide.
    """

    def __init__(
        self,
        type: str,
        title: str,
        description: str = "",
        priority: int = 3,
        content: Optional[Dict[str, Any]] = None,
        integration_guide: str = "",
        estimated_impact: str = "medium",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.type = type  # content/structured_data/editorial
        self.title = title
        self.description = description
        self.priority = priority  # 1-5 (1 = most urgent)
        self.content = content or {}
        self.integration_guide = integration_guide
        self.estimated_impact = estimated_impact  # low/medium/high

    def validate(self) -> bool:
        """Validate recommendation."""
        if not self.title:
            return False
        if self.type not in ["content", "structured_data", "editorial"]:
            return False
        if not (1 <= self.priority <= 5):
            return False
        if self.estimated_impact not in ["low", "medium", "high"]:
            return False
        return True

    def test(self) -> TestResult:
        """Test recommendation."""
        if not self.validate():
            return TestResult(False, "Invalid recommendation configuration")

        if not self.content:
            return TestResult(False, "Recommendation must have content")

        if not self.integration_guide:
            return TestResult(False, "Integration guide is required")

        return TestResult(True, "Recommendation is valid")

    def generate(self, context: Dict[str, Any]) -> "OptimizationRecommendation":
        """
        Generate recommendation content.

        Will be implemented by GenerateAgent in Phase 3.
        For now, generates placeholder content.
        """
        if self.type == "structured_data":
            self.content = {
                "format": "JSON-LD",
                "schema": "Organization",
                "data": {
                    "@context": "https://schema.org",
                    "@type": "Organization",
                    "name": context.get("company_name", ""),
                    "description": f"Description optimisée pour {context.get('company_name', '')}",
                }
            }
        elif self.type == "content":
            self.content = {
                "format": "HTML",
                "sections": [
                    {
                        "heading": f"À propos de {context.get('company_name', '')}",
                        "content": "Contenu optimisé IA..."
                    }
                ]
            }
        elif self.type == "editorial":
            self.content = {
                "format": "Markdown",
                "recommendations": [
                    "Utiliser des mots-clés longue traîne",
                    "Structurer le contenu avec des sous-titres",
                    "Ajouter des FAQ pertinentes"
                ]
            }

        self.touch()
        return self

    def export(self, format: str = "html") -> str:
        """
        Export recommendation.

        Formats: html, json, markdown
        """
        if format == "json":
            import json
            return json.dumps(self.to_dict(), indent=2)
        elif format == "html":
            return f"<h2>{self.title}</h2><p>{self.description}</p>"
        elif format == "markdown":
            return f"## {self.title}\n\n{self.description}\n\n### Intégration\n\n{self.integration_guide}"
        else:
            raise ValueError(f"Unknown export format: {format}")

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "content": self.content,
            "integration_guide": self.integration_guide,
            "estimated_impact": self.estimated_impact,
        })
        return base
