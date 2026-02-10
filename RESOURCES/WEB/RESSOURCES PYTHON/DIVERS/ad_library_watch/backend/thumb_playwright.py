from __future__ import annotations

from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright


def _pick_largest_img(page) -> Optional[str]:
    # Renvoie le src de l'image la plus "grande" (bbox max)
    imgs = page.query_selector_all("img")
    best = None
    best_area = 0

    for img in imgs:
        try:
            box = img.bounding_box()
            if not box:
                continue
            area = (box.get("width", 0) or 0) * (box.get("height", 0) or 0)
            if area > best_area:
                src = img.get_attribute("src") or ""
                if src:
                    best_area = area
                    best = src
        except Exception:
            continue

    return best


def render_snapshot_thumbnail(snapshot_url: str, out_dir: str | Path, ad_id: str, timeout_ms: int = 20000) -> Optional[str]:
    """
    Ouvre ad_snapshot_url avec Chromium, capture une miniature en PNG.
    Retourne le chemin du fichier local (string) ou None.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{ad_id}.png"

    # cache
    if out_path.exists() and out_path.stat().st_size > 0:
        return str(out_path)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 1280, "height": 720})
            page = ctx.new_page()

            page.goto(snapshot_url, wait_until="domcontentloaded", timeout=timeout_ms)
            # Laisse le temps au rendu
            page.wait_for_timeout(1200)

            # 1) si video poster existe, on screenshot la zone video
            vid = page.query_selector("video")
            if vid:
                try:
                    vid.scroll_into_view_if_needed()
                    page.wait_for_timeout(250)
                    vid.screenshot(path=str(out_path))
                    ctx.close()
                    browser.close()
                    return str(out_path)
                except Exception:
                    pass

            # 2) sinon, screenshot de l'image la plus grande
            src = _pick_largest_img(page)
            if src:
                img = page.query_selector(f'img[src="{src}"]')
                if img:
                    try:
                        img.scroll_into_view_if_needed()
                        page.wait_for_timeout(250)
                        img.screenshot(path=str(out_path))
                        ctx.close()
                        browser.close()
                        return str(out_path)
                    except Exception:
                        pass

            # 3) fallback: screenshot de la page (au moins tu vois l’annonce)
            page.screenshot(path=str(out_path), full_page=False)

            ctx.close()
            browser.close()
            return str(out_path)

    except Exception:
        return None
