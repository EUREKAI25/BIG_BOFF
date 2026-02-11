#!/usr/bin/env python3
"""
BIG_BOFF Search — Module Événements (standalone)
Gestion d'événements avec récurrence, tags et vues temporelles.

Module autonome : importable + CLI.

Usage CLI :
    python3 events.py add "Anniversaire Maman" --date 2026-03-15 --tags "famille,anniversaire" --recurrence yearly
    python3 events.py upcoming              # vue jour (défaut)
    python3 events.py upcoming --week       # vue semaine
    python3 events.py upcoming --month      # vue mois
    python3 events.py list --from 2026-02-01 --to 2026-02-28
    python3 events.py delete --id 3

API importable :
    from events import add_event, get_upcoming, list_events, get_event
"""

import sys
import re
from datetime import datetime, timedelta
from calendar import monthrange

from config import (
    DB_PATH,
    ID_OFFSET_EVENT,
    STOP_WORDS,
    extract_keywords,
    get_db,
)

# Noms de mois en français pour les tags
MOIS_FR = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril",
    5: "mai", 6: "juin", 7: "juillet", 8: "août",
    9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre",
}

JOURS_FR = {
    0: "lundi", 1: "mardi", 2: "mercredi", 3: "jeudi",
    4: "vendredi", 5: "samedi", 6: "dimanche",
}

RECURRENCE_LABELS = {
    "none": "",
    "daily": "chaque jour",
    "weekly": "chaque semaine",
    "monthly": "chaque mois",
    "yearly": "chaque année",
}


# ── Table ─────────────────────────────────────────────

def setup_events_table(conn):
    """Crée la table events si elle n'existe pas."""
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            date_start TEXT NOT NULL,
            date_end TEXT,
            location TEXT DEFAULT '',
            tags_raw TEXT DEFAULT '',
            recurrence TEXT DEFAULT 'none',
            recurrence_interval INTEGER DEFAULT 1,
            recurrence_count INTEGER,
            recurrence_end TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON events(date_start)")

    # Colonnes ajoutées pour les sous-types (ALTER TABLE idempotent)
    for col, default in [("subtype", "'generic'"), ("contact_id", "NULL"), ("lieu_id", "NULL")]:
        try:
            c.execute(f"ALTER TABLE events ADD COLUMN {col} TEXT DEFAULT {default}" if col == "subtype"
                      else f"ALTER TABLE events ADD COLUMN {col} INTEGER DEFAULT {default}")
        except Exception:
            pass  # colonne existe déjà

    conn.commit()


# ── Helpers ───────────────────────────────────────────

def _parse_dt(s):
    """Parse une date string en datetime. Accepte YYYY-MM-DD ou YYYY-MM-DD HH:MM."""
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _format_date_fr(dt):
    """Formate une date en français : 'lundi 15 mars 2026 à 10:00'."""
    jour = JOURS_FR[dt.weekday()]
    mois = MOIS_FR[dt.month]
    s = f"{jour} {dt.day} {mois} {dt.year}"
    if dt.hour or dt.minute:
        s += f" à {dt.hour:02d}:{dt.minute:02d}"
    return s


def _row_to_dict(row):
    """Convertit un tuple DB en dict événement."""
    if not row:
        return None
    d = {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "date_start": row[3],
        "date_end": row[4],
        "location": row[5],
        "tags_raw": row[6],
        "recurrence": row[7],
        "recurrence_interval": row[8],
        "recurrence_count": row[9],
        "recurrence_end": row[10],
        "created_at": row[11],
        "updated_at": row[12],
    }
    # Colonnes ajoutées (peuvent ne pas exister dans les anciennes lignes)
    if len(row) > 13:
        d["subtype"] = row[13] or "generic"
    else:
        d["subtype"] = "generic"
    if len(row) > 14:
        d["contact_id"] = row[14]
    else:
        d["contact_id"] = None
    if len(row) > 15:
        d["lieu_id"] = row[15]
    else:
        d["lieu_id"] = None
    return d


def _event_tags(title, date_start, tags_raw="", subtype="generic"):
    """Génère les tags automatiques pour un événement.

    Retourne une liste de tuples (tag_display, tag_normalized).
    """
    from config import normalize_tag

    seen = {}  # normalized -> display (pour éviter les doublons)

    # Tag principal
    seen["event"] = "event"

    # Sous-type
    if subtype and subtype != "generic":
        seen[subtype] = subtype  # anniversaire, rendez_vous

    # Mots du titre
    for tag_display, tag_normalized in extract_keywords(title):
        if tag_normalized not in seen:
            seen[tag_normalized] = tag_display

    # Tags manuels
    if tags_raw:
        for t in tags_raw.split(","):
            t = t.strip().lower()
            if t and t not in STOP_WORDS:
                normalized = normalize_tag(t)
                if normalized not in seen:
                    seen[normalized] = t

    # Mois + année de la date
    dt = _parse_dt(date_start)
    if dt:
        mois = MOIS_FR.get(dt.month)
        if mois:
            seen[mois] = mois
        year = str(dt.year)
        seen[year] = year

    return [(display, normalized) for normalized, display in seen.items()]


def _save_tags(conn, event_id, tags):
    """Insère les tags d'un événement dans la table tags.

    Args:
        tags: liste de tuples (tag_display, tag_normalized)
    """
    c = conn.cursor()
    item_id = -(event_id + ID_OFFSET_EVENT)
    for tag_display, tag_normalized in tags:
        try:
            c.execute("INSERT INTO tags (item_id, tag, tag_display) VALUES (?, ?, ?)",
                      (item_id, tag_normalized, tag_display))
        except Exception:
            pass


def _delete_tags(conn, event_id):
    """Supprime tous les tags d'un événement."""
    c = conn.cursor()
    item_id = -(event_id + ID_OFFSET_EVENT)
    c.execute("DELETE FROM tags WHERE item_id = ?", (item_id,))


def _add_months(dt, months):
    """Ajoute N mois à une date, en gérant les débordements de jours."""
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


# ── Récurrence ────────────────────────────────────────

def get_occurrences(event, from_date, to_date):
    """Génère les dates d'un événement récurrent dans une période.

    Args:
        event: dict événement (depuis _row_to_dict)
        from_date: datetime début de la période
        to_date: datetime fin de la période

    Returns:
        list[datetime]: dates des occurrences dans la période, triées
    """
    dt_start = _parse_dt(event["date_start"])
    if not dt_start:
        return []

    rec = event.get("recurrence", "none")
    interval = event.get("recurrence_interval", 1) or 1
    max_count = event.get("recurrence_count")
    rec_end = _parse_dt(event.get("recurrence_end"))

    # Événement ponctuel
    if rec == "none":
        if from_date <= dt_start <= to_date:
            return [dt_start]
        return []

    occurrences = []
    current = dt_start
    count = 0

    # Générer les occurrences (max 1000 pour éviter boucle infinie)
    for _ in range(10000):
        if current > to_date:
            break
        if rec_end and current > rec_end:
            break
        if max_count and count >= max_count:
            break

        if current >= from_date:
            occurrences.append(current)

        count += 1

        # Avancer selon le type de récurrence
        if rec == "daily":
            current = current + timedelta(days=interval)
        elif rec == "weekly":
            current = current + timedelta(weeks=interval)
        elif rec == "monthly":
            current = _add_months(current, interval)
        elif rec == "yearly":
            current = _add_months(current, 12 * interval)
        else:
            break

    return occurrences


# ── CRUD ──────────────────────────────────────────────

def add_event(title, date_start, date_end=None, description="",
              location="", tags_raw="", recurrence="none",
              recurrence_interval=1, recurrence_count=None,
              recurrence_end=None, subtype="generic",
              contact_id=None, lieu_id=None, db_path=None):
    """Crée un événement et ses tags.

    Validation :
        - anniversaire : contact_id obligatoire, recurrence defaut yearly
        - rendez_vous : contact_id ET lieu_id obligatoires

    Returns:
        dict: l'événement créé (avec id)
    Raises:
        ValueError si validation échoue
    """
    # Validation sous-types
    if subtype == "anniversaire":
        if not contact_id:
            raise ValueError("Anniversaire : contact_id obligatoire")
        if recurrence == "none":
            recurrence = "yearly"
    elif subtype == "rendez_vous":
        if not contact_id:
            raise ValueError("Rendez-vous : contact_id obligatoire")
        if not lieu_id:
            raise ValueError("Rendez-vous : lieu_id obligatoire")

    conn = get_db(db_path)
    setup_events_table(conn)
    c = conn.cursor()

    c.execute("""
        INSERT INTO events (title, description, date_start, date_end, location,
                           tags_raw, recurrence, recurrence_interval,
                           recurrence_count, recurrence_end,
                           subtype, contact_id, lieu_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, description, date_start, date_end, location,
          tags_raw, recurrence, recurrence_interval,
          recurrence_count, recurrence_end,
          subtype, contact_id, lieu_id))

    event_id = c.lastrowid
    tags = _event_tags(title, date_start, tags_raw, subtype)
    _save_tags(conn, event_id, tags)

    conn.commit()
    event = get_event(event_id, db_path=db_path, _conn=conn)
    conn.close()
    return event


def update_event(event_id, db_path=None, **kwargs):
    """Modifie un événement existant.

    Args:
        event_id: ID de l'événement
        **kwargs: champs à modifier (title, date_start, description, etc.)

    Returns:
        dict: l'événement mis à jour, ou None si introuvable
    """
    allowed = {"title", "description", "date_start", "date_end", "location",
               "tags_raw", "recurrence", "recurrence_interval",
               "recurrence_count", "recurrence_end",
               "subtype", "contact_id", "lieu_id"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return get_event(event_id, db_path=db_path)

    conn = get_db(db_path)
    c = conn.cursor()

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    set_clause += ", updated_at = datetime('now','localtime')"
    values = list(updates.values()) + [event_id]

    c.execute(f"UPDATE events SET {set_clause} WHERE id = ?", values)

    # Recréer les tags
    _delete_tags(conn, event_id)
    event = get_event(event_id, db_path=db_path, _conn=conn)
    if event:
        tags = _event_tags(event["title"], event["date_start"],
                           event.get("tags_raw", ""), event.get("subtype", "generic"))
        _save_tags(conn, event_id, tags)

    conn.commit()
    conn.close()
    return event


def delete_event(event_id, db_path=None):
    """Supprime un événement et ses tags.

    Returns:
        bool: True si supprimé, False si introuvable
    """
    conn = get_db(db_path)
    c = conn.cursor()

    c.execute("SELECT id FROM events WHERE id = ?", (event_id,))
    if not c.fetchone():
        conn.close()
        return False

    _delete_tags(conn, event_id)
    c.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
    return True


def get_event(event_id, db_path=None, _conn=None):
    """Retourne un événement par son ID.

    Returns:
        dict ou None
    """
    conn = _conn or get_db(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    row = c.fetchone()
    if not _conn:
        conn.close()
    return _row_to_dict(row)


def list_events(from_date=None, to_date=None, db_path=None):
    """Liste les événements dans une période, avec expansion des récurrences.

    Args:
        from_date: str ou datetime (défaut : aujourd'hui)
        to_date: str ou datetime (défaut : +1 an)

    Returns:
        list[dict]: événements avec "occurrence_date" ajouté, triés par date
    """
    if isinstance(from_date, str):
        from_date = _parse_dt(from_date)
    if isinstance(to_date, str):
        to_date = _parse_dt(to_date)

    now = datetime.now()
    if not from_date:
        from_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if not to_date:
        to_date = from_date + timedelta(days=365)

    conn = get_db(db_path)
    setup_events_table(conn)
    c = conn.cursor()
    c.execute("SELECT * FROM events")
    rows = c.fetchall()
    conn.close()

    results = []
    for row in rows:
        event = _row_to_dict(row)
        occs = get_occurrences(event, from_date, to_date)
        for occ in occs:
            entry = dict(event)
            entry["occurrence_date"] = occ.strftime("%Y-%m-%d %H:%M")
            entry["occurrence_date_fr"] = _format_date_fr(occ)
            results.append(entry)

    results.sort(key=lambda e: e["occurrence_date"])
    return results


# ── Vue temporelle ────────────────────────────────────

def get_upcoming(mode="day", db_path=None):
    """Retourne les événements groupés par période temporelle.

    Args:
        mode: "day" | "week" | "month" | "year"

    Returns:
        dict avec 3 clés (les noms dépendent du mode), chaque valeur = liste triée
    """
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Définir les bornes selon le mode
    if mode == "day":
        end_p1 = today + timedelta(days=1)   # fin "aujourd'hui"
        end_p2 = today + timedelta(days=2)   # fin "demain"
        end_all = today + timedelta(days=90)  # horizon 3 mois
        keys = ("today", "tomorrow", "later")
        labels = ("Aujourd'hui", "Demain", "Plus tard")
    elif mode == "week":
        # Début de cette semaine (lundi)
        week_start = today - timedelta(days=today.weekday())
        end_p1 = week_start + timedelta(days=7)
        end_p2 = week_start + timedelta(days=14)
        end_all = today + timedelta(days=180)
        keys = ("this_week", "next_week", "later")
        labels = ("Cette semaine", "Semaine prochaine", "Plus tard")
    elif mode == "month":
        # Début de ce mois
        month_start = today.replace(day=1)
        next_month = _add_months(month_start, 1)
        after_next = _add_months(month_start, 2)
        end_p1 = next_month
        end_p2 = after_next
        end_all = _add_months(today, 12)
        keys = ("this_month", "next_month", "later")
        labels = ("Ce mois", "Mois prochain", "Plus tard")
    elif mode == "year":
        year_start = today.replace(month=1, day=1)
        next_year = year_start.replace(year=year_start.year + 1)
        after_next = year_start.replace(year=year_start.year + 2)
        end_p1 = next_year
        end_p2 = after_next
        end_all = after_next + timedelta(days=365)
        keys = ("this_year", "next_year", "later")
        labels = ("Cette année", "Année prochaine", "Plus tard")
    else:
        raise ValueError(f"Mode inconnu : {mode}")

    # Récupérer tous les événements dans la fenêtre
    all_events = list_events(from_date=today, to_date=end_all, db_path=db_path)

    # Répartir dans les 3 buckets
    buckets = {k: [] for k in keys}
    for ev in all_events:
        occ = _parse_dt(ev["occurrence_date"])
        if not occ:
            continue
        if occ < end_p1:
            buckets[keys[0]].append(ev)
        elif occ < end_p2:
            buckets[keys[1]].append(ev)
        else:
            buckets[keys[2]].append(ev)

    return {"groups": buckets, "keys": keys, "labels": labels}


# ── CLI ───────────────────────────────────────────────

def _cli_add(args):
    """CLI: events.py add 'titre' --date YYYY-MM-DD [options]"""
    if len(args) < 1:
        print("Usage : python3 events.py add \"Titre\" --date YYYY-MM-DD [--end YYYY-MM-DD HH:MM] "
              "[--desc \"...\"] [--loc \"...\"] [--tags \"t1,t2\"] "
              "[--recurrence daily|weekly|monthly|yearly] [--interval N] "
              "[--count N] [--rec-end YYYY-MM-DD]")
        return

    title = args[0]
    date_start = None
    date_end = None
    description = ""
    location = ""
    tags_raw = ""
    recurrence = "none"
    interval = 1
    count = None
    rec_end = None

    i = 1
    while i < len(args):
        if args[i] == "--date" and i + 1 < len(args):
            date_start = args[i + 1]
            # Vérifier si l'heure suit
            if i + 2 < len(args) and re.match(r'\d{2}:\d{2}', args[i + 2]):
                date_start += " " + args[i + 2]
                i += 1
            i += 2
        elif args[i] == "--end" and i + 1 < len(args):
            date_end = args[i + 1]
            if i + 2 < len(args) and re.match(r'\d{2}:\d{2}', args[i + 2]):
                date_end += " " + args[i + 2]
                i += 1
            i += 2
        elif args[i] == "--desc" and i + 1 < len(args):
            description = args[i + 1]
            i += 2
        elif args[i] == "--loc" and i + 1 < len(args):
            location = args[i + 1]
            i += 2
        elif args[i] == "--tags" and i + 1 < len(args):
            tags_raw = args[i + 1]
            i += 2
        elif args[i] == "--recurrence" and i + 1 < len(args):
            recurrence = args[i + 1]
            i += 2
        elif args[i] == "--interval" and i + 1 < len(args):
            interval = int(args[i + 1])
            i += 2
        elif args[i] == "--count" and i + 1 < len(args):
            count = int(args[i + 1])
            i += 2
        elif args[i] == "--rec-end" and i + 1 < len(args):
            rec_end = args[i + 1]
            i += 2
        else:
            i += 1

    if not date_start:
        print("Erreur : --date requis")
        return

    event = add_event(
        title=title,
        date_start=date_start,
        date_end=date_end,
        description=description,
        location=location,
        tags_raw=tags_raw,
        recurrence=recurrence,
        recurrence_interval=interval,
        recurrence_count=count,
        recurrence_end=rec_end,
    )

    rec_label = RECURRENCE_LABELS.get(recurrence, "")
    print(f"Événement créé (id={event['id']}) :")
    print(f"  {event['title']}")
    dt = _parse_dt(event['date_start'])
    if dt:
        print(f"  {_format_date_fr(dt)}")
    if rec_label:
        print(f"  Récurrence : {rec_label} (intervalle={interval})")
    if tags_raw:
        print(f"  Tags : {tags_raw}")


def _cli_upcoming(args):
    """CLI: events.py upcoming [--week|--month|--year]"""
    mode = "day"
    for a in args:
        if a == "--week":
            mode = "week"
        elif a == "--month":
            mode = "month"
        elif a == "--year":
            mode = "year"

    result = get_upcoming(mode=mode)
    keys = result["keys"]
    labels = result["labels"]
    groups = result["groups"]

    total = sum(len(groups[k]) for k in keys)
    if total == 0:
        print("Aucun événement à venir.")
        return

    for key, label in zip(keys, labels):
        events = groups[key]
        if not events:
            continue
        print(f"\n{'─' * 40}")
        print(f"  {label} ({len(events)})")
        print(f"{'─' * 40}")
        for ev in events:
            rec = RECURRENCE_LABELS.get(ev.get("recurrence", "none"), "")
            rec_str = f" | {rec}" if rec else ""
            print(f"  [{ev['id']}] {ev['title']}")
            print(f"       {ev['occurrence_date_fr']}{rec_str}")
            if ev.get("tags_raw"):
                print(f"       tags: {ev['tags_raw']}")
            if ev.get("location"):
                print(f"       lieu: {ev['location']}")


def _cli_list(args):
    """CLI: events.py list [--from YYYY-MM-DD] [--to YYYY-MM-DD]"""
    from_date = None
    to_date = None
    i = 0
    while i < len(args):
        if args[i] == "--from" and i + 1 < len(args):
            from_date = args[i + 1]
            i += 2
        elif args[i] == "--to" and i + 1 < len(args):
            to_date = args[i + 1]
            i += 2
        else:
            i += 1

    events = list_events(from_date=from_date, to_date=to_date)
    if not events:
        print("Aucun événement dans cette période.")
        return

    print(f"\n{len(events)} événement(s) :")
    for ev in events:
        rec = RECURRENCE_LABELS.get(ev.get("recurrence", "none"), "")
        rec_str = f" | {rec}" if rec else ""
        print(f"  [{ev['id']}] {ev['title']} — {ev['occurrence_date_fr']}{rec_str}")


def _cli_delete(args):
    """CLI: events.py delete --id N"""
    event_id = None
    for i, a in enumerate(args):
        if a == "--id" and i + 1 < len(args):
            event_id = int(args[i + 1])

    if event_id is None:
        print("Usage : python3 events.py delete --id <event_id>")
        return

    if delete_event(event_id):
        print(f"Événement {event_id} supprimé.")
    else:
        print(f"Événement {event_id} introuvable.")


def main():
    args = sys.argv[1:]

    if not args:
        print("Usage :")
        print("  python3 events.py add \"Titre\" --date YYYY-MM-DD [options]")
        print("  python3 events.py upcoming [--week|--month|--year]")
        print("  python3 events.py list [--from YYYY-MM-DD] [--to YYYY-MM-DD]")
        print("  python3 events.py delete --id <N>")
        return

    cmd = args[0]
    rest = args[1:]

    if cmd == "add":
        _cli_add(rest)
    elif cmd == "upcoming":
        _cli_upcoming(rest)
    elif cmd == "list":
        _cli_list(rest)
    elif cmd == "delete":
        _cli_delete(rest)
    else:
        print(f"Commande inconnue : {cmd}")
        print("Commandes : add, upcoming, list, delete")


if __name__ == "__main__":
    main()
