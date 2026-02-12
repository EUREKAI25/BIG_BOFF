"""Prompts multilingues pour les requêtes IA."""
from typing import Dict

# Prompts système pour l'IA (contexte général)
SYSTEM_PROMPTS: Dict[str, str] = {
    "fr": """Tu es un assistant qui aide les utilisateurs à trouver les meilleures entreprises locales.
Lorsqu'on te demande des recommandations, tu dois :
- Toujours fournir des noms d'entreprises spécifiques (pas de descriptions génériques)
- Classer tes recommandations par ordre de préférence
- Être concret et précis dans tes réponses
- Répondre UNIQUEMENT en français""",

    "en": """You are a helpful assistant helping users find the best local businesses.
When asked for recommendations, you should:
- Always provide specific company names (no generic descriptions)
- Rank your recommendations in order of preference
- Be concrete and precise in your answers
- Respond ONLY in English""",

    "es": """Eres un asistente que ayuda a los usuarios a encontrar las mejores empresas locales.
Cuando se te pide recomendaciones, debes:
- Siempre proporcionar nombres específicos de empresas (no descripciones genéricas)
- Clasificar tus recomendaciones por orden de preferencia
- Ser concreto y preciso en tus respuestas
- Responder ÚNICAMENTE en español""",

    "de": """Du bist ein hilfreicher Assistent, der Nutzern hilft, die besten lokalen Unternehmen zu finden.
Wenn du um Empfehlungen gebeten wirst, solltest du:
- Immer spezifische Firmennamen angeben (keine allgemeinen Beschreibungen)
- Deine Empfehlungen nach Präferenz ordnen
- Konkret und präzise in deinen Antworten sein
- NUR auf Deutsch antworten""",

    "it": """Sei un assistente che aiuta gli utenti a trovare le migliori aziende locali.
Quando ti vengono chieste raccomandazioni, devi:
- Fornire sempre nomi di aziende specifiche (no descrizioni generiche)
- Classificare le tue raccomandazioni in ordine di preferenza
- Essere concreto e preciso nelle tue risposte
- Rispondere SOLO in italiano""",
}

# Prompts utilisateur (templates de requêtes)
USER_PROMPT_TEMPLATES: Dict[str, str] = {
    "fr": """L'utilisateur cherche des recommandations. Fournis une réponse structurée et utile.

Requête : {query}

Liste tes meilleures recommandations par ordre de préférence.""",

    "en": """User is looking for recommendations. Please provide a helpful, structured response.

Query: {query}

Please list your top recommendations in order of preference.""",

    "es": """El usuario busca recomendaciones. Proporciona una respuesta estructurada y útil.

Consulta: {query}

Lista tus mejores recomendaciones en orden de preferencia.""",

    "de": """Der Benutzer sucht nach Empfehlungen. Bitte gib eine hilfreiche, strukturierte Antwort.

Anfrage: {query}

Bitte liste deine Top-Empfehlungen in der Reihenfolge der Präferenz auf.""",

    "it": """L'utente cerca raccomandazioni. Fornisci una risposta strutturata e utile.

Domanda: {query}

Elenca le tue migliori raccomandazioni in ordine di preferenza.""",
}


def get_system_prompt(language: str = "fr") -> str:
    """
    Récupère le prompt système dans la langue spécifiée.

    Args:
        language: Code langue ISO (fr, en, es, de, it)

    Returns:
        Prompt système dans la langue demandée (fallback sur français)
    """
    return SYSTEM_PROMPTS.get(language.lower(), SYSTEM_PROMPTS["fr"])


def get_user_prompt_template(language: str = "fr") -> str:
    """
    Récupère le template de prompt utilisateur dans la langue spécifiée.

    Args:
        language: Code langue ISO (fr, en, es, de, it)

    Returns:
        Template de prompt utilisateur dans la langue demandée (fallback sur français)
    """
    return USER_PROMPT_TEMPLATES.get(language.lower(), USER_PROMPT_TEMPLATES["fr"])


def format_user_prompt(query: str, language: str = "fr") -> str:
    """
    Formate un prompt utilisateur avec la requête spécifiée.

    Args:
        query: La requête de l'utilisateur
        language: Code langue ISO (fr, en, es, de, it)

    Returns:
        Prompt utilisateur formaté dans la langue demandée
    """
    template = get_user_prompt_template(language)
    return template.format(query=query)
