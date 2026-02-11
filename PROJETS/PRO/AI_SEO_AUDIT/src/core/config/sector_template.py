"""SectorTemplate - Sector-specific configuration."""
from typing import List, Dict, Any
from ..object import Object, TestResult


class SectorTemplate(Object):
    """
    Sector template configuration.

    Extends: Object → config.template.Template

    Provides sector-specific queries, keywords, and signals.
    """

    def __init__(
        self,
        sector_id: str,
        sector_name: Dict[str, str],  # {lang: name}
        queries_patterns: List[str],
        signals_priority: List[str],
        keywords: List[str],
        **kwargs
    ):
        super().__init__(**kwargs)
        self.sector_id = sector_id
        self.sector_name = sector_name
        self.queries_patterns = queries_patterns
        self.signals_priority = signals_priority
        self.keywords = keywords

    def validate(self) -> bool:
        """Validate template."""
        if not self.sector_id:
            return False
        if not self.sector_name or not isinstance(self.sector_name, dict):
            return False
        if not self.queries_patterns:
            return False
        return True

    def test(self) -> TestResult:
        """Test template."""
        if not self.validate():
            return TestResult(False, "Invalid template configuration")

        # Test that we can generate queries
        try:
            queries = self.generate_queries(3, company="TestCo", location="Paris")
            if len(queries) < 3:
                return TestResult(False, "Could not generate enough queries")
        except Exception as e:
            return TestResult(False, f"Query generation failed: {e}")

        return TestResult(True, "Template is valid")

    def customize(self, company: str, location: str = "") -> List[str]:
        """
        Customize queries for specific company.

        Replaces placeholders in query patterns.
        """
        queries = []
        for pattern in self.queries_patterns:
            query = pattern.replace("{company}", company)
            query = query.replace("{location}", location)
            queries.append(query)
        return queries

    def generate_queries(self, count: int, company: str = "", location: str = "") -> List[str]:
        """
        Generate N queries from patterns.

        Uses patterns and keywords to create diverse queries.
        """
        queries = self.customize(company, location)

        # Add keyword-based queries
        for keyword in self.keywords[:count]:
            if company:
                queries.append(f"{keyword} {company}")
            else:
                queries.append(keyword)

        return queries[:count]

    def adapt_language(self, lang: str) -> "SectorTemplate":
        """
        Adapt template to specific language.

        Creates a copy with translated patterns.
        """
        # For MVP, just return self
        # In Phase 4 (i18n), will translate patterns
        return self

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "sector_id": self.sector_id,
            "sector_name": self.sector_name,
            "queries_patterns": self.queries_patterns,
            "signals_priority": self.signals_priority,
            "keywords": self.keywords,
        })
        return base

    @classmethod
    def get_restaurant_template(cls) -> "SectorTemplate":
        """Get pre-configured restaurant template."""
        return cls(
            sector_id="restaurant",
            sector_name={
                "fr": "Restaurant",
                "en": "Restaurant",
                "es": "Restaurante",
                "de": "Restaurant",
                "it": "Ristorante"
            },
            queries_patterns=[
                "meilleur restaurant {location}",
                "{company} avis",
                "bon restaurant {location}",
                "restaurant recommandé {location}",
                "{company} menu et prix",
                "où manger {location}",
            ],
            signals_priority=[
                "google_my_business",
                "reviews_rating",
                "menu_structured_data",
                "opening_hours",
                "photos_quality"
            ],
            keywords=[
                "restaurant", "cuisine", "gastronomie", "chef",
                "menu", "réservation", "table"
            ]
        )
