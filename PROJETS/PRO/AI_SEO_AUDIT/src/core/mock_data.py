"""Mock data pour le mode démo (évite les appels OpenAI payants)."""
from typing import Dict, List

# Réponses mockées réalistes pour différents types de requêtes
MOCK_RESPONSES: Dict[str, str] = {
    "meilleur restaurant": """Pour les meilleurs restaurants, je recommande :

1. **Chez Marie** - Cuisine française traditionnelle, ambiance chaleureuse, excellents avis clients. Prix moyen 35€.

2. **Le Bistrot du Coin** - Spécialités régionales, produits frais du marché. Très apprécié pour le rapport qualité-prix.

3. **La Table Gourmande** - Cuisine gastronomique, chef étoilé, cadre élégant. Menu dégustation à partir de 65€.

4. **L'Auberge du Terroir** - Cuisine du terroir, ambiance familiale, parfait pour les groupes.

5. **Le Gourmet** - Fusion moderne, carte des vins exceptionnelle.""",

    "bon restaurant": """Voici mes recommandations pour un bon restaurant :

1. **Le Comptoir** - Excellente cuisine bistrot, accueil chaleureux, prix raisonnables (20-30€).

2. **Chez Marie** - Cuisine maison authentique, produits frais, très bonnes critiques.

3. **La Brasserie** - Grand choix de plats, service rapide, idéal pour déjeuner.

4. **Le Petit Zinc** - Ambiance typique, spécialités locales, bon rapport qualité-prix.""",

    "restaurant recommandé": """Je vous recommande ces restaurants :

1. **La Table d'Hôte** - Cuisine raffinée, service impeccable, cadre cosy.

2. **Le Relais** - Spécialités régionales, chef talentueux, ambiance conviviale.

3. **Chez Marie** - Valeur sûre, cuisine généreuse, accueil familial.

4. **Le Jardin Secret** - Terrasse agréable, cuisine créative, excellent pour l'été.""",

    "avis": """Voici ce que je peux vous dire :

**Le Gourmet** bénéficie d'excellentes critiques :
- Note moyenne : 4.5/5
- Points forts : Qualité des plats, présentation soignée, service attentionné
- Ambiance élégante et feutrée

**La Brasserie du Coin** est très appréciée :
- Note : 4.3/5
- Clientèle locale fidèle
- Prix corrects pour la qualité

**Chez Marie** obtient de très bons retours :
- Note : 4.7/5
- Cuisine authentique
- Rapport qualité-prix excellent""",

    "menu et prix": """Concernant les menus et tarifs :

**Le Bistrot** propose :
- Menu du jour : 18€ (entrée + plat + dessert)
- Formule déjeuner : 15€ (plat + dessert)
- Carte : 25-35€ en moyenne

**La Table** affiche :
- Menu découverte : 42€
- Menu gastronomique : 65€
- Plats à la carte : 18-28€

**Chez Marie** :
- Formule midi : 14€
- Menu complet : 28€
- Plats : 12-22€""",

    "où manger": """Pour manger dans le secteur, plusieurs bonnes options :

**Centre-ville** :
- Le Central - Brasserie animée, service continu
- Chez Paul - Cuisine traditionnelle
- La Terrasse - Belle vue, carte variée

**Quartier historique** :
- L'Ancien Café - Cadre authentique
- Chez Marie - Institution locale
- Le Vieux Moulin - Spécialités régionales"""
}


def get_mock_response(query: str) -> str:
    """
    Retourne une réponse mockée réaliste selon la requête.

    Args:
        query: La requête de l'utilisateur

    Returns:
        Réponse mockée correspondante ou réponse générique
    """
    query_lower = query.lower()

    # Cherche une correspondance dans les mots-clés
    for keyword, response in MOCK_RESPONSES.items():
        if keyword in query_lower:
            return response

    # Réponse générique si pas de match
    return """Voici quelques recommandations :

1. **Le Grand Restaurant** - Cuisine de qualité, service professionnel, ambiance agréable.

2. **Chez Marie** - Établissement reconnu, cuisine authentique, excellent accueil.

3. **La Maison Gourmande** - Spécialités maison, produits frais, bon rapport qualité-prix.

4. **Le Bistrot Central** - Cuisine bistrot traditionnelle, ambiance conviviale."""


def get_mock_audit_results(company_name: str, queries: List[str]) -> List[Dict]:
    """
    Génère des résultats d'audit mockés réalistes.

    Args:
        company_name: Nom de l'entreprise auditée
        queries: Liste des requêtes testées

    Returns:
        Liste de résultats mockés
    """
    results = []

    for i, query in enumerate(queries):
        # Simule une détection dans 40% des cas
        company_mentioned = i % 5 in [1, 2]  # Positions 1 et 2 sur 5

        # Position variable si mentionné
        position = i % 3 + 1 if company_mentioned else None

        # Concurrents fictifs mais réalistes
        competitors = [
            "Le Grand Restaurant",
            "La Table Gourmande",
            "Le Bistrot du Coin",
            "L'Auberge du Terroir",
            "Le Gourmet"
        ][:3 + (i % 3)]  # 3 à 5 concurrents

        # Génère la réponse mockée
        response = get_mock_response(query)

        results.append({
            "query": query,
            "ai_provider": "chatgpt",
            "company_mentioned": company_mentioned,
            "position": position,
            "competitors": competitors,
            "raw_response": response
        })

    return results
