"""
BIG_BOFF Search — Configuration centralisée
Module partagé : chemins, constantes, stop words, helpers.
Importable par tous les scripts d'indexation et le serveur.
"""

import re
import sqlite3
from collections import Counter
from pathlib import Path

# Import config loader pour chemins centralisés
try:
    from config_loader import load_config
    _config = load_config()
except ImportError:
    # Fallback si config_loader pas disponible (ancien mode)
    _config = None

try:
    import snowballstemmer
    _stemmer = snowballstemmer.stemmer('french')
    STEMMING_ENABLED = True
except ImportError:
    _stemmer = None
    STEMMING_ENABLED = False

# POS tagging pour filtrer les adjectifs
try:
    import spacy
    _nlp = spacy.load('fr_core_news_sm', disable=['parser', 'ner'])  # On garde juste le tagger
    POS_TAGGING_ENABLED = True
except (ImportError, OSError):
    _nlp = None
    POS_TAGGING_ENABLED = False

# ── Chemins ──────────────────────────────────────────

# Utilise config_loader si disponible, sinon fallback hardcodé
if _config:
    DB_PATH = _config['paths']['db_path']
    DROPBOX_ROOT = _config['paths']['dropbox_root']
    ACCOUNTS_PATH = _config['paths']['email_accounts_file']
else:
    # Fallback (ancien mode, compatibilité)
    DB_PATH = "/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/MAINTENANCE/catalogue.db"
    DROPBOX_ROOT = "/Users/nathalie/Dropbox"
    ACCOUNTS_PATH = str(Path(__file__).parent / "email_accounts.json")

SRC_DIR = Path(__file__).parent


def get_identity_path():
    """Retourne Path vers ~/.bigboff/identity.json"""
    try:
        from config_loader import CONFIG_DIR
        return CONFIG_DIR / "identity.json"
    except ImportError:
        # Fallback si config_loader pas disponible
        return Path.home() / ".bigboff" / "identity.json"


# ── Conventions ID (ranges négatifs) ─────────────────

ID_OFFSET_EMAIL = 100000    # item_id = -(email_id + 100000)
ID_OFFSET_NOTE  = 200000    # item_id = -(note_id  + 200000)
ID_OFFSET_VAULT = 300000    # item_id = -(vault_id + 300000)
ID_OFFSET_VIDEO = 400000    # item_id = -(video_id + 400000)
ID_OFFSET_EVENT   = 500000    # item_id = -(event_id   + 500000)
ID_OFFSET_CONTACT = 600000    # item_id = -(contact_id + 600000)
ID_OFFSET_LIEU    = 700000    # item_id = -(lieu_id    + 700000)
ID_OFFSET_USER    = 800000    # item_id = -(user_id    + 800000) [Phase P2P]

# ── Stop words unifiés ───────────────────────────────
# Fusion des 5 listes existantes (emails, notes, content, tags, vault)

STOP_WORDS = {
    # Vide / ponctuation
    "",
    # Articles & prépositions FR
    "a", "de", "du", "le", "la", "les", "un", "une", "des",
    "et", "ou", "en", "au", "aux", "par", "pour", "sur", "dans", "avec",
    # Pronoms / déterminants FR
    "mon", "ton", "son", "mes", "tes", "ses", "notre", "votre", "leur",
    "cette", "ces", "tout", "tous", "toute", "toutes",
    "que", "qui", "quoi", "dont", "quel", "quelle",
    # Verbes / mots courants FR (transcriptions)
    "est", "sont", "ont", "fait", "mais", "plus", "pas", "très",
    "bon", "bien", "merci", "bonjour", "bonne", "cordialement",
    "faire", "donc", "vous", "nous", "même", "être", "avoir",
    "quand", "peut", "parce", "comme", "aussi", "encore", "alors",
    "après", "avant", "ça", "cet", "ils", "elles", "lui", "moi",
    "toi", "dit", "dire", "vais", "vas", "ici", "là",
    "peu", "déjà", "voilà", "oui", "non", "juste", "vraiment",
    "suis", "était", "avez", "êtes", "avait",
    # Articles & prépositions EN
    "an", "the", "is", "it", "to", "of", "in", "on", "at", "by",
    "for", "and", "or", "not", "no", "yes", "if", "do", "so",
    "you", "your", "can", "will", "just", "like", "that", "this",
    "what", "how", "but", "are", "was", "were", "been", "have",
    "has", "had", "would", "could", "should", "they", "them",
    "their", "there", "here", "with", "about", "also", "more",
    "very", "really", "going", "know", "want", "think",
    # Email
    "re", "fwd", "fw", "tr", "ref", "objet", "subject",
    # Web
    "http", "https", "www", "com", "org", "net", "fr",
    # Système / chemins
    "ds_store", "icon", "thumbs", "db", "macosx",
    "big", "boff", "big_boff", "____big_boff___",
    "projets", "dropbox", "users", "nathalie",
    "copie", "copy", "old", "new", "tmp", "temp",
    # Code (les plus génériques)
    "true", "false", "none", "null", "undefined", "this", "self",
    "return", "import", "from", "def", "class", "function",
    "var", "let", "const", "then", "else", "elif",
    "while", "with", "pass", "break", "continue",
    "try", "catch", "except", "finally", "async", "await",
    "print", "console", "log",
    "get", "set", "has", "add", "put", "post", "delete",
    "utf", "ascii", "encoding", "charset",
    # Noms de dossier génériques (polluent les recherches)
    "dossier", "resources", "objects", "vendor", "projects", "actions",
    "default", "init", "meta", "versions", "first",
    # Stop words anglais supplémentaires
    "want", "again", "just", "will", "like", "does",
    "about", "into", "them", "than", "only", "also",
    "very", "some", "over", "each", "much",
    "these", "those", "other", "most", "such",
    "when", "where", "which", "there", "then",
    "make", "made", "after", "before", "between", "through",
    "during", "under", "above", "below", "here", "well", "back",
    "even", "still", "same", "able", "being", "come", "done",
    "find", "give", "help", "keep", "know", "last", "long",
    "look", "many", "next", "part", "take", "tell", "turn",
    "used", "using", "work",
    # Code — identifiants ultra-génériques
    "public", "private", "protected", "static", "void", "int", "str",
    "string", "bool", "boolean", "float", "double", "list", "dict",
    "array", "object", "type", "interface", "enum", "struct",
    "error", "warning", "todo", "fixme", "hack", "note", "xxx",
    # Paramètres URL de tracking (Facebook, Google, Microsoft, Instagram, etc.)
    "fbclid", "mibextid", "igshid", "igsh",
    "gclid", "gbraid", "wbraid", "msclkid",
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
    "utm", "source", "campaign", "medium",
}

# Tags de 3 lettres autorisés (tout autre mot de 3 lettres est ignoré)
TAGS_3_WHITELIST = {
    # Extensions / formats
    "php", "jpg", "png", "css", "pdf", "mp4", "mov", "gif", "svg", "mp3",
    "csv", "xml", "txt", "sql", "zip", "wav", "exe", "psd", "tsx", "jsx",
    "yml", "ini", "m4a", "ttf", "pyc", "ppt", "tgz", "wmv", "otf", "htm",
    "bz2", "jar", "dat", "tmp", "log", "cfg",
    # Tech / dev
    "api", "src", "dev", "img", "app", "web", "doc", "cli", "git", "npm",
    "aws", "ssh", "dns", "vpn", "ssl", "url", "uri", "sdk", "jwt", "rss",
    "ftp", "cms", "erp", "seo", "bot", "cpu", "ram", "usb", "ocr", "llm",
    "gpt", "mvc", "e2e", "ops", "hub", "env", "sys", "lib", "pub", "dom",
    "nlp", "nav", "ios", "mac", "win", "vue", "pip", "cmd", "bin", "std",
    # Business / projet
    "pro", "mvp", "rdv", "bdd", "pay", "tva", "roi", "job", "kdp", "art",
    "bio", "eco", "pme", "sms", "vip", "diy", "ltd", "inc", "sas", "btc",
    "eur", "usd", "ceo", "kpi", "ads", "crm", "ovh", "sfr",
    # Utiles
    "bof", "tag", "iso", "geo", "zen", "age", "loi", "rib", "eft",
}

# ── Filtres anti-bruit ───────────────────────────────

TAG_MAX_LENGTH = 30  # Au-delà, c'est du bruit (noms de tests, hash, etc.)

NOISE_PREFIXES = ("test_",)  # Noms de fonctions de test Python

# Chemins à exclure du catalogue (source maps, caches, dépendances minifiées)
EXCLUDED_PATH_PATTERNS = (
    "/cache/", "/Cache/", "/dist/", "/vendor/",
    "/__pycache__/", "/node_modules/",
    "/.git/", "/.Trash/",
)
EXCLUDED_EXTENSIONS = {".map"}


def normalize_tag(word):
    """Normalise un mot vers sa racine (stemming français).

    "chercher", "cherche", "cherché" → "cherch"
    "meilleur", "meilleurs" → "meilleur"

    Réduit les déclinaisons pour améliorer la recherche.
    """
    if not STEMMING_ENABLED or not word:
        return word.lower()
    # Garder les mots techniques intacts (extensions, acronymes)
    if len(word) == 3 and word.lower() in TAGS_3_WHITELIST:
        return word.lower()
    if word.isupper() and len(word) <= 5:  # Acronymes courts (API, HTML)
        return word.lower()
    return _stemmer.stemWord(word.lower())


def is_valid_tag(tag):
    """Vérifie qu'un tag est valide (pas de bruit).

    Filtre centralisé utilisé par tous les scripts d'indexation.
    """
    if not tag:
        return False
    # Rejeter les tags avec des caractères non-alphabétiques (sauf accents français)
    if not all(c.isalpha() or c in 'àâäéèêëïîôùûüÿçœæ' for c in tag):
        return False
    if len(tag) < 3:
        return False
    if len(tag) > TAG_MAX_LENGTH:
        return False
    if tag in STOP_WORDS:
        return False
    if len(tag) == 3 and tag not in TAGS_3_WHITELIST:
        return False
    if any(tag.startswith(p) for p in NOISE_PREFIXES):
        return False
    # Rejeter les mots avec des chiffres collés (sublym72, lns3...)
    # sauf les acronymes techniques purs (mp4, h264, utf8...)
    if any(c.isdigit() for c in tag):
        # Autoriser si c'est entièrement alphanum court et dans la whitelist
        if len(tag) <= 5 and tag in TAGS_3_WHITELIST:
            return True
        return False
    return True


def should_index_path(rel_path):
    """Vérifie qu'un chemin ne fait pas partie des exclusions."""
    path_lower = rel_path.lower()
    for pattern in EXCLUDED_PATH_PATTERNS:
        if pattern.lower() in path_lower:
            return False
    return True


# Délimiteurs pour split de texte en mots
SPLIT_PATTERN = re.compile(r'[-_.,;:!?()\[\]{}"\'\/\\@#&+=<>|~`\s\d]+')


# ── Helpers ──────────────────────────────────────────

def get_db(path=None):
    """Connexion SQLite avec WAL mode."""
    conn = sqlite3.connect(path or DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def filter_adjectives(words):
    """Filtre les adjectifs d'une liste de mots via POS tagging.

    Retourne uniquement les mots qui ne sont PAS des adjectifs (ADJ).
    Si POS tagging désactivé, retourne tous les mots.
    """
    if not POS_TAGGING_ENABLED or not _nlp or not words:
        return words

    # Traiter par batch (plus efficace)
    text = " ".join(words)
    doc = _nlp(text)

    # Filtrer : garder tout SAUF les ADJ
    filtered = []
    for token in doc:
        # ADJ = adjectif, DET = déterminant (le, la, un...)
        if token.pos_ not in ('ADJ', 'DET'):
            filtered.append(token.text)

    return filtered


def extract_keywords(text, min_len=3, stop_words=None):
    """Extrait les mots-clés d'un texte via is_valid_tag() + stemming + filtrage adjectifs.

    Retourne une liste de tuples (original, normalized).
    Pour chaque forme normalisée, on garde la première occurrence originale.
    """
    # Étape 1 : Collecter tous les mots valides
    valid_words = []
    for w in SPLIT_PATTERN.split(text.lower()):
        if is_valid_tag(w):
            valid_words.append(w)

    # Étape 2 : Filtrer les adjectifs via POS tagging
    filtered_words = filter_adjectives(valid_words)

    # Étape 3 : Normaliser et dédupliquer
    seen = {}  # normalized -> original
    for w in filtered_words:
        normalized = normalize_tag(w)
        if normalized not in seen:
            seen[normalized] = w

    return [(original, normalized) for normalized, original in seen.items()]


def extract_frequent_keywords(text, min_len=3, min_count=2, top_n=30, stop_words=None):
    """Extrait les mots-clés fréquents d'un texte long (transcription, body...).

    Retourne une liste de tuples (original, normalized) triés par fréquence décroissante.
    Pour chaque forme normalisée, on garde la première occurrence originale.
    """
    seen = {}  # normalized -> original
    normalized_words = []
    for w in SPLIT_PATTERN.split(text.lower()):
        if is_valid_tag(w):
            normalized = normalize_tag(w)
            if normalized not in seen:
                seen[normalized] = w
            normalized_words.append(normalized)

    counts = Counter(normalized_words)
    return [(seen[normalized], normalized) for normalized, c in counts.most_common(top_n) if c >= min_count]
