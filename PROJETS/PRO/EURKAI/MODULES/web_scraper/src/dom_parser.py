"""
web_scraper.dom_parser
───────────────────────
Convertit un HTML brut en arbre DOM JSON sérialisable.
Utilise BeautifulSoup (lxml ou html.parser en fallback).
"""
from __future__ import annotations

from typing import Any


def html_to_dom(html: str) -> dict:
    """
    Parse le HTML et retourne un arbre DOM JSON.

    Structure de chaque nœud :
        {
            "type":     "element" | "text",
            "tag":      str,          # "div", "p", "img", …
            "attrs":    {key: value},
            "text":     str,          # texte direct (non récursif)
            "children": [node, …]
        }
    """
    try:
        from bs4 import BeautifulSoup, NavigableString, Tag, Comment
    except ImportError:
        return {"error": "beautifulsoup4 non installé", "html_length": len(html)}

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    def _node(el: Any) -> dict | None:
        # Commentaires HTML → ignorer
        if isinstance(el, Comment):
            return None
        # Nœud texte
        if isinstance(el, NavigableString):
            text = str(el).strip()
            if not text:
                return None
            return {"type": "text", "content": text}
        # Nœud élément
        if not isinstance(el, Tag):
            return None

        # Normaliser les attributs (certains sont des listes dans BS4)
        attrs: dict = {}
        for k, v in (el.attrs or {}).items():
            attrs[str(k)] = " ".join(v) if isinstance(v, list) else str(v)

        # Texte direct (sans descendre dans les enfants)
        direct_text = el.string
        node: dict = {
            "type":  "element",
            "tag":   el.name,
            "attrs": attrs,
        }
        if direct_text and direct_text.strip():
            node["text"] = direct_text.strip()

        children = []
        for child in el.children:
            c = _node(child)
            if c is not None:
                children.append(c)
        if children:
            node["children"] = children

        return node

    result = _node(soup)
    return result or {}


def extract_meta(html: str) -> dict:
    """
    Extrait les métadonnées de la page :
    title, description, og:*, canonical, charset, lang.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return {}

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    meta: dict = {}

    # Title
    title_tag = soup.find("title")
    if title_tag:
        meta["title"] = title_tag.get_text(strip=True)

    # Lang
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        meta["lang"] = html_tag["lang"]

    # Charset
    charset_tag = soup.find("meta", charset=True)
    if charset_tag:
        meta["charset"] = charset_tag["charset"]

    # Meta name tags
    for tag in soup.find_all("meta", attrs={"name": True, "content": True}):
        name = tag["name"].lower()
        if name in ("description", "keywords", "author", "robots", "viewport"):
            meta[name] = tag["content"]

    # Open Graph
    og: dict = {}
    for tag in soup.find_all("meta", property=lambda p: p and p.startswith("og:")):
        og[tag["property"][3:]] = tag.get("content", "")
    if og:
        meta["og"] = og

    # Canonical
    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        meta["canonical"] = canonical["href"]

    return meta
