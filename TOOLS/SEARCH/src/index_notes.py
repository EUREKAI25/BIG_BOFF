#!/usr/bin/env python3
"""
BIG_BOFF Search — Indexation des Apple Notes
Lit les fichiers exportés, les insère dans catalogue.db avec tags.
"""

import sqlite3
import re
import os
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
    METADATA_FETCH_AVAILABLE = True
except ImportError:
    METADATA_FETCH_AVAILABLE = False
    print("⚠️  requests/beautifulsoup4 non installés - métadonnées URL désactivées")
    print("   pip install requests beautifulsoup4")

DB_PATH = "/Users/nathalie/Dropbox/____BIG_BOFF___/TOOLS/MAINTENANCE/catalogue.db"
EXPORT_DIR = "/tmp/apple_notes_export"

STOP_WORDS = {
    "", "a", "an", "the", "de", "du", "le", "la", "les", "un", "une", "des",
    "et", "ou", "en", "au", "aux", "par", "pour", "sur", "dans", "avec",
    "est", "sont", "ont", "fait", "mais", "plus", "pas", "que", "qui",
    "mon", "ton", "son", "mes", "tes", "ses", "notre", "votre", "leur",
    "cette", "ces", "tout", "tous", "toute", "toutes", "très",
    "bon", "bien", "merci", "bonjour", "bonne",
    "http", "https", "www", "com", "org", "net", "fr",
    "big", "boff", "big_boff",
    # Paramètres URL de tracking (Facebook, Google, Microsoft, etc.)
    "fbclid", "mibextid", "igshid", "igsh",
    "gclid", "gbraid", "wbraid", "msclkid",
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
    "ref", "source", "campaign", "medium",
}


def setup_notes_table(conn):
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            folder TEXT,
            date_modif TEXT,
            body TEXT,
            UNIQUE(title, date_modif)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_notes_title ON notes(title)")
    conn.commit()


def setup_videos_table(conn):
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            platform TEXT,
            title TEXT,
            source_note_id INTEGER,
            date_added TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_videos_url ON videos(url)")
    conn.commit()


def setup_url_cache_table(conn):
    """Table de cache pour les métadonnées d'URLs.

    Évite de refetch les mêmes URLs à chaque indexation.
    """
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS url_metadata_cache (
            url TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            keywords TEXT,
            fetched_at TEXT,
            fetch_success INTEGER DEFAULT 1
        )
    """)
    conn.commit()


# ── Patterns vidéo ──────────────────────────────────

VIDEO_PATTERNS = [
    # YouTube
    (r'https?://(?:www\.)?youtube\.com/watch\?[^\s]*v=[\w-]+[^\s]*', "youtube"),
    (r'https?://youtu\.be/[\w-]+[^\s]*', "youtube"),
    (r'https?://(?:www\.)?youtube\.com/shorts/[\w-]+[^\s]*', "youtube"),
    (r'https?://(?:www\.)?youtube\.com/embed/[\w-]+[^\s]*', "youtube"),
    # Facebook (vidéos, reels, share, watch, mobile)
    (r'https?://(?:www\.)?facebook\.com/[^\s]*/videos/[^\s]+', "facebook"),
    (r'https?://(?:www\.)?facebook\.com/watch[^\s]*', "facebook"),
    (r'https?://(?:www\.)?facebook\.com/share/[rv]/[^\s]+', "facebook"),
    (r'https?://m\.facebook\.com/story\.php[^\s]+', "facebook"),
    (r'https?://fb\.watch/[^\s]+', "facebook"),
    # Vimeo
    (r'https?://(?:www\.)?vimeo\.com/\d+[^\s]*', "vimeo"),
    # Dailymotion
    (r'https?://(?:www\.)?dailymotion\.com/video/[\w-]+[^\s]*', "dailymotion"),
    (r'https?://dai\.ly/[\w-]+[^\s]*', "dailymotion"),
    # Instagram Reels
    (r'https?://(?:www\.)?instagram\.com/reel/[\w-]+[^\s]*', "instagram"),
    # TikTok (desktop + mobile)
    (r'https?://(?:www\.)?tiktok\.com/@[^\s]*/video/\d+[^\s]*', "tiktok"),
    (r'https?://vm\.tiktok\.com/[\w-]+[^\s]*', "tiktok"),
]


def extract_video_urls(body):
    """Extrait les URLs vidéo d'un texte. Retourne [(url, platform), ...]."""
    if not body:
        return []
    results = []
    seen = set()
    for pattern, platform in VIDEO_PATTERNS:
        for match in re.finditer(pattern, body, re.IGNORECASE):
            url = match.group(0).rstrip(".,;:!?)>]\"'")
            if url not in seen:
                seen.add(url)
                results.append((url, platform))
    return results


def fetch_youtube_title(url):
    """Récupère le titre d'une vidéo YouTube via oEmbed (gratuit, sans clé API)."""
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(url, safe='')}&format=json"
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("title", "")
    except Exception:
        return ""


def fetch_url_metadata(url, conn=None, use_cache=True):
    """Récupère les métadonnées d'une URL (title, description, keywords).

    Args:
        url: URL to fetch
        conn: SQLite connection (optionnel, pour le cache)
        use_cache: Si True, utilise le cache DB

    Retourne un dict avec 'title', 'description', 'keywords'.
    Gratuit, illimité, scalable.
    """
    if not METADATA_FETCH_AVAILABLE:
        return {'title': '', 'description': '', 'keywords': ''}

    # Chercher dans le cache
    if use_cache and conn:
        c = conn.cursor()
        c.execute("SELECT title, description, keywords, fetch_success FROM url_metadata_cache WHERE url = ?", (url,))
        row = c.fetchone()
        if row:
            # Déjà en cache
            if row[3] == 0:  # fetch_success = 0 → échec précédent, ne pas réessayer
                return {'title': '', 'description': '', 'keywords': ''}
            return {'title': row[0] or '', 'description': row[1] or '', 'keywords': row[2] or ''}

    try:
        # Headers pour éviter les blocages bot
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        # Timeout court pour ne pas bloquer
        resp = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
        if resp.status_code != 200:
            return {'title': '', 'description': '', 'keywords': ''}

        soup = BeautifulSoup(resp.text, 'html.parser')

        # Title : OpenGraph > Twitter Card > <title>
        title = ''
        og_title = soup.find('meta', property='og:title')
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        html_title = soup.find('title')

        if og_title and og_title.get('content'):
            title = og_title.get('content')
        elif twitter_title and twitter_title.get('content'):
            title = twitter_title.get('content')
        elif html_title and html_title.string:
            title = html_title.string

        # Description : OpenGraph > Twitter Card > meta description
        description = ''
        og_desc = soup.find('meta', property='og:description')
        twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
        meta_desc = soup.find('meta', attrs={'name': 'description'})

        if og_desc and og_desc.get('content'):
            description = og_desc.get('content')
        elif twitter_desc and twitter_desc.get('content'):
            description = twitter_desc.get('content')
        elif meta_desc and meta_desc.get('content'):
            description = meta_desc.get('content')

        # Keywords
        keywords = ''
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = meta_keywords.get('content')

        result = {
            'title': title.strip() if title else '',
            'description': description.strip() if description else '',
            'keywords': keywords.strip() if keywords else ''
        }

        # Sauvegarder dans le cache
        if conn:
            c = conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO url_metadata_cache (url, title, description, keywords, fetched_at, fetch_success)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (url, result['title'], result['description'], result['keywords'], datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()

        return result

    except Exception as e:
        # Sauvegarder l'échec dans le cache pour ne pas réessayer
        if conn:
            c = conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO url_metadata_cache (url, title, description, keywords, fetched_at, fetch_success)
                VALUES (?, '', '', '', ?, 0)
            """, (url, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
        # Silencieux : ne pas bloquer l'indexation si une URL échoue
        return {'title': '', 'description': '', 'keywords': ''}


def extract_tags_from_metadata(metadata):
    """Extrait des tags pertinents depuis les métadonnées d'une page.

    Args:
        metadata: dict avec 'title', 'description', 'keywords'

    Returns:
        set de tags
    """
    tags = set()

    # Keywords (déjà des mots-clefs fournis par la page)
    if metadata.get('keywords'):
        for word in re.split(r'[,;]+', metadata['keywords']):
            word = word.strip().lower()
            if len(word) >= 3 and word not in STOP_WORDS and word.replace('-', '').replace('_', '').isalpha():
                tags.add(word)

    # Title
    if metadata.get('title'):
        for word in re.split(r'[\s\-_.,;:!?()\[\]{}"/\'|]+', metadata['title'].lower()):
            if len(word) >= 3 and word not in STOP_WORDS and word.isalpha():
                tags.add(word)

    # Description - mots fréquents seulement
    if metadata.get('description'):
        words = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', metadata['description'].lower())
        freq = {}
        for w in words:
            if w not in STOP_WORDS:
                freq[w] = freq.get(w, 0) + 1
        # Top 10 mots (min 2 occurrences)
        for word, count in sorted(freq.items(), key=lambda x: -x[1])[:10]:
            if count >= 2:
                tags.add(word)

    return tags


def extract_note_tags(title, folder, body, conn=None):
    tags = set()
    tags.add("note")

    # Folder
    if folder:
        for word in re.split(r'[\s\-_]+', folder.lower()):
            if len(word) >= 3 and word not in STOP_WORDS:
                tags.add(word)

    # Titre
    if title:
        for word in re.split(r'[\s\-_.,;:!?()[\]{}"/\']+', title.lower()):
            if len(word) >= 3 and word not in STOP_WORDS and word.isalpha():
                tags.add(word)

    # Corps — mots fréquents
    if body:
        words = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', body.lower())
        freq = {}
        for w in words:
            if w not in STOP_WORDS and len(w) >= 3:
                freq[w] = freq.get(w, 0) + 1
        # Top 20 mots (min 2 occurrences)
        for word, count in sorted(freq.items(), key=lambda x: -x[1])[:20]:
            if count >= 2:
                tags.add(word)

        # Détecter les URLs YouTube
        if "youtube" in body.lower() or "youtu.be" in body.lower():
            tags.add("youtube")
            tags.add("video")

        # Détecter les URLs - extraire métadonnées de la page
        urls = re.findall(r'https?://[^\s]+', body)
        if urls:
            tags.add("lien")
            for url in urls:
                # Extraire uniquement le domaine principal (ex: facebook, youtube, instagram)
                match = re.search(r'://(?:www\.)?([^./]+)', url)
                if match:
                    domain_main = match.group(1).lower()
                    # Garder seulement les domaines connus/pertinents
                    if domain_main in {'facebook', 'youtube', 'instagram', 'twitter', 'linkedin',
                                      'github', 'medium', 'substack', 'notion', 'tiktok', 'vimeo'}:
                        tags.add(domain_main)

                # Fetch métadonnées de la page pour extraire les vrais tags
                # (title, description, keywords de la page plutôt que parser l'URL)
                metadata = fetch_url_metadata(url, conn=conn)
                if metadata:
                    url_tags = extract_tags_from_metadata(metadata)
                    tags.update(url_tags)

    return tags


def parse_exported_notes():
    """Parse les fichiers exportés par AppleScript."""
    notes = []
    for filename in sorted(os.listdir(EXPORT_DIR)):
        if not filename.endswith('.txt'):
            continue
        filepath = os.path.join(EXPORT_DIR, filename)
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Découper par ---END---
        entries = content.split("---END---")
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue

            title = ""
            date = ""
            body = ""

            lines = entry.split('\n')
            body_lines = []
            in_body = False
            for line in lines:
                if line.startswith("TITLE:"):
                    title = line[6:].strip()
                elif line.startswith("DATE:"):
                    date = line[5:].strip()
                elif line.startswith("BODY:"):
                    body = line[5:].strip()
                    in_body = True
                elif in_body:
                    body_lines.append(line)

            if body_lines:
                body = body + "\n" + "\n".join(body_lines)

            if title or body:
                notes.append({
                    "title": title,
                    "date": date,
                    "body": body.strip(),
                })

    return notes


def extract_videos_from_notes(conn):
    """Parcourt toutes les notes, extrait les URLs vidéo et les insère dans la table videos."""
    setup_videos_table(conn)
    c = conn.cursor()

    c.execute("SELECT id, title, body, date_modif FROM notes")
    all_notes = c.fetchall()
    print(f"Parcours de {len(all_notes)} notes pour extraction vidéo...")

    inserted = 0
    skipped = 0
    tag_batch = []
    youtube_titles_fetched = 0

    for note_id, note_title, body, date_modif in all_notes:
        if not body:
            continue
        urls = extract_video_urls(body)
        for url, platform in urls:
            # Insérer la vidéo (IGNORE si URL déjà en base)
            try:
                # Tenter de récupérer le titre pour YouTube
                title = ""
                if platform == "youtube":
                    title = fetch_youtube_title(url)
                    if title:
                        youtube_titles_fetched += 1
                if not title:
                    # Utiliser le titre de la note comme contexte
                    title = note_title or ""

                c.execute("""
                    INSERT OR IGNORE INTO videos (url, platform, title, source_note_id, date_added)
                    VALUES (?, ?, ?, ?, ?)
                """, (url, platform, title, note_id, datetime.now().strftime("%Y-%m-%d %H:%M")))

                video_id = c.lastrowid
                if not video_id:
                    skipped += 1
                    continue

                # Tags pour cette vidéo : -(video_id + 400000)
                vid_tag_id = -(video_id + 400000)
                tags = {"video", platform}
                # Mots du titre vidéo
                if title:
                    for word in re.split(r'[\s\-_.,;:!?()\[\]{}"/\']+', title.lower()):
                        if len(word) >= 3 and word not in STOP_WORDS and word.isalpha():
                            tags.add(word)
                # Mots du titre de la note (contexte)
                if note_title and note_title != title:
                    for word in re.split(r'[\s\-_.,;:!?()\[\]{}"/\']+', note_title.lower()):
                        if len(word) >= 3 and word not in STOP_WORDS and word.isalpha():
                            tags.add(word)

                for tag in tags:
                    tag_batch.append((vid_tag_id, tag))

                inserted += 1
                if inserted % 20 == 0:
                    print(f"  {inserted} vidéos extraites...")

            except Exception as e:
                print(f"  Erreur pour {url}: {e}")
                skipped += 1

    if tag_batch:
        c.executemany("INSERT INTO tags (item_id, tag) VALUES (?, ?)", tag_batch)
    conn.commit()

    # Stats
    c.execute("SELECT COUNT(*) FROM videos")
    total_videos = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tags WHERE item_id < -400000")
    total_video_tags = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT platform) FROM videos")
    platforms = c.fetchone()[0]

    # Détail par plateforme
    c.execute("SELECT platform, COUNT(*) FROM videos GROUP BY platform ORDER BY COUNT(*) DESC")
    platform_detail = c.fetchall()

    print(f"\n=== RÉSULTAT EXTRACTION VIDÉOS ===")
    print(f"Vidéos extraites : {inserted}")
    print(f"Déjà en base : {skipped}")
    print(f"Titres YouTube récupérés : {youtube_titles_fetched}")
    print(f"Total vidéos en base : {total_videos}")
    print(f"Tags vidéo : {total_video_tags}")
    print(f"Plateformes : {platforms}")
    for plat, cnt in platform_detail:
        print(f"  {plat}: {cnt}")


def main():
    # Mode --extract-videos
    if "--extract-videos" in sys.argv:
        print("=== BIG_BOFF Search — Extraction vidéos des notes ===")
        print(f"Base : {DB_PATH}\n")
        conn = sqlite3.connect(DB_PATH)
        extract_videos_from_notes(conn)
        conn.close()
        print("\nTerminé !")
        return

    print("=== BIG_BOFF Search — Indexation des Apple Notes ===")
    print(f"Base : {DB_PATH}\n")

    notes = parse_exported_notes()
    print(f"Notes exportées : {len(notes)}")

    conn = sqlite3.connect(DB_PATH)
    setup_notes_table(conn)
    setup_url_cache_table(conn)
    c = conn.cursor()

    indexed = 0
    skipped = 0
    tag_batch = []

    for note in notes:
        title = note["title"]
        date = note["date"]
        body = note["body"]

        # Insérer la note
        try:
            c.execute("""
                INSERT OR IGNORE INTO notes (title, date_modif, body)
                VALUES (?, ?, ?)
            """, (title, date, body))
            note_id = c.lastrowid
            if not note_id:
                skipped += 1
                continue
        except Exception:
            skipped += 1
            continue

        # Tags
        tags = extract_note_tags(title, "", body, conn=conn)
        # Convention : note_id négatif = -(note.id + 200000)
        tag_id = -(note_id + 200000)
        for tag in tags:
            tag_batch.append((tag_id, tag))

        indexed += 1

    if tag_batch:
        c.executemany("INSERT INTO tags (item_id, tag) VALUES (?, ?)", tag_batch)
        conn.commit()

    # Stats
    c.execute("SELECT COUNT(*) FROM notes")
    total_notes = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tags WHERE item_id < -200000 AND item_id >= -300000")
    total_note_tags = c.fetchone()[0]

    print(f"\n=== RÉSULTAT ===")
    print(f"Notes indexées : {indexed}")
    print(f"Déjà en base : {skipped}")
    print(f"Total notes en base : {total_notes}")
    print(f"Tags notes : {total_note_tags}")

    conn.close()
    print("\nTerminé !")


if __name__ == "__main__":
    main()
