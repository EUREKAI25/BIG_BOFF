"""Traductions pour les descriptions d'analyse et recommendations."""
from typing import Dict, List

# Descriptions des gaps (problèmes de visibilité)
GAP_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    "low_mention_rate": {
        "fr": "Votre entreprise n'apparaît que dans {mentioned}/{total} requêtes ({rate}%). Cela signifie que l'IA ne vous recommande pas assez souvent. Vos concurrents sont plus visibles.",
        "en": "Your company appears in only {mentioned}/{total} queries ({rate}%). This means the AI doesn't recommend you often enough. Your competitors are more visible.",
        "es": "Su empresa aparece solo en {mentioned}/{total} consultas ({rate}%). Esto significa que la IA no te recomienda con suficiente frecuencia. Sus competidores son más visibles.",
        "de": "Ihr Unternehmen erscheint nur in {mentioned}/{total} Anfragen ({rate}%). Das bedeutet, dass die KI Sie nicht oft genug empfiehlt. Ihre Konkurrenten sind sichtbarer.",
        "it": "La tua azienda appare solo in {mentioned}/{total} query ({rate}%). Ciò significa che l'IA non ti raccomanda abbastanza spesso. I tuoi concorrenti sono più visibili.",
    },
    "competitors_more_visible": {
        "fr": "Ces concurrents apparaissent plus souvent que vous : {competitors}. Ils ont probablement un meilleur référencement et plus d'avis positifs.",
        "en": "These competitors appear more often than you: {competitors}. They likely have better SEO and more positive reviews.",
        "es": "Estos competidores aparecen más a menudo que usted: {competitors}. Probablemente tienen mejor SEO y más reseñas positivas.",
        "de": "Diese Konkurrenten erscheinen häufiger als Sie: {competitors}. Sie haben wahrscheinlich besseres SEO und mehr positive Bewertungen.",
        "it": "Questi concorrenti appaiono più spesso di te: {competitors}. Probabilmente hanno un SEO migliore e più recensioni positive.",
    },
    "poor_positioning": {
        "fr": "Lorsque vous êtes mentionné, vous apparaissez souvent en position basse ({count} fois). L'IA vous cite, mais ne vous met pas en avant. Il faut renforcer votre autorité.",
        "en": "When you are mentioned, you often appear in a low position ({count} times). The AI cites you, but doesn't highlight you. You need to strengthen your authority.",
        "es": "Cuando te mencionan, a menudo apareces en una posición baja ({count} veces). La IA te cita, pero no te destaca. Necesitas fortalecer tu autoridad.",
        "de": "Wenn Sie erwähnt werden, erscheinen Sie oft in einer niedrigen Position ({count} Mal). Die KI zitiert Sie, hebt Sie aber nicht hervor. Sie müssen Ihre Autorität stärken.",
        "it": "Quando vieni menzionato, appari spesso in una posizione bassa ({count} volte). L'IA ti cita, ma non ti mette in evidenza. Devi rafforzare la tua autorità.",
    },
    "missing_structured_data": {
        "fr": "Vos données structurées (Schema.org) sont manquantes ou incomplètes. Les IA utilisent ces données pour comprendre qui vous êtes et ce que vous proposez. Sans ça, elles ne peuvent pas vous recommander efficacement.",
        "en": "Your structured data (Schema.org) is missing or incomplete. AIs use this data to understand who you are and what you offer. Without it, they can't recommend you effectively.",
        "es": "Sus datos estructurados (Schema.org) faltan o están incompletos. Las IA usan estos datos para entender quién eres y qué ofreces. Sin ellos, no pueden recomendarte eficazmente.",
        "de": "Ihre strukturierten Daten (Schema.org) fehlen oder sind unvollständig. KIs nutzen diese Daten, um zu verstehen, wer Sie sind und was Sie anbieten. Ohne sie können sie Sie nicht effektiv empfehlen.",
        "it": "I tuoi dati strutturati (Schema.org) sono mancanti o incompleti. Le IA usano questi dati per capire chi sei e cosa offri. Senza di essi, non possono raccomandarti efficacemente.",
    },
    "content_not_optimized": {
        "fr": "Votre contenu n'est pas optimisé pour être compris par les IA. Elles ont du mal à extraire les informations clés (services, points forts, spécialités). Un contenu clair et structuré améliorerait drastiquement votre visibilité.",
        "en": "Your content is not optimized to be understood by AIs. They struggle to extract key information (services, strengths, specialties). Clear and structured content would drastically improve your visibility.",
        "es": "Tu contenido no está optimizado para ser entendido por las IA. Les cuesta extraer información clave (servicios, fortalezas, especialidades). Un contenido claro y estructurado mejoraría drásticamente tu visibilidad.",
        "de": "Ihr Inhalt ist nicht optimiert, um von KIs verstanden zu werden. Sie haben Schwierigkeiten, wichtige Informationen zu extrahieren (Dienstleistungen, Stärken, Spezialitäten). Klarer und strukturierter Inhalt würde Ihre Sichtbarkeit drastisch verbessern.",
        "it": "Il tuo contenuto non è ottimizzato per essere compreso dalle IA. Faticano a estrarre informazioni chiave (servizi, punti di forza, specialità). Un contenuto chiaro e strutturato migliorerebbe drasticamente la tua visibilità.",
    }
}

# Titres des recommendations
RECOMMENDATION_TITLES: Dict[str, Dict[str, str]] = {
    "structured_data": {
        "fr": "Ajouter des données structurées Schema.org",
        "en": "Add Schema.org structured data",
        "es": "Añadir datos estructurados Schema.org",
        "de": "Schema.org-strukturierte Daten hinzufügen",
        "it": "Aggiungere dati strutturati Schema.org",
    },
    "content": {
        "fr": "Optimiser le contenu pour les IA",
        "en": "Optimize content for AIs",
        "es": "Optimizar contenido para IA",
        "de": "Inhalte für KIs optimieren",
        "it": "Ottimizzare il contenuto per le IA",
    },
    "editorial": {
        "fr": "Appliquer les bonnes pratiques éditoriales",
        "en": "Apply editorial best practices",
        "es": "Aplicar las mejores prácticas editoriales",
        "de": "Redaktionelle Best Practices anwenden",
        "it": "Applicare le migliori pratiche editoriali",
    },
    "authority": {
        "fr": "Renforcer votre autorité et visibilité",
        "en": "Strengthen your authority and visibility",
        "es": "Fortalecer su autoridad y visibilidad",
        "de": "Ihre Autorität und Sichtbarkeit stärken",
        "it": "Rafforzare la tua autorità e visibilità",
    }
}


def get_gap_description(
    gap_type: str,
    language: str = "fr",
    **format_args
) -> str:
    """
    Récupère la description d'un gap dans la langue spécifiée.

    Args:
        gap_type: Type de gap (low_mention_rate, competitors_more_visible, etc.)
        language: Code langue ISO
        **format_args: Arguments pour formatter la description

    Returns:
        Description formatée dans la langue demandée
    """
    descriptions = GAP_DESCRIPTIONS.get(gap_type, {})
    description = descriptions.get(language.lower(), descriptions.get("fr", ""))

    if format_args:
        return description.format(**format_args)
    return description


def get_recommendation_title(
    rec_type: str,
    language: str = "fr"
) -> str:
    """
    Récupère le titre d'une recommendation dans la langue spécifiée.

    Args:
        rec_type: Type de recommendation (structured_data, content, etc.)
        language: Code langue ISO

    Returns:
        Titre dans la langue demandée
    """
    titles = RECOMMENDATION_TITLES.get(rec_type, {})
    return titles.get(language.lower(), titles.get("fr", ""))
