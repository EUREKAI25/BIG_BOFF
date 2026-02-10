#!/usr/bin/env python3
"""
Meta Ad Library API MVP collector
- Query /ads_archive by keywords
- Outputs JSON with:
  - keyword
  - ad id, page_id, page_name
  - ad_snapshot_url
  - delivery start/stop + computed longevity_days
  - publisher_platforms
  - creative text fields if present
  - media_url (best-effort from snapshot og:image / og:video)
  - target_url (best-effort from snapshot outbound link)
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs, unquote

import requests


GRAPH_VERSION_DEFAULT = "v23.0"
ADS_ARCHIVE_ENDPOINT = "https://graph.facebook.com/{version}/ads_archive"
DEFAULT_TIMEOUT = 20


@dataclass
class Config:
    access_token: str
    graph_version: str = GRAPH_VERSION_DEFAULT
    reached_countries: List[str] = None
    ad_active_status: str = "ALL"  # ACTIVE | INACTIVE | ALL
    ad_type: str = "ALL"           # ALL | POLITICAL_AND_ISSUE_ADS etc. (optional)
    limit: int = 50                # API page size (not total)
    max_ads_per_keyword: int = 200 # stop after N ads per keyword
    sleep_s: float = 0.2           # gentle pacing


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_meta_time(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    # Meta often returns ISO 8601, sometimes with +0000, sometimes Z.
    # Try a couple of formats.
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    # Fallback: try to normalize Z
    try:
        if s.endswith("Z"):
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        return datetime.fromisoformat(s)
    except Exception:
        return None


def longevity_days(start: Optional[datetime], stop: Optional[datetime]) -> Optional[float]:
    if not start:
        return None
    end = stop or utcnow()
    delta = end - start
    return round(delta.total_seconds() / 86400.0, 3)


def http_get_json(url: str, params: Dict[str, Any], timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def http_get_text(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.text


def extract_og_media(html: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (media_type, media_url) best-effort from OpenGraph tags.
    media_type: 'image' | 'video' | None
    """
    # og:video has priority if present
    m = re.search(r'<meta[^>]+property=["\']og:video["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    if m:
        return ("video", m.group(1))

    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    if m:
        return ("image", m.group(1))

    return (None, None)


def extract_target_url(html: str) -> Optional[str]:
    """
    Best-effort extraction of an outbound destination.
    Common patterns:
      - l.facebook.com/l.php?u=<ENCODED_URL>
      - direct https links in CTA area
    We:
      1) look for l.php?u=
      2) fallback: first https:// link that isn't obviously Meta internal
    """
    # 1) l.facebook.com redirect
    m = re.search(r'https?://l\.facebook\.com/l\.php\?[^"\']*u=([^"&]+)', html, re.I)
    if m:
        try:
            return unquote(m.group(1))
        except Exception:
            return m.group(1)

    # 2) Sometimes link appears as href with encoded URL
    m = re.search(r'href=["\'](https?://l\.facebook\.com/l\.php\?[^"\']+)["\']', html, re.I)
    if m:
        try:
            parsed = urlparse(m.group(1))
            qs = parse_qs(parsed.query)
            if "u" in qs and qs["u"]:
                return unquote(qs["u"][0])
            return m.group(1)
        except Exception:
            return m.group(1)

    # 3) Fallback: pick a non-meta https link (very rough)
    candidates = re.findall(r'href=["\'](https?://[^"\']+)["\']', html, re.I)
    for url in candidates:
        host = urlparse(url).netloc.lower()
        if any(x in host for x in ["facebook.com", "fb.com", "instagram.com", "meta.com", "l.facebook.com"]):
            continue
        return url

    return None


def build_fields() -> str:
    """
    Keep this conservative. Graph will just omit fields that don't exist.
    """
    return ",".join([
        "id",
        "page_id",
        "page_name",
        "ad_snapshot_url",
        "ad_delivery_start_time",
        "ad_delivery_stop_time",
        "publisher_platforms",
        # Creative text arrays (often present)
        "ad_creative_bodies",
        "ad_creative_link_titles",
        "ad_creative_link_descriptions",
        "ad_creative_link_captions",
        # Some regions/ad types may include these:
        "impressions",
        "spend",
        "demographic_distribution",
    ])


def query_ads_for_keyword(cfg: Config, keyword: str) -> List[Dict[str, Any]]:
    url = ADS_ARCHIVE_ENDPOINT.format(version=cfg.graph_version)

    reached = cfg.reached_countries or ["IT"]  # default: Italy (change as needed)
    params = {
        "search_terms": keyword,
        "ad_reached_countries": json.dumps(reached),
        "ad_active_status": cfg.ad_active_status,
        "ad_type": cfg.ad_type,
        "fields": build_fields(),
        "limit": cfg.limit,
        "access_token": cfg.access_token,
    }

    out: List[Dict[str, Any]] = []
    next_url: Optional[str] = None

    while True:
        if next_url:
            data = http_get_json(next_url, params={})  # next_url already contains token & params
        else:
            data = http_get_json(url, params=params)

        items = data.get("data", [])
        for ad in items:
            ad["__keyword"] = keyword
            out.append(ad)
            if len(out) >= cfg.max_ads_per_keyword:
                return out

        paging = data.get("paging", {})
        next_url = paging.get("next")
        if not next_url:
            break

        time.sleep(cfg.sleep_s)

    return out


def enrich_from_snapshot(ad: Dict[str, Any]) -> Dict[str, Any]:
    snapshot = ad.get("ad_snapshot_url")
    if not snapshot:
        return ad

    try:
        html = http_get_text(snapshot)
    except Exception as e:
        ad["snapshot_fetch_error"] = str(e)
        return ad

    media_type, media_url = extract_og_media(html)
    target = extract_target_url(html)

    if media_url:
        ad["media_type"] = media_type
        ad["media_url"] = media_url
    if target:
        ad["target_url"] = target

    return ad


def normalize_output(ad: Dict[str, Any]) -> Dict[str, Any]:
    start = parse_meta_time(ad.get("ad_delivery_start_time"))
    stop = parse_meta_time(ad.get("ad_delivery_stop_time"))

    return {
        "keyword": ad.get("__keyword"),
        "library_id": ad.get("id"),
        "page_id": ad.get("page_id"),
        "page_name": ad.get("page_name"),
        "ad_snapshot_url": ad.get("ad_snapshot_url"),
        "publisher_platforms": ad.get("publisher_platforms"),
        "delivery_start_time_utc": start.isoformat() if start else None,
        "delivery_stop_time_utc": stop.isoformat() if stop else None,
        "longevity_days": longevity_days(start, stop),
        # Creative text (keep arrays as-is)
        "bodies": ad.get("ad_creative_bodies"),
        "link_titles": ad.get("ad_creative_link_titles"),
        "link_descriptions": ad.get("ad_creative_link_descriptions"),
        "link_captions": ad.get("ad_creative_link_captions"),
        # Optional transparency metrics (ranges/estimates depending on region/type)
        "impressions": ad.get("impressions"),
        "spend": ad.get("spend"),
        "demographic_distribution": ad.get("demographic_distribution"),
        # Snapshot-enriched (best-effort)
        "media_type": ad.get("media_type"),
        "media_url": ad.get("media_url"),   # = "imgurl" for images in your MVP
        "target_url": ad.get("target_url"),
        "errors": ad.get("snapshot_fetch_error"),
    }


def main() -> int:
    token = os.environ.get("META_ACCESS_TOKEN", "").strip()
    if not token:
        print("ERROR: set META_ACCESS_TOKEN env var", file=sys.stderr)
        return 2

    cfg = Config(
        access_token=token,
        graph_version=os.environ.get("META_GRAPH_VERSION", GRAPH_VERSION_DEFAULT),
        reached_countries=json.loads(os.environ.get("META_REACHED_COUNTRIES", '["IT"]')),
        ad_active_status=os.environ.get("META_AD_ACTIVE_STATUS", "ALL"),
        ad_type=os.environ.get("META_AD_TYPE", "ALL"),
        limit=int(os.environ.get("META_LIMIT", "50")),
        max_ads_per_keyword=int(os.environ.get("META_MAX_ADS_PER_KEYWORD", "80")),
        sleep_s=float(os.environ.get("META_SLEEP_S", "0.2")),
    )

    # ---- MVP keywords here ----
    keywords = [
        "law of attraction",
        "manifestation",
        "vision board",
        "future self",
    ]

    all_rows: List[Dict[str, Any]] = []
    for kw in keywords:
        ads = query_ads_for_keyword(cfg, kw)
        for ad in ads:
            # Best-effort: enrich with media_url and target_url by fetching snapshot page.
            ad = enrich_from_snapshot(ad)
            all_rows.append(normalize_output(ad))

    payload = {
        "generated_at_utc": utcnow().isoformat(),
        "graph_version": cfg.graph_version,
        "reached_countries": cfg.reached_countries,
        "ad_active_status": cfg.ad_active_status,
        "ad_type": cfg.ad_type,
        "count": len(all_rows),
        "data": all_rows,
    }

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
