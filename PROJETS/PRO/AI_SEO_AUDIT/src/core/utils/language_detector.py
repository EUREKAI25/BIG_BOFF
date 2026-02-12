"""Détection automatique de la langue."""
import locale
from typing import Optional


def detect_system_language() -> str:
    """
    Détecte la langue du système.

    Returns:
        Code langue ISO (fr, en, es, de, it) - défaut : fr
    """
    try:
        # Récupère la locale système
        lang, _ = locale.getdefaultlocale()

        if not lang:
            return "fr"

        # Extrait le code langue (ex: fr_FR -> fr)
        lang_code = lang.split('_')[0].lower()

        # Langues supportées
        supported_langs = ["fr", "en", "es", "de", "it"]

        if lang_code in supported_langs:
            return lang_code

        # Fallback sur français
        return "fr"

    except Exception:
        return "fr"


def normalize_language_code(lang: Optional[str]) -> str:
    """
    Normalise un code langue.

    Args:
        lang: Code langue (peut être fr, fr-FR, FR, français, etc.)

    Returns:
        Code langue ISO normalisé (fr, en, es, de, it)
    """
    if not lang:
        return detect_system_language()

    # Nettoie et convertit en minuscules
    lang = lang.strip().lower()

    # Mappings courants
    mappings = {
        "français": "fr",
        "french": "fr",
        "francais": "fr",
        "english": "en",
        "anglais": "en",
        "spanish": "es",
        "espagnol": "es",
        "español": "es",
        "german": "de",
        "allemand": "de",
        "deutsch": "de",
        "italian": "it",
        "italien": "it",
        "italiano": "it",
    }

    # Vérifie dans les mappings
    if lang in mappings:
        return mappings[lang]

    # Extrait le code langue si format fr-FR ou fr_FR
    if '-' in lang or '_' in lang:
        lang = lang.split('-')[0].split('_')[0]

    # Langues supportées
    supported_langs = ["fr", "en", "es", "de", "it"]

    if lang in supported_langs:
        return lang

    # Fallback
    return "fr"


def get_browser_language_from_header(accept_language: Optional[str]) -> str:
    """
    Extrait la langue préférée depuis le header HTTP Accept-Language.

    Args:
        accept_language: Valeur du header Accept-Language (ex: "fr-FR,fr;q=0.9,en;q=0.8")

    Returns:
        Code langue ISO normalisé
    """
    if not accept_language:
        return detect_system_language()

    try:
        # Parse le header (format: fr-FR,fr;q=0.9,en;q=0.8)
        languages = accept_language.split(',')

        # Prend la première langue (la plus prioritaire)
        if languages:
            first_lang = languages[0].split(';')[0].strip()
            return normalize_language_code(first_lang)

    except Exception:
        pass

    return detect_system_language()
