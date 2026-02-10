#!/usr/bin/env python3
"""
BIG_BOFF Search — Transcriptions YouTube
Récupère les sous-titres des vidéos YouTube et crée des tags depuis le contenu.
Module autonome : utilisable en CLI ou en import.

Usage :
    python3 youtube_transcripts.py              # Toutes les vidéos sans transcription
    python3 youtube_transcripts.py --id 5       # Une seule vidéo
    python3 youtube_transcripts.py --force      # Re-traiter même si déjà fait
"""

import re
import sys
import time

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    IpBlocked,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
)

# Pause entre requêtes YouTube (secondes) pour éviter le rate limit
REQUEST_DELAY = 2

from config import (
    DB_PATH,
    ID_OFFSET_VIDEO,
    extract_frequent_keywords,
    get_db,
)

# Langues préférées (ordre de priorité)
PREFERRED_LANGS = ["fr", "en"]


# ── API publique ─────────────────────────────────────

def extract_video_id(url):
    """Extrait le video_id YouTube depuis une URL (divers formats)."""
    patterns = [
        r"(?:youtube\.com/watch\?.*v=|youtu\.be/|youtube\.com/shorts/|youtube\.com/embed/)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def get_transcript(video_url, langs=None):
    """Récupère la transcription brute d'une vidéo YouTube.

    Args:
        video_url: URL YouTube (tout format)
        langs: liste de langues préférées (défaut: ["fr", "en"])

    Returns:
        str: texte de la transcription, ou "" si indisponible
    """
    vid = extract_video_id(video_url)
    if not vid:
        return ""

    if langs is None:
        langs = PREFERRED_LANGS

    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(vid, languages=langs)
        return " ".join(snippet.text for snippet in transcript.snippets)
    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable):
        return ""
    except (IpBlocked, RequestBlocked) as e:
        raise  # Remonter pour arrêter le batch
    except Exception:
        return ""


def extract_tags_from_transcript(text, top_n=30, min_count=2):
    """Extrait les mots-clés fréquents d'une transcription.

    Returns:
        list[str]: tags triés par fréquence
    """
    if not text or len(text) < 20:
        return []
    return extract_frequent_keywords(text, min_len=3, min_count=min_count, top_n=top_n)


# ── Traitement DB ────────────────────────────────────

def process_single_video(video_id, db_path=None, force=False):
    """Traite une seule vidéo : fetch transcription + crée tags.

    Returns:
        dict: {"id": int, "title": str, "transcript_len": int, "tags_added": int}
    """
    conn = get_db(db_path)
    c = conn.cursor()

    c.execute("SELECT id, url, title, transcript FROM videos WHERE id = ?", (video_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return {"id": video_id, "error": "vidéo introuvable"}

    vid_id, url, title, existing_transcript = row

    # Déjà traitée ?
    if existing_transcript is not None and not force:
        conn.close()
        return {"id": vid_id, "title": title, "transcript_len": len(existing_transcript),
                "tags_added": 0, "skipped": True}

    # Fetch transcription
    text = get_transcript(url)

    # Ne pas écraser une transcription existante par du vide (rate limit, etc.)
    if not text and existing_transcript:
        text = existing_transcript
    else:
        # Sauvegarder (vide = pas de sous-titres dispo, NULL = pas encore tenté)
        c.execute("UPDATE videos SET transcript = ? WHERE id = ?", (text, vid_id))

    # Extraire et ajouter les tags
    tags_added = 0
    if text:
        tags = extract_tags_from_transcript(text)
        item_id = -(vid_id + ID_OFFSET_VIDEO)
        for tag in tags:
            try:
                c.execute("INSERT INTO tags (item_id, tag) VALUES (?, ?)", (item_id, tag))
                tags_added += 1
            except Exception:
                pass  # Tag déjà existant

    conn.commit()
    conn.close()
    return {"id": vid_id, "title": title, "transcript_len": len(text),
            "tags_added": tags_added, "skipped": False}


def process_all_videos(db_path=None, force=False):
    """Traite toutes les vidéos YouTube sans transcription.

    Returns:
        dict: statistiques globales
    """
    conn = get_db(db_path)
    c = conn.cursor()

    # Ajouter la colonne transcript si elle n'existe pas
    try:
        c.execute("ALTER TABLE videos ADD COLUMN transcript TEXT DEFAULT NULL")
        conn.commit()
    except Exception:
        pass  # Colonne existe déjà

    # Sélectionner les vidéos YouTube à traiter
    if force:
        c.execute("SELECT id, url, title FROM videos WHERE platform = 'youtube'")
    else:
        c.execute("SELECT id, url, title FROM videos WHERE platform = 'youtube' AND transcript IS NULL")

    videos = c.fetchall()
    conn.close()

    total = len(videos)
    if total == 0:
        print("Aucune vidéo YouTube à traiter.")
        return {"total": 0, "transcribed": 0, "failed": 0, "tags_added": 0}

    print(f"\n{'='*60}")
    print(f"Transcriptions YouTube — {total} vidéo(s) à traiter")
    print(f"{'='*60}\n")

    transcribed = 0
    failed = 0
    total_tags = 0

    for i, (vid_id, url, title) in enumerate(videos, 1):
        print(f"[{i}/{total}] {title or url}...", end=" ", flush=True)

        try:
            result = process_single_video(vid_id, db_path, force=True)
        except (IpBlocked, RequestBlocked):
            print("BLOQUÉ par YouTube (IP ban)")
            print(f"\nArrêt : YouTube bloque les requêtes. Réessayez dans 1-2h.")
            print(f"Progression : {transcribed} transcriptions récupérées avant blocage.")
            break

        if result.get("transcript_len", 0) > 0:
            transcribed += 1
            total_tags += result["tags_added"]
            print(f"OK ({result['transcript_len']} chars, {result['tags_added']} tags)")
        else:
            failed += 1
            print("pas de sous-titres")

        # Pause entre requêtes pour éviter le rate limit
        if i < total:
            time.sleep(REQUEST_DELAY)

    print(f"\n{'='*60}")
    print(f"Résultat : {transcribed}/{total} transcriptions récupérées")
    print(f"Tags ajoutés : {total_tags}")
    if failed:
        print(f"Sans sous-titres : {failed}")
    print(f"{'='*60}\n")

    return {"total": total, "transcribed": transcribed, "failed": failed, "tags_added": total_tags}


def retag_all_videos(db_path=None):
    """Re-tague toutes les vidéos depuis les transcriptions déjà stockées en DB.

    Utile après mise à jour des STOP_WORDS, sans re-fetcher YouTube.
    """
    conn = get_db(db_path)
    c = conn.cursor()

    c.execute("SELECT id, title, transcript FROM videos WHERE transcript IS NOT NULL AND transcript != ''")
    videos = c.fetchall()

    if not videos:
        print("Aucune transcription en base.")
        conn.close()
        return

    print(f"\nRe-tagging {len(videos)} vidéo(s) depuis les transcriptions stockées...\n")

    total_tags = 0
    for vid_id, title, transcript in videos:
        item_id = -(vid_id + ID_OFFSET_VIDEO)
        # Supprimer les anciens tags de transcription (garder "video", plateforme, mots du titre)
        # On supprime tous les tags et on recrée depuis la transcription
        # Récupérer les tags de base (non-transcription) pour les préserver
        c.execute("SELECT tag FROM tags WHERE item_id = ?", (item_id,))
        old_tags = {row[0] for row in c.fetchall()}

        new_tags = set(extract_tags_from_transcript(transcript))
        # Tags de base à préserver (existants qui ne viennent pas de la transcription)
        # On remplace tout : supprimer puis réinsérer base + transcription
        c.execute("DELETE FROM tags WHERE item_id = ?", (item_id,))

        # Réinsérer : garder les tags originaux (video, plateforme, mots du titre)
        # + nouveaux tags de transcription
        all_tags = old_tags | new_tags
        for tag in all_tags:
            try:
                c.execute("INSERT INTO tags (item_id, tag) VALUES (?, ?)", (item_id, tag))
            except Exception:
                pass
        added = len(new_tags - old_tags)
        removed = len(old_tags - all_tags)
        total_tags += len(new_tags)
        print(f"  {title}: {len(new_tags)} tags transcription")

    conn.commit()
    conn.close()
    print(f"\nTerminé. {total_tags} tags de transcription au total.")


# ── CLI ──────────────────────────────────────────────

def main():
    force = "--force" in sys.argv
    retag = "--retag" in sys.argv

    # Mode retag : re-tagger depuis transcriptions stockées
    if retag:
        retag_all_videos()
        return

    # Mode single video
    if "--id" in sys.argv:
        idx = sys.argv.index("--id")
        if idx + 1 < len(sys.argv):
            vid_id = int(sys.argv[idx + 1])
            try:
                result = process_single_video(vid_id, force=force)
            except (IpBlocked, RequestBlocked):
                print(f"YouTube bloque les requêtes (IP ban). Réessayez dans 1-2h.")
                return
            if result.get("skipped"):
                print(f"Vidéo {vid_id} déjà traitée ({result['transcript_len']} chars). Utilisez --force pour re-traiter.")
            elif result.get("error"):
                print(f"Erreur : {result['error']}")
            else:
                print(f"Vidéo {vid_id} : {result['transcript_len']} chars, {result['tags_added']} tags ajoutés")
        else:
            print("Usage : python3 youtube_transcripts.py --id <video_id>")
        return

    # Mode batch (toutes les vidéos)
    process_all_videos(force=force)


if __name__ == "__main__":
    main()
