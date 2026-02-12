"""GenerateAgent - Generates optimization recommendations."""
from typing import List, Dict, Any
from ...core.object import Object, TestResult
from ...core.domain.competitor_analysis import CompetitorAnalysis
from ...core.domain.optimization_recommendation import OptimizationRecommendation


class GenerateAgent(Object):
    """
    Generate Agent - Phase 3 of audit process.

    Extends: Object → flow.agent.Agent

    Responsibilities:
    - Generate optimized content
    - Create structured data (JSON-LD)
    - Produce integration guides
    - Generate mockups (plan Pro)
    """

    def __init__(self, language: str = "fr", **kwargs):
        super().__init__(**kwargs)
        self.language = language

    def validate(self) -> bool:
        """Validate agent configuration."""
        return True

    def test(self) -> TestResult:
        """Test agent functionality."""
        # Create mock analysis
        from ...core.domain.competitor_analysis import Gap
        mock_analysis = CompetitorAnalysis(target_company="Test Co")
        mock_analysis.visibility_gaps = [
            Gap("structured_data", "Missing Schema.org", "high"),
            Gap("content", "Content not optimized", "medium"),
        ]

        try:
            recommendations = self.execute(mock_analysis)
            if not recommendations:
                return TestResult(False, "Execute returned empty list")
            if len(recommendations) < len(mock_analysis.visibility_gaps):
                return TestResult(False, "Not enough recommendations generated")
        except Exception as e:
            return TestResult(False, f"Execute failed: {e}")

        return TestResult(True, "Generate agent is operational")

    def execute(self, analysis: CompetitorAnalysis) -> List[OptimizationRecommendation]:
        """
        Execute recommendation generation.

        Args:
            analysis: CompetitorAnalysis with identified gaps

        Returns:
            List of OptimizationRecommendation objects
        """
        recommendations = []

        # Generate recommendation for each gap
        for i, gap in enumerate(analysis.visibility_gaps):
            if gap.type == "structured_data":
                rec = self._generate_structured_data_recommendation(
                    analysis.target_company, gap, priority=i+1
                )
            elif gap.type == "content":
                rec = self._generate_content_recommendation(
                    analysis.target_company, gap, priority=i+1
                )
            elif gap.type == "editorial":
                rec = self._generate_editorial_recommendation(
                    analysis.target_company, gap, priority=i+1
                )
            elif gap.type == "authority":
                rec = self._generate_authority_recommendation(
                    analysis.target_company, gap, priority=i+1
                )
            else:
                continue

            if rec:
                recommendations.append(rec)

        self.touch()
        return recommendations

    def _generate_structured_data_recommendation(
        self, company: str, gap, priority: int
    ) -> OptimizationRecommendation:
        """Generate Schema.org structured data recommendation."""
        content = {
            "format": "JSON-LD",
            "schema": "Organization",
            "code": {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": company,
                "description": f"Description de {company} optimisée pour les IA",
                "url": f"https://www.example.com",
                "logo": f"https://www.example.com/logo.png",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "Paris",
                    "addressCountry": "FR"
                },
                "aggregateRating": {
                    "@type": "AggregateRating",
                    "ratingValue": "4.5",
                    "reviewCount": "100"
                }
            }
        }

        integration_guide = f"""# Intégration des données structurées

## 1. Copier le code JSON-LD

Copiez le code JSON-LD fourni ci-dessous.

## 2. Insérer dans le HTML

Ajoutez ce code dans la section `<head>` de votre page d'accueil :

```html
<script type="application/ld+json">
{content['code']}
</script>
```

## 3. Adapter les valeurs

Remplacez les valeurs d'exemple par vos vraies informations :
- `name` : Nom de votre entreprise
- `description` : Description claire et concise
- `url` : URL de votre site
- `logo` : URL de votre logo
- `address` : Votre adresse complète
- `aggregateRating` : Vos vraies notes (ou supprimer si pas pertinent)

## 4. Valider

Testez avec l'outil de test de données structurées de Google :
https://search.google.com/test/rich-results
"""

        from ...core.config.translations import get_recommendation_title

        title = get_recommendation_title("structured_data", self.language)

        return OptimizationRecommendation(
            type="structured_data",
            title=title,
            description=gap.description,
            priority=min(priority, 5),
            content=content,
            integration_guide=integration_guide,
            estimated_impact="high"
        )

    def _generate_content_recommendation(
        self, company: str, gap, priority: int
    ) -> OptimizationRecommendation:
        """Generate content optimization recommendation."""
        content = {
            "format": "HTML",
            "sections": [
                {
                    "heading": f"À propos de {company}",
                    "content": f"{company} est reconnu pour [expertise principale]. "
                               f"Nous offrons [services/produits] à [audience cible].",
                    "keywords": ["expertise", "services", "qualité"]
                },
                {
                    "heading": "Nos points forts",
                    "content": f"- Expérience de [X années]\n"
                               f"- [Nombre] clients satisfaits\n"
                               f"- Spécialistes certifiés\n"
                               f"- Service [caractéristique unique]",
                    "keywords": ["expérience", "satisfaction", "expertise"]
                },
                {
                    "heading": "FAQ",
                    "content": "Q: Pourquoi choisir {company} ?\n"
                               "R: [Réponse détaillée avec mots-clés]\n\n"
                               "Q: Quels sont vos tarifs ?\n"
                               "R: [Réponse transparente]\n\n"
                               "Q: Comment nous contacter ?\n"
                               "R: [Informations de contact]",
                    "keywords": ["choisir", "tarifs", "contact"]
                }
            ]
        }

        integration_guide = f"""# Intégration du contenu optimisé

## 1. Structure du contenu

Organisez votre page avec ces sections dans cet ordre :
1. À propos (description claire)
2. Points forts (liste à puces)
3. FAQ (questions/réponses)

## 2. Optimisation pour IA

- Utilisez des phrases complètes et naturelles
- Répondez directement aux questions courantes
- Structurez avec des titres clairs (H2, H3)
- Évitez le jargon, soyez clair et précis

## 3. Mise en forme HTML

```html
<section>
  <h2>À propos de {company}</h2>
  <p>[Votre description]</p>
</section>

<section>
  <h2>Nos points forts</h2>
  <ul>
    <li>[Point fort 1]</li>
    <li>[Point fort 2]</li>
  </ul>
</section>

<section>
  <h2>Questions fréquentes</h2>
  <div class="faq-item">
    <h3>Pourquoi choisir {company} ?</h3>
    <p>[Réponse]</p>
  </div>
</section>
```

## 4. Mots-clés naturels

Intégrez naturellement ces termes dans votre contenu :
{', '.join(content['sections'][0]['keywords'])}
"""

        from ...core.config.translations import get_recommendation_title

        title = get_recommendation_title("content", self.language)

        return OptimizationRecommendation(
            type="content",
            title=title,
            description=gap.description,
            priority=min(priority, 5),
            content=content,
            integration_guide=integration_guide,
            estimated_impact="high"
        )

    def _generate_editorial_recommendation(
        self, company: str, gap, priority: int
    ) -> OptimizationRecommendation:
        """Generate editorial guidelines recommendation."""
        content = {
            "format": "Markdown",
            "guidelines": [
                "**Clarté** : Phrases courtes, vocabulaire simple",
                "**Structure** : Titres clairs, paragraphes courts",
                "**Questions/Réponses** : Anticiper les questions des utilisateurs",
                "**Contexte** : Expliquer qui vous êtes, ce que vous faites",
                "**Preuve** : Inclure chiffres, témoignages, certifications",
                "**Actualité** : Mettre à jour régulièrement",
            ],
            "checklist": [
                "[ ] Description claire de l'entreprise en 1-2 phrases",
                "[ ] Services/produits expliqués simplement",
                "[ ] Points de différenciation vs concurrents",
                "[ ] FAQ avec 5-10 questions courantes",
                "[ ] Informations de contact visibles",
                "[ ] Témoignages ou preuves sociales",
            ]
        }

        integration_guide = f"""# Guide éditorial pour optimisation IA

## Principes clés

{chr(10).join('- ' + g for g in content['guidelines'])}

## Checklist de validation

Avant de publier votre contenu, vérifiez :

{chr(10).join(content['checklist'])}

## Exemple de structure optimale

### Page d'accueil de {company}

**Titre H1** : {company} - [Activité principale en quelques mots]

**Section 1 - À propos**
Description claire : qui, quoi, où, pour qui

**Section 2 - Services**
Liste des services avec description courte

**Section 3 - Avantages**
3-5 points forts concrets

**Section 4 - FAQ**
5-10 questions avec réponses détaillées

**Section 5 - Contact**
Informations complètes de contact
"""

        from ...core.config.translations import get_recommendation_title

        title = get_recommendation_title("editorial", self.language)

        return OptimizationRecommendation(
            type="editorial",
            title=title,
            description=gap.description,
            priority=min(priority, 5),
            content=content,
            integration_guide=integration_guide,
            estimated_impact="medium"
        )

    def _generate_authority_recommendation(
        self, company: str, gap, priority: int
    ) -> OptimizationRecommendation:
        """Generate authority/visibility recommendation."""
        content = {
            "format": "Markdown",
            "actions": [
                "Créer/optimiser profil Google My Business",
                "Encourager les avis clients authentiques",
                "Être présent sur annuaires sectoriels pertinents",
                "Créer du contenu régulier (blog, actualités)",
                "Partager expertise (interviews, articles invités)",
            ]
        }

        integration_guide = f"""# Améliorer la visibilité et l'autorité

## Actions prioritaires

1. **Google My Business**
   - Créer/compléter le profil
   - Ajouter photos de qualité
   - Répondre aux avis
   - Publier des actualités régulières

2. **Avis clients**
   - Demander des avis après chaque prestation
   - Répondre à tous les avis (positifs et négatifs)
   - Afficher les témoignages sur votre site

3. **Présence en ligne**
   - S'inscrire sur annuaires pertinents (PagesJaunes, etc.)
   - Vérifier cohérence des informations (NAP : Name, Address, Phone)
   - Créer profils réseaux sociaux professionnels

4. **Contenu régulier**
   - Publier 1-2 articles/mois sur votre expertise
   - Partager actualités de l'entreprise
   - Répondre aux questions courantes en détail

5. **Preuves d'expertise**
   - Afficher certifications, formations
   - Mentionner expérience, années d'activité
   - Partager études de cas (avec permission)
"""

        from ...core.config.translations import get_recommendation_title

        title = get_recommendation_title("authority", self.language)

        return OptimizationRecommendation(
            type="editorial",
            title=title,
            description=gap.description,
            priority=min(priority, 5),
            content=content,
            integration_guide=integration_guide,
            estimated_impact="medium"
        )

    def generate_guide(self, recommendations: List[OptimizationRecommendation], company: str) -> str:
        """
        Generate complete integration guide (PDF-ready).

        Will be used by export service in Phase 4.
        """
        guide = f"""# Guide d'optimisation IA - {company}

## Introduction

Ce guide vous aide à améliorer votre visibilité dans les recommandations des intelligences artificielles (ChatGPT, Claude, Gemini, etc.).

## Vos recommandations prioritaires

"""
        for i, rec in enumerate(sorted(recommendations, key=lambda r: r.priority), 1):
            guide += f"""
### {i}. {rec.title}

**Priorité** : P{rec.priority} | **Impact estimé** : {rec.estimated_impact}

{rec.description}

{rec.integration_guide}

---
"""

        guide += """
## Support

Pour toute question sur ce guide :
- Email : support@ai-seo-audit.com
- Documentation : https://docs.ai-seo-audit.com

---

*Généré par AI SEO Audit*
"""

        return guide
