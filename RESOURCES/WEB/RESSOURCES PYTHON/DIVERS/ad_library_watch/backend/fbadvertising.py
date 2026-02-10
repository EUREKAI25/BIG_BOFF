import requests
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
from backend.thumb_playwright import render_snapshot_thumbnail

GRAPH = "https://graph.facebook.com/v24.0/ads_archive"



def parse_date(s):
    return datetime.strptime(s[:10], "%Y-%m-%d").date() if s else None


def human_delta(start, end):
    r = relativedelta(end, start)
    return f"{r.years} ans {r.months} mois {r.days} jours", (end - start).days


def is_active(start, stop, today):
    if not start:
        return False
    if stop is None:
        return True
    return start <= today <= stop


def extract_image(snapshot_url):
    try:
        r = requests.get(
            snapshot_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]

        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]

        video = soup.find("video")
        if video and video.get("poster"):
            return video["poster"]

    except Exception:
        pass

    return None

def build_params(token: str, keyword: str, countries: list[str], limit: int):
    """
    IMPORTANT: Graph API attend ad_reached_countries en paramètres répétés.
    Exemple: ...&ad_reached_countries=FR&ad_reached_countries=BE
    """
    params = [
        ("access_token", token),
        ("search_terms", keyword),
        ("limit", str(int(limit))),
        ("fields", "id,page_name,ad_delivery_start_time,ad_delivery_stop_time,ad_snapshot_url"),
    ]
    for c in countries or []:
        c = (c or "").strip().upper()
        if c:
            params.append(("ad_reached_countries", c))
    return params


def extract_image(snapshot_url: str):
    """
    Tente d'extraire une image depuis la page snapshot (og:image > img > poster video).
    """
    try:
        r = requests.get(snapshot_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]

        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]

        video = soup.find("video")
        if video and video.get("poster"):
            return video["poster"]

    except Exception:
        return None

    return None


def collect_ads(
    token: str,
    keyword: str,
    countries: list[str],
    limit: int = 50,
    active_only: bool = True,
    version: str = "v24.0",
):
    """
    Collecte ads via Graph API ads_archive + pagination paging.next.
    Retour: liste de dicts enrichis (status, longevity_days, image_url).
    """
    graph = f"https://graph.facebook.com/{version}/ads_archive"

    url = graph
    params = build_params(token, keyword, countries, limit)

    ads = []
    while True:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        payload = r.json()

        for ad in payload.get("data", []):
            start = parse_date(ad.get("ad_delivery_start_time"))
            stop = parse_date(ad.get("ad_delivery_stop_time")) or date.today()
            if start:
                _, days = human_delta(start, stop)
            else:
                days = 0

            active = ad.get("ad_delivery_stop_time") in (None, "")
            if active_only and not active:
                continue

            ad["status"] = "ACTIVE" if active else "STOPPED"
            ad["longevity_days"] = days
            snap = ad.get("ad_snapshot_url") or ""
            ad["image_url"] = extract_image(snap) if snap else None

            ads.append(ad)
            if len(ads) >= int(limit):
                break

        if len(ads) >= int(limit):
            break

        next_url = payload.get("paging", {}).get("next")
        if not next_url:
            break
        url = next_url
        params = None

    return sorted(ads, key=lambda x: x.get("longevity_days", 0), reverse=True)
